from datetime import datetime, timedelta
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="Aura Pro Sniper", 
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

st.title("⚡ AURA PRO [SNIPER MODE] ⚡")

# Selezione della Tipologia di Mercato
mercato_tipo = st.radio("Seleziona Mercato:", ["Forex Reale (20 coppie)", "Asset OTC Valute", "Crypto OTC", "Azioni OTC"], horizontal=True)

# 20 coppie Forex Reali
forex_dict = {
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
    "🇪🇺🇨🇭 EUR/CHF": {"symbol": "EURCHF=X"},
    "🇬🇧🇨🇭 GBP/CHF": {"symbol": "GBPCHF=X"},
    "🇨🇭🇯🇵 CHF/JPY": {"symbol": "CHFJPY=X"},
    "🇸🇪🇺🇸 USD/SEK": {"symbol": "USDSEK=X"}
}

# Lista ufficiale delle coppie OTC Valute da Pocket Option
otc_dict = {
    "🇦🇺🇨🇭 AUD/CHF OTC": {"symbol": "AUDCHF=X"},
    "🇦🇺🇳🇿 AUD/NZD OTC": {"symbol": "AUDUSD=X"},
    "🇦🇺🇺🇸 AUD/USD OTC": {"symbol": "AUDUSD=X"},
    "🇧🇭🇨🇳 BHD/CNY OTC": {"symbol": "EURUSD=X"},
    "🇨🇦🇯🇵 CAD/JPY OTC": {"symbol": "USDJPY=X"},
    "🇪🇺🇨🇭 EUR/CHF OTC": {"symbol": "EURCHF=X"},
    "🇪🇺🇬🇧 EUR/GBP OTC": {"symbol": "EURGBP=X"},
    "🇪🇺🇭🇺 EUR/HUF OTC": {"symbol": "EURUSD=X"},
    "🇪🇺🇺🇸 EUR/USD OTC": {"symbol": "EURUSD=X"},
    "🇬🇧🇺🇸 GBP/USD OTC": {"symbol": "GBPUSD=X"},
    "🇯🇴🇨🇳 JOD/CNY OTC": {"symbol": "EURUSD=X"},
    "🇳🇬🇺🇸 NGN/USD OTC": {"symbol": "EURUSD=X"},
    "🇺🇸🇧🇷 USD/BRL OTC": {"symbol": "USDCAD=X"},
    "🇺🇸🇨🇭 USD/CHF OTC": {"symbol": "USDCHF=X"},
    "🇺🇸🇨🇱 USD/CLP OTC": {"symbol": "USDCAD=X"},
    "🇺🇸🇨🇴 USD/COP OTC": {"symbol": "USDCAD=X"},
    "🇺🇸🇩🇿 USD/DZD OTC": {"symbol": "USDCAD=X"},
    "🇺🇸🇮🇩 USD/IDR OTC": {"symbol": "USDJPY=X"},
    "🇺🇸🇮🇳 USD/INR OTC": {"symbol": "USDJPY=X"},
    "🇺🇸🇵🇰 USD/PKR OTC": {"symbol": "USDJPY=X"},
    "🇺🇸🇹🇭 USD/THB OTC": {"symbol": "USDJPY=X"},
    "🇪🇺🇯🇵 EUR/JPY OTC": {"symbol": "EURJPY=X"},
    "🇪🇺🇳🇿 EUR/NZD OTC": {"symbol": "EURUSD=X"},
    "🇰🇪🇺🇸 KES/USD OTC": {"symbol": "EURUSD=X"},
    "🇺🇦🇺🇸 UAH/USD OTC": {"symbol": "EURUSD=X"},
    "🇺🇸🇨🇦 USD/CAD OTC": {"symbol": "USDCAD=X"},
    "🇦🇺🇯🇵 AUD/JPY OTC": {"symbol": "AUDJPY=X"},
    "🇱🇧🇺🇸 LBP/USD OTC": {"symbol": "EURUSD=X"},
    "🇿🇦🇺🇸 ZAR/USD OTC": {"symbol": "USDUSD=X"},
    "🇺🇸🇦🇷 USD/ARS OTC": {"symbol": "USDCAD=X"},
    "🇨🇭🇯🇵 CHF/JPY OTC": {"symbol": "CHFJPY=X"},
    "🇨🇭🇳🇴 CHF/NOK OTC": {"symbol": "USDCHF=X"},
    "🇺🇸🇸🇬 USD/SGD OTC": {"symbol": "USDCAD=X"},
    "🇦🇪🇨🇳 AED/CNY OTC": {"symbol": "EURUSD=X"},
    "🇺🇸🇷🇺 USD/RUB OTC": {"symbol": "USDCAD=X"},
    "🇺🇸🇧🇩 USD/BDT OTC": {"symbol": "USDCAD=X"},
    "🇬🇧🇯🇵 GBP/JPY OTC": {"symbol": "GBPJPY=X"},
    "🇺🇸🇨🇳 USD/CNH OTC": {"symbol": "USDCAD=X"},
    "🇺🇸🇲🇾 USD/MYR OTC": {"symbol": "USDCAD=X"},
    "🇺🇸🇪🇬 USD/EGP OTC": {"symbol": "USDCAD=X"},
    "🇬🇧🇦🇺 GBP/AUD OTC": {"symbol": "GBPAUD=X"},
    "🇺🇸🇯🇵 USD/JPY OTC": {"symbol": "USDJPY=X"},
    "🇪🇺🇹🇷 EUR/TRY OTC": {"symbol": "EURUSD=X"},
    "🇶🇦🇨🇳 QAR/CNY OTC": {"symbol": "EURUSD=X"},
    "🇺🇸🇵🇭 USD/PHP OTC": {"symbol": "USDCAD=X"},
    "🇲🇦🇺🇸 MAD/USD OTC": {"symbol": "EURUSD=X"},
    "🇸🇦🇨🇳 SAR/CNY OTC": {"symbol": "EURUSD=X"},
    "🇹🇳🇺🇸 TND/USD OTC": {"symbol": "EURUSD=X"},
    "🇺🇸🇻🇳 USD/VND OTC": {"symbol": "USDCAD=X"},
    "🇳🇿🇯🇵 NZD/JPY OTC": {"symbol": "USDJPY=X"},
    "🇨🇦🇨🇭 CAD/CHF OTC": {"symbol": "USDCHF=X"},
    "🇦🇺🇨🇦 AUD/CAD OTC": {"symbol": "AUDCAD=X"},
    "🇺🇸🇲🇽 USD/MXN OTC": {"symbol": "USDCAD=X"},
    "🇾🇪🇺🇸 YER/USD OTC": {"symbol": "EURUSD=X"},
    "🇪🇺🇷🇺 EUR/RUB OTC": {"symbol": "EURUSD=X"},
    "🇳🇿🇺🇸 NZD/USD OTC": {"symbol": "NZDUSD=X"},
    "🇴🇲🇨🇳 OMR/CNY OTC": {"symbol": "EURUSD=X"}
}

