"""
⚡ AURA PRO - Edizione Onesta ⚡
================================
Novità rispetto alla versione precedente:
1. Confidence FAKE rimossa -> statistiche REALI da database segnali (win rate effettivo)
2. RSI di Wilder corretto (smoothing esponenziale, non media semplice)
3. Timeframe M3/M10 gestiti con resample (prima: M3 analizzava candele da 2 min - BUG)
4. Allineamento UTC per countdown e scadenze (prima: ora locale del server - BUG)
5. Segnali salvati su SQLite + verifica esiti automatica dopo la scadenza
6. Backtest integrato per validare la regola sui dati storici
7. Cache dei download Yahoo (scanner molto più veloce)
8. Token Telegram da st.secrets (mai hardcoded)
9. Stato invalidato quando cambi asset/timeframe (prima mostrava segnali fantasma - BUG)

NOTA ONESTA: i prezzi "OTC" di Pocket Option sono sintetici e generati dal broker.
Questo strumento usa dati di mercato REALI come proxy: la correlazione con l'OTC
del broker NON è garantita. Usa il database delle statistiche per scoprire se
la regola funziona davvero sul tuo mercato.
"""

from datetime import datetime, timedelta, timezone
import sqlite3
import requests
import pandas as pd
import yfinance as yf
import streamlit as st
import streamlit.components.v1 as components

# ============================= CONFIG =============================
st.set_page_config(page_title="Aura Pro", page_icon="⚡", layout="centered")

DB_PATH = "aura_signals.db"
PAYOUT = 0.85  # <-- modifica col payout reale del broker (0.85 = vinci 85% della puntata)
MIN_SAMPLES = 20  # campioni minimi per mostrare una statistica "validata"

st.markdown(
    """
    <style>
    .main { background-color: #121212; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold;
        background-color: #1f1f1f; color: #00ffcc; border: 1px solid #333333; }
    .stButton>button:hover { background-color: #333333; color: #ffffff; border-color: #00ffcc; }
    .analysis-box { background-color: #1a1a1a; padding: 15px; border-radius: 8px;
        border: 1px solid #00ffcc; margin-top: 15px; }
    .standby-box { background-color: #1a1a1a; padding: 15px; border-radius: 8px;
        border: 1px solid #ff4444; margin-top: 15px; text-align: center;
        color: #ff4444; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⚡ AURA PRO ⚡")

# ============================= DATABASE =============================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT, asset TEXT, ticker TEXT, timeframe TEXT,
            direction TEXT, entry_time_utc TEXT, rsi REAL,
            outcome TEXT DEFAULT NULL, checked INTEGER DEFAULT 0
        )""")
    conn.commit()
    conn.close()

def save_signal(asset, ticker, tf, direction, entry_utc, rsi):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO signals (created_at, asset, ticker, timeframe, direction, entry_time_utc, rsi) VALUES (?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), asset, ticker, tf, direction, entry_utc, rsi))
    conn.commit()
    conn.close()

def get_signals_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM signals WHERE checked=1 AND outcome IS NOT NULL", conn)
    conn.close()
    return df

init_db()

# ============================= DATI =============================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(ticker, interval, period="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, timeout=10)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except Exception:
        return pd.DataFrame()

def resample_to(df, rule):
    return df.resample(rule).agg(
        {"Open": "first", "High": "max", "Low": "min",
         "Close": "last", "Volume": "sum"}).dropna()

# Mappa timeframe -> (intervallo Yahoo, regola resample)
TF_MAP = {
    "M1 (60s)": ("1m", None),
    "M3 (180s)": ("1m", "3min"),
    "M5 (300s)": ("5m", None),
    "M10 (600s)": ("5m", "10min"),
    "M15 (900s)": ("15m", None),
}
TF_SECONDS = {"M1 (60s)": 60, "M3 (180s)": 180, "M5 (300s)": 300,
              "M10 (600s)": 600, "M15 (900s)": 900}

# ============================= INDICATORI =============================
def wilder_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)

