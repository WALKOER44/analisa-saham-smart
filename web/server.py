import json
import os
import sys
import math
import time as time_module
import threading
from datetime import datetime, timedelta
import yfinance as yf
import requests
from flask import Flask, render_template, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
try:
    from config import TOKEN as TELEGRAM_BOT_TOKEN, CHAT_ID as TELEGRAM_CHAT_ID, IS_LOCAL
except ImportError:
    TELEGRAM_BOT_TOKEN = os.getenv("TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("CHAT_ID", "")
    IS_LOCAL = os.getenv("IS_LOCAL", "False").strip().lower() in ("true", "1", "yes")

REALTIME_DATA = {}
REALTIME_LOCK = threading.Lock()
DAILY_SUMMARY_CACHE = {}
NEWS_CACHE = []
NEWS_CACHE_TIME = 0
DAILY_SUMMARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "daily_summary.json")

def send_telegram_message(text):
    if IS_LOCAL:
        print("[LOCAL MODE] send_telegram_message dialihkan ke console:")
        print("-" * 55)
        print(text)
        print("-" * 55)
        return True
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_ID.split(",") if cid.strip()]
    if not chat_ids:
        return False
    all_ok = True
    for cid in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            r = requests.post(url, data={"chat_id": cid, "text": text, "parse_mode": "Markdown"}, timeout=10)
            if not r.ok:
                all_ok = False
                print(f"[TELEGRAM] Error sending to {cid}: {r.text}")
            else:
                print(f"[TELEGRAM] Pesan berhasil dikirim ke {cid}")
        except Exception as e:
            all_ok = False
            print(f"[TELEGRAM] Error sending to {cid}: {e}")
    return all_ok

def fetch_news_for_symbol(symbol):
    try:
        stock = yf.Ticker(symbol)
        news = stock.news or []
        result = []
        for item in news[:5]:
            result.append({
                "title": item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "link": item.get("link", ""),
                "summary": item.get("summary", ""),
                "time": datetime.now().strftime("%H:%M")
            })
        return result
    except Exception:
        return []

def get_aggregated_news():
    global NEWS_CACHE, NEWS_CACHE_TIME
    now = time_module.time()
    if NEWS_CACHE and now - NEWS_CACHE_TIME < 120:
        return NEWS_CACHE
    try:
        from utils.fetch_data import SYMBOLS
        all_news = []
        seen = set()
        for sym in SYMBOLS[:8]:
            try:
                news = fetch_news_for_symbol(sym)
                for item in news:
                    key = item["title"]
                    if key and key not in seen:
                        seen.add(key)
                        item["symbol"] = sym.replace(".JK", "")
                        all_news.append(item)
            except Exception:
                continue
        if all_news:
            NEWS_CACHE = all_news[:20]
            NEWS_CACHE_TIME = now
            return NEWS_CACHE
    except Exception:
        pass

    if NEWS_CACHE:
        return NEWS_CACHE

    try:
        fallback_url = "https://query1.finance.yahoo.com/v8/finance/chart/^JKSE?range=1d&interval=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(fallback_url, headers=headers, timeout=5)
        if resp.ok:
            NEWS_CACHE = [{
                "title": "Data pasar IHSG tersedia. Buka halaman detail untuk info lebih lanjut.",
                "publisher": "Yahoo Finance",
                "link": "https://finance.yahoo.com/quote/%5EJKSE/",
                "symbol": "IHSG",
                "time": datetime.now().strftime("%H:%M")
            }]
            NEWS_CACHE_TIME = now
    except Exception:
        pass

    return NEWS_CACHE or []

BASE = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(BASE, "..", "data", "history.json")
LAST_STATE_PATH = os.path.join(BASE, "..", "data", "last_state.json")

app = Flask(__name__,
    template_folder=os.path.join(BASE, "templates"),
    static_folder=os.path.join(BASE, "static"),
    static_url_path="/static"
)

COMPANY_CACHE = {}
COMPANY_CACHE_TIME = {}

SHORT_CACHE = {}
SHORT_CACHE_TTL = 120

def get_cached(key, ttl=SHORT_CACHE_TTL):
    now = time_module.time()
    if key in SHORT_CACHE and now - SHORT_CACHE[key]["time"] < ttl:
        return SHORT_CACHE[key]["data"]
    return None

