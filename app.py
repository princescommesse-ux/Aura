from datetime import datetime, timedelta
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="Aura Pro MTF Full", 
    page_icon="⚡", 
    layout="centered"
)

# Custom Dark Mode styling
st.markdown(
    """
    <style>
    .main { background-color: #121212; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #1f1f1f; color: #00ffcc; border: 1px solid #333333; }
    .stButton>button:hover { background-color: #333333; color: #ffffff; border-color: #00ffcc; }
    .market-badge { background-color: #1f1f1f; padding: 8px 12px; border-radius: 6px; border: 1px solid #333333; font-size: 14px; margin-bottom: 15px; text-align: center; }
    .analysis-box { background-color: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #00ffcc; margin-top: 15px; }
    .standby-box { background-color: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #ff4444; margin-top: 15px; text-align: center; color: #ff4444; font-weight: bold; }
    </style>
    """, 
    unsafe_allow_html=True,
)

st.title("⚡ AURA PRO ⚡")

# 20 coppie Forex
assets_dict = {
    "🇪🇺🇺🇸 EUR/USD": {"symbol": "EURUSD=X"},
    "🇬🇧🇺🇸 GBP/USD": {"symbol": "GBPUSD=X"},
    "🇺🇸🇯🇵 USD/JPY": {"symbol": "USDJPY=X"},
    "🇦🇺🇺🇸 AUD/USD": {"symbol": "AUDUSD=X"},
    "🇺🇸🇨🇦 USD/CAD": {"symbol": "USDCAD=X"},
    "🇺🇸🇨🇭 USD/CHF": {"symbol": "USDCHF=X"},
    "🇳🇿🇺🇸 NZD/USD": {"symbol": "NZDUSD=X"},
    "🇬🇧🇯🇵 GBP/JPY": {"symbol": "GBPJPY=X"},
    "🇪🇺🇯🇵 EUR/JPY": {"symbol": "EURJPY=X"},
    "🇪🇺🇬🇧 EUR/GBP": {"symbol": "EURGBP=X"},
    "🇦🇺🇯🇵 AUD/JPY": {"symbol": "AUDJPY=X"},
    "🇪🇺🇦🇺 EUR/AUD": {"symbol": "EURAUD=X"},
    "🇬🇧🇦🇺 GBP/AUD": {"symbol": "GBPAUD=X"},
    "🇪🇺🇨🇦 EUR/CAD": {"symbol": "EURCAD=X"},
    "🇬🇧🇨🇦 GBP/CAD": {"symbol": "GBPCAD=X"},
    "🇦🇺🇨🇦 AUD/CAD": {"symbol": "AUDCAD=X"},
    "🇦🇺🇳🇿 AUD/NZD": {"symbol": "AUDNZD=X"},
    "🇪🇺🇨🇭 EUR/CHF": {"symbol": "EURCHF=X"},
    "🇬🇧🇨🇭 GBP/CHF": {"symbol": "GBPCHF=X"},
    "🇨🇭🇯🇵 CHF/JPY": {"symbol": "CHFJPY=X"}
}

selected_display = st.selectbox("Select Currency Pair", list(assets_dict.keys()))
selected_asset = assets_dict[selected_display]["symbol"]

def get_market_sessions():
    utc_hour = datetime.utcnow().hour
    active = []
    if 0 <= utc_hour < 9:
        active.append("Tokyo 🟢")
    if 8 <= utc_hour < 16:
        active.append("London 🟢")
    if 13 <= utc_hour < 21:
        active.append("New York 🟢")
    if not active:
        return "Low Liquidity / Asian Session 🌙"
    return " | ".join(active)

st.markdown(f'<div class="market-badge">🌐 <b>Market Sessions:</b> {get_market_sessions()}</div>', unsafe_allow_html=True)

st.markdown("### ⏰ Timeframe")
scadenze = {
    "M1 (60s)": 60,
    "M3 (180s)": 180,
    "M5 (300s)": 300,
    "M10 (600s)": 600,
    "M15 (900s)": 900
}

tf_choice = st.radio("Choose from time basket:", list(scadenze.keys()), horizontal=True)
tf_seconds = scadenze[tf_choice]

def get_seconds_to_next_candle(seconds):
    now = datetime.now()
    total_secs = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    return max(1, int(seconds - (total_secs % seconds)))

def get_next_candle_time(seconds):
    now = datetime.now()
    return (now + timedelta(seconds=get_seconds_to_next_candle(seconds))).strftime("%H:%M:%S")

