def detect_doji(open_prices, close_prices, threshold=0.01):
    if not open_prices or not close_prices:
        return False
    o = open_prices[-1]
    c = close_prices[-1]
    body = abs(c - o)
    if body == 0:
        return True
    return body / max(abs(o), abs(c)) < threshold

def detect_hammer(open_prices, high, low, close_prices):
    if len(open_prices) < 1:
        return False
    o = open_prices[-1]
    h = high[-1]
    l = low[-1]
    c = close_prices[-1]
    body = abs(c - o)
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)
    if body == 0:
        return False
    return lower_wick >= 2 * body and upper_wick <= body * 0.3

def detect_shooting_star(open_prices, high, low, close_prices):
    if len(open_prices) < 1:
        return False
    o = open_prices[-1]
    h = high[-1]
    l = low[-1]
    c = close_prices[-1]
    body = abs(c - o)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    if body == 0:
        return False
    return upper_wick >= 2 * body and lower_wick <= body * 0.3

def detect_engulfing(open_prices, close_prices):
    if len(open_prices) < 2:
        return False, None
    o1, o2 = open_prices[-2], open_prices[-1]
    c1, c2 = close_prices[-2], close_prices[-1]
    body1 = abs(c1 - o1)
    body2 = abs(c2 - o2)
    if body1 == 0 or body2 == 0:
        return False, None
    if c1 > o1 and c2 < o2 and o2 < c1 and c2 < o1:
        return True, "bearish"
    if c1 < o1 and c2 > o2 and o2 > c1 and c2 > o1:
        return True, "bullish"
    return False, None

def detect_all(open_prices, high, low, close_prices):
    patterns = []
    if detect_doji(open_prices, close_prices):
        patterns.append("Doji")
    if detect_hammer(open_prices, high, low, close_prices):
        patterns.append("Hammer")
    if detect_shooting_star(open_prices, high, low, close_prices):
        patterns.append("ShootingStar")
    engulfing = detect_engulfing(open_prices, close_prices)
    if engulfing[0]:
        patterns.append(f"Engulfing_{engulfing[1]}")
    return patterns