def add_indicators(df):
    df = df.copy()
    close = df["Close"]
    df["rsi"] = wilder_rsi(close)
    df["ema9"] = close.ewm(span=9, adjust=False).mean()
    df["ema21"] = close.ewm(span=21, adjust=False).mean()
    sma20 = close.rolling(window=20).mean()
    std20 = close.rolling(window=20).std()
    df["bb_upper"] = sma20 + 2 * std20
    df["bb_lower"] = sma20 - 2 * std20
    bullish = df["ema9"] > df["ema21"]
    buy = (bullish & (df["rsi"] <= 45)) | (close <= df["bb_lower"] * 1.001)
    sell = (~bullish & (df["rsi"] >= 55)) | (close >= df["bb_upper"] * 0.999)
    df["signal"] = 0
    df.loc[buy & ~sell, "signal"] = 1
    df.loc[sell & ~buy, "signal"] = -1
    return df

def load_analysis_frame(ticker, tf_label, period="1d"):
    iv, rule = TF_MAP[tf_label]
    df = fetch_data(ticker, iv, period=period)
    if df.empty:
        return df
    if rule:
        df = resample_to(df, rule)
    if len(df) < 25:
        return pd.DataFrame()
    return add_indicators(df)

# ============================= UTILITÀ TEMPO (UTC!) =============================
def utc_now():
    return datetime.now(timezone.utc)

def seconds_to_next_candle(tf_sec):
    now = utc_now()
    secs = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1e6
    wait = tf_sec - (secs % tf_sec)
    return max(1, int(round(wait)))

def next_candle_close_utc(tf_sec):
    return utc_now() + timedelta(seconds=seconds_to_next_candle(tf_sec))

# ============================= TELEGRAM (da secrets) =============================
def send_telegram(message):
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
    except Exception:
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": message,
                                "parse_mode": "Markdown"}, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

# ============================= VERIFICA ESITI =============================
def check_pending_outcomes():
    conn = sqlite3.connect(DB_PATH)
    pending = conn.execute(
        "SELECT id, ticker, timeframe, direction, entry_time_utc FROM signals WHERE checked=0").fetchall()
    checked = 0
    for sid, ticker, tf, direction, entry_str in pending:
        df = load_analysis_frame(ticker, tf)
        if df.empty:
            continue
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        entry_ts = pd.to_datetime(entry_str)
        candles = df[df.index >= entry_ts]
        if candles.empty:
            continue  # mercato chiuso o dato non ancora disponibile: riprova dopo
        candle = candles.iloc[0]
        o, c = float(candle["Open"]), float(candle["Close"])
        if abs(c - o) < 1e-12:
            outcome = "TIE"
        elif ("BUY" in direction and c > o) or ("SELL" in direction and c < o):
            outcome = "WIN"
        else:
            outcome = "LOSS"
        conn.execute("UPDATE signals SET outcome=?, checked=1 WHERE id=?", (outcome, sid))
        checked += 1
    conn.commit()
    conn.close()
    return checked

# ============================= STATISTICHE REALI =============================
def real_stats_for(asset, tf_label):
    """Win rate effettivo dal DB. Ritorna (vinti, persi, pareggi, win_rate%)."""
    df = get_signals_df()
    if df.empty:
        return 0, 0, 0, None
    sub = df[(df["asset"] == asset) & (df["timeframe"] == tf_label)]
    w = int((sub["outcome"] == "WIN").sum())
    l = int((sub["outcome"] == "LOSS").sum())
    t = int((sub["outcome"] == "TIE").sum())
    wr = (w / (w + l) * 100) if (w + l) > 0 else None
    return w, l, t, wr

# ============================= BACKTEST =============================
def backtest(ticker, tf_label, days=30):
    df = load_analysis_frame(ticker, tf_label, period=f"{days}d")
    if len(df) < 30:
        return None
    sig = df["signal"].values
    opens, closes = df["Open"].values, df["Close"].values
    w = l = t = 0
    for i in range(len(df) - 1):
        if sig[i] == 0:
            continue
        o, c = opens[i + 1], closes[i + 1]
        if abs(c - o) < 1e-12:
            t += 1
        elif (sig[i] == 1 and c > o) or (sig[i] == -1 and c < o):
            w += 1
        else:
            l += 1
    total = w + l
    wr = w / total * 100 if total else 0.0
    return {"signals": total, "wins": w, "losses": l, "ties": t, "win_rate": wr}