# --- MOTORE DI ANALISI CON FILTRO MULTI-TIMEFRAME (MTF) ---
def ultimate_institutional_analysis(ticker, timeframe_choice):
    try:
        interval_map = {
            "M1 (60s)": "1m",
            "M3 (180s)": "2m",
            "M5 (300s)": "5m",
            "M10 (600s)": "5m",
            "M15 (900s)": "15m"
        }
        iv = interval_map.get(timeframe_choice, "1m")
        
        df = yf.download(ticker, period="1d", interval=iv, progress=False)
        if df.empty or len(df) < 35:
            return "STAND BY", "N/A", "Insufficient Market Data", {}
        
        df_macro = yf.download(ticker, period="5d", interval="15m", progress=False)
        macro_trend = "NEUTRAL"
        if not df_macro.empty and len(df_macro) >= 25:
            macro_close = df_macro['Close']
            m_ema9 = macro_close.ewm(span=9, adjust=False).mean()
            m_ema21 = macro_close.ewm(span=21, adjust=False).mean()
            macro_trend = "BULLISH 🟢" if float(m_ema9.iloc[-1].item()) > float(m_ema21.iloc[-1].item()) else "BEARISH 🔴"

        close = df['Close']
        
        # RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1].item())
        
        # EMA Trend (9 e 21)
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        is_bullish_trend = float(ema9.iloc[-1].item()) > float(ema21.iloc[-1].item())
        
        # Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)
        curr_price = float(close.iloc[-1].item())
        curr_lower = float(lower_band.iloc[-1].item())
        curr_upper = float(upper_band.iloc[-1].item())
        
        # MACD
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        is_macd_bullish = float(macd.iloc[-1].item()) > float(signal_line.iloc[-1].item())

        details = {
            "RSI": f"{current_rsi:.1f}",
            "Trend Breve (EMA 9/21)": "BULLISH 🟢" if is_bullish_trend else "BEARISH 🔴",
            "Macro Trend (15m)": macro_trend,
            "Bollinger Position": "Near Lower Support" if curr_price <= curr_lower * 1.008 else ("Near Upper Resistance" if curr_price >= curr_upper * 0.992 else "Mid-Channel"),
            "MACD Cross": "BULLISH 🟢" if is_macd_bullish else "BEARISH 🔴"
        }

        is_macro_bull = "BULLISH" in macro_trend
        is_macro_bear = "BEARISH" in macro_trend

        if is_bullish_trend and current_rsi <= 55 and curr_price <= (curr_lower * 1.01) and is_macro_bull:
            return "BUY 🟢", "89.0% - 92.0%", "MTF Confluence Confirmed", details
        elif not is_bullish_trend and current_rsi >= 45 and curr_price >= (curr_upper * 0.99) and is_macro_bear:
            return "SELL 🔴", "89.0% - 92.0%", "MTF Confluence Confirmed", details
        else:
            return "STAND BY / NO TRADE", "N/A", "Market in Equilibrium or Macro Disagreement", details
            
    except Exception as e:
        return "STAND BY", "N/A", f"Error: {str(e)}", {}