def set_cached(key, data):
    SHORT_CACHE[key] = {"data": data, "time": time_module.time()}

def yf_fetch(ticker, method="history", period="1mo", interval="1d", max_retries=2):
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            if method == "history":
                return stock.history(period=period, interval=interval)
            elif method == "info":
                return stock.info
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time_module.sleep(1)
    return None

def read_history():
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def read_last_state():
    try:
        with open(LAST_STATE_PATH) as f:
            return json.load(f)
    except:
        return {}

def flatten(items):
    result = []
    for entry in items:
        for d in entry.get("data", []):
            result.append({
                "time": entry["time"],
                "symbol": d.get("symbol", ""),
                "signal": d.get("signal", "HOLD"),
                "price": d.get("price", 0),
                "score": d.get("score", 0),
                "trend": d.get("trend", ""),
                "note": d.get("note", ""),
                "strength": d.get("strength", ""),
                "change_pct": d.get("change_pct", 0),
                "position": d.get("position", 0),
                "rsi": d.get("rsi", 0),
                "ma20": d.get("ma20", 0),
                "atr": d.get("atr", 0),
                "buy": d.get("buy", 0),
                "sell": d.get("sell", 0),
                "sl": d.get("sl", 0),
                "rr": d.get("rr", 0),
                "confidence": d.get("confidence", 50),
                "reasoning": d.get("reasoning", ""),
                "is_top3": d.get("is_top3", False),
                "rank": d.get("rank", 0)
            })
    return result

def get_latest_flattened():
    history = read_history()
    if not history:
        return []
    latest = history[-1]
    time_str = latest["time"]
    result = []
    for d in latest.get("data", []):
        entry = {
            "time": time_str,
            "symbol": d.get("symbol", ""),
            "signal": d.get("signal", "HOLD"),
            "price": d.get("price", 0),
            "score": d.get("score", 0),
            "trend": d.get("trend", ""),
            "note": d.get("note", ""),
            "strength": d.get("strength", ""),
            "change_pct": d.get("change_pct", 0),
            "position": d.get("position", 0),
            "rsi": d.get("rsi", 0),
            "ma20": d.get("ma20", 0),
            "atr": d.get("atr", 0),
            "buy": d.get("buy", 0),
            "sell": d.get("sell", 0),
            "sl": d.get("sl", 0),
            "rr": d.get("rr", 0),
            "confidence": d.get("confidence", 50),
            "reasoning": d.get("reasoning", ""),
            "is_top3": d.get("is_top3", False),
            "rank": d.get("rank", 0)
        }
        result.append(entry)
    return result

@app.route("/api/live")
def api_live():
    try:
        from utils.fetch_data import SYMBOLS
        result = {}
        for sym in SYMBOLS:
            try:
                hist = yf_fetch(sym, "history", "2d", "1d")
                if hist is not None and not hist.empty:
                    close = hist["Close"].iloc[-1]
                    if len(hist) > 1:
                        prev_close = hist["Close"].iloc[-2]
                        change = float(close - prev_close)
                        change_pct = round((change / prev_close) * 100, 2)
                    else:
                        change = 0.0
                        change_pct = 0.0
                    high = float(hist["High"].max())
                    low = float(hist["Low"].min())
                    volume = int(hist["Volume"].sum())
                    result[sym] = {
                        "price": round(float(close), 2),
                        "change": round(change, 2),
                        "change_pct": change_pct,
                        "high": round(high, 2),
                        "low": round(low, 2),
                        "volume": volume,
                        "time": datetime.now().strftime("%H:%M:%S")
                    }
            except:
                continue
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    return jsonify(flatten(read_history()))

@app.route("/api/latest")
def api_latest():
    cached = get_cached("api_latest")
    if cached:
        return jsonify(cached)
    data = get_latest_flattened()
    set_cached("api_latest", data)
    return jsonify(data)

@app.route("/api/buy")
def api_buy():
    return jsonify([i for i in flatten(read_history()) if i["signal"] == "BUY"])

@app.route("/api/sell")
def api_sell():
    return jsonify([i for i in flatten(read_history()) if i["signal"] == "SELL"])

@app.route("/api/top3")
def api_top3():
    latest = get_latest_flattened()
    top3 = [i for i in latest if i.get("is_top3")]
    return jsonify(sorted(top3, key=lambda x: x["score"], reverse=True))

