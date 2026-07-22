import sys
import os
import time
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.server import app, send_telegram_message, generate_daily_summary, get_aggregated_news
from utils.fetch_data import get_stock_data
from ai.analyzer import analyze_market
from utils.save_data import save_history
from utils.portfolio import add_trade

LIVE_START = 9
LIVE_END = 16

def is_market_hours():
    now = datetime.now()
    return now.weekday() < 5 and LIVE_START <= now.hour < LIVE_END

def clean_symbol(sym):
    return sym.replace(".JK", "")

def format_telegram_broadcast(results, ihsg_data=None):
    top3 = sorted([r for r in results if r.get("is_top3")], key=lambda x: x.get("rank", 99))
    gainers = sorted(results, key=lambda x: x.get("change_pct", 0), reverse=True)[:3]
    losers = sorted(results, key=lambda x: x.get("change_pct", 0))[:3]
    now = datetime.now()

    lines = [f"\U0001f4e1 **Update Pasar 5 Menit** ({now.strftime('%H:%M WIB')})"]
    if ihsg_data:
        arrow = "\U0001f7e2" if ihsg_data.get("change_pct", 0) >= 0 else "\U0001f534"
        lines.append(f"{arrow} IHSG: {ihsg_data.get('price', 0):,.0f} ({ihsg_data['change_pct']:+.2f}%)")
    lines.append("")

    if gainers:
        lines.append("\U0001f4c8 **Top Gainers:**")
        for r in gainers:
            sym = clean_symbol(r["symbol"])
            lines.append(f"\u2022 {sym}: +{r['change_pct']:.2f}% ({r['signal']})")
    if losers:
        lines.append("\U0001f4c9 **Top Losers:**")
        for r in losers:
            sym = clean_symbol(r["symbol"])
            lines.append(f"\u2022 {sym}: {r['change_pct']:.2f}% ({r['signal']})")

    signal_changes = [r for r in results if r.get("signal") in ("BUY", "SELL")]
    if signal_changes:
        lines.append("")
        lines.append("\U0001f6a8 **Alert Sinyal:**")
        for r in signal_changes[:5]:
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

def run_analysis_once():
    if not is_market_hours():
        print(f"[UPDATER] Market CLOSED - skipping fetch")
        return None
    data = get_stock_data()
    if not data:
        print(f"[UPDATER] No data fetched")
        return None
    results = analyze_market(data)
    save_history(results)
    for r in results:
        add_trade(r["symbol"], r["signal"], r["price"])
    print(f"[UPDATER] {datetime.now().strftime('%H:%M:%S')} - {len(results)} stocks updated")
    return results

def real_time_updater():
    print(f"[UPDATER] Force fetch data saat server start...")
    run_analysis_once()
    while True:
        try:
            if is_market_hours():
                run_analysis_once()
            else:
                time.sleep(60)
                continue
        except Exception as e:
            print(f"[30s-UPDATER] Error: {e}")
        time.sleep(30)

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

def do_telegram_broadcast():
    from web.server import read_history
    history = read_history()
    if not history:
        print(f"[TELEGRAM-5MIN] No history data available")
        return
    latest = history[-1]
    data = latest.get("data", [])
    ihsg_data = build_ihsg_data()
    msg = format_telegram_broadcast(data, ihsg_data)
    send_telegram_message(msg)
    now = datetime.now()
    print(f"[TELEGRAM-5MIN] Broadcast sent at {now.strftime('%H:%M')} - {len(data)} stocks, {sum(1 for d in data if d.get('signal') in ('BUY','SELL'))} sinyal")

def telegram_broadcaster():
    print(f"[TELEGRAM] Force broadcast saat server start...")
    if is_market_hours():
        do_telegram_broadcast()
    last_broadcast = time.time()
    while True:
        try:
            now = datetime.now()
            if is_market_hours():
                elapsed = time.time() - last_broadcast
                if elapsed >= 300:
                    do_telegram_broadcast()
                    last_broadcast = time.time()
                time.sleep(30)
            else:
                last_broadcast = 0
                time.sleep(60)
        except Exception as e:
            print(f"[TELEGRAM-5MIN] Error: {e}")
            time.sleep(30)

def daily_summary_scheduler():
    print(f"[DAILY-SUMMARY] Scheduler started - akan kirim otomatis jam 16:05 WIB")
    while True:
        try:
            now = datetime.now()
            is_weekday = now.weekday() < 5
            target_hour, target_min = 16, 5
            if is_weekday and now.hour == target_hour and target_min <= now.minute < target_min + 5:
                from web.server import DAILY_SUMMARY_CACHE
                today = now.strftime("%Y-%m-%d")
                if DAILY_SUMMARY_CACHE.get("date") != today or not DAILY_SUMMARY_CACHE.get("generated"):
                    print(f"[DAILY-SUMMARY] Generating closing report for {today}...")
                    summary = generate_daily_summary()
                    if summary:
                        send_telegram_message(summary)
                        print(f"[DAILY-SUMMARY] Report sent to Telegram at {now.strftime('%H:%M')}")
                time.sleep(300)
            else:
                time.sleep(30)
        except Exception as e:
            print(f"[DAILY-SUMMARY] Error: {e}")
            time.sleep(30)

def force_initial_fetch():
    print(f"[INIT] Melakukan fetch data awal...")
    results = run_analysis_once()
    if results and is_market_hours():
        ihsg_data = build_ihsg_data()
        msg = format_telegram_broadcast(results, ihsg_data)
        send_telegram_message(msg)
        print(f"[INIT] Broadcast awal terkirim ke Telegram")
    print(f"[INIT] Data awal siap. Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

_threads_started = False
def start_background_scheduler(force_broadcast=True):
    global _threads_started
    if _threads_started:
        return
    _threads_started = True
    print("=" * 55)
    print("  ANALISA SAHAM SMART - FULL SERVER + SCHEDULER")
    print("=" * 55)
    print(f"  Market hours: {LIVE_START}:00 - {LIVE_END}:00 WIB (weekdays)")
    print(f"  Real-time fetch: every 30s during market hours")
    print(f"  Telegram broadcast: every 5 min during market hours")
    print(f"  Daily closing summary: at {LIVE_END}:05 WIB")
    print("=" * 55)
    if force_broadcast:
        force_initial_fetch()
    threads = [
        threading.Thread(target=real_time_updater, daemon=True, name="rt-updater"),
        threading.Thread(target=telegram_broadcaster, daemon=True, name="tg-broadcaster"),
        threading.Thread(target=daily_summary_scheduler, daemon=True, name="daily-summary"),
    ]
    for t in threads:
        t.start()
        print(f"[MAIN] Started {t.name}")

start_background_scheduler()

if __name__ == "__main__":
    print(f"[MAIN] Starting Flask development server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
