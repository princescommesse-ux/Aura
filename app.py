import math
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

st.set_page_config(page_title="Aura Pro", page_icon="⚡", layout="centered")

st.markdown(
    """
    <style>
    .main { background-color: #121212; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #1f1f1f; color: #00ffcc; border: 1px solid #333333; }
    .stButton>button:hover { background-color: #333333; color: #ffffff; border-color: #00ffcc; }
    .market-badge { background-color: #1f1f1f; padding: 8px 12px; border-radius: 6px; border: 1px solid #333333; font-size: 14px; margin-bottom: 15px; text-align: center; }
    .analysis-box { background-color: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #00ffcc; margin-top: 15px; }
    .standby-box { background-color: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #ff4444; margin-top: 15px; color: #ff4444; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⚡ AURA PRO ⚡")
st.caption("Strumento di studio. Nessun segnale garantisce profitto: guarda le statistiche storiche reali qui sotto.")

PAIRS = {
    "🇪🇺🇺🇸 EUR/USD": "EURUSD=X", "🇬🇧🇺🇸 GBP/USD": "GBPUSD=X", "🇺🇸🇯🇵 USD/JPY": "USDJPY=X",
    "🇦🇺🇺🇸 AUD/USD": "AUDUSD=X", "🇺🇸🇨🇦 USD/CAD": "USDCAD=X", "🇺🇸🇨🇭 USD/CHF": "USDCHF=X",
    "🇳🇿🇺🇸 NZD/USD": "NZDUSD=X", "🇬🇧🇯🇵 GBP/JPY": "GBPJPY=X", "🇪🇺🇯🇵 EUR/JPY": "EURJPY=X",
    "🇪🇺🇬🇧 EUR/GBP": "EURGBP=X", "🇦🇺🇯🇵 AUD/JPY": "AUDJPY=X", "🇪🇺🇦🇺 EUR/AUD": "EURAUD=X",
    "🇬🇧🇦🇺 GBP/AUD": "GBPAUD=X", "🇪🇺🇨🇦 EUR/CAD": "EURCAD=X", "🇬🇧🇨🇦 GBP/CAD": "GBPCAD=X",
    "🇦🇺🇨🇦 AUD/CAD": "AUDCAD=X", "🇪🇺🇨🇭 EUR/CHF": "EURCHF=X", "🇬🇧🇨🇭 GBP/CHF": "GBPCHF=X",
    "🇨🇭🇯🇵 CHF/JPY": "CHFJPY=X",
}

# timeframe -> (secondi, intervallo da scaricare, regola di resample o None)
TIMEFRAMES = {
    "M1": (60, "1m", None),
    "M3": (180, "1m", "3min"),
    "M5": (300, "5m", None),
    "M10": (600, "5m", "10min"),
    "M15": (900, "15m", None),
}

PAYOUT_DEFAULT = 85

selected_display = st.selectbox("Coppia", list(PAIRS.keys()))
ticker = PAIRS[selected_display]

st.markdown("### ⏰ Timeframe")
tf_choice = st.radio("Scadenza = 1 candela", list(TIMEFRAMES.keys()), horizontal=True)
tf_seconds, tf_interval, tf_resample = TIMEFRAMES[tf_choice]

payout_pct = st.slider("Payout del broker (%)", 60, 95, PAYOUT_DEFAULT)
payout = payout_pct / 100
breakeven = 1 / (1 + payout)


# ---------- sessioni / tempo (tutto in UTC) ----------
def get_market_sessions() -> str:
    h = datetime.now(timezone.utc).hour
    active = []
    if 0 <= h < 9:
        active.append("Tokyo 🟢")
    if 8 <= h < 16:
        active.append("London 🟢")
    if 13 <= h < 21:
        active.append("New York 🟢")
    return " | ".join(active) if active else "Bassa liquidità 🌙"


st.markdown(f'<div class="market-badge">🌐 <b>Sessioni (UTC):</b> {get_market_sessions()}</div>',
            unsafe_allow_html=True)


def seconds_to_next_candle(seconds: int) -> int:
    return max(1, int(seconds - (time.time() % seconds)))


def next_candle_time_utc(seconds: int) -> str:
    t = datetime.now(timezone.utc) + timedelta(seconds=seconds_to_next_candle(seconds))
    return t.strftime("%H:%M:%S UTC")


# ---------- dati ----------
@st.cache_data(ttl=30, show_spinner=False)
def load_data(symbol: str, interval: str, resample: str | None) -> pd.DataFrame:
    df = yf.download(symbol, period="5d", interval=interval, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()
    if resample and not df.empty:
        df = df["Close"].resample(resample).last().dropna().to_frame("Close")
    return df[["Close"]]


# ---------- indicatori ----------
def rsi_wilder(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + gain / loss)


def compute_signals(close: pd.Series):
    rsi = rsi_wilder(close)
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    bull = ema9 > ema21
    sma, sd = close.rolling(20).mean(), close.rolling(20).std()
    upper, lower = sma + 2 * sd, sma - 2 * sd
    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    macd_bull = macd > macd.ewm(span=9, adjust=False).mean()

    buy = bull & (rsi <= 55) & (close <= lower * 1.01)
    sell = (~bull) & (rsi >= 45) & (close >= upper * 0.99)
    sig = pd.Series(0, index=close.index)
    sig[buy] = 1
    sig[sell] = -1
    return sig, rsi, bull, upper, lower, macd_bull


def wilson_interval(wins: int, n: int, z: float = 1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = wins / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def historical_stats(close: pd.Series, sig: pd.Series) -> dict:
    move = close.shift(-1) - close
    mask = (sig != 0) & move.notna()
    s, m = sig[mask], move[mask]
    wins = int((((s == 1) & (m > 0)) | ((s == -1) & (m < 0))).sum())
    n = int(mask.sum())
    lo, hi = wilson_interval(wins, n)
    return {"n": n, "wr": wins / n if n else float("nan"), "lo": lo, "hi": hi}


def analyze(symbol: str):
    try:
        df = load_data(symbol, tf_interval, tf_resample)
        if len(df) < 60:
            return "STAND BY", "Dati insufficienti", {}, None
        close = df["Close"].astype(float).iloc[:-1]  # scarta la candela ancora aperta
        sig, rsi, bull, upper, lower, macd_bull = compute_signals(close)

        price = float(close.iloc[-1])
        details = {
            "RSI": f"{float(rsi.iloc[-1]):.1f}",
            "Trend (EMA 9/21)": "RIALZISTA 🟢" if bull.iloc[-1] else "RIBASSISTA 🔴",
            "Bollinger": "Vicino al supporto" if price <= float(lower.iloc[-1]) * 1.008
            else ("Vicino alla resistenza" if price >= float(upper.iloc[-1]) * 0.992 else "Centro canale"),
            "MACD": "RIALZISTA 🟢" if macd_bull.iloc[-1] else "RIBASSISTA 🔴",
        }
        stats = historical_stats(close, sig)
        last = int(sig.iloc[-1])
        if last == 1:
            return "BUY 🟢", "Confluenza confermata", details, stats
        if last == -1:
            return "SELL 🔴", "Confluenza confermata", details, stats
        return "STAND BY / NO TRADE", "Mercato in equilibrio", details, stats
    except Exception as e:
        return "STAND BY", f"Errore: {e}", {}, None


def send_telegram_alert(display_name, timeframe, direction, entry_time):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    except Exception:
        return  # secrets non configurati: nessun avviso
    message = (
        f"⚡ *AURA PRO* ⚡\n\n"
        f"🔹 *Asset:* `{display_name}`\n"
        f"⏰ *Timeframe:* `{timeframe}`\n"
        f"🎯 *Direzione:* *{direction}*\n"
        f"🕒 *Entrata:* `{entry_time}`\n"
        f"🛡️ *Rischio:* `max 1% del capitale`"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=3,
        )
    except Exception:
        pass


# ---------- stato ----------
for key, default in {
    "active": False, "asset": None, "tf": None, "tf_sec": None, "direction": None,
    "time": None, "status": None, "details": {}, "stats": None,
}.items():
    st.session_state.setdefault(key, default)

if st.button("🚀 Analizza"):
    direction, status, details, stats = analyze(ticker)
    st.session_state.update(
        active=True, asset=selected_display, tf=tf_choice, tf_sec=tf_seconds,
        direction=direction, status=status, details=details, stats=stats,
        time=next_candle_time_utc(tf_seconds),
    )
    if "STAND BY" not in direction:
        send_telegram_alert(selected_display, tf_choice, direction, st.session_state.time)

if st.session_state.active:
    s = st.session_state
    st.success("Analisi completata")
    st.markdown("### RISULTATO")
    st.markdown(
        f"* **Asset:** `{s.asset}`\n"
        f"* **Timeframe:** `{s.tf}`\n"
        f"* **Direzione:** **{s.direction}**\n"
        f"* **Entrata (chiusura candela):** `{s.time}`\n"
        f"* **Stato filtri:** `{s.status}`\n"
        f"* **Gestione del rischio:** `max 1% del capitale`"
    )

    st.markdown("### 📈 Statistica storica reale (ultimi 5 giorni)")
    st_ = s.stats
    if st_ and st_["n"] > 0:
        st.markdown(
            f"* **Segnali passati:** `{st_['n']}`\n"
            f"* **Win rate storico:** `{st_['wr']:.1%}` (IC 95%: `{st_['lo']:.1%} – {st_['hi']:.1%}`)\n"
            f"* **Win rate di pareggio al payout {payout_pct}%:** `{breakeven:.1%}`"
        )
        if st_["n"] < 100:
            st.warning("Campione piccolo (<100 segnali): il win rate non è affidabile.")
        elif st_["lo"] <= breakeven:
            st.error("Non c'è evidenza di un vantaggio: l'intervallo include il pareggio o sta sotto.")
        else:
            st.info("Vantaggio storico apparente. Conferma con backtest su periodi più lunghi.")
    else:
        st.info("Statistiche non disponibili.")

    d = s.details
    if d:
        box = "standby-box" if "STAND BY" in s.direction else "analysis-box"
        title = "🛑 STAND BY" if "STAND BY" in s.direction else "📊 METRICHE ALLINEATE"
        st.markdown(
            f"""<div class="{box}"><h4>{title}</h4>
            <p><b>RSI (14):</b> {d.get('RSI')}</p>
            <p><b>Trend:</b> {d.get('Trend (EMA 9/21)')}</p>
            <p><b>Bollinger:</b> {d.get('Bollinger')}</p>
            <p><b>MACD:</b> {d.get('MACD')}</p></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("### ⏳ Countdown candela")
    left = seconds_to_next_candle(s.tf_sec)
    components.html(
        f"""
        <div id="cd" style="font-size:28px;font-weight:bold;color:#00ffcc;text-align:center;background:#1f1f1f;padding:15px;border-radius:8px;border:1px solid #333;">...</div>
        <script>
        var t = {left};
        function tick() {{
            var el = document.getElementById("cd");
            if (t <= 0) {{ el.innerHTML = "⏰ CANDELA CHIUSA"; el.style.color = "#ff4444"; return; }}
            var m = Math.floor(t / 60), s = t % 60;
            el.innerHTML = "⏱️ " + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
            t--;
        }}
        setInterval(tick, 1000); tick();
        </script>
        """,
        height=80,
    )