# ============================= ASSET =============================
forex_dict = {
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X", "USD/CAD": "USDCAD=X", "USD/CHF": "USDCHF=X",
    "NZD/USD": "NZDUSD=X", "GBP/JPY": "GBPJPY=X", "EUR/JPY": "EURJPY=X",
    "EUR/GBP": "EURGBP=X", "AUD/JPY": "AUDJPY=X", "EUR/AUD": "EURAUD=X",
    "GBP/AUD": "GBPAUD=X", "EUR/CAD": "EURCAD=X", "GBP/CAD": "GBPCAD=X",
    "AUD/CAD": "AUDCAD=X", "EUR/CHF": "EURCHF=X", "GBP/CHF": "GBPCHF=X",
    "CHF/JPY": "CHFJPY=X",
}
# NOTA: "OTC" usa gli stessi dati reali come proxy. I prezzi OTC del broker
# sono sintetici: questi segnali vanno validati con le statistiche reali.
otc_dict = {k + " OTC": v for k, v in forex_dict.items()}
crypto_dict = {"BTC OTC": "BTC-USD", "ETH OTC": "ETH-USD", "SOL OTC": "SOL-USD"}

MODE_FOREX, MODE_OTC, MODE_CRYPTO = "Forex Reale", "Asset OTC Valute", "Crypto OTC"

mercato_tipo = st.radio("Seleziona Modalità:",
                        ["🚀 Scanner Globale", MODE_FOREX, MODE_OTC, MODE_CRYPTO],
                        horizontal=True)

selected_display, selected_asset = None, None
if mercato_tipo != "🚀 Scanner Globale":
    if mercato_tipo == MODE_FOREX:
        source = forex_dict
    elif mercato_tipo == MODE_OTC:
        source = otc_dict
        st.warning("⚠️ I prezzi OTC del broker sono sintetici: qui usi dati di mercato "
                   "reali come proxy. Valida la regola con le statistiche reali prima di operare.")
    else:
        source = crypto_dict
    selected_display = st.selectbox("Seleziona Asset", list(source.keys()))
    selected_asset = source[selected_display]

st.markdown("### ⏰ Timeframe")
tf_choice = st.radio("Scegli la scadenza:", list(TF_SECONDS.keys()),
                     horizontal=True, key="tf")
tf_sec = TF_SECONDS[tf_choice]

# ---- invalidazione stato quando cambi selezione (fix "segnale fantasma") ----
state_key = f"{mercato_tipo}|{selected_display}|{tf_choice}"
if st.session_state.get("active_key") != state_key:
    for k in ["sig_direction", "sig_entry", "sig_rsi", "sig_details", "signal_ready"]:
        st.session_state.pop(k, None)
    st.session_state["active_key"] = state_key

