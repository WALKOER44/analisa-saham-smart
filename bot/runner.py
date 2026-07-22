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


def is_market_hours():
    now = datetime.now()
    return now.weekday() < 5 and LIVE_START <= now.hour < LIVE_END


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


def telegram_broadcaster():
    last_broadcast = 0
    while True:
        try:
            if is_market_hours():
                if time.time() - last_broadcast >= 300:
                    history = read_history()
                    if history:
                        latest = history[-1]
                        data = latest.get("data", [])
                        ihsg = build_ihsg_data()
                        msg = format_market_pulse(data, ihsg, is_daily=False)
                        send_message(msg)
                        print(f"[BROADCASTER] 5-min update sent ({len(data)} stocks)")
                        last_broadcast = time.time()
                time.sleep(30)
            else:
                last_broadcast = 0
                time.sleep(60)
        except Exception as e:
            print(f"[BROADCASTER] Error: {e}")
            time.sleep(30)


def daily_summary_scheduler():
    while True:
        try:
            now = datetime.now()
            if now.weekday() < 5 and now.hour == 16 and now.minute == 5:
                history = read_history()
                if history:
                    latest = history[-1]
                    data = latest.get("data", [])
                    ihsg = build_ihsg_data()
                    msg = format_market_pulse(data, ihsg, is_daily=True)
                    send_message(msg)
                    print(f"[DAILY] Closing report sent")
                time.sleep(300)
            time.sleep(30)
        except Exception as e:
            print(f"[DAILY] Error: {e}")
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
        # Keep process alive for local testing
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[EXIT] Local mode stopped")
    else:
        print("=" * 55)
        print("  TELEGRAM BOT - ALL SERVICES (ONLINE MODE)")
        print("=" * 55)
        print(f"  Market hours: {LIVE_START}:00-{LIVE_END}:00 WIB (weekdays)")
        print(f"  Signal notifier: real-time (30s)")
        print(f"  Market broadcast: every 5 min during market hours")
        print(f"  Daily summary: at {LIVE_END}:05 WIB")
        print("=" * 55)

        t_polling = threading.Thread(target=start_polling_background, daemon=True, name="polling")
        t_polling.start()

        services = [
            threading.Thread(target=check_real_time, daemon=True, name="notifier"),
            threading.Thread(target=telegram_broadcaster, daemon=True, name="broadcaster"),
            threading.Thread(target=daily_summary_scheduler, daemon=True, name="daily-summary"),
        ]
        for t in services:
            t.start()
            print(f"[MAIN] Started {t.name}")

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[EXIT] Bot stopped")
