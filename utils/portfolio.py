import json
from datetime import datetime

def add_trade(symbol, action, price):
    try:
        with open("data/portfolio.json") as f:
            data = json.load(f)
    except:
        data = []

    trade = {
        "symbol": symbol,
        "action": action,
        "price": price,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    existing = [i for i, d in enumerate(data) if d.get("symbol") == symbol]
    if existing:
        for idx in reversed(existing):
            data.pop(idx)

    data.append(trade)

    with open("data/portfolio.json", "w") as f:
        json.dump(data, f, indent=4)
