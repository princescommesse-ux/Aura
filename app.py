from datetime import datetime, timedelta
import numpy as np
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

st.set_page_config(page_title="Aura Pro", page_icon="⚡", layout="centered")

st.markdown("""
<style>
.main { background-color: #0d0d0d; color: #ffffff; }
h1, h2, h3 { color: #2ecc71 !important; font-weight: bold; }
.stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #161616; color: #2ecc71; border: 2px solid #2ecc71; font-size: 18px; }
.stButton>button:hover { background-color: #2ecc71; color: #000000; border-color: #2ecc71; }
.analysis-box { background-color: #141414; padding: 18px; border-radius: 10px; border: 2px solid #2ecc71; margin-top: 15px; color: #ffffff; }
.analysis-box h4 { color: #2ecc71 !important; font-size: 20px; }
.standby-box { background-color: #141414; padding: 18px; border-radius: 10px; border: 2px solid #ff4444; margin-top: 15px; text-align: left; color: #ffffff; }
.signal-buy { color: #2ecc71; font-weight: bold; font-size: 20px; }
.signal-sell { color: #ff4444; font-weight: bold; font-size: 20px; }
.signal-standby { color: #ff4444; font-weight: bold; font-size: 20px; }
.session-badge-open { background-color: #1b4d3e; color: #2ecc71; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; border: 1px solid #2ecc71; }
.session-badge-closed { background-color: #3d1b1b; color: #ff4444; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; border: 1px solid #ff4444; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ AURA PRO ⚡")

def get_forex_market_status():
    now_utc = datetime.utcnow()
    weekday = now_utc.weekday()
    hour = now_utc.hour
    is_weekend = False
    if weekday == 5:
        is_weekend = True
    elif weekday == 6 and hour < 22:
        is_weekend = True
    elif weekday == 4 and hour >= 22:
        is_weekend = True
    return not is_weekend, now_utc

def get_active_sessions(now_utc):
    hour = now_utc.hour
    sydney = 22 <= hour or hour < 7
    tokyo = 0 <= hour < 9
    london = 8 <= hour < 17
    new_york = 13 <= hour < 22
    return {"Sydney": sydney, "Tokyo": tokyo, "London": london, "New York": new_york}

market_open, current_utc_time = get_forex_market_status()
sessions = get_active_sessions(current_utc_time)

st.markdown("### 🌐 Forex Market Sessions (UTC)")
cols = st.columns(4)
session_names = [("Sydney", sessions["Sydney"]), ("Tokyo", sessions["Tokyo"]), ("London", sessions["London"]), ("New York", sessions["New York"])]
for idx, (s_name, s_status) in enumerate(session_names):
    with cols[idx]:
        if s_status and market_open:
            st.markdown(f"**{s_name}**<br><span class='session-badge-open'>OPEN 🟢</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**{s_name}**<br><span class='session-badge-closed'>CLOSED 🔴</span>", unsafe_allow_html=True)

st.markdown("---")

if not market_open:
    st.markdown('<div class="standby-box" style="border: 2px solid #ff4444; text-align: center; padding: 20px;"><h3 style="color: #ff4444; margin-top: 0;">💤 MERCATO FOREX CHIUSO (WEEKEND)</h3><p style="color:#ffffff; font-size: 16px;">Il mercato delle valute è chiuso per il fine settimana. Le analisi su yFinance non sono disponibili fino alla riapertura (Domenica ore 22:00 UTC). Puoi testare la modalità Crypto OTC.</p></div>', unsafe_allow_html=True)

mercato_tipo = st.radio("Seleziona Modalità:", ["🚀 Scanner Globale", "Forex Reale", "Asset OTC Valute", "Crypto OTC"], horizontal=True)

forex_dict = {
    "🇪🇺🇺🇸 EUR/USD": {"symbol": "EURUSD=X"}, "🇬🇧🇺🇸 GBP/USD": {"symbol": "GBPUSD=X"},
    "🇺🇸🇯🇵 USD/JPY": {"symbol": "USDJPY=X"}, "🇦🇺🇺🇸 AUD/USD": {"symbol": "AUDUSD=X"},
    "🇺🇸🇨🇦 USD/CAD": {"symbol": "USDCAD=X"}, "🇺🇸🇨🇭 USD/CHF": {"symbol": "USDCHF=X"},
    "🇬🇧🇯🇵 GBP/JPY": {"symbol": "GBPJPY=X"}, "🇪🇺🇯🇵 EUR/JPY": {"symbol": "EURJPY=X"},
    "🇪🇺🇬🇧 EUR/GBP": {"symbol": "EURGBP=X"}, "🇦🇺🇯🇵 AUD/JPY": {"symbol": "AUDJPY=X"},
    "🇬🇧🇦🇺 GBP/AUD": {"symbol": "GBPAUD=X"}, "🇪🇺🇨🇦 EUR/CAD": {"symbol": "EURCAD=X"},
    "🇬🇧🇨🇦 GBP/CAD": {"symbol": "GBPCAD=X"}, "🇦🇺🇨🇦 AUD/CAD": {"symbol": "AUDCAD=X"},
    "🇪🇺🇨🇭 EUR/CHF": {"symbol": "EURCHF=X"}, "🇬🇧🇨🇭 GBP/CHF": {"symbol": "GBPCHF=X"},
    "🇨🇭🇯🇵 CHF/JPY": {"symbol": "CHFJPY=X"}
}

otc_dict = {
    "🇦🇺🇨🇭 AUD/CHF OTC": {"symbol": "AUDCHF=X"}, "🇦🇺🇺🇸 AUD/USD OTC": {"symbol": "AUDUSD=X"},
    "🇨🇦🇯🇵 CAD/JPY OTC": {"symbol": "CADJPY=X"}, "🇪🇺🇨🇭 EUR/CHF OTC": {"symbol": "EURCHF=X"},
    "🇪🇺🇬🇧 EUR/GBP OTC": {"symbol": "EURGBP=X"}, "🇪🇺🇺🇸 EUR/USD OTC": {"symbol": "EURUSD=X"},
    "🇬🇧🇺🇸 GBP/USD OTC": {"symbol": "GBPUSD=X"}, "🇺🇸🇨🇭 USD/CHF OTC": {"symbol": "USDCHF=X"},
    "🇪🇺🇯🇵 EUR/JPY OTC": {"symbol": "EURJPY=X"}, "🇺🇸🇨🇦 USD/CAD OTC": {"symbol": "USDCAD=X"},
    "🇦🇺🇯🇵 AUD/JPY OTC": {"symbol": "AUDJPY=X"}, "🇨🇭🇯🇵 CHF/JPY OTC": {"symbol": "CHFJPY=X"},
    "🇬🇧🇯🇵 GBP/JPY OTC": {"symbol": "GBPJPY=X"}, "🇬🇧🇦🇺 GBP/AUD OTC": {"symbol": "GBPAUD=X"},
    "🇺🇸🇯🇵 USD/JPY OTC": {"symbol": "USDJPY=X"}, "🇳🇿🇯🇵 NZD/JPY OTC": {"symbol": "NZDJPY=X"},
    "🇳🇿🇺🇸 NZD/USD OTC": {"symbol": "NZDUSD=X"}, "🇨🇦🇨🇭 CAD/CHF OTC": {"symbol": "CADCHF=X"},
    "🇦🇺🇨🇦 AUD/CAD OTC": {"symbol": "AUDCAD=X"}
}

crypto_otc_dict = {
    "₿ Bitcoin OTC": {"symbol": "BTC-USD"},
    "Ξ Ethereum OTC": {"symbol": "ETH-USD"},
    "☀️ Solana OTC": {"symbol": "SOL-USD"}
}

if mercato_tipo != "🚀 Scanner Globale":
    if mercato_tipo == "Forex Reale":
        selected_display = st.selectbox("Select Currency Pair", list(forex_dict.keys()), key="snp_asset_forex")
        selected_asset = forex_dict[selected_display]["symbol"]
    elif mercato_tipo == "Asset OTC Valute":
        selected_display = st.selectbox("Select OTC Asset", list(otc_dict.keys()), key="snp_asset_otc")
        selected_asset = otc_dict[selected_display]["symbol"]
    else:
        selected_display = st.selectbox("Select Crypto OTC Asset", list(crypto_otc_dict.keys()), key="snp_asset_crypto")
        selected_asset = crypto_otc_dict[selected_display]["symbol"]

st.markdown("### ⏰ Timeframe")
scadenze = {"M1 (60s)": 60, "M3 (180s)": 180, "M5 (300s)": 300, "M10 (600s)": 600, "M15 (900s)": 900}
tf_choice = st.radio("Choose from time basket:", list(scadenze.keys()), horizontal=True, key="snp_tf")
tf_seconds = scadenze[tf_choice]

def get_seconds_to_next_candle(seconds):
    now = datetime.utcnow() + timedelta(hours=1)
    total_secs = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    rem = total_secs % seconds
    return max(1, int(round(seconds - rem)))

def get_next_candle_time(seconds):
    now = datetime.utcnow() + timedelta(hours=1)
    secs_left = get_seconds_to_next_candle(seconds)
    target_time = now + timedelta(seconds=secs_left + seconds)
    total_epoch_secs = int(target_time.timestamp())
    aligned_epoch_secs = total_epoch_secs - (total_epoch_secs % seconds)
    return datetime.fromtimestamp(aligned_epoch_secs).strftime("%H:%M:%S")

def calculate_adx(df, period=14):
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['+DM'] = np.where((df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']), np.maximum(df['High'] - df['High'].shift(1), 0), 0)
    df['-DM'] = np.where((df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)), np.maximum(df['Low'].shift(1) - df['Low'], 0), 0)
    tr_smooth = df['TR'].rolling(window=period).sum()
    plus_di = 100 * (df['+DM'].rolling(window=period).sum() / tr_smooth)
    minus_di = 100 * (df['-DM'].rolling(window=period).sum() / tr_smooth)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    return dx.rolling(window=period).mean().iloc[-1]

def ultimate_institutional_analysis(ticker, timeframe_choice, tf_sec):
    try:
        interval_map = {"M1 (60s)": ("1m", "5m"), "M3 (180s)": ("2m", "15m"), "M5 (300s)": ("5m", "15m"), "M10 (600s)": ("5m", "30m"), "M15 (900s)": ("15m", "1h")}
        iv_micro, iv_macro = interval_map.get(timeframe_choice, ("1m", "5m"))
        df = yf.download(ticker, period="1d", interval=iv_micro, progress=False)
        df_macro = yf.download(ticker, period="5d", interval=iv_macro, progress=False)
        if df.empty or len(df) < 25 or df_macro.empty or len(df_macro) < 25:
            return "STAND BY", "N/A", "Insufficient Market Data", {}
        close = df['Close']
        curr_price = float(close.iloc[-1].item())
        adx_val = float(calculate_adx(df))
        if np.isnan(adx_val) or adx_val < 18.0:
            return "STAND BY / NO TRADE", "N/A", "Weak Trend / Market Chop", {"ADX": f"{adx_val:.1f}"}
        macro_close = df_macro['Close']
        macro_bullish = float(macro_close.ewm(span=9, adjust=False).mean().iloc[-1].item()) > float(macro_close.ewm(span=21, adjust=False).mean().iloc[-1].item())
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        current_rsi = float((100 - (100 / (1 + (gain / loss)))).iloc[-1].item())
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        curr_lower = float((sma20 - (std20 * 2)).iloc[-1].item())
        curr_upper = float((sma20 + (std20 * 2)).iloc[-1].item())
        details = {
            "RSI": f"{current_rsi:.1f}",
            "Trend Macro": "BULLISH 🟢" if macro_bullish else "BEARISH 🔴",
            "ADX Strength": f"{adx_val:.1f} (Strong)" if adx_val >= 25 else f"{adx_val:.1f} (Moderate)",
            "Bollinger Position": "Support Touch" if curr_price <= curr_lower * 1.005 else ("Resistance Touch" if curr_price >= curr_upper * 0.995 else "Channel")
        }
        direction = "STAND BY / NO TRADE"
        if current_rsi <= 46 and macro_bullish and (curr_price <= curr_lower * 1.01):
            direction = "BUY 🟢"
        elif current_rsi >= 54 and (not macro_bullish) and (curr_price >= curr_upper * 0.99):
            direction = "SELL 🔴"
        else:
            return "STAND BY / NO TRADE", "N/A", "Timeframes Misaligned", details
        base_score = 80.0 + (max(0.0, (46.0 - current_rsi) * 0.9) if "BUY" in direction else max(0.0, (current_rsi - 54.0) * 0.9))
        final_score = min(max(base_score, 81.0), 97.5)
        return direction, f"{final_score:.1f}%", "Confluence Verified", details
    except Exception as e:
        return "STAND BY", "N/A", f"Error: {str(e)}", {}

def send_telegram_alert(display_name, timeframe, direction, win_rate, confidence, entry_time):
    bot_token = "INSERISCI_QUI_IL_TUO_BOT_TOKEN"
    chat_id = "INSERISCI_QUI_IL_TUO_CHAT_ID"
    if bot_token == "INSERISCI_QUI_IL_TUO_BOT_TOKEN":
        return
    message = "⚡ *AURA PRO SIGNAL* ⚡\n\n🔹 *Asset:* `" + display_name + "`\n⏰ *Timeframe:* `" + timeframe + "`\n🎯 *Direction:* *" + direction + "*\n🕒 *Entry Time:* `" + entry_time + "`\n📈 *Confidence:* `" + win_rate + "`\n🛡️ *Status:* `" + confidence + "`"
    try:
        requests.post("https://api.telegram.org/bot" + bot_token + "/sendMessage", json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=3)
    except Exception:
        pass

if "signal_active_snp" not in st.session_state: st.session_state.signal_active_snp = False
if "scanner_results" not in st.session_state: st.session_state.scanner_results = []
if "cached_asset_display_snp" not in st.session_state: st.session_state.cached_asset_display_snp = None
if "cached_tf_choice_snp" not in st.session_state: st.session_state.cached_tf_choice_snp = None
if "cached_tf_seconds_snp" not in st.session_state: st.session_state.cached_tf_seconds_snp = None
if "cached_direction_snp" not in st.session_state: st.session_state.cached_direction_snp =