@app.route("/api/state")
def api_state():
    return jsonify(read_last_state())

COMPANY_NAMES = {
    "BBCA.JK": "Bank Central Asia Tbk",
    "BBRI.JK": "Bank Rakyat Indonesia Tbk",
    "BMRI.JK": "Bank Mandiri Tbk",
    "BBNI.JK": "Bank Negara Indonesia Tbk",
    "TLKM.JK": "Telkom Indonesia Tbk",
    "ASII.JK": "Astra International Tbk",
    "ICBP.JK": "Indofood CBP Sukses Makmur Tbk",
    "INDF.JK": "Indofood Sukses Makmur Tbk",
    "UNVR.JK": "Unilever Indonesia Tbk",
    "ADRO.JK": "Adaro Energy Indonesia Tbk",
    "GOTO.JK": "Gojek Tokopedia Tbk",
    "PTBA.JK": "Bukit Asam Tbk",
    "ANTM.JK": "Aneka Tambang Tbk",
    "CPIN.JK": "Charoen Pokphand Indonesia Tbk",
    "KLBF.JK": "Kalbe Farma Tbk",
    "SMGR.JK": "Semen Indonesia Tbk",
    "PGAS.JK": "Perusahaan Gas Negara Tbk",
    "EXCL.JK": "XL Axiata Tbk",
    "MEDC.JK": "Medco Energi Internasional Tbk",
    "JSMR.JK": "Jasa Marga Tbk"
}

COMPANY_SECTORS = {
    "BBCA.JK": "Financial Services", "BBRI.JK": "Financial Services",
    "BMRI.JK": "Financial Services", "BBNI.JK": "Financial Services",
    "TLKM.JK": "Telecommunications", "EXCL.JK": "Telecommunications",
    "ASII.JK": "Industrials", "SMGR.JK": "Industrials",
    "JSMR.JK": "Industrials",
    "ICBP.JK": "Consumer Defensive", "INDF.JK": "Consumer Defensive",
    "UNVR.JK": "Consumer Defensive", "CPIN.JK": "Consumer Defensive",
    "KLBF.JK": "Consumer Defensive",
    "ADRO.JK": "Energy", "PTBA.JK": "Energy",
    "ANTM.JK": "Energy", "MEDC.JK": "Energy",
    "GOTO.JK": "Technology"
}

@app.route("/api/company/<symbol>")
def api_company(symbol):
    now = time_module.time()
    cached = get_cached("company_" + symbol)
    if cached:
        return jsonify(cached)
    if symbol in COMPANY_CACHE and now - COMPANY_CACHE_TIME.get(symbol, 0) < 3600:
        set_cached("company_" + symbol, COMPANY_CACHE[symbol])
        return jsonify(COMPANY_CACHE[symbol])

    fallback = {
        "name": COMPANY_NAMES.get(symbol, symbol.replace(".JK", "")),
        "sector": COMPANY_SECTORS.get(symbol, "-"),
        "industry": "-",
        "marketCap": 0,
        "peRatio": 0,
        "eps": 0,
        "dividendYield": 0,
        "high52": 0,
        "low52": 0,
        "volume": 0,
        "avgVolume": 0,
        "website": "",
        "previousClose": 0,
        "open": 0
    }

    try:
        info = yf_fetch(symbol, "info", max_retries=1)
        if info and not info.get("error"):
            company = {
                "name": info.get("longName") or info.get("shortName") or fallback["name"],
                "sector": info.get("sector") or fallback["sector"],
                "industry": info.get("industry") or "-",
                "marketCap": info.get("marketCap") or 0,
                "peRatio": info.get("trailingPE") or info.get("forwardPE") or 0,
                "eps": info.get("trailingEps") or 0,
                "dividendYield": info.get("dividendYield") or 0,
                "high52": info.get("fiftyTwoWeekHigh") or 0,
                "low52": info.get("fiftyTwoWeekLow") or 0,
                "volume": info.get("volume") or 0,
                "avgVolume": info.get("averageVolume") or 0,
                "website": info.get("website") or "",
                "previousClose": info.get("previousClose") or 0,
                "open": info.get("open") or info.get("regularMarketOpen") or 0
            }
            COMPANY_CACHE[symbol] = company
            COMPANY_CACHE_TIME[symbol] = now
            set_cached("company_" + symbol, company)
            return jsonify(company)

        hist = yf_fetch(symbol, "history", "3mo", "1d")
        if hist is not None and not hist.empty:
            clean = hist.dropna(subset=["Close"])
            if not clean.empty:
                last = clean.iloc[-1]
                high52 = float(clean["High"].max())
                low52 = float(clean["Low"].min())
                fallback["previousClose"] = round(float(last["Close"]), 2)
                fallback["open"] = round(float(last["Open"]), 2)
                fallback["high52"] = round(high52, 2)
                fallback["low52"] = round(low52, 2)
                fallback["volume"] = int(clean["Volume"].sum())
                fallback["avgVolume"] = int(clean["Volume"].mean())
        COMPANY_CACHE[symbol] = fallback
        COMPANY_CACHE_TIME[symbol] = now
        set_cached("company_" + symbol, fallback)
        return jsonify(fallback)
    except Exception as e:
        COMPANY_CACHE[symbol] = fallback
        COMPANY_CACHE_TIME[symbol] = now
        set_cached("company_" + symbol, fallback)
        return jsonify(fallback)