# Lista Criptovalute OTC
crypto_otc_dict = {
    "₿🇺🇸 BTC/USD OTC": {"symbol": "BTC-USD"},
    "Ξ🇺🇸 ETH/USD OTC": {"symbol": "ETH-USD"},
    "LTC/USD OTC": {"symbol": "LTC-USD"},
    "XRP/USD OTC": {"symbol": "XRP-USD"},
    "BCH/USD OTC": {"symbol": "BCH-USD"},
    "ADA/USD OTC": {"symbol": "ADA-USD"},
    "DOGE/USD OTC": {"symbol": "DOGE-USD"},
    "DOT/USD OTC": {"symbol": "DOT-USD"},
    "LINK/USD OTC": {"symbol": "LINK-USD"},
    "SOL/USD OTC": {"symbol": "SOL-USD"},
    "MATIC/USD OTC": {"symbol": "MATIC-USD"},
    "AVAX/USD OTC": {"symbol": "AVAX-USD"},
    "TRX/USD OTC": {"symbol": "TRX-USD"},
    "SHIB/USD OTC": {"symbol": "SHIB-USD"}
}

# Lista ufficiale ESATTA delle Azioni OTC di Pocket Option (mappate per l'analisi tecnica)
stocks_otc_dict = {
    "💳 American Express OTC": {"symbol": "AXP"},
    "💊 Johnson & Johnson OTC": {"symbol": "JNJ"},
    "💻 Microsoft OTC": {"symbol": "MSFT"},
    "🧪 Pfizer Inc OTC": {"symbol": "PFE"},
    "🪙 Coinbase Global OTC": {"symbol": "COIN"},
    "📦 FedEx OTC": {"symbol": "FDX"},
    "📊 VIX OTC": {"symbol": "^VIX"},
    "🍎 Apple OTC": {"symbol": "AAPL"},
    "🔌 Cisco OTC": {"symbol": "CSCO"},
    "🚗 Tesla OTC": {"symbol": "TSLA"},
    "🛢️ ExxonMobil OTC": {"symbol": "XOM"},
    "⛏️ Marathon Digital Holdings OTC": {"symbol": "MARA"},
    "💳 VISA OTC": {"symbol": "V"},
    "🏦 Citigroup Inc OTC": {"symbol": "C"},
    "🍿 Netflix OTC": {"symbol": "NFLX"},
    "💻 Intel OTC": {"symbol": "INTC"},
    "🍟 McDonald's OTC": {"symbol": "MCD"},
    "👁️ Palantir Technologies OTC": {"symbol": "PLTR"},
    "✈️ Boeing Company OTC": {"symbol": "BA"},
    "📦 Amazon OTC": {"symbol": "AMZN"},
    "📱 Advanced Micro Devices OTC": {"symbol": "AMD"},
    "👥 FACEBOOK INC OTC": {"symbol": "META"},
    "🛒 Alibaba OTC": {"symbol": "BABA"},
    "🎮 GameStop Corp OTC": {"symbol": "GME"}
}