# ============================= SIDEBAR: STATISTICHE E BACKTEST =============================
with st.sidebar:
    st.markdown("### 📊 Le tue statistiche reali")
    breakeven = 1 / (1 + PAYOUT) * 100
    st.caption(f"Payout impostato: {PAYOUT*100:.0f}% → serve un win rate > "
               f"{breakeven:.1f}% per essere in profitto.")
    stats_df = get_signals_df()
    if not stats_df.empty:
        w = int((stats_df.outcome == "WIN").sum())
        l = int((stats_df.outcome == "LOSS").sum())
        t = int((stats_df.outcome == "TIE").sum())
        if w + l > 0:
            wr = w / (w + l) * 100
            color = "🟢" if wr >= breakeven else "🔴"
            st.metric(f"{color} Win rate reale (globale)",
                      f"{wr:.1f}%", f"{w}W / {l}L / {t}T")
        by_asset = (stats_df[stats_df.outcome != "TIE"]
                    .groupby("asset")["outcome"]
                    .agg(total="count", wins=lambda s: (s == "WIN").sum()))
        by_asset["wr%"] = (by_asset.wins / by_asset.total * 100).round(1)
        st.dataframe(by_asset[["total", "wr%"]], use_container_width=True)
    else:
        st.info("Nessun segnale verificato ancora. Genera segnali e attendi le scadenze.")

    st.markdown("---")
    st.markdown("### 🔬 Backtest della regola (30 giorni)")
    bt_target = st.selectbox("Asset da testare",
                             list(forex_dict.keys()),
                             key="bt_asset") if mercato_tipo == "🚀 Scanner Globale" else None
    if mercato_tipo != "🚀 Scanner Globale":
        bt_target = selected_display
    if bt_target:
        if st.button("Esegui backtest"):
            bt_ticker = (forex_dict | otc_dict | crypto_dict)[bt_target]
            res = backtest(bt_ticker, tf_choice, days=30)
            if res is None:
                st.error("Dati insufficienti per il backtest.")
            else:
                verdict = "🟢 Sopra breakeven" if res["win_rate"] >= breakeven else "🔴 Sotto breakeven"
                st.write(f"Segnali: **{res['signals']}** | {res['wins']}W / "
                         f"{res['losses']}L / {res['ties']}T")
                st.write(f"Win rate storico: **{res['win_rate']:.1f}%** → {verdict}")
                st.caption("Se è sotto breakeven, la regola perde soldi su questo "
                           "asset/timeframe: NON operarla, cambia asset o timeframe.")

# ============================= ANALISI LIVE =============================
def run_analysis(ticker, tf_label):
    df = load_analysis_frame(ticker, tf_label)
    if df.empty:
        return None
    row = df.iloc[-1]
    rsi = float(row["rsi"])
    sig = int(row["signal"])
    details = {
        "RSI (14, Wilder)": f"{rsi:.1f}",
        "Trend (EMA 9/21)": "BULLISH 🟢" if row["ema9"] > row["ema21"] else "BEARISH 🔴",
        "Bollinger": ("Sotto banda inferiore" if float(row["Close"]) <= float(row["bb_lower"])
                      else "Sopra banda superiore" if float(row["Close"]) >= float(row["bb_upper"])
                      else "Nel canale"),
    }
    return {"signal": sig, "rsi": rsi, "details": details}

col1, col2 = st.columns(2)
with col1:
    run_clicked = st.button("🚀 ANALIZZA / SCANSIONA")
with col2:
    if st.button("🔄 Verifica esiti scaduti"):
        n = check_pending_outcomes()
        st.success(f"{n} esiti aggiornati.")

# verifica automatica a ogni rerun (zero costo se non ci sono pending)
check_pending_outcomes()

if run_clicked:
    if mercato_tipo == "🚀 Scanner Globale":
        results = []
        combined = {**forex_dict, **otc_dict}
        bar = st.progress(0)
        for i, (name, ticker) in enumerate(combined.items()):
            r = run_analysis(ticker, tf_choice)
            if r and r["signal"] != 0:
                w, l, t, wr = real_stats_for(name, tf_choice)
                validated = wr is not None and (w + l) >= MIN_SAMPLES
                results.append({
                    "asset": name,
                    "direction": "BUY 🟢" if r["signal"] == 1 else "SELL 🔴",
                    "entry": next_candle_close_utc(tf_sec).strftime("%H:%M:%S"),
                    "rsi": r["rsi"],
                    "live_wr": f"{wr:.1f}% ({w}W/{l}L)" if validated else f"non validato ({w+l} campioni)",
                })
                save_signal(name, ticker, tf_choice,
                            "BUY" if r["signal"] == 1 else "SELL",
                            next_candle_close_utc(tf_sec).isoformat(), r["rsi"])
            bar.progress((i + 1) / len(combined))
        bar.empty()
        st.session_state["scanner_results"] = results
    else:
        r = run_analysis(selected_asset, tf_choice)
        if r is None:
            st.session_state["signal_ready"] = False
            st.error("Dati insufficienti (mercato chiuso o nessuna candela).")
        elif r["signal"] == 0:
            st.session_state["signal_ready"] = False
            st.session_state["sig_details"] = r["details"]
            st.session_state["sig_standby"] = True
        else:
            entry = next_candle_close_utc(tf_sec)
            st.session_state.update({
                "signal_ready": True, "sig_standby": False,
                "sig_direction": "BUY 🟢" if r["signal"] == 1 else "SELL 🔴",
                "sig_entry": entry.strftime("%H:%M:%S UTC"),
                "sig_rsi": r["rsi"], "sig_details": r["details"],
            })
            w, l, t, wr = real_stats_for(selected_display, tf_choice)
            st.session_state["sig_wr"] = wr
            st.session_state["sig_samples"] = w + l
            save_signal(selected_display, selected_asset, tf_choice,
                        "BUY" if r["signal"] == 1 else "SELL", entry.isoformat(), r["rsi"])
            send_telegram(
                f"⚡ AURA PRO\n{selected_display} | {tf_choice}\n"
                f"Direzione: {st.session_state['sig_direction']}\n"
                f"Entrata: {st.session_state['sig_entry']}\nRSI: {r['rsi']:.1f}")