@app.route("/api/market")
def api_market():
    cached = get_cached("api_market")
    if cached:
        return jsonify(cached)
    result = {}
    try:
        ihsg_hist = yf_fetch("^JKSE", "history", "2d", "1d")
        if not ihsg_hist.empty:
            close = float(ihsg_hist["Close"].iloc[-1])
            prev_close = float(ihsg_hist["Close"].iloc[-2]) if len(ihsg_hist) > 1 else close
            change = close - prev_close
            pct = (change / prev_close) * 100
            result["ihsg"] = {
                "price": round(close, 2),
                "change": round(change, 2),
                "change_pct": round(pct, 2)
            }
    except:
        result["ihsg"] = None

    try:
        usd_hist = yf_fetch("USDIDR=X", "history", "2d", "1d")
        if not usd_hist.empty:
            close = float(usd_hist["Close"].iloc[-1])
            prev_close = float(usd_hist["Close"].iloc[-2]) if len(usd_hist) > 1 else close
            change = close - prev_close
            pct = (change / prev_close) * 100
            result["usd_idr"] = {
                "price": round(close, 2),
                "change": round(change, 2),
                "change_pct": round(pct, 2)
            }
    except:
        result["usd_idr"] = None

    set_cached("api_market", result)
    return jsonify(result)

@app.route("/api/intraday/<symbol>")
def api_intraday(symbol):
    cached = get_cached("intra_" + symbol)
    if cached:
        return jsonify(cached)
    try:
        hist = yf_fetch(symbol, "history", "1d", "15m")
        if hist is None or hist.empty:
            hist = yf_fetch(symbol, "history", "5d", "1d")
        if not hist.empty:
            prices = []
            for idx, row in hist.iterrows():
                prices.append({
                    "time": idx.strftime("%H:%M") if hist.index[-1].date() == idx.date() else idx.strftime("%m/%d"),
                    "price": round(float(row["Close"]), 2),
                    "open": round(float(row["Open"]), 2)
                })
            change = round(prices[-1]["price"] - prices[0]["open"], 2)
            pct = round((change / prices[0]["open"]) * 100, 2) if prices[0]["open"] else 0
            result = {
                "prices": prices,
                "change": change,
                "change_pct": pct,
                "high": max(p["price"] for p in prices),
                "low": min(p["price"] for p in prices)
            }
            set_cached("intra_" + symbol, result)
            return jsonify(result)
    except:
        pass
    return jsonify({"prices": [], "change": 0, "change_pct": 0, "high": 0, "low": 0})

@app.route("/api/market_live")
def api_market_live():
    result = {}
    for key, symbol, label in [("ihsg", "^JKSE", "IHSG"), ("usd", "USDIDR=X", "USD/IDR")]:
        try:
            hist = yf_fetch(symbol, "history", "2d", "15m")
            if hist is None or hist.empty:
                hist = yf_fetch(symbol, "history", "5d", "1d")
            if hist is not None and not hist.empty:
                prices = []
                for idx, row in hist.iterrows():
                    prices.append({
                        "t": idx.strftime("%H:%M") if hist.index[-1].date() == idx.date() else idx.strftime("%m/%d"),
                        "p": round(float(row["Close"]), 2)
                    })
                if len(prices) >= 2:
                    first = prices[0]["p"]
                    last = prices[-1]["p"]
                    chg = round(last - first, 2)
                    pct = round((chg / first) * 100, 2) if first else 0
                    result[key] = {
                        "label": label,
                        "prices": prices,
                        "price": last,
                        "change": chg,
                        "change_pct": pct,
                        "high": max(p["p"] for p in prices),
                        "low": min(p["p"] for p in prices)
                    }
        except:
            result[key] = {"label": label, "prices": [], "price": 0, "change": 0, "change_pct": 0, "high": 0, "low": 0}
    return jsonify(result)

