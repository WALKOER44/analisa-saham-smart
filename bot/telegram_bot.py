import logging
import requests
from config import TOKEN

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


def send_message(msg, chat_id=None):
    from config import CHAT_ID
    targets = [chat_id] if chat_id else [cid.strip() for cid in str(CHAT_ID).split(",") if cid.strip()]
    if not targets:
        return
    for cid in targets:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": cid, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            print(f"[TELEGRAM] Error sending to {cid}: {e}")


def run_polling():
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

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("status", cmd_status))

    print("[TELEGRAM-BOT] Starting polling...")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    run_polling()