# ============================= OUTPUT =============================
if mercato_tipo == "🚀 Scanner Globale" and "scanner_results" in st.session_state:
    res = st.session_state["scanner_results"]
    st.markdown("### 🎯 SEGNALI TROVATI")
    if res:
        for r in res:
            st.markdown(f"""<div class="analysis-box">
                <h4>{r['asset']} → <b>{r['direction']}</b></h4>
                <p>Entrata (UTC): {r['entry']} | RSI: {r['rsi']:.1f} |
                Win rate reale: {r['live_wr']}</p></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="standby-box">
            <h4>🛑 NESSUN SEGNALE</h4><p>Riprova tra qualche istante o cambia timeframe.</p>
            </div>""", unsafe_allow_html=True)

elif mercato_tipo != "🚀 Scanner Globale":
    if st.session_state.get("sig_standby"):
        d = st.session_state.get("sig_details", {})
        st.markdown(f"""<div class="standby-box">
            <h4>🛑 STAND BY: NESSUNA CONFLUENZA</h4>
            <p style="text-align:left; color:#fff;">RSI: {d.get('RSI (14, Wilder)', 'N/A')} |
            Trend: {d.get('Trend (EMA 9/21)', 'N/A')} | {d.get('Bollinger', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)
    elif st.session_state.get("signal_ready"):
        st.markdown(f"""<div class="analysis-box">
            <h4>🎯 SEGNALE: {st.session_state['sig_direction']}</h4>
            <p><b>Asset:</b> {selected_display} | <b>Scadenza:</b> {tf_choice}</p>
            <p><b>Entrata (chiusura candela):</b> {st.session_state['sig_entry']}</p>
            <p><b>RSI:</b> {st.session_state['sig_rsi']:.1f} |
            <b>Trend:</b> {st.session_state['sig_details'].get('Trend (EMA 9/21)')} |
            <b>Bollinger:</b> {st.session_state['sig_details'].get('Bollinger')}</p>
            </div>""", unsafe_allow_html=True)

        samples = st.session_state.get("sig_samples", 0)
        wr = st.session_state.get("sig_wr")
        if wr is not None and samples >= MIN_SAMPLES:
            ok = wr >= 1 / (1 + PAYOUT) * 100
            st.metric("Win rate REALE di questa regola su questo asset",
                      f"{wr:.1f}%", "sopra breakeven ✅" if ok else "sotto breakeven ❌",
                      delta_color="normal" if ok else "inverse")
        else:
            st.info(f"Questa regola ha solo {samples} segnali verificati su questo asset "
                    f"(minimo {MIN_SAMPLES} per validarla). Prima di puntare soldi, "
                    "lascia lavorare il database: genera segnali e premi 'Verifica esiti scaduti'.")

        # Countdown sincronizzato UTC
     