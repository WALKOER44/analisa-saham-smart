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

        if is_daily:
            try:
                ihsg_save = ihsg or {}
                gainers = sorted(data, key=lambda x: x.get("change_pct", 0), reverse=True)[:3]
                losers = sorted(data, key=lambda x: x.get("change_pct", 0))[:3]
                top3 = sorted([r for r in data if r.get("is_top3")], key=lambda x: x.get("score", 0), reverse=True)
                summary_entry = {
                    "text": msg,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "generated": True,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "data": data,
                    "ihsg": ihsg_save,
                    "gainers": gainers,
                    "losers": losers,
                    "top3": top3
                }
                summary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "daily_summary.json")
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(summary_entry, f, ensure_ascii=False, indent=2)
                print(f"[{tag}] Daily summary saved to data/daily_summary.json")
            except Exception as e:
                print(f"[{tag}] Failed to save daily summary: {e}")

        return True
    return False


def market_scheduler():
    last_broadcast = 0.0
    closing_sent_date = None

    while True:
        try:
            now = datetime.now()
            today = now.date()
            weekday = now.weekday()
            hour = now.hour

            is_weekday = weekday < 5

            if not is_weekday:
                closing_sent_date = None
                time.sleep(120)
                continue

            is_open = LIVE_START <= hour < LIVE_END
            is_past_close = hour >= LIVE_END

            if is_open:
                now_ts = time.time()
                if now_ts - last_broadcast >= BROADCAST_INTERVAL:
                    build_and_send(is_daily=False)
                    last_broadcast = now_ts
                time.sleep(30)
                continue

            if is_past_close and closing_sent_date != today:
                build_and_send(is_daily=True)
                closing_sent_date = today
                print(f"[SCHEDULER] Closing recap sent for {today}. Silent until next market day.")
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
