from datetime import datetime

MEDAL = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}

SEP = "\u2501" * 25

SECTOR_MAP = {
    "BBCA.JK": "Perbankan", "BBRI.JK": "Perbankan",
    "BMRI.JK": "Perbankan", "BBNI.JK": "Perbankan",
    "TLKM.JK": "Telekomunikasi", "EXCL.JK": "Telekomunikasi",
    "ASII.JK": "Industri", "SMGR.JK": "Industri",
    "JSMR.JK": "Industri",
    "ICBP.JK": "Konsumen", "INDF.JK": "Konsumen",
    "UNVR.JK": "Konsumen", "CPIN.JK": "Konsumen",
    "KLBF.JK": "Konsumen",
    "ADRO.JK": "Energi", "PTBA.JK": "Energi",
    "ANTM.JK": "Energi", "MEDC.JK": "Energi", "PGAS.JK": "Energi",
    "GOTO.JK": "Teknologi"
}

SECTOR_EMOJI = {
    "Perbankan": "\U0001f3e6",
    "Telekomunikasi": "\U0001f4f1",
    "Industri": "\U0001f3ed",
    "Konsumen": "\U0001f6d2",
    "Energi": "\U000026a1",
    "Teknologi": "\U0001f4bb"
}


def clean_symbol(sym):
    return sym.replace(".JK", "")


def get_sector(symbol):
    return SECTOR_MAP.get(symbol, "Lainnya")


def sentiment_label(pct):
    if pct is None:
        return "Netral"
    if pct >= 0.5:
        return "Bullish"
    if pct <= -0.5:
        return "Bearish"
    return "Netral"


def ihsg_arrow(pct):
    if pct is None:
        return "\u25b6"
    return "\U0001f7e2" if pct >= 0 else "\U0001f534"


def format_number(n):
    if n is None:
        return "N/A"
    return f"{n:,.0f}"


def target_price(r):
    tp = r.get("sell") or r.get("target")
    if tp and tp > 0:
        return f"Rp{float(tp):,.0f}"
    return "-"


def full_reasoning(r):
    reasoning = r.get("reasoning", "")
    if reasoning and len(reasoning) > 10:
        return reasoning
    note = r.get("note", "")
    note_map = {
        "Rebound": "Fase rebound setelah tren turun, mendekati support.",
        "Accumulation": "Sideways dengan harga stabil, cocok akumulasi.",
        "Take Profit": "Mendekati jenuh beli, ambil profit.",
        "Uptrend": "Tren naik sehat, tahan posisi.",
        "Downtrend": "Tren turun, hindari beli.",
        "Overbought": "Zona overbought, risiko koreksi.",
        "Sideways": "Pergerakan sideways, belum ada sinyal jelas.",
    }
    return note_map.get(note, "-")


def build_narrative(data, ihsg_data=None):
    total = len(data)
    bullish = sum(1 for d in data if d.get("change_pct", 0) > 0)
    bearish = sum(1 for d in data if d.get("change_pct", 0) < 0)
    flat = total - bullish - bearish

    buys = sum(1 for d in data if d.get("signal") == "BUY")
    sells = sum(1 for d in data if d.get("signal") == "SELL")
    holds = total - buys - sells

    avg_change = sum(d.get("change_pct", 0) for d in data) / total if total else 0

    lines = []
    if avg_change > 0.5:
        lines.append("\U0001f7e2 *Pasar Hari Ini: Positif*")
        if ihsg_data and ihsg_data.get("change_pct", 0) > 0:
            lines.append("Mayoritas saham menghijau didorong sentimen positif di pasar.")
        else:
            lines.append("Rata-rata saham mencatat kenaikan meskipun IHSG cenderung flat.")
    elif avg_change < -0.5:
        lines.append("\U0001f534 *Pasar Hari Ini: Negatif*")
        lines.append("Tekanan jual mendominasi dengan mayoritas saham di zona merah.")
    else:
        lines.append("\U0001f7e1 *Pasar Hari Ini: Mixed/Cenderung Flat*")
        lines.append("Pergerakan terbatas dengan sentimen pasar yang berimbang.")

    lines.append(
        f"\U0001f4ca {bullish} naik \u00b7 {bearish} turun \u00b7 {flat} flat "
        f"(Rata-rata: {avg_change:+.2f}%)"
    )
    lines.append(
        f"\U0001f3c6 Sinyal: {buys} BUY \u00b7 {sells} SELL \u00b7 {holds} HOLD"
    )

    # Oversold / Overbought summary
    oversold = sum(1 for d in data if d.get("rsi", 50) < 35)
    overbought = sum(1 for d in data if d.get("rsi", 50) > 70)
    parts = []
    if oversold:
        parts.append(f"{oversold} oversold (RSI<35)")
    if overbought:
        parts.append(f"{overbought} overbought (RSI>70)")
    if parts:
        lines.append("\U0001f4cd " + " \u00b7 ".join(parts))

    return "\n".join(lines)


