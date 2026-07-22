from datetime import datetime

MEDAL = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}

SEP = "\u2501" * 25


def clean_symbol(sym):
    return sym.replace(".JK", "")


def sentiment_label(pct):
    if pct is None:
        return "Neutral"
    if pct >= 0.5:
        return "Bullish"
    if pct <= -0.5:
        return "Bearish"
    return "Neutral"


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


def brief_reason(r):
    note = r.get("note", "")
    reasoning = r.get("reasoning", "")
    if reasoning and len(reasoning) > 10:
        return reasoning[:120]
    if note:
        note_map = {
            "Rebound": "Fase rebound setelah tren turun, mendekati support.",
            "Accumulation": "Sideways dengan harga stabil, cocok akumulasi.",
            "Take Profit": "Mendekati jenuh beli, ambil profit.",
            "Uptrend": "Tren naik sehat, tahan posisi.",
            "Downtrend": "Tren turun, hindari beli.",
            "Overbought": "Zona overbought, risiko koreksi.",
            "Sideways": "Pergerakan sideways, belum ada sinyal jelas.",
        }
        return note_map.get(note, note)
    return "-"


def build_signal_pct_line(data):
    if not data:
        return ""
    bullish = sum(1 for d in data if d.get("change_pct", 0) > 0)
    bearish = sum(1 for d in data if d.get("change_pct", 0) < 0)
    flat = len(data) - bullish - bearish
    parts = []
    if bullish:
        parts.append(f"\U0001f7e2 {bullish} naik")
    if bearish:
        parts.append(f"\U0001f534 {bearish} turun")
    if flat:
        parts.append(f"\u26aa {flat} flat")
    return " \u00b7 ".join(parts)


def format_market_pulse(data, ihsg_data=None, is_daily=False):
    now = datetime.now()
    label = "DAILY MARKET PULSE & ANALYSIS" if is_daily else "MARKET PULSE & ANALYSIS"
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
    lines.append(SEP)
    lines.append("")

    # ── IHSG ──
    if ihsg_data:
        pct = ihsg_data.get("change_pct")
        price = ihsg_data.get("price")
        arrow = ihsg_arrow(pct)
        label_sentimen = sentiment_label(pct)
        lines.append(
            f"\U0001f4c8 *IHSG*"
        )
        sign = "+" if pct is not None and pct >= 0 else ""
        lines.append(
            f"`{format_number(price)}` ({sign}{pct:.2f}%) \u2014 {arrow} {label_sentimen}"
        )
    else:
        lines.append("\U0001f4c8 *IHSG*\n\u2014 Data tidak tersedia")
    lines.append("")

    # ── Top Gainers ──
    if gainers:
        lines.append(f"\u2501\u2501\u2501 Top Gainers \u2501\u2501\u2501")
        for r in gainers:
            sym = clean_symbol(r["symbol"])
            pct = r.get("change_pct", 0)
            sig = r.get("signal", "HOLD")
            lines.append(f"\U0001f7e2 `{sym}` +{pct:.2f}% \u2014 {sig}")
    lines.append("")

    # ── Top Losers ──
    if losers:
        lines.append(f"\u2501\u2501\u2501 Top Losers \u2501\u2501\u2501")
        for r in losers:
            sym = clean_symbol(r["symbol"])
            pct = r.get("change_pct", 0)
            sig = r.get("signal", "HOLD")
            lines.append(f"\U0001f534 `{sym}` {pct:.2f}% \u2014 {sig}")
    lines.append("")

    # ── Signals ──
    signals = [r for r in data if r.get("signal") in ("BUY", "SELL")]
    if signals:
        lines.append(f"\u2501\u2501\u2501 Signal Alert \u2501\u2501\u2501")
        for r in signals[:5]:
            sym = clean_symbol(r["symbol"])
            icon = "\U0001f7e2" if r["signal"] == "BUY" else "\U0001f534"
            lines.append(
                f"{icon} `{sym}` **{r['signal']}** (skor: {r['score']:+d})"
            )
    lines.append("")

    # ── TOP 3 PICKS ──
    if top3:
        lines.append(SEP)
        lines.append("")
        lines.append("\U0001f3c6 *TOP 3 PICKS RECOGNITION*")
        for r in top3:
            rank = r.get("rank", 0)
            medal = MEDAL.get(rank, f"#{rank}")
            sym = clean_symbol(r["symbol"])
            sig = r.get("signal", "HOLD")
            score = r.get("score", 0)
            tp = target_price(r)
            reason = brief_reason(r)
            lines.append("")
            lines.append(
                f"{medal} `{sym}` \u2014 **{sig}**"
            )
            lines.append(f"   \U0001f3af Skor: `{score:+d}` | Target: {tp}")
            lines.append(f"   \U0001f4ac {reason}")
    lines.append("")

    # ── Footer ──
    lines.append(SEP)
    pulse_line = build_signal_pct_line(data)
    if pulse_line:
        lines.append(f"\U0001f4ca *Market Pulse:* {pulse_line}")
    lines.append("")
    lines.append(
        "\U0001f4cc *Disclaimer:* Informasi ini merupakan hasil analisis otomatis "
        "berbasis data historis dan tidak dapat dijadikan sebagai rekomendasi "
        "investasi resmi. Keputusan investasi sepenuhnya berada di tangan pengguna. "
        "Selalu lakukan riset mandiri sebelum bertransaksi."
    )

    return "\n".join(lines)
