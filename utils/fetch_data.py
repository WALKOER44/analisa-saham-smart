import yfinance as yf

SYMBOLS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK",
    "TLKM.JK", "ASII.JK", "ICBP.JK",
    "INDF.JK", "UNVR.JK", "ADRO.JK",
    "GOTO.JK", "PTBA.JK", "ANTM.JK", "CPIN.JK",
    "KLBF.JK", "SMGR.JK", "PGAS.JK", "EXCL.JK",
    "MEDC.JK", "JSMR.JK"
]

import math

def get_stock_data():
    results = []
    for sym in SYMBOLS:
        stock = yf.Ticker(sym)
        hist = stock.history(period="3mo")
        if not hist.empty:
            clean = hist.dropna(subset=["Close"])
            if clean.empty:
                print(f"[SKIP] {sym} no valid close price")
                continue
            price = float(clean["Close"].iloc[-1])
            row_idx = hist.index.get_loc(clean.index[-1])
            prices = [float(p) for p in hist["Close"].values[:row_idx+1]]
            high = [float(p) for p in hist["High"].values[:row_idx+1]]
            low = [float(p) for p in hist["Low"].values[:row_idx+1]]
            volume = [float(v) for v in hist["Volume"].values[:row_idx+1]]
            open_prices = [float(p) for p in hist["Open"].values[:row_idx+1]]
            results.append({
                "symbol": sym,
                "price": price,
                "history": prices,
                "high": high,
                "low": low,
                "volume": volume,
                "open": open_prices
            })
    return results

def get_histories():
    result = {}
    for sym in SYMBOLS:
        stock = yf.Ticker(sym)
        hist = stock.history(period="3mo")
        if not hist.empty:
            clean = hist.dropna(subset=["Close"])
            if clean.empty:
                continue
            row_idx = hist.index.get_loc(clean.index[-1])
            result[sym] = {
                "close": [float(p) for p in hist["Close"].values[:row_idx+1]],
                "high": [float(p) for p in hist["High"].values[:row_idx+1]],
                "low": [float(p) for p in hist["Low"].values[:row_idx+1]],
                "volume": [float(v) for v in hist["Volume"].values[:row_idx+1]]
            }
    return result