def build_sector_performance(data):
    sectors = {}
    for d in data:
        sec = get_sector(d["symbol"])
        if sec not in sectors:
            sectors[sec] = {"stocks": [], "total": 0, "count": 0}
        sectors[sec]["stocks"].append(d)
        sectors[sec]["total"] += d.get("change_pct", 0)
        sectors[sec]["count"] += 1

    lines = []
    lines.append("\U0001f4ca *Kinerja Sektor*")

    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]["total"] / x[1]["count"], reverse=True)

    for sec, info in sorted_sectors:
        avg = info["total"] / info["count"]
        emoji = SECTOR_EMOJI.get(sec, "\U0001f4cc")
        arrow = "\U0001f7e2" if avg >= 0 else "\U0001f534"
        gainers = sum(1 for s in info["stocks"] if s.get("change_pct", 0) > 0)
        losers = info["count"] - gainers
        best = max(info["stocks"], key=lambda s: s.get("change_pct", 0))
        worst = min(info["stocks"], key=lambda s: s.get("change_pct", 0))
        lines.append(
            f"{emoji} *{sec}*: {arrow} {avg:+.2f}% ({gainers}\U0001f7e2/{losers}\U0001f534)"
        )
        lines.append(
            f"   \U0001f3c6 {clean_symbol(best['symbol'])} {best.get('change_pct',0):+.2f}%"
            f"  \U0001f4a9 {clean_symbol(worst['symbol'])} {worst.get('change_pct',0):+.2f}%"
        )
    return "\n".join(lines)


