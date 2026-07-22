# Analisa Saham Smart — Full-Stack Sistem Analisa Saham Otomatis

Sistem analisa 20 saham unggulan Indonesia otomatis dengan AI, notifikasi Telegram, dashboard web real-time, dan MCP server untuk AI assistant. Tema **Luxury Gold & Deep Bronze** dengan layout 2 kolom yang lega.

---

## Fitur Lengkap

### AI Engine (`ai/`)
- **Indikator Teknikal**: RSI, SMA, EMA, ATR, price change, range position
- **Deteksi Trend**: UPTREND / DOWNTREND / FLAT
- **Scoring System**: Skor -3 sampai +3 berdasarkan kombinasi indikator
- **Confidence Level**: Persentase keyakinan (0-99%) tiap sinyal
- **Ranking**: Otomatis ranking TOP 3 saham terbaik
- **Candlestick Patterns**: Deteksi Doji, Hammer, Shooting Star, Engulfing
- **Reasoning Generator**: Penjelasan natural language tiap rekomendasi
- **Entry/Exit Strategy**: Hitung Buy price, Target, Stop Loss, Risk/Reward
- **Learning Engine**: Analisa histori sinyal buy/sell per saham
- **AI Daily Closing Summary**: Laporan penutupan pasar harian otomatis via AI (dikirim ke Telegram pukul 16:05 WIB)

### Telegram Bot (`bot/`)
- Kirim hasil analisa ke Telegram via Bot API
- **Real-time Notifier**: Monitor tiap 30 detik, alert jika signal berubah
- Format pesan: icon + harga + trend + signal + reasoning
- Auto-update TOP 3 rekomendasi
- **Group Broadcast**: Update ringkas tiap 5 menit saat jam pasar buka (09:00-16:00 WIB)
- **AI Daily Closing Report**: Laporan eksekutif penutupan pasar otomatis pukul 16:05 WIB
- **Dukungan Group Chat ID**: Support ID Grup/Supergroup (diawali `-100`)

### Web Dashboard (`web/`) — Luxury Gold Theme
- **Flask REST API**: 25+ endpoint dengan in-memory caching (TTL 120 detik)
- **Theme**: Luxury Gold & Deep Bronze — palet eksklusif
- **Layout 2 Kolom**: Grid saham 2 kolom + sidebar kanan untuk Ringkasan Pasar & Top Movers
- **Ticker Tape**: Running text harga saham berjalan dengan aksen gold
- **Real-time Flash Effect**: Angka berkedip hijau (naik) / merah (turun) saat harga berubah
- **Animasi**: Fade-in card, hover glow, skeleton loading, pulse live indicator
- **Auto-refresh**: Data pasar tiap 3-5 detik, berita tiap 30 detik tanpa reload halaman
- **Search & Filter**: Cari saham by nama/kode, filter by sektor (Banking, Mining, Consumer, Tech, Industrial)
- **Pagination**: 12 item per halaman
- **Detail Modal**: Buka instan dengan skeleton loading, data lengkap + chart intraday + prediksi
- **Chart Utama**: IHSG & USD/IDR dengan grace 10% sumbu Y, tooltip presisi
- **Sparklines**: Mini chart 20 hari di setiap card saham
- **Market Status**: Indikator OPEN/CLOSED + LIVE REALTIME MARKET pulse
- **Running News Sidebar**: Berita keuangan terkini tiap 30 detik
- **Daily Summary Modal**: Ringkasan penutupan pasar harian dalam bentuk laporan eksekutif

### MCP Server (`mcp_server.py`)
- Integrasi dengan AI assistant via MCP protocol
- Tool: `get_latest_signals()` — ambil signal terbaru via MCP

### Scheduler & Automation (`run_server.py`)
- **Live Mode**: auto-analisis tiap 5 menit saat market buka (09:00-16:00)
- **30s Real-time Fetch**: Fetch harga & berita tiap 30 detik saat jam pasar buka
- **5-min Telegram Broadcast**: Update ringkas pasar & sinyal ke Telegram tiap 5 menit
- **AI Daily Closing Summary**: Laporan penutupan otomatis pukul 16:05 WIB
- **Final Mode**: 1x analisis saat market tutup
- **Background Notifier**: berjalan terus meski analisis selesai

### Data Management
- History otomatis dengan deduplikasi (max 500 entries)
- Track portofolio/trade per saham
- In-memory caching untuk endpoint detail saham (company, intraday, chart, prediksi)

---

## Struktur Folder

