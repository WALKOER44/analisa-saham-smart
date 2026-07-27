import asyncio
import json
import logging
import os
import requests
from config import TOKEN, IS_LOCAL, LOCAL_LLM_ENDPOINT, LOCAL_LLM_MODEL, OWNER_ID

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

MESSAGE_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "message_log.json"
)


def _load_message_log():
    try:
        with open(MESSAGE_LOG_PATH) as f:
            return json.load(f)
    except:
        return {}


def _save_message_log(log):
    os.makedirs(os.path.dirname(MESSAGE_LOG_PATH), exist_ok=True)
    with open(MESSAGE_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def send_to_local_llm(msg):
    """Kirim pesan ke LLM lokal (Ollama / LM Studio / OpenAI-compatible) untuk diproses."""
    prompt = (
        "Berikut adalah hasil analisis saham otomatis. "
        "Buat ringkasan dalam bahasa Indonesia yang informatif dan mudah dibaca:\n\n"
        f"{msg}"
    )

    try:
        resp = requests.post(
            f"{LOCAL_LLM_ENDPOINT}/api/generate",
            json={
                "model": LOCAL_LLM_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        if resp.status_code == 200:
            result = resp.json()
            response_text = result.get("response", "")
            print("\n" + "=" * 55)
            print("  [LOCAL LLM] Response:")
            print(response_text)
            print("=" * 55 + "\n")
            return response_text
        else:
            print(f"[LOCAL LLM] HTTP {resp.status_code}: {resp.text}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"[LOCAL LLM] Gagal terhubung ke {LOCAL_LLM_ENDPOINT}. Pastikan Ollama/LM Studio berjalan.")
        print("[LOCAL LLM] Fallback: output dicetak ke console saja.")
        print("\n" + "-" * 55)
        print(msg)
        print("-" * 55 + "\n")
    except Exception as e:
        print(f"[LOCAL LLM] Error: {e}")

    print("\n" + "-" * 55)
    print(msg)
    print("-" * 55 + "\n")
    return msg


def send_message(msg, chat_id=None):
    from config import CHAT_ID

    if IS_LOCAL:
        return send_to_local_llm(msg)

    targets = [chat_id] if chat_id else [cid.strip() for cid in str(CHAT_ID).split(",") if cid.strip()]
    if not targets:
        return

    log = _load_message_log()

    max_len = 4096

    def _send_single(cid, text):
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            resp = requests.post(url, data={"chat_id": cid, "text": text, "parse_mode": "Markdown"}, timeout=10)
            if resp.ok:
                result = resp.json()
                msg_id = result.get("result", {}).get("message_id")
                if msg_id:
                    key = str(cid)
                    if key not in log:
                        log[key] = []
                    log[key].append(msg_id)
                    _save_message_log(log)
        except Exception as e:
            print(f"[TELEGRAM] Error sending to {cid}: {e}")

    for cid in targets:
        if len(msg) <= max_len:
            _send_single(cid, msg)
        else:
            parts = [msg[i:i+max_len] for i in range(0, len(msg), max_len)]
            for part in parts:
                _send_single(cid, part)


def get_chat_owner_and_admins(chat_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatAdministrators"
        resp = requests.post(url, data={"chat_id": chat_id}, timeout=10)
        if resp.ok:
            result = resp.json()
            owner_id = None
            admin_ids = []
            for admin in result.get("result", []):
                uid = admin["user"]["id"]
                status = admin.get("status", "")
                if status == "creator":
                    owner_id = uid
                admin_ids.append(uid)
            return owner_id, admin_ids
    except Exception as e:
        print(f"[TELEGRAM] Error getting admins: {e}")
    return None, []


def is_authorized_admin(chat_id, user_id):
    owner_id, admin_ids = get_chat_owner_and_admins(chat_id)
    if user_id == owner_id:
        return True
    if user_id in admin_ids:
        return True
    if OWNER_ID and str(user_id) == OWNER_ID:
        return True
    return False


def delete_bot_messages(chat_id):
    log = _load_message_log()
    key = str(chat_id)
    deleted = 0
    if key not in log:
        return 0
    for msg_id in log[key]:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
            resp = requests.post(url, data={"chat_id": chat_id, "message_id": msg_id}, timeout=10)
            if resp.ok:
                deleted += 1
        except:
            pass
    log[key] = []
    _save_message_log(log)
    return deleted


def _build_application():
    from telegram.ext import Application, CommandHandler

    async def cmd_start(update, context):
        await update.message.reply_text(
            "\U0001f4e1 Bot Analisa Saham berjalan!\n"
            "Kirim /help untuk daftar perintah."
        )

    async def cmd_help(update, context):
        await update.message.reply_text(
            "/start - Mulai bot\n"
            "/help - Bantuan ini\n"
            "/status - Status sistem\n"
            "/clear - Hapus semua pesan bot (Admin/Owner saja)"
        )

    async def cmd_status(update, context):
        await update.message.reply_text("\u2705 Bot aktif dan berjalan.")

    async def cmd_clear(update, context):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        if not is_authorized_admin(chat_id, user_id):
            await update.message.reply_text(
                "\u26a0\ufe0f Akses ditolak. Hanya Owner / Creator / Admin grup yang dapat menggunakan perintah ini."
            )
            return

        count = delete_bot_messages(chat_id)
        msg = await update.message.reply_text(
            f"\u2705 Berhasil menghapus {count} pesan bot."
        )

        await asyncio.sleep(5)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
            await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
        except:
            pass

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("clear", cmd_clear))
    return app


def run_polling():
    _build_application().run_polling(allowed_updates=["message"])


def start_polling_background():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = _build_application()

    try:
        loop.run_until_complete(app.initialize())
        loop.run_until_complete(app.start())
        loop.run_until_complete(app.updater.start_polling(allowed_updates=["message"]))
        print("[TELEGRAM-BOT] Polling started (background)")
        loop.run_forever()
    except Exception as e:
        print(f"[TELEGRAM-BOT] Fatal error: {e}")
        logging.exception(e)
    finally:
        try:
            loop.run_until_complete(app.updater.stop())
            loop.run_until_complete(app.stop())
            loop.run_until_complete(app.shutdown())
        except:
            pass


if __name__ == "__main__":
    run_polling()
