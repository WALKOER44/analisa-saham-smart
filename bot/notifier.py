import json
import time
from datetime import datetime
from utils.fetch_data import get_stock_data
from ai.analyzer import analyze_market
from utils.save_data import save_history
from utils.portfolio import add_trade
from bot.telegram_bot import send_message

LAST_STATE_FILE = "data/last_state.json"
POLL_INTERVAL = 30
LIVE_START = 9
LIVE_END = 16


def is_market_hours():
    now = datetime.now()
    return now.weekday() < 5 and LIVE_START <= now.hour < LIVE_END


def load_last_state():
    try:
        with open(LAST_STATE_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_last_state(state):
    with open(LAST_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def clean_symbol(sym):
    return sym.replace(".JK", "")


def format_alert(sym, signal, price, trend, note, score, reasoning=""):
    icon = "\U0001f7e2" if signal == "BUY" else ("\U0001f534" if signal == "SELL" else "\u26aa")
    msg = (
        f"{icon} *[{sym}]*\n"
        f"\U0001f4b0 Harga: Rp{price:,.0f}\n"
        f"\U0001f4c8 Trend: {trend}\n"
        f"\U0001f4e2 Signal: *{signal}*\n"
        f"\U0001f525 {note} (score: {score:+d})\n"
        f"\U0001f552 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    if reasoning:
        msg += f"\n\U0001f4ac {reasoning[:120]}"
    return msg


def format_top3(top3):
    lines = ["\U0001f3c6 *TOP 3 Rekomendasi*"]
    for r in top3:
        icon = "\U0001f7e2" if r["signal"] == "BUY" else "\U0001f534" if r["signal"] == "SELL" else "\u26aa"
        lines.append(f"{icon} #{r['rank']} {clean_symbol(r['symbol'])} \u2014 {r['signal']} ({r['score']:+d}) | {r['note']}")
    return "\n".join(lines)


def check_real_time():
    print("[NOTIFIER] Real-time check started")
    prev = load_last_state()

    while True:
        try:
            data = get_stock_data()
            if not data:
                time.sleep(POLL_INTERVAL)
                continue

            results = analyze_market(data)
            save_history(results)

            market_open = is_market_hours()

            for r in results:
                sym = r["symbol"]
                clean = clean_symbol(sym)
                signal = r["signal"]
                score = r["score"]
                old = prev.get(sym, {})

                if market_open:
                    old_signal = old.get("signal", "HOLD")
                    old_score = old.get("score", 0)

                    should_alert = False
                    if signal != old_signal:
                        should_alert = True
                    elif signal == old_signal and old.get("signal") != "HOLD":
                        if score != old_score:
                            should_alert = True

                    if should_alert:
                        msg = format_alert(clean, signal, r["price"], r["trend"], r["note"], score, r.get("reasoning", ""))
                        send_message(msg)
                        print(f"[NOTIFIER] Alert {clean}: {signal} (score {score:+d})")

                prev[sym] = {
                    "signal": signal,
                    "price": r["price"],
                    "score": score,
                    "trend": r["trend"],
                    "note": r["note"],
                    "reasoning": r.get("reasoning", ""),
                    "time": datetime.now().isoformat()
                }
                add_trade(sym, signal, r["price"])

            if market_open:
                new_top3 = sorted([r for r in results if r["is_top3"]], key=lambda x: x["rank"])
                old_top3_sigs = prev.get("_top3", [])
                new_top3_sigs = [(r["symbol"], r["signal"], r["score"]) for r in new_top3]

                if new_top3_sigs != old_top3_sigs:
                    msg = format_top3(new_top3)
                    send_message(msg)
                    print("[NOTIFIER] TOP 3 updated")
                    prev["_top3"] = new_top3_sigs

            save_last_state(prev)

        except Exception as e:
            print(f"[NOTIFIER] Error: {e}")

        time.sleep(POLL_INTERVAL)