```
ai_saham_bot/
├── app.py              # Main controller: loop analisis, scheduler live market
├── config.py           # Load konfigurasi dari .env (TOKEN, CHAT_ID, API_KEY)
├── .env                # Secret token & API key (JANGAN di-share)
├── requirement.txt     # Dependencies Python
├── run_server.py       # Entry point utama: Flask + Scheduler (30s fetch, 5min Telegram, Daily Summary)
├── mcp_server.py       # MCP Server untuk integrasi AI assistant
├── start_all.bat       # Batch script: start Flask + MCP Server
├── test_saham.py       # Test fetching data saham
├── test_telegram.py    # Test kirim pesan Telegram
│
├── ai/                 # ◀ OTAK AI (Analisa & Keputusan)
│   ├── analyzer.py     #   Main analyzer: trend, scoring, confidence, ranking TOP 3
│   ├── indicators.py   #   Indikator teknikal: RSI, SMA, EMA, ATR, price change
│   ├── strategy.py     #   Hitung entry price, target, stop loss, risk/reward
│   ├── patterns.py     #   Deteksi pola candlestick: Doji, Hammer, Shooting Star, Engulfing
│   └── learning.py     #   Learning dari history: statistik buy/sell per saham
│
├── utils/              # ◀ HELPER & UTILITY
│   ├── fetch_data.py   #   Ambil data 20 saham dari Yahoo Finance
│   ├── save_data.py    #   Simpan hasil analisis ke history.json (dedup otomatis)
│   ├── portfolio.py    #   Tracking portofolio/trade ke portfolio.json
│   └── scheduler.py    #   Scheduler: auto-run saat jam market (09:00-16:00)
│
├── bot/                # ◀ TELEGRAM BOT
│   ├── telegram_bot.py #   Kirim pesan ke Telegram via Bot API
│   └── notifier.py     #   Real-time monitor: deteksi perubahan signal & alert
│
├── web/                # ◀ DASHBOARD WEB (Flask + Chart.js) — Luxury Gold Theme
│   ├── server.py       #   Flask REST API (25+ endpoint) + in-memory caching + Telegram helper
│   ├── templates/
│   │   └── index.html  #   Frontend dashboard 2 kolom + sidebar + ticker tape
│   └── static/
│       └── style.css   #   Luxury Gold & Deep Bronze theme + glassmorphism + animasi flash
│
└── data/               # ◀ STORAGE (JSON)
    ├── history.json    #   Riwayat hasil analisa
    ├── last_state.json #   State terakhir untuk real-time notifier
    └── portfolio.json  #   Data portofolio / trade
```

---

## Tema Luxury Gold & Deep Bronze

| Elemen | Warna |
|--------|-------|
| Background Utama | Deep Charcoal Obsidian `#0D0D11` |
| Card Background | Glassmorphism Cokelat Tua `#1A1714` |
| Border Card | Gold Metallic `rgba(212,175,55,0.15)` |
| Primary Accent | Warm Gold `#D4AF37` / `#E5C158` |
| Text Highlight | Soft Cream Gold `#F4E8C1` |
| Buy Badge | Green Neon `#00FF88` |
| Sell Badge | Crimson Red `#FF2244` |
| Hold Badge | Muted Gold `#B8960F` |

---

## Cara Jalankan

```bash
# 1. Full server + scheduler (rekomendasi)
python run_server.py
# Buka http://localhost:5000
# Scheduler berjalan: 30s fetch, 5-min Telegram, daily summary 16:05 WIB

# 2. Web dashboard (standalone, tanpa scheduler)
cd web && python server.py

# 3. Analisa saham (AI + Telegram standalone)
python app.py

# 4. MCP Server (untuk integrasi AI assistant)
python mcp_server.py

# 5. Semua service sekaligus
start_all.bat
```

## Dependencies
```
flask requests python-dotenv numpy yfinance schedule
```

---

## Konfigurasi Telegram Bot & Grup

### 1. Buat Variabel `.env`

Buka file `.env` di root proyek dan isi dengan:

```ini
TOKEN=YOUR_TOKEN
CHAT_ID=YOUR_CHAT_ID
API_KEY=YOUR_API_KEY
```

