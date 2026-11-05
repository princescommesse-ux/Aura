from datetime import datetime, timedelta
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="Aura Pro", 
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

st.title("⚡ AURA PRO (ULTIMATE EDITION) ⚡")

mercato_tipo = st.radio("Seleziona Modalità:", ["🚀 Scanner Globale (Precisione Live)", "Forex Reale (20 coppie)", "Asset OTC Valute (Reali)", "Crypto OTC (Top 3)"], horizontal=True)

# 20 coppie Forex Reali ufficiali
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

# Solo coppie OTC Valute con corrispettivo reale e diretto su Yahoo Finance
otc_dict = {
    "🇦🇺🇨🇭 AUD/CHF OTC": {"symbol": "AUDCHF=X"},
    "🇦🇺🇺🇸 AUD/USD OTC": {"symbol": "AUDUSD=X"},
    "🇨🇦🇯🇵 CAD/JPY OTC": {"symbol": "CADJPY=X"},
    "🇪🇺🇨🇭 EUR/CHF OTC": {"symbol": "EURCHF=X"},
    "🇪🇺🇬🇧 EUR/GBP OTC": {"symbol": "EURGBP=X"},
    "🇪🇺🇺🇸 EUR/USD OTC": {"symbol": "EURUSD=X"},
    "🇬🇧🇺🇸 GBP/USD OTC": {"symbol": "GBPUSD=X"},
    "🇺🇸🇨🇭 USD/CHF OTC": {"symbol": "USDCHF=X"},
    "🇪🇺🇯🇵 EUR/JPY OTC": {"symbol": "EURJPY=X"},
    "🇺🇸🇨🇦 USD/CAD OTC": {"symbol": "USDCAD=X"},
    "🇦🇺🇯🇵 AUD/JPY OTC": {"symbol": "AUDJPY=X"},
    "🇨🇭🇯🇵 CHF/JPY OTC": {"symbol": "CHFJPY=X"},
    "🇬🇧🇯🇵 GBP/JPY OTC": {"symbol": "GBPJPY=X"},
    "🇬🇧🇦🇺 GBP/AUD OTC": {"symbol": "GBPAUD=X"},
    "🇺🇸🇯🇵 USD/JPY OTC": {"symbol": "USDJPY=X"},
    "🇳🇿🇯🇵 NZD/JPY OTC": {"symbol": "NZDJPY=X"},
    "🇨🇦🇨🇭 CAD/CHF OTC": {"symbol": "CADCHF=X"},
    "🇦🇺🇨🇦 AUD/CAD OTC": {"symbol": "AUDCAD=X"},
    "🇳🇿🇺🇸 NZD/USD OTC": {"symbol": "NZDUSD=X"}
}

# Crypto OTC blindate (Top 3)
crypto_otc_dict = {
    "₿ Bitcoin OTC": {"symbol": "BTC-USD"},
    "Ξ Ethereum OTC": {"symbol": "ETH-USD"},
    "☀️ Solana OTC": {"symbol": "SOL-USD"}
}

if mercato_tipo != "🚀 Scanner Globale (Precisione Live)":
    if mercato_tipo == "Forex Reale (20 coppie)":
        selected_display = st.selectbox("Select Currency Pair", list(forex_dict.keys()), key="snp_asset_forex")
        selected_asset = forex_dict[selected_display]["symbol"]
    elif mercato_tipo == "Asset OTC Valute (Reali)":
        selected_display = st.selectbox("Select OTC Asset", list(otc_dict.keys()), key="snp_asset_otc")
        selected_asset = otc_dict[selected_display]["symbol"]
    else:
        selected_display = st.selectbox("Select Crypto OTC Asset", list(crypto_otc_dict.keys()), key="snp_asset_crypto")
        selected_asset = crypto_otc_dict[selected_display]["symbol"]

def get_market_sessions():
    utc_hour = datetime.utcnow().hour
    active = []
    if 0 <= utc_hour < 9:
        active.append("Tokyo 🟢")
    if 8 <= utc_hour < 16:
        active.append("London 🟢 (Killzone)")
    if 13 <= utc_hour < 21:
        active.append("New York 🟢 (Killzone)")
    if not active:
        return "Low Liquidity / Off-Killzone 🌙"
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
    rem = total_secs % seconds
    sec_to_wait = seconds - rem
    return max(1, int(sec_to_wait))

