import numpy as np

def price_change(prices, period=5):
    if len(prices) < period + 1:
        return 0
    return 100 * (prices[-1] - prices[-period - 1]) / prices[-period - 1]

def range_position(price, high, low, period=14):
    if len(high) < period or len(low) < period:
        return 0.5
    recent_high = max(high[-period:])
    recent_low = min(low[-period:])
    rng = recent_high - recent_low
    if rng == 0:
        return 0.5
    return (price - recent_low) / rng

def sma(prices, period=20):
    if len(prices) < period:
        return np.mean(prices)
    return np.mean(prices[-period:])

def ema(prices, period=14):
    if len(prices) < period:
        return np.mean(prices)
    multiplier = 2 / (period + 1)
    result = np.mean(prices[:period])
    for price in prices[period:]:
        result = (price - result) * multiplier + result
    return result

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = np.diff(prices)
    gains = deltas[deltas >= 0]
    losses = -deltas[deltas < 0]
    avg_gain = np.mean(gains) if len(gains) > 0 else 1
    avg_loss = np.mean(losses) if len(losses) > 0 else 1
    for i in range(period, len(deltas)):
        if deltas[i] >= 0:
            avg_gain = (avg_gain * (period - 1) + deltas[i]) / period
            avg_loss = (avg_loss * (period - 1)) / period
        else:
            avg_gain = (avg_gain * (period - 1)) / period
            avg_loss = (avg_loss * (period - 1) + abs(deltas[i])) / period
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def atr(high, low, close, period=14):
    if len(high) < 2 or len(low) < 2 or len(close) < 2:
        return 0
    tr_list = []
    for i in range(1, len(close)):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr_list.append(max(hl, hc, lc))
    if not tr_list:
        return 0
    return np.mean(tr_list[-period:])