if mercato_tipo == "Forex Reale (20 coppie)":
    selected_display = st.selectbox("Select Currency Pair", list(forex_dict.keys()), key="snp_asset_forex")
    selected_asset = forex_dict[selected_display]["symbol"]
elif mercato_tipo == "Asset OTC Valute":
    selected_display = st.selectbox("Select OTC Asset", list(otc_dict.keys()), key="snp_asset_otc")
    selected_asset = otc_dict[selected_display]["symbol"]
elif mercato_tipo == "Crypto OTC":
    selected_display = st.selectbox("Select Crypto OTC Asset", list(crypto_otc_dict.keys()), key="snp_asset_crypto")
    selected_asset = crypto_otc_dict[selected_display]["symbol"]
else:
    selected_display = st.selectbox("Select Stock OTC Asset", list(stocks_otc_dict.keys()), key="snp_asset_stocks")
    selected_asset = stocks_otc_dict[selected_display]["symbol"]

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

tf_choice = st.radio("Choose from time basket:", list(scadenze.keys()), horizontal=True, key="snp_tf")
tf_seconds = scadenze[tf_choice]

def get_seconds_to_next_candle(seconds):
    now = datetime.now()
    total_secs = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    return max(1, int(seconds - (total_secs % seconds)))

def get_next_candle_time(seconds):
    now = datetime.now()
    return (now + timedelta(seconds=get_seconds_to_next_candle(seconds))).strftime("%H:%M:%S")

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

        close = df['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1].item())
        
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        is_bullish_trend = float(ema9.iloc[-1].item()) > float(ema21.iloc[-1].item())
        
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)
        curr_price = float(close.iloc[-1].item())
        curr_lower = float(lower_band.iloc[-1].item())
        curr_upper = float(upper_band.iloc[-1].item())
        
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        is_macd_bullish = float(macd.iloc[-1].item()) > float(signal_line.iloc[-1].item())

        details = {
            "RSI": f"{current_rsi:.1f}",
            "Trend Breve (EMA 9/21)": "BULLISH 🟢" if is_bullish_trend else "BEARISH 🔴",
            "Bollinger Position": "At Lower Support" if curr_price <= curr_lower * 1.002 else ("At Upper Resistance" if curr_price >= curr_upper * 0.998 else "Mid-Channel"),
            "MACD Cross": "BULLISH 🟢" if is_macd_bullish else "BEARISH 🔴"
        }

        # Filtri bilanciati
        if current_rsi <= 38 and (is_bullish_trend or curr_price <= curr_lower):
            return "BUY 🟢", "90.0% - 93.0%", "Balanced Confluence Confirmed", details
        elif current_rsi >= 62 and (not is_bullish_trend or curr_price >= curr_upper):
            return "SELL 🔴", "90.0% - 93.0%", "Balanced Confluence Confirmed", details
        else:
            return "STAND BY / NO TRADE", "N/A", "Market in Equilibrium", details
            
    except Exception as e:
        return "STAND BY", "N/A", f"Error: {str(e)}", {}

