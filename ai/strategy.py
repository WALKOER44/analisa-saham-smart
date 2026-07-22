import math

def calculate_entry_exit(price, atr_val=0):
    if math.isnan(price) or price <= 0:
        return 0, 0, 0, 0
    if atr_val and atr_val > 0 and price > 0:
        atr_pct = atr_val / price
        if atr_pct < 0.01:
            atr_pct = 0.02
        elif atr_pct > 0.05:
            atr_pct = 0.05
        buy = round(price * (1 - atr_pct * 0.5))
        sell = round(price * (1 + atr_pct * 2.0))
        sl = round(price * (1 - atr_pct * 1.5))
    else:
        buy = round(price * 0.98)
        sell = round(price * 1.04)
        sl = round(price * 0.96)
    rr = round((sell - price) / (price - sl), 2) if price - sl > 0 else 0
    return buy, sell, sl, rr