@app.route("/api/market_status")
def api_market_status():
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()
    is_weekday = weekday < 5
    is_open = is_weekday and 9 <= hour < 16
    return jsonify({
        "open": is_open,
        "time": now.strftime("%H:%M"),
        "date": now.strftime("%A, %d %B %Y"),
        "status": "OPEN" if is_open else "CLOSED"
    })

@app.route("/api/sparklines")
def api_sparklines():
    try:
        from utils.fetch_data import SYMBOLS
        result = {}
        for sym in SYMBOLS:
            hist = yf_fetch(sym, "history", "1mo", "1d")
            if not hist.empty:
                clean = hist.dropna(subset=["Close"])
                if clean.empty:
                    continue
                prices = []
                for idx, row in clean.iterrows():
                    prices.append(round(float(row["Close"]), 2))
                if len(prices) >= 5:
                    result[sym] = {
                        "prices": prices[-20:],
                        "change_pct": round((prices[-1] - prices[0]) / prices[0] * 100, 2) if prices[0] else 0
                    }
        return jsonify(result)
    except:
        return jsonify({})

@app.route("/api/predictions/<symbol>")
def api_predictions(symbol):
    cached = get_cached("pred_" + symbol)
    if cached:
        return jsonify(cached)
    try:
        hist = yf_fetch(symbol, "history", "1mo", "1d")
        if hist.empty:
            return jsonify({"prediction": None, "target": 0, "direction": "neutral"})

        clean = hist.dropna(subset=["Close"])
        if len(clean) < 5:
            return jsonify({"prediction": None, "target": 0, "direction": "neutral"})

        prices = [float(p) for p in clean["Close"].values]
        n = len(prices)
        x_avg = n / 2
        y_avg = sum(prices) / n
        num = sum((i - x_avg) * (p - y_avg) for i, p in enumerate(prices))
        den = sum((i - x_avg) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0
        last_price = prices[-1]
        pred_price = last_price + slope * 5
        direction = "up" if slope > 0 else "down"
        change_pct = round((pred_price - last_price) / last_price * 100, 2)

        result = {
            "prediction": round(pred_price, 2),
            "last_price": last_price,
            "direction": direction,
            "change_pct": change_pct,
            "slope": round(slope, 2)
        }
        set_cached("pred_" + symbol, result)
        return jsonify(result)
    except:
        return jsonify({"prediction": None, "target": 0, "direction": "neutral"})

@app.route("/api/history_chart/<symbol>")
def api_history_chart(symbol):
    cached = get_cached("hist_" + symbol)
    if cached:
        return jsonify(cached)
    try:
        hist = yf_fetch(symbol, "history", "3mo", "1d")
        if not hist.empty:
            prices = []
            for idx, row in hist.iterrows():
                close_val = float(row["Close"])
                if math.isnan(close_val):
                    continue
                prices.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "close": round(close_val, 2)
                })
            if len(prices) < 2:
                result = {"prices": [], "change": 0, "change_pct": 0, "high": 0, "low": 0}
                set_cached("hist_" + symbol, result)
                return jsonify(result)
            change = round(prices[-1]["close"] - prices[0]["close"], 2)
            pct = round((change / prices[0]["close"]) * 100, 2) if prices[0]["close"] else 0
            result = {
                "prices": prices,
                "change": change,
                "change_pct": pct,
                "high": max(p["close"] for p in prices),
                "low": min(p["close"] for p in prices)
            }
            set_cached("hist_" + symbol, result)
            return jsonify(result)
    except:
        pass
    return jsonify({"prices": [], "change": 0, "change_pct": 0, "high": 0, "low": 0})

