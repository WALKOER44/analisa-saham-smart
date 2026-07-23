import sys
import os
import json
import time
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.telegram_bot import start_polling_background, send_message
from bot.notifier import check_real_time
from bot.formatter import format_market_pulse

LIVE_START = 9
LIVE_END = 16
BROADCAST_INTERVAL = 1800


def is_market_hours():
    now = datetime.now()
    return now.weekday() < 5 and LIVE_START <= now.hour < LIVE_END


def is_market_day():
    return datetime.now().weekday() < 5


def is_closing_moment(now):
    return is_market_day() and now.hour == LIVE_END and now.minute == 0


def is_silent_hours():
    now = datetime.now()
    if now.weekday() >= 5:
        return True
    return now.hour < LIVE_START or now.hour >= LIVE_END


def read_history():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "history.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def build_ihsg_data():
    try:
        import yfinance as yf
        ihsg = yf.Ticker("^JKSE").history(period="2d", interval="1d")
        if not ihsg.empty:
            c = float(ihsg["Close"].iloc[-1])
            p = float(ihsg["Close"].iloc[-2]) if len(ihsg) > 1 else c
            return {"price": round(c, 2), "change_pct": round((c - p) / p * 100, 2)}
    except:
        pass
    return None


def build_and_send(is_daily=False):
    history = read_history()
    if history:
        latest = history[-1]
        data = latest.get("data", [])
        ihsg = build_ihsg_data()
        msg = format_market_pulse(data, ihsg, is_daily=is_daily)
        send_message(msg)
        tag = "DAILY CLOSING" if is_daily else "30-min BROADCAST"
        print(f"[{tag}] Sent ({len(data)} stocks)")
        return True
    return False


def market_scheduler():
    last_broadcast = 0.0
    closing_sent_today = False
    closing_sent_date = None

    while True:
        try:
            now = datetime.now()
            today = now.date()

            if not is_market_day():
                closing_sent_today = False
                closing_sent_date = None
                time.sleep(120)
                continue

            if is_market_hours():
                closing_sent_today = False
                closing_sent_date = None
                now_ts = time.time()
                if now_ts - last_broadcast >= BROADCAST_INTERVAL:
                    build_and_send(is_daily=False)
                    last_broadcast = now_ts
                time.sleep(30)
                continue

            if is_closing_moment(now) and not closing_sent_today and today != closing_sent_date:
                build_and_send(is_daily=True)
                closing_sent_today = True
                closing_sent_date = today
                print("[SCHEDULER] Closing recap sent. Bot is now silent until 09:00 tomorrow.")
                time.sleep(60)
                continue

            time.sleep(60)

        except Exception as e:
            print(f"[SCHEDULER] Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    from config import IS_LOCAL

    if IS_LOCAL:
        print("=" * 55)
        print("  LOCAL MODE - Scheduler & Polling DISABLED")
        print("=" * 55)
        print("  IS_LOCAL=True terdeteksi.")
        print("  Background scheduler tidak dijalankan untuk")
        print("  menghindari bentrok/spam ke Telegram utama.")
        print("  Output akan dialihkan ke LLM lokal")
        print("  atau dicetak ke console.")
        print("=" * 55)
        print()
        print("  Jalankan analisis manual melalui:")
        print("    python app.py")
        print("=" * 55)
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[EXIT] Local mode stopped")
    else:
        print("=" * 55)
        print("  TELEGRAM BOT - SCHEDULER SAHAM")
        print("=" * 55)
        print(f"  Market hours: Senin-Jumat {LIVE_START}:00-{LIVE_END}:00 WIB")
        print(f"  Periodic update: setiap 30 menit (1 pesan gabungan)")
        print(f"  Closing recap: pukul {LIVE_END}:00 WIB (1x, lalu silent)")
        print(f"  Di luar jam pasar / weekend: TIDAK ada pesan")
        print(f"  Polling Telegram: aktif (termasuk /clear command)")
        print("=" * 55)

        t_polling = threading.Thread(target=start_polling_background, daemon=True, name="polling")
        t_polling.start()

        t_notifier = threading.Thread(target=check_real_time, daemon=True, name="notifier")
        t_notifier.start()
        print("[MAIN] Started notifier (internal state tracking, no per-stock alerts)")

        t_scheduler = threading.Thread(target=market_scheduler, daemon=True, name="scheduler")
        t_scheduler.start()
        print("[MAIN] Started market_scheduler (30-min broadcast + 16:00 closing recap)")

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[EXIT] Bot stopped")
