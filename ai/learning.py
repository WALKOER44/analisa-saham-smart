import json
from collections import defaultdict

def learn():
    try:
        with open("data/history.json") as f:
            history = json.load(f)
    except:
        return {}

    stats = defaultdict(lambda: {
        "buy_count": 0, "sell_count": 0,
        "total": 0, "avg_score": 0
    })

    for h in history:
        for s in h.get("data", []):
            sym = s["symbol"]
            stats[sym]["total"] += 1
            t = stats[sym]["total"]
            stats[sym]["avg_score"] = (stats[sym]["avg_score"] * (t - 1) + s.get("score", 0)) / t
            if s.get("signal") == "BUY":
                stats[sym]["buy_count"] += 1
            elif s.get("signal") == "SELL":
                stats[sym]["sell_count"] += 1

    result = {}
    for sym, v in stats.items():
        net = v["buy_count"] - v["sell_count"]
        result[sym] = {
            "total": v["total"],
            "avg_score": round(v["avg_score"], 2),
            "buy_signals": v["buy_count"],
            "sell_signals": v["sell_count"],
            "net_bias": net
        }

    return result
