import asyncio
import json
import logging
import requests
from config import TOKEN, IS_LOCAL, LOCAL_LLM_ENDPOINT, LOCAL_LLM_MODEL

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


def send_to_local_llm(msg):
    """Kirim pesan ke LLM lokal (Ollama / LM Studio / OpenAI-compatible) untuk diproses."""
    prompt = (
        "Berikut adalah hasil analisis saham otomatis. "
        "Buat ringkasan dalam bahasa Indonesia yang informatif dan mudah dibaca:\n\n"
        f"{msg}"
    )

    try:
        # Ollama format
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

    # Fallback: print ke console
    print("\n" + "-" * 55)
    print(msg)
    print("-" * 55 + "\n")
    return msg


def send_message(msg, chat_id=None):
    from config import CHAT_ID

    # Local mode: arahkan ke LLM lokal, jangan kirim ke Telegram
    if IS_LOCAL:
        return send_to_local_llm(msg)

    # Online mode: kirim ke Telegram seperti biasa
    targets = [chat_id] if chat_id else [cid.strip() for cid in str(CHAT_ID).split(",") if cid.strip()]
    if not targets:
        return
    for cid in targets:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": cid, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            print(f"[TELEGRAM] Error sending to {cid}: {e}")


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
            "/status - Status sistem"
        )

    async def cmd_status(update, context):
        await update.message.reply_text("\u2705 Bot aktif dan berjalan.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
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
