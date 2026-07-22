from ai.indicators import price_change, range_position, sma, rsi, atr
from ai.strategy import calculate_entry_exit

SHORT_PERIOD = 5
MED_PERIOD = 10
RANGE_PERIOD = 14
TREND_UP_THRESHOLD = 1.0
TREND_DN_THRESHOLD = -1.0
NEAR_LOW = 0.25
NEAR_HIGH = 0.75

def get_trend(change_pct):
    if change_pct > TREND_UP_THRESHOLD:
        return "UPTREND"
    elif change_pct < TREND_DN_THRESHOLD:
        return "DOWNTREND"
    return "FLAT"

def is_stabilizing(prices):
    if len(prices) < MED_PERIOD + 1:
        return False
    short_chg = price_change(prices, SHORT_PERIOD)
    med_chg = price_change(prices, MED_PERIOD)
    if med_chg < 0 and short_chg > med_chg * 0.6:
        return True
    return False

def is_weakening(prices):
    if len(prices) < MED_PERIOD + 1:
        return False
    short_chg = price_change(prices, SHORT_PERIOD)
    med_chg = price_change(prices, MED_PERIOD)
    if med_chg > 0 and short_chg < med_chg * 0.5:
        return True
    return False

def calc_confidence(signal, score, rsi_val, pos, trend, atr_val, price):
    base = 50
    if signal == "BUY":
        base = 65
        if score >= 3: base += 15
        if rsi_val < 40: base += 10
        if rsi_val < 30: base += 5
        if pos <= 0.15: base += 10
        elif pos <= 0.25: base += 5
        if trend == "DOWNTREND": base += 5
    elif signal == "SELL":
        base = 65
        if rsi_val > 65: base += 10
        if rsi_val > 70: base += 5
        if pos >= 0.9: base += 10
        elif pos >= 0.75: base += 5
        if trend == "UPTREND": base += 5
    else:
        if score >= 1: base = 60
        elif score <= -1: base = 40
        else: base = 50
        if abs(rsi_val - 50) < 5: base += 5
    return min(max(base, 0), 99)

def make_reasoning(sym, signal, note, trend, score, rsi_val, pos, chg_pct, ma20, price):
    if signal == "BUY":
        if note == "Rebound":
            return (
                f"{sym} saat ini dalam fase rebound setelah tren turun. "
                f"Harga di posisi {pos*100:.0f}% dari range 14-hari (mendekati support). "
                f"Laju penurunan mulai melambat, mengindikasikan potensi pembalikan arah. "
                f"RSI di {rsi_val} (mulai pulih dari jenuh jual). "
                f"Rekomendasi: akumulasi beli untuk target jangka pendek."
            )
        elif note == "Accumulation":
            return (
                f"{sym} bergerak sideways dengan harga stabil di kisaran {pos*100:.0f}% range. "
                f"Tidak ada tekanan jual signifikan. "
                f"RSI di {rsi_val} (netral), memberikan peluang akumulasi. "
                f"MA20 di Rp{ma20:,.0f} sejajar dengan harga, menandakan keseimbangan. "
                f"Rekomendasi: cocok untuk akumulasi bertahap."
            )
    elif signal == "SELL":
        return (
            f"{sym} mendekati titik jenuh beli di posisi {pos*100:.0f}% range. "
            f"Momentum kenaikan mulai melemah, volume menurun. "
            f"RSI di {rsi_val} (mendekati overbought). "
            f"Rekomendasi: ambil profit, harga berpotensi koreksi."
        )
    else:
        if note == "Uptrend":
            return (
                f"{sym} dalam tren naik yang sehat dengan kenaikan {chg_pct:+.2f}%. "
                f"Harga di atas MA20 (Rp{ma20:,.0f}), menandakan tren positif. "
                f"RSI di {rsi_val} (masih netral). Belum ada sinyal jenuh beli. "
                f"Rekomendasi: tahan posisi, pantau untuk potensi kenaikan lanjutan."
            )
        elif note == "Overbought":
            return (
                f"{sym} sudah berada di zona overbought (posisi {pos*100:.0f}% range). "
                f"Meski tren masih naik, risiko koreksi meningkat. "
                f"RSI di {rsi_val} (tinggi). "
                f"Rekomendasi: waspada, jangan tambah posisi."
            )
        elif note == "Downtrend":
            return (
                f"{sym} dalam tren turun {chg_pct:+.2f}% dalam 5 hari. "
                f"Harga di bawah MA20 (Rp{ma20:,.0f}). "
                f"RSI di {rsi_val}. "
                f"Rekomendasi: hindari beli, tunggu sinyal rebound."
            )
        else:
            return (
                f"{sym} bergerak sideways/uchered dengan perubahan {chg_pct:+.2f}%. "
                f"RSI di {rsi_val} (netral). "
                f"Rekomendasi: tahan, belum ada sinyal jelas."
            )

def analyze_market(data):
    results = []
    for stock in data:
        prices = stock["history"]
        high = stock.get("high", prices)
        low = stock.get("low", prices)
        price = stock["price"]

        chg_pct = round(price_change(prices, SHORT_PERIOD), 2)
        trend = get_trend(chg_pct)
        pos = range_position(price, high, low, RANGE_PERIOD)
        rsi_val = round(rsi(prices), 1)
        atr_val = round(atr(high, low, prices), 2)
        ma20 = round(sma(prices, 20), 2)

        signal = "HOLD"
        score = 0
        note = ""
        strength = ""

        if trend == "DOWNTREND":
            if pos <= NEAR_LOW and is_stabilizing(prices):
                signal = "BUY"
                note = "Rebound"
                if pos <= 0.15 and chg_pct > -3:
                    score = 3
                    strength = "STRONG"
                else:
                    score = 2
                    strength = "NORMAL"
            else:
                note = "Downtrend"
                score = -1

        elif trend == "FLAT":
            if pos <= 0.55 and not (len(prices) > SHORT_PERIOD and price_change(prices, SHORT_PERIOD) < -0.5):
                signal = "BUY"
                note = "Accumulation"
                score = 2
                strength = "NORMAL"
            else:
                note = "Sideways"
                score = 0 if 0.3 <= pos <= 0.7 else -1

        elif trend == "UPTREND":
            if pos >= NEAR_HIGH and is_weakening(prices):
                signal = "SELL"
                note = "Take Profit"
                score = -2
                strength = "NORMAL"
            elif pos >= 0.9:
                note = "Overbought"
                score = -1
            else:
                note = "Uptrend"
                score = 1

        confidence = calc_confidence(signal, score, rsi_val, pos, trend, atr_val, price)
        reasoning = make_reasoning(
            stock["symbol"].replace(".JK", ""),
            signal, note, trend, score, rsi_val, pos, chg_pct, ma20, price
        )

        buy, sell, sl, rr = calculate_entry_exit(price, atr_val)

        results.append({
            "symbol": stock["symbol"],
            "price": round(price, 2),
            "change_pct": chg_pct,
            "trend": trend,
            "position": round(pos, 2),
            "score": score,
            "confidence": confidence,
            "strength": strength,
            "signal": signal,
            "note": note,
            "reasoning": reasoning,
            "rsi": rsi_val,
            "ma20": ma20,
            "atr": atr_val,
            "buy": buy,
            "sell": sell,
            "sl": sl,
            "rr": rr
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    top3 = [r["symbol"] for r in results[:3]]

    for r in results:
        r["rank"] = results.index(r) + 1
        r["is_top3"] = r["symbol"] in top3

    return results