def format_market_pulse(data, ihsg_data=None, is_daily=False):
    now = datetime.now()
    label = "DAILY CLOSING REPORT" if is_daily else "\U0001f4e1 MARKET PULSE"
    header_time = now.strftime("%d %b %Y \u2014 %H:%M WIB")

    gainers = sorted(data, key=lambda x: x.get("change_pct", 0), reverse=True)[:3]
    losers = sorted(data, key=lambda x: x.get("change_pct", 0))[:3]
    top3 = sorted(
        [r for r in data if r.get("is_top3")],
        key=lambda x: (x.get("rank", 99), -x.get("score", 0)),
    )[:3]

    lines = []

    # ── Header ──
    lines.append(f"\U0001f4ca *{label}*")
    lines.append(f"\U0001f550 {header_time}")
    if is_daily:
        lines.append("\U0001f3af *Ringkasan Penutupan Pasar*")
    lines.append("")
    lines.append(SEP)
    lines.append("")

    # ── Market Narrative ──
    lines.append(build_narrative(data, ihsg_data))
    lines.append("")

    # ── IHSG ──
    if ihsg_data:
        pct = ihsg_data.get("change_pct")
        price = ihsg_data.get("price")
        arrow = ihsg_arrow(pct)
        label_sentimen = sentiment_label(pct)
        sign = "+" if pct is not None and pct >= 0 else ""
        lines.append(f"\U0001f4c8 *IHSG*")
        lines.append(f"`{format_number(price)}` ({sign}{pct:.2f}%) \u2014 {arrow} {label_sentimen}")
    else:
        lines.append("\U0001f4c8 *IHSG*\n\u2014 Data tidak tersedia")
    lines.append("")

    # ── Sector Performance ──
    lines.append(SEP)
    lines.append("")
    lines.append(build_sector_performance(data))
    lines.append("")

    # ── Top Gainers ──
    if gainers:
        lines.append(SEP)
        lines.append("")
        lines.append(f"\U0001f7e2 *Top Gainers*")
        for r in gainers:
            sym = clean_symbol(r["symbol"])
            pct = r.get("change_pct", 0)
            sig = r.get("signal", "HOLD")
            rsi = r.get("rsi", 50)
            lines.append(
                f"\U0001f7e2 `{sym}` +{pct:.2f}% \u2014 {sig} (RSI {rsi})"
            )
    lines.append("")

    # ── Top Losers ──
    if losers:
        lines.append(f"\U0001f534 *Top Losers*")
        for r in losers:
            sym = clean_symbol(r["symbol"])
            pct = r.get("change_pct", 0)
            sig = r.get("signal", "HOLD")
            rsi = r.get("rsi", 50)
            lines.append(
                f"\U0001f534 `{sym}` {pct:.2f}% \u2014 {sig} (RSI {rsi})"
            )
    lines.append("")

    # ── Signals Alert ──
    signals = [r for r in data if r.get("signal") in ("BUY", "SELL")]
    if signals:
        lines.append(SEP)
        lines.append("")
        lines.append(f"\U0001f514 *Signal Alert*")
        for r in signals[:5]:
            sym = clean_symbol(r["symbol"])
            icon = "\U0001f7e2" if r["signal"] == "BUY" else "\U0001f534"
            conf = r.get("confidence", 0)
            bar = "\u2588" * int(conf / 10) + "\u2591" * (10 - int(conf / 10))
            lines.append(
                f"{icon} `{sym}` **{r['signal']}** | Skor: {r['score']:+d} | Keyakinan: {conf}%"
            )
            lines.append(f"   \U0001f4ac {full_reasoning(r)}")
    lines.append("")

    # ── TOP 3 PICKS ──
    if top3:
        lines.append(SEP)
        lines.append("")
        lines.append(f"\U0001f3c6 *TOP 3 RECOMMENDATIONS*")
        for r in top3:
            rank = r.get("rank", 0)
            medal = MEDAL.get(rank, f"#{rank}")
            sym = clean_symbol(r["symbol"])
            sig = r.get("signal", "HOLD")
            score = r.get("score", 0)
            conf = r.get("confidence", 0)
            tp = target_price(r)
            sl = f"Rp{r.get('sl',0):,.0f}" if r.get("sl") else "-"
            rr = r.get("rr", 0)
            reason = full_reasoning(r)
            lines.append("")
            lines.append(
                f"{medal} `{sym}` \u2014 **{sig}** (Skor: {score:+d} | Keyakinan: {conf}%)"
            )
            lines.append(f"   \U0001f3af Target: {tp} | SL: {sl} | R/R: {rr:.2f}")
            lines.append(f"   \U0001f4d6 {reason[:200]}")
    lines.append("")

    # ── Market Outlook ──
    lines.append(SEP)
    lines.append("")
    lines.append("\U0001f52e *Market Outlook*")

    ihsg_pct = ihsg_data.get("change_pct", 0) if ihsg_data else 0
    buy_count = sum(1 for d in data if d.get("signal") == "BUY")
    sell_count = sum(1 for d in data if d.get("signal") == "SELL")
    avg_rsi = sum(d.get("rsi", 50) for d in data) / len(data) if data else 50

    if is_daily:
        if ihsg_pct > 0.5 and buy_count > sell_count:
            outlook = "Sentimen positif masih dominan. Potensi lanjutan penguatan di sesi berikutnya jika support bertahan."
        elif ihsg_pct < -0.5 and sell_count > buy_count:
            outlook = "Tekanan jual masih ada. Waspada koreksi lanjutan jika level support ditembus."
        elif avg_rsi > 65:
            outlook = "Rata-rata RSI cukup tinggi, waspadai potensi koreksi teknikal dalam waktu dekat."
        elif avg_rsi < 40:
            outlook = "Rata-rata RSI mendekati oversold, peluang technical rebound terbuka."
        else:
            outlook = "Pergerakan diperkirakan masih terbatas dengan kecenderungan sideways. Pantau sentimen global dan data makro."
    else:
        if buy_count > sell_count * 1.5:
            outlook = "Sinyal beli mendominasi. Prospek positif untuk sisa sesi hari ini, pantau level resistance terdekat."
        elif sell_count > buy_count * 1.5:
            outlook = "Sinyal jual meningkat. Disarankan hati-hati, perhatikan manajemen risiko."
        else:
            outlook = "Pasar bergerak mixed. Disarankan wait and see sambil menunggu konfirmasi arah yang lebih jelas."

    lines.append(f"\U0001f4ac {outlook}")
    lines.append("")

    # ── Footer ──
    lines.append(SEP)
    lines.append("")
    pulse_line_data = data
    if pulse_line_data:
        b = sum(1 for d in pulse_line_data if d.get("change_pct", 0) > 0)
        bj = sum(1 for d in pulse_line_data if d.get("change_pct", 0) < 0)
        fl = len(pulse_line_data) - b - bj
        lines.append(f"\U0001f4ca *Market Pulse:* {' \u00b7 '.join(filter(None, [f'\U0001f7e2 {b} naik' if b else '', f'\U0001f534 {bj} turun' if bj else '', f'\u26aa {fl} flat' if fl else '']))}")
    lines.append("")
    lines.append(
        "\U0001f4cc *Disclaimer:* Informasi ini merupakan hasil analisis otomatis "
        "berbasis data historis dan tidak dapat dijadikan sebagai rekomendasi "
        "investasi resmi. Keputusan investasi sepenuhnya berada di tangan pengguna. "
        "Selalu lakukan riset mandiri sebelum bertransaksi."
    )

    return "\n".join(lines)