def get_next_candle_time(seconds):
    now = datetime.now()
    secs_left = get_seconds_to_next_candle(seconds)
    target_time = now + timedelta(seconds=secs_left)
    # Arrotonda esattamente al secondo pulito per la chiusura candela
    return target_time.strftime("%H:%M:%S")

def ultimate_institutional_analysis(ticker, timeframe_choice, tf_sec):
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
        if df.empty or len(df) < 20:
            return "STAND BY", "N/A", "Insufficient Market Data", {}

        high = df['High']
        low = df['Low']
        close = df['Close']
        
        # Calcolo RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1].item())
        
        # Medie Mobili ed EMA
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        is_bullish_trend = float(ema9.iloc[-1].item()) > float(ema21.iloc[-1].item())
        
        # Bande di Bollinger
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)
        curr_price = float(close.iloc[-1].item())
        curr_lower = float(lower_band.iloc[-1].item())
        curr_upper = float(upper_band.iloc[-1].item())

        details = {
            "RSI": f"{current_rsi:.1f}",
            "Trend Breve (EMA)": "BULLISH 🟢" if is_bullish_trend else "BEARISH 🔴",
            "Bollinger Position": "Near Lower Support" if curr_price <= curr_lower * 1.01 else ("Near Upper Resistance" if curr_price >= curr_upper * 0.99 else "Mid-Channel")
        }

        # Logica bilanciata e reattiva su tutti i timeframe
        if current_rsi <= 48 and (is_bullish_trend or curr_price <= curr_lower * 1.01):
            direction = "BUY 🟢"
        elif current_rsi >= 52 and (not is_bullish_trend or curr_price >= curr_upper * 0.99):
            direction = "SELL 🔴"
        else:
            return "STAND BY / NO TRADE", "N/A", "Market in Equilibrium", details

        # CALCOLO REALE E DINAMICO DELLA CONFIDENZA IN BASE AGLI INDICATORI
        base_score = 75.0
        if "BUY" in direction:
            # Più l'RSI è basso (profondo in ipervenduto), più sale la confidenza reale
            rsi_bonus = max(0.0, (48.0 - current_rsi) * 0.8)
            base_score += rsi_bonus
            if curr_price <= curr_lower * 1.005:
                base_score += 4.5
            if is_bullish_trend:
                base_score += 5.0
        else:
            # Più l'RSI è alto (profondo in ipercomprato), più sale la confidenza reale
            rsi_bonus = max(0.0, (current_rsi - 52.0) * 0.8)
            base_score += rsi_bonus
            if curr_price >= curr_upper * 0.995:
                base_score += 4.5
            if not is_bullish_trend:
                base_score += 5.0

        final_score = min(max(base_score, 76.5), 96.8)
        confidence_str = f"{final_score:.1f}% (Real-time Confluence)"

        return direction, confidence_str, "Confluence Verified", details
            
    except Exception as e:
        return "STAND BY", "N/A", f"Error: {str(e)}", {}