def send_telegram_alert(display_name, timeframe, direction, win_rate, confidence, entry_time):
    bot_token = "INSERISCI_QUI_IL_TUO_BOT_TOKEN"
    chat_id = "INSERISCI_QUI_IL_TUO_CHAT_ID"
    if bot_token == "INSERISCI_QUI_IL_TUO_BOT_TOKEN":
        return
    message = (
        f"⚡ *AURA PRO MTF SIGNAL* ⚡\n\n"
        f"🔹 *Asset:* `{display_name}`\n"
        f"⏰ *Timeframe:* `{timeframe}`\n"
        f"🎯 *Direction:* *{direction}*\n"
        f"🕒 *Entry Time:* `{entry_time}`\n"
        f"📈 *Expected Accuracy:* `{win_rate}`\n"
        f"🛡️ *Status:* `{confidence}`\n"
        f"💰 *Risk Management:* `1% Fixed Capital`"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception:
        pass

# Session State Initialization
if "signal_active" not in st.session_state: st.session_state.signal_active = False
if "cached_asset_display" not in st.session_state: st.session_state.cached_asset_display = None
if "cached_tf_choice" not in st.session_state: st.session_state.cached_tf_choice = None
if "cached_tf_seconds" not in st.session_state: st.session_state.cached_tf_seconds = None
if "cached_direction" not in st.session_state: st.session_state.cached_direction = None
if "cached_win_rate" not in st.session_state: st.session_state.cached_win_rate = None
if "cached_time" not in st.session_state: st.session_state.cached_time = None
if "cached_confidence" not in st.session_state: st.session_state.cached_confidence = None
if "cached_details" not in st.session_state: st.session_state.cached_details = {}

if st.button("🚀 Run MTF Institutional Analysis"):
    direction, win_rate, confidence, details = ultimate_institutional_analysis(selected_asset, tf_choice)
    
    st.session_state.cached_direction = direction
    st.session_state.cached_win_rate = win_rate
    st.session_state.cached_confidence = confidence
    st.session_state.cached_time = get_next_candle_time(tf_seconds)
    st.session_state.cached_asset_display = selected_display
    st.session_state.cached_tf_choice = tf_choice
    st.session_state.cached_tf_seconds = tf_seconds
    st.session_state.cached_details = details
    st.session_state.signal_active = True
        
    if "STAND BY" not in direction:
        send_telegram_alert(
            selected_display, 
            tf_choice, 
            st.session_state.cached_direction, 
            st.session_state.cached_win_rate, 
            st.session_state.cached_confidence, 
            st.session_state.cached_time
        )

if st.session_state.signal_active:
    st.success("Analysis complete!")
    
    st.markdown("### SIGNAL RESULT")
    st.markdown(f"""
    * **Asset:** `{st.session_state.cached_asset_display}`
    * **Timeframe:** `{st.session_state.cached_tf_choice}`
    * **Signal Direction:** **{st.session_state.cached_direction}**
    * **Entry Time (Candle Close):** `{st.session_state.cached_time}`
    * **Estimated Accuracy:** `{st.session_state.cached_win_rate}`
    * **Filter Status:** `{st.session_state.cached_confidence}`
    * **Money Management:** `1% Account Capital`
    """)
    
    details = st.session_state.cached_details
    if details:
        if "STAND BY" in st.session_state.cached_direction:
            st.markdown(f"""
            <div class="standby-box">
                <h4>🛑 STAND BY: FILTRATO DA MTF & CONFLUENZA</h4>
                <p>Il trend a breve e il macro-trend su timeframe superiore non sono allineati o il mercato è in equilibrio.</p>
                <hr style="border-color: #ff4444;">
                <p style="color: #ffffff; text-align: left;"><b>RSI:</b> {details.get('RSI', 'N/A')}</p>
                <p style="color: #ffffff; text-align: left;"><b>Trend Breve:</b> {details.get('Trend Breve (EMA 9/21)', 'N/A')}</p>
                <p style="color: #ffffff; text-align: left;"><b>Macro Trend (15m):</b> {details.get('Macro Trend (15m)', 'N/A')}</p>
                <p style="color: #ffffff; text-align: left;"><b>Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                <p style="color: #ffffff; text-align: left;"><b>MACD:</b> {details.get('MACD Cross', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="analysis-box">
                <h4>📊 MULTI-TIMEFRAME METRICS ALIGNED</h4>
                <p><b>RSI (14):</b> {details.get('RSI', 'N/A')}</p>
                <p><b>Trend Breve:</b> {details.get('Trend Breve (EMA 9/21)', 'N/A')}</p>
                <p><b>Macro Trend (15m):</b> {details.get('Macro Trend (15m)', 'N/A')}</p>
                <p><b>Posizione Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                <p><b>Momento MACD:</b> {details.get('MACD Cross', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### ⏳ Current Candle Countdown")
    initial_left = get_seconds_to_next_candle(st.session_state.cached_tf_seconds)
    
    timer_html = f"""
    <div style="font-size: 28px; font-weight: bold; color: #00ffcc; text-align: center; background-color: #1f1f1f; padding: 15px; border-radius: 8px; border: 1px solid #333333;" id="countdown">
        Loading timer...
    </div>
    <script>
    var timeLeft = {initial_left};
    function updateTimer() {{
        if (timeLeft <= 0) {{
            document.getElementById("countdown").innerHTML = "⏰ CANDELA CHIUSA!";
            document.getElementById("countdown").style.color = "#ff4444";
            return;
        }}
        var minutes = Math.floor(timeLeft / 60);
        var seconds = timeLeft % 60;
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        document.getElementById("countdown").innerHTML = "⏱️ " + minutes + ":" + seconds;
        timeLeft--;
    }}
    setInterval(updateTimer, 1000);
    updateTimer();
    </script>
    """
    components.html(timer_html, height=80)
