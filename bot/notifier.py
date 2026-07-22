import json
import time
from datetime import datetime
from utils.fetch_data import get_stock_data
from ai.analyzer import analyze_market
from utils.save_data import save_history
from utils.portfolio import add_trade

LAST_STATE_FILE = "data/last_state.json"
POLL_INTERVAL = 30


def load_last_state():
    try:
        with open(LAST_STATE_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_last_state(state):
    with open(LAST_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def check_real_time():
    print("[NOTIFIER] Real-time internal tracker started (no per-stock alerts)")
    prev = load_last_state()

    while True:
        try:
            data = get_stock_data()
            if not data:
                time.sleep(POLL_INTERVAL)
                continue

            results = analyze_market(data)
            save_history(results)

            for r in results:
                sym = r["symbol"]
                signal = r["signal"]
                score = r["score"]

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

            save_last_state(prev)

        except Exception as e:
            print(f"[NOTIFIER] Error: {e}")

        time.sleep(POLL_INTERVAL)