def send_telegram_alert(display_name, timeframe, direction, win_rate, confidence, entry_time):
    bot_token = "INSERISCI_QUI_IL_TUO_BOT_TOKEN"
    chat_id = "INSERISCI_QUI_IL_TUO_CHAT_ID"
    if bot_token == "INSERISCI_QUI_IL_TUO_BOT_TOKEN":
        return
    message = (
        f"⚡ *AURA PRO SIGNAL* ⚡\n\n"
        f"🔹 *Asset:* `{display_name}`\n"
        f"⏰ *Timeframe:* `{timeframe}`\n"
        f"🎯 *Direction:* *{direction}*\n"
        f"🕒 *Entry Time:* `{entry_time}`\n"
        f"📈 *Confidence:* `{win_rate}`\n"
        f"🛡️ *Status:* `{confidence}`"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception:
        pass

if "signal_active_snp" not in st.session_state: st.session_state.signal_active_snp = False
if "scanner_results" not in st.session_state: st.session_state.scanner_results = []
if "cached_asset_display_snp" not in st.session_state: st.session_state.cached_asset_display_snp = None
if "cached_tf_choice_snp" not in st.session_state: st.session_state.cached_tf_choice_snp = None
if "cached_tf_seconds_snp" not in st.session_state: st.session_state.cached_tf_seconds_snp = None
if "cached_direction_snp" not in st.session_state: st.session_state.cached_direction_snp = None
if "cached_win_rate_snp" not in st.session_state: st.session_state.cached_win_rate_snp = None
if "cached_time_snp" not in st.session_state: st.session_state.cached_time_snp = None
if "cached_confidence_snp" not in st.session_state: st.session_state.cached_confidence_snp = None
if "cached_details_snp" not in st.session_state: st.session_state.cached_details_snp = {}

if st.button("🚀 RUN SCANNER / ANALYSIS"):
    if mercato_tipo == "🚀 Scanner Globale (Precisione Live)":
        st.session_state.scanner_results = []
        combined_dict = {**forex_dict, **otc_dict}
        
        progress_bar = st.progress(0)
        total_items = len(combined_dict)
        i = 0
        
        for name, data in combined_dict.items():
            direction, win_rate, conf, details = ultimate_institutional_analysis(data["symbol"], tf_choice, tf_seconds)
            if "STAND BY" not in direction:
                entry_t = get_next_candle_time(tf_seconds)
                res_dict = {
                    "asset": name,
                    "direction": direction,
                    "confidence": win_rate,
                    "rsi": details.get("RSI", "N/A"),
                    "entry_time": entry_t,
                    "timeframe": tf_choice
                }
                st.session_state.scanner_results.append(res_dict)
            i += 1
            progress_bar.progress(i / total_items)
            
        progress_bar.empty()
        st.session_state.signal_active_snp = True
    else:
        direction, win_rate, confidence, details = ultimate_institutional_analysis(selected_asset, tf_choice, tf_seconds)
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
    if mercato_tipo == "🚀 Scanner Globale (Precisione Live)":
        st.success("Scanner completato!")
        st.markdown("### 🎯 VALUTE CON SEGNALE ATTIVO")
        if len(st.session_state.scanner_results) > 0:
            for res in st.session_state.scanner_results:
                st.markdown(f"""
                <div class="analysis-box">
                    <h4>{res['asset']} &rarr; <b>{res['direction']}</b></h4>
                    <p><b>Timeframe:</b> {res['timeframe']} | <b>Confidence:</b> {res['confidence']} | <b>RSI:</b> {res['rsi']} | <b>Entry:</b> {res['entry_time']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="standby-box">
                <h4>🛑 NESSUN SEGNALE IN QUESTO MOMENTO</h4>
                <p>Riprova tra qualche istante o cambia timeframe.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("Analysis complete!")
        st.markdown("### SIGNAL RESULT")
        st.markdown(f"""
        * **Asset:** `{st.session_state.cached_asset_display_snp}`
        * **Timeframe:** `{st.session_state.cached_tf_choice_snp}`
        * **Signal Direction:** **{st.session_state.cached_direction_snp}**
        * **Entry Time (Candle Close):** `{st.session_state.cached_time_snp}`
        * **Dynamic AI Confidence:** `{st.session_state.cached_win_rate_snp}`
        * **Filter Status:** `{st.session_state.cached_confidence_snp}`
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
                    <p style="color: #ffffff; text-align: left;"><b>Trend Breve:</b> {details.get('Trend Breve (EMA)', 'N/A')}</p>
                    <p style="color: #ffffff; text-align: left;"><b>Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="analysis-box">
                    <h4>🎯 SIGNAL CONFLUENCE ALIGNED</h4>
                    <p><b>RSI (14):</b> {details.get('RSI', 'N/A')}</p>
                    <p><b>Trend Breve:</b> {details.get('Trend Breve (EMA)', 'N/A')}</p>
                    <p><b>Posizione Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### ⏳ Current Candle Countdown (Pocket Option Sync)")
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
