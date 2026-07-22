import sys
import os
import json
import time
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.telegram_bot import run_polling, send_message
from bot.notifier import check_real_time

LIVE_START = 9
LIVE_END = 16


def is_market_hours():
    now = datetime.now()
    return now.weekday() < 5 and LIVE_START <= now.hour < LIVE_END


def clean_symbol(sym):
    return sym.replace(".JK", "")


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


def format_broadcast(data, ihsg_data=None):
    gainers = sorted(data, key=lambda x: x.get("change_pct", 0), reverse=True)[:3]
    losers = sorted(data, key=lambda x: x.get("change_pct", 0))[:3]
    top3 = sorted([r for r in data if r.get("is_top3")], key=lambda x: x.get("rank", 99))
    now = datetime.now()

    lines = [f"\U0001f4e1 **Update Pasar 5 Menit** ({now.strftime('%H:%M WIB')})"]
    if ihsg_data:
        arrow = "\U0001f7e2" if ihsg_data.get("change_pct", 0) >= 0 else "\U0001f534"
        lines.append(f"{arrow} IHSG: {ihsg_data.get('price', 0):,.0f} ({ihsg_data['change_pct']:+.2f}%)")
    lines.append("")

    if gainers:
        lines.append("\U0001f4c8 **Top Gainers:**")
        for r in gainers:
            lines.append(f"\u2022 {clean_symbol(r['symbol'])}: +{r['change_pct']:.2f}% ({r['signal']})")
    if losers:
        lines.append("\U0001f4c9 **Top Losers:**")
        for r in losers:
            lines.append(f"\u2022 {clean_symbol(r['symbol'])}: {r['change_pct']:.2f}% ({r['signal']})")

    signals = [r for r in data if r.get("signal") in ("BUY", "SELL")]
    if signals:
        lines.append("")
        lines.append("\U0001f6a8 **Alert Sinyal:**")
        for r in signals[:5]:
            sym = clean_symbol(r["symbol"])
            icon = "\U0001f7e2" if r["signal"] == "BUY" else "\U0001f534"
            lines.append(f"{icon} {sym}: **{r['signal']}** (skor: {r['score']:+d})")

    if top3:
        lines.append("")
        lines.append("\U0001f3c6 **TOP 3 Rekomendasi:**")
        for r in top3:
            sym = clean_symbol(r["symbol"])
            lines.append(f"\u2022 #{r['rank']} {sym}: **{r['signal']}** | Skor {r['score']:+d} | {r['note']}")

    return "\n".join(lines)


def format_daily_summary(data, ihsg_data):
    now = datetime.now()
    gainers = sorted(data, key=lambda x: x.get("change_pct", 0), reverse=True)[:3]
    losers = sorted(data, key=lambda x: x.get("change_pct", 0))[:3]
    top3 = sorted([r for r in data if r.get("is_top3")], key=lambda x: x.get("score", 0), reverse=True)

    lines = [f"\U0001f4ca **RINGKASAN PENUTUPAN PASAR HARIAN**"]
    lines.append(f"\U0001f5d3 {now.strftime('%d %B %Y')}")
    lines.append("")
    lines.append("\U0001f4c8 **Performa IHSG:**")
    if ihsg_data:
        arrow = "\U0001f7e2" if ihsg_data["change_pct"] >= 0 else "\U0001f534"
        lines.append(f"{arrow} IHSG: {ihsg_data['price']:,.0f} ({ihsg_data['change_pct']:+.2f}%)")
    lines.append("")

    lines.append("\U0001f4c8 **Performa Saham:**")
    for r in gainers:
        sym = clean_symbol(r["symbol"])
        lines.append(f"\u2022 {sym}: Naik {r['change_pct']:+.2f}% (skor: {r['score']:+d})")
    for r in losers:
        sym = clean_symbol(r["symbol"])
        lines.append(f"\u2022 {sym}: Turun {r['change_pct']:+.2f}% (skor: {r['score']:+d})")
    lines.append("")

    lines.append("\U0001f4a1 **Rekomendasi:**")
    if top3:
        for r in top3[:3]:
            sym = clean_symbol(r["symbol"])
            lines.append(f"\u2022 {sym}: **{r['signal']}** | {r['note']}")
    else:
        lines.append("\u2022 Belum ada rekomendasi.")

    bullish = sum(1 for d in data if d.get("change_pct", 0) > 0)
    bearish = sum(1 for d in data if d.get("change_pct", 0) < 0)
    lines.append("")
    lines.append("\U0001f52e **Proyeksi:**")
    trend = "bullish" if bullish > bearish else "bearish"
    lines.append(f"Sentimen {trend} ({bullish} naik vs {bearish} turun).")

    return "\n".join(lines)


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
                        msg = format_broadcast(data, ihsg)
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
                    msg = format_daily_summary(data, ihsg)
                    send_message(msg)
                    print(f"[DAILY] Closing report sent")
                time.sleep(300)
            time.sleep(30)
        except Exception as e:
            print(f"[DAILY] Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    print("=" * 55)
    print("  TELEGRAM BOT - ALL SERVICES")
    print("=" * 55)
    print(f"  Market hours: {LIVE_START}:00-{LIVE_END}:00 WIB (weekdays)")
    print(f"  Signal notifier: real-time (30s)")
    print(f"  Market broadcast: every 5 min during market hours")
    print(f"  Daily summary: at {LIVE_END}:05 WIB")
    print("=" * 55)

    t_polling = threading.Thread(target=run_polling, daemon=True, name="polling")
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
