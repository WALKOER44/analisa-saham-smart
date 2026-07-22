import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.telegram_bot import run_polling

if __name__ == "__main__":
    print("=" * 50)
    print("  TELEGRAM BOT - CONTINUOUS POLLING")
    print("=" * 50)
    run_polling()