@app.route("/api/market_history/<mtype>")
def api_market_history(mtype):
    symbol = "^JKSE" if mtype == "ihsg" else "USDIDR=X"
    label = "IHSG" if mtype == "ihsg" else "USD/IDR"
    try:
        hist = yf_fetch(symbol, "history", "3mo", "1d")
        if not hist.empty:
            prices = []
            for idx, row in hist.iterrows():
                close_val = float(row["Close"])
                if math.isnan(close_val):
                    continue
                prices.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "close": round(close_val, 2)
                })
            if len(prices) < 2:
                return jsonify({"prices": [], "change": 0, "change_pct": 0, "high": 0, "low": 0})
            change = round(prices[-1]["close"] - prices[0]["close"], 2)
            pct = round((change / prices[0]["close"]) * 100, 2) if prices[0]["close"] else 0
            return jsonify({
                "label": label,
                "prices": prices,
                "change": change,
                "change_pct": pct,
                "high": max(p["close"] for p in prices),
                "low": min(p["close"] for p in prices)
            })
    except:
        pass
    return jsonify({"label": label, "prices": [], "change": 0, "change_pct": 0, "high": 0, "low": 0})

@app.route("/api/portfolio")
def api_portfolio():
    path = os.path.join(BASE, "..", "data", "portfolio.json")
    try:
        with open(path, encoding="utf-8") as f:
            return jsonify(json.load(f))
    except:
        return jsonify([])

@app.route("/api/delete_all", methods=["DELETE"])
def api_delete_all():
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)
    return jsonify({"status": "ok"})

@app.route("/api/sectors")
def api_sectors():
    return jsonify(COMPANY_SECTORS)

@app.route("/api/symbols")
def api_symbols():
    from utils.fetch_data import SYMBOLS
    return jsonify(SYMBOLS)

@app.route("/api/market-data")
def api_market_data():
    cached = get_cached("api_market_data")
    if cached:
        return jsonify(cached)
    result = {}
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour
    is_open = weekday < 5 and 9 <= hour < 16
    result["status"] = {"open": is_open, "time": now.strftime("%H:%M"), "date": now.strftime("%A, %d %B %Y")}

    try:
        ihsg = yf_fetch("^JKSE", "history", "2d", "1d")
        if ihsg is not None and not ihsg.empty:
            c = float(ihsg["Close"].iloc[-1])
            p = float(ihsg["Close"].iloc[-2]) if len(ihsg) > 1 else c
            result["ihsg"] = {"price": round(c, 2), "change": round(c - p, 2), "change_pct": round((c - p) / p * 100, 2)}
    except:
        result["ihsg"] = None

    try:
        usd = yf_fetch("USDIDR=X", "history", "2d", "1d")
        if usd is not None and not usd.empty:
            c = float(usd["Close"].iloc[-1])
            p = float(usd["Close"].iloc[-2]) if len(usd) > 1 else c
            result["usd_idr"] = {"price": round(c, 2), "change": round(c - p, 2), "change_pct": round((c - p) / p * 100, 2)}
    except:
        result["usd_idr"] = None

    try:
        from utils.fetch_data import SYMBOLS
        prices = {}
        for sym in SYMBOLS:
            hist = yf_fetch(sym, "history", "2d", "1d")
            if hist is not None and not hist.empty:
                c = float(hist["Close"].iloc[-1])
                p = float(hist["Close"].iloc[-2]) if len(hist) > 1 else c
                chg = round((c - p) / p * 100, 2)
                prices[sym] = {"price": round(c, 2), "change_pct": chg}
        result["prices"] = prices
    except:
        result["prices"] = {}

    result["news"] = get_aggregated_news()
    set_cached("api_market_data", result)
    return jsonify(result)

@app.route("/api/news")
def api_news():
    return jsonify(get_aggregated_news())

@app.route("/api/daily-summary", methods=["GET"])
def api_daily_summary_get():
    if DAILY_SUMMARY_CACHE.get("generated"):
        return jsonify({
            "summary": DAILY_SUMMARY_CACHE.get("text", ""),
            "date": DAILY_SUMMARY_CACHE.get("date", ""),
            "generated": True
        })
    try:
        if os.path.exists(DAILY_SUMMARY_PATH):
            with open(DAILY_SUMMARY_PATH, encoding="utf-8") as f:
                saved = json.load(f)
            if saved.get("generated"):
                DAILY_SUMMARY_CACHE["text"] = saved.get("text", "")
                DAILY_SUMMARY_CACHE["date"] = saved.get("date", "")
                DAILY_SUMMARY_CACHE["generated"] = True
                return jsonify({
                    "summary": saved.get("text", ""),
                    "date": saved.get("date", ""),
                    "generated": True
                })
    except Exception as e:
        print(f"[DAILY SUMMARY] File read error: {e}")
    return jsonify({
        "summary": "",
        "date": "",
        "generated": False
    })