- **TOKEN**: Bot Token dari [@BotFather](https://t.me/BotFather) di Telegram.
- **CHAT_ID**: ID chat tujuan (bisa user ID atau Group ID).

### 2. Cara Membuat Bot Telegram

1. Buka Telegram, cari **@BotFather**.
2. Kirim perintah `/newbot` dan ikuti petunjuknya.
3. Setelah jadi, BotFather akan memberikan **Bot Token** — salin ke `TOKEN` di `.env`.

### 3. Cara Memasukkan Bot ke Grup & Mendapatkan Group Chat ID

#### Opsi A: Menggunakan @RawDataBot (paling mudah)

1. Buka Telegram, cari **@RawDataBot**.
2. Klik **Start** atau `/start`.
3. **Tambahkan bot @RawDataBot ke Grup Anda**:
   - Buka grup target → klik nama grup → **Add Members** → cari `@RawDataBot`.
4. @RawDataBot akan otomatis mengirim pesan berisi **raw JSON data** grup.
5. Cari field `chat` → `id` — nilainya adalah Group Chat ID.
   - Contoh: `"id": -1001234567891`
6. **Hapus @RawDataBot dari grup** setelah mendapatkan ID.
7. Salin ID tersebut (termasuk tanda `-` di depan) ke `CHAT_ID` di `.env`.

#### Opsi B: Forward pesan ke @getidsbot

1. Buka **@getidsbot** di Telegram, klik Start.
2. Forward pesan dari grup target ke bot tersebut.
3. Bot akan membalas dengan informasi termasuk **Chat ID** grup.

### 4. Jadikan Bot sebagai Admin Grup

Agar bot bisa mengirim pesan ke grup secara otomatis:

1. Buka grup target di Telegram.
2. Klik nama grup → **Administrators** → **Add Admin**.
3. Cari nama bot Anda dan pilih.
4. **WAJIB** berikan izin **"Send Messages"** (minimal).
5. Klik **Save**.

### 5. Verifikasi Bot Bekerja

Jalankan script test:

```bash
python test_telegram.py
```

Jika sukses, bot akan mengirim pesan test ke grup/chat tujuan.

### Catatan Penting

- **Group ID Supergroup** selalu diawali dengan `-100` (misal: `-1001234567891`).
- Bot harus **menjadi anggota grup** untuk bisa mengirim pesan.
- Jika bot tidak bisa kirim pesan, pastikan bot sudah di-**Add Admin** dengan izin **Send Messages**.
- Setiap pembaruan kode selanjutnya **WAJIB** meng-update file `README.md` secara otomatis.

## Data Saham (20 Saham Indonesia)
| Sektor | Saham |
|--------|-------|
| Financial Services | BBCA, BBRI, BMRI, BBNI |
| Telecommunications | TLKM, EXCL |
| Consumer Defensive | ICBP, INDF, UNVR, CPIN, KLBF |
| Energy | ADRO, PTBA, ANTM, MEDC |
| Industrials | ASII, SMGR, JSMR |
| Technology | GOTO |

---

## ⚠️ ATURAN PERMANEN
Setiap kali melakukan perubahan kode (backend, frontend, atau struktur folder), **README.md ini WAJIB diperbarui** agar selalu mencerminkan arsitektur dan fitur terkini. Jangan biarkan dokumentasi usang/ketinggalan.

---

## Endpoint API Lengkap

| Endpoint | Method | Deskripsi |
|----------|--------|-----------|
| `/` | GET | Dashboard web utama |
| `/api/data` | GET | Semua riwayat sinyal |
| `/api/latest` | GET | Sinyal terbaru (dengan cache 120s) |
| `/api/live` | GET | Harga real-time 20 saham dari Yahoo Finance |
| `/api/buy` | GET | Filter sinyal BUY |
| `/api/sell` | GET | Filter sinyal SELL |
| `/api/top3` | GET | TOP 3 rekomendasi terbaik |
| `/api/state` | GET | State terakhir (dari notifier) |
| `/api/market` | GET | Data IHSG & USD/IDR |
| `/api/market_live` | GET | Chart intraday IHSG & USD/IDR |
| `/api/market_status` | GET | Status pasar (OPEN/CLOSED) |
| `/api/market-data` | GET | Paket data lengkap: status + IHSG + USD + harga + berita |
| `/api/news` | GET | Berita keuangan terkini (agregasi dari Yahoo Finance) |
| `/api/daily-summary` | GET | Ringkasan penutupan pasar harian |
| `/api/company/<symbol>` | GET | Data fundamental perusahaan |
| `/api/intraday/<symbol>` | GET | Pergerakan intraday saham |
| `/api/history_chart/<symbol>` | GET | Riwayat 3 bulan saham |
| `/api/predictions/<symbol>` | GET | Prediksi 5 hari (regresi linear) |
| `/api/sparklines` | GET | Data sparkline 20 hari |
| `/api/sectors` | GET | Mapping sektor per saham |
| `/api/symbols` | GET | Daftar simbol saham |
| `/api/portfolio` | GET | Data portofolio/trade |
| `/api/delete_all` | DELETE | Hapus semua riwayat |