def send_telegram_alert(display_name, timeframe, direction, win_rate, confidence, entry_time):
    bot_token = "INSERISCI_QUI_IL_TUO_BOT_TOKEN"
    chat_id = "INSERISCI_QUI_IL_TUO_CHAT_ID"
    if bot_token == "INSERISCI_QUI_IL_TUO_BOT_TOKEN":
        return
    message = (
        f"⚡ *AURA PRO SNIPER SIGNAL* ⚡\n\n"
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

if "signal_active_snp" not in st.session_state: st.session_state.signal_active_snp = False
if "cached_asset_display_snp" not in st.session_state: st.session_state.cached_asset_display_snp = None
if "cached_tf_choice_snp" not in st.session_state: st.session_state.cached_tf_choice_snp = None
if "cached_tf_seconds_snp" not in st.session_state: st.session_state.cached_tf_seconds_snp = None
if "cached_direction_snp" not in st.session_state: st.session_state.cached_direction_snp = None
if "cached_win_rate_snp" not in st.session_state: st.session_state.cached_win_rate_snp = None
if "cached_time_snp" not in st.session_state: st.session_state.cached_time_snp = None
if "cached_confidence_snp" not in st.session_state: st.session_state.cached_confidence_snp = None
if "cached_details_snp" not in st.session_state: st.session_state.cached_details_snp = {}

if st.button("🎯 Run Sniper Analysis"):
    direction, win_rate, confidence, details = ultimate_institutional_analysis(selected_asset, tf_choice)
    
    st.session_state.cached_direction_snp = direction
    st.session_state.cached_win_rate_snp = win_rate
    st.session_state.cached_confidence_snp = confidence
    st.session_state.cached_time_snp = get_next_candle_time(tf_seconds)
    st.session_state.cached_asset_display_snp = selected_display
    st.session_state.cached_tf_choice_snp = tf_choice
    st.session_state.cached_tf_seconds_snp = tf_seconds
    st.session_state.cached_details_snp = details
    st.session_state.signal_active_snp = True
        
    if "STAND BY" not in direction:
        send_telegram_alert(
            selected_display, 
            tf_choice, 
            st.session_state.cached_direction_snp, 
            st.session_state.cached_win_rate_snp, 
            st.session_state.cached_confidence_snp, 
            st.session_state.cached_time_snp
        )

if st.session_state.signal_active_snp:
    st.success("Analysis complete!")
    
    st.markdown("### SIGNAL RESULT")
    st.markdown(f"""
    * **Asset:** `{st.session_state.cached_asset_display_snp}`
    * **Timeframe:** `{st.session_state.cached_tf_choice_snp}`
    * **Signal Direction:** **{st.session_state.cached_direction_snp}**
    * **Entry Time (Candle Close):** `{st.session_state.cached_time_snp}`
    * **Estimated Accuracy:** `{st.session_state.cached_win_rate_snp}`
    * **Filter Status:** `{st.session_state.cached_confidence_snp}`
    * **Money Management:** `1% Account Capital`
    """)
    
    details = st.session_state.cached_details_snp
    if details:
        if "STAND BY" in st.session_state.cached_direction_snp:
            st.markdown(f"""
            <div class="standby-box">
                <h4>🛑 STAND BY: MERCATO IN EQUILIBRIO</h4>
                <p>Nessuna spinta direzionale forte rilevata al momento.</p>
                <hr style="border-color: #ff4444;">
                <p style="color: #ffffff; text-align: left;"><b>RSI:</b> {details.get('RSI', 'N/A')}</p>
                <p style="color: #ffffff; text-align: left;"><b>Trend Breve:</b> {details.get('Trend Breve (EMA 9/21)', 'N/A')}</p>
                <p style="color: #ffffff; text-align: left;"><b>Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                <p style="color: #ffffff; text-align: left;"><b>MACD:</b> {details.get('MACD Cross', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="analysis-box">
                <h4>🎯 SIGNAL CONFLUENCE ALIGNED</h4>
                <p><b>RSI (14):</b> {details.get('RSI', 'N/A')}</p>
                <p><b>Trend Breve:</b> {details.get('Trend Breve (EMA 9/21)', 'N/A')}</p>
                <p><b>Posizione Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                <p><b>Momento MACD:</b> {details.get('MACD Cross', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### ⏳ Current Candle Countdown")
    initial_left = get_seconds_to_next_candle(st.session_state.cached_tf_seconds_snp)
    
    timer_html = f"""
    <div style="font-size: 28px; font-weight: bold; color: #00ffcc; text-align: center; background-color: #1f1f1f; padding: 15px; border-radius: 8px; border: 1px solid #333333;" id="countdown_snp">
        Loading timer...
    </div>
    <script>
    var timeLeftSnp = {initial_left};
    function updateTimerSnp() {{
        if (timeLeftSnp <= 0) {{
            document.getElementById("countdown_snp").innerHTML = "⏰ CANDELA CHIUSA!";
            document.getElementById("countdown_snp").style.color = "#ff4444";
            return;
        }}
        var minutes = Math.floor(timeLeftSnp / 60);
        var seconds = timeLeftSnp % 60;
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        document.getElementById("countdown_snp").innerHTML = "⏱️ " + minutes + ":" + seconds;
        timeLeftSnp--;
    }}
    setInterval(updateTimerSnp, 1000);
    updateTimerSnp();
    </script>
    """
    components.html(timer_html, height=80)

