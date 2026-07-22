import json
from datetime import datetime, timedelta

MAX_ENTRIES = 500

def save_history(results):
    try:
        with open("data/history.json", encoding="utf-8") as f:
            history = json.load(f)
    except:
        history = []

    now = datetime.now()
    entry = {
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "data": results
    }

    if history:
        last = history[-1]
        last_time = datetime.strptime(last["time"], "%Y-%m-%d %H:%M:%S")
        if now - last_time < timedelta(minutes=10):
            same = True
            for a, b in zip(last["data"], results):
                if a.get("signal") != b.get("signal") or a.get("symbol") != b.get("symbol"):
                    same = False
                    break
            if same:
                return

    history.append(entry)

    if len(history) > MAX_ENTRIES:
        history = history[-MAX_ENTRIES:]

    with open("data/history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)
