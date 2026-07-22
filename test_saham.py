import yfinance as yf

def get_stock_data(symbol="BBCA.JK"):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        name = info.get("longName") or info.get("shortName") or symbol

        print("[DATA] Nama:", name)
        print("[DATA] Simbol:", symbol)
        print("[DATA] Harga:", info.get("currentPrice") or info.get("regularMarketPrice", "N/A"))
        print("[DATA] High:", info.get("dayHigh", "N/A"))
        print("[DATA] Low:", info.get("dayLow", "N/A"))

    except Exception as e:
        print("[ERROR] Gagal ambil data:", e)

if __name__ == "__main__":
    get_stock_data()