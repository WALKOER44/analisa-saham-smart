import time
import threading
from datetime import datetime
from utils.fetch_data import get_stock_data
from ai.analyzer import analyze_market
from utils.save_data import save_history
from utils.portfolio import add_trade
from bot.telegram_bot import send_message
from bot.notifier import check_real_time

LIVE_START = 9
LIVE_END = 16
INTERVAL_SECONDS = 30 * 60

def clean_symbol(sym):
    return sym.replace(".JK", "")

def format_message(sym, price, trend, signal, note):
    icon = "🟢" if signal == "BUY" else ("🔴" if signal == "SELL" else "⚪")
    return (
        f"{icon} [{sym}]\n"
        f"\U0001f4b0 Harga: {price}\n"
        f"\U0001f4c8 Status: {trend}\n"
        f"\U0001f4e2 Signal: {signal}\n"
        f"\U0001f525 Ket: {note}\n"
        f"\U0001f552 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

def run_analysis():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] Running analysis...")

    data = get_stock_data()
    if not data:
        print("[WARN] No data fetched")
        return []

    results = analyze_market(data)

    save_history(results)

    top3 = [r for r in results if r["is_top3"]]
    print(f"\n[TOP 3 RANKING]")
    for r in top3:
        c = clean_symbol(r["symbol"])
        print(f"  #{r['rank']} {c:6s} | {r['signal']:5s} | score={r['score']:+d} | {r['trend']:10s} | {r['note']}")

    for r in results:
        add_trade(r["symbol"], r["signal"], r["price"])
        c = clean_symbol(r["symbol"])
        flag = " ★" if r["is_top3"] else ""
        print(f"  {c:6s}{flag} | {r['signal']:5s} | score={r['score']:+d} | {r['trend']:10s} | {r['note']}")

    print(f"\n[DONE] {len(results)} stocks analyzed")
    return results

def is_market_hours():
    now = datetime.now()
    return LIVE_START <= now.hour < LIVE_END

def run():
    from config import IS_LOCAL

    mode_label = "LOCAL" if IS_LOCAL else "ONLINE"
    print("=" * 55)
    print("ANALISA SAHAM SMART - SISTEM SIGNAL CERDAS")
    print("=" * 55)
    if IS_LOCAL:
        print(f"Mode: LOCAL (console / local LLM, scheduler disabled)")
        print(f"Notifier: disabled (tidak ada spam ke Telegram)")
    else:
        print(f"Mode: ONLINE ({LIVE_START}:00-{LIVE_END}:00 / FINAL 1x)")
        print(f"Notifier: real-time tiap 60 detik (alert BUY kuat / SELL)")
    print("=" * 55)

    if not IS_LOCAL:
        notifier_thread = threading.Thread(target=check_real_time, daemon=True)
        notifier_thread.start()
        print("[MAIN] Real-time notifier started (background)\n")
    else:
        print("[LOCAL MODE] Notifier tidak dijalankan. Output ke console / local LLM.\n")

    if is_market_hours():
        print(f"[LIVE MODE] Market OPEN - every {INTERVAL_SECONDS // 60} min")
        run_analysis()
        while is_market_hours():
            print(f"[LIVE MODE] Next in {INTERVAL_SECONDS // 60} min...")
            time.sleep(INTERVAL_SECONDS)
            if is_market_hours():
                run_analysis()
        print("[LIVE MODE] Market closed. Final analysis...")
        run_analysis()
    else:
        print("[FINAL MODE] Market CLOSED - single run")
        run_analysis()

    print(f"\n[DONE] Analysis complete. (mode: {mode_label})")
    print("[DONE] Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[EXIT] System stopped")

if __name__ == "__main__":
    run()