def generate_daily_summary():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    if DAILY_SUMMARY_CACHE.get("date") == today and DAILY_SUMMARY_CACHE.get("generated"):
        return DAILY_SUMMARY_CACHE.get("text", "")

    try:
        history = read_history()
        latest = history[-1] if history else None
        ihsg = yf_fetch("^JKSE", "history", "5d", "1d")
        ihsg_data = {}
        if ihsg is not None and not ihsg.empty:
            c = float(ihsg["Close"].iloc[-1])
            p = float(ihsg["Close"].iloc[-2]) if len(ihsg) > 1 else c
            ihsg_data = {"price": round(c, 2), "change_pct": round((c - p) / p * 100, 2)}

        data = latest.get("data", []) if latest else []
        gainers = sorted(data, key=lambda x: x.get("change_pct", 0), reverse=True)[:3]
        losers = sorted(data, key=lambda x: x.get("change_pct", 0))[:3]
        top3 = sorted([r for r in data if r.get("is_top3")], key=lambda x: x.get("score", 0), reverse=True)

        lines = [f"\U0001f4ca **RINGKASAN PENUTUPAN PASAR HARIAN - ANALISA SAHAM SMART**"]
        lines.append(f"\U0001f5d3 Tanggal: {now.strftime('%d %B %Y')}")
        lines.append("")
        lines.append("\U0001f4c8 **Performa IHSG:**")
        if ihsg_data:
            arrow = "\U0001f7e2" if ihsg_data["change_pct"] >= 0 else "\U0001f534"
            lines.append(f"{arrow} IHSG: {ihsg_data['price']:,.0f} ({ihsg_data['change_pct']:+.2f}%)")
        lines.append("")

        lines.append("\U0001f4c8 **Performa Saham & Analisis:**")
        for r in gainers:
            sym = r.get("symbol", "").replace(".JK", "")
            lines.append(f"\u2022 {sym}: Naik {r.get('change_pct', 0):+.2f}% - {r.get('note', '')} (skor: {r.get('score', 0):+d})")
        for r in losers:
            sym = r.get("symbol", "").replace(".JK", "")
            lines.append(f"\u2022 {sym}: Turun {r.get('change_pct', 0):+.2f}% - {r.get('note', '')} (skor: {r.get('score', 0):+d})")
        lines.append("")

        lines.append("\U0001f4a1 **Rekomendasi & Jangka Waktu:**")
        if top3:
            for r in top3[:3]:
                sym = r.get("symbol", "").replace(".JK", "")
                sig = r.get("signal", "HOLD")
                tp = r.get("sell", 0)
                reason = r.get("reasoning", "")[:100]
                lines.append(f"\u2022 {sym}: Status **{sig}** (Target: Rp{tp:,.0f}) - {reason}")
        else:
            lines.append("\u2022 Belum ada data rekomendasi untuk hari ini.")
        lines.append("")

        ihsg_trend = "positif" if ihsg_data.get("change_pct", 0) >= 0 else "negatif"
        bullish_count = sum(1 for d in data if d.get("change_pct", 0) > 0)
        bearish_count = sum(1 for d in data if d.get("change_pct", 0) < 0)
        lines.append("\U0001f52e **Proyeksi Esok Hari:**")
        lines.append(f"Sentimen pasar hari ini cenderung {'bullish' if bullish_count > bearish_count else 'bearish'} ({bullish_count} naik vs {bearish_count} turun). IHSG ditutup {ihsg_trend}. Disarankan strategi konservatif dengan selektif memilih saham berfundamental kuat. Pantau pergerakan nilai tukar USD/IDR dan berita global untuk antisipasi reversal.")

        text = "\n".join(lines)
        DAILY_SUMMARY_CACHE["text"] = text
        DAILY_SUMMARY_CACHE["date"] = today
        DAILY_SUMMARY_CACHE["generated"] = True
        return text
    except Exception as e:
        print(f"[DAILY SUMMARY] Error: {e}")
        return ""

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
