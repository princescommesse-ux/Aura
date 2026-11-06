from datetime import datetime, timedelta
import numpy as np
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

# Custom Dark Mode styling (Verde classico #2ecc71 e Bianco)
st.markdown(
    """
    <style>
    .main { background-color: #0d0d0d; color: #ffffff; }
    h1, h2, h3 { color: #2ecc71 !important; font-weight: bold; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        background-color: #161616; 
        color: #2ecc71; 
        border: 2px solid #2ecc71; 
        font-size: 18px;
    }
    .stButton>button:hover { 
        background-color: #2ecc71; 
        color: #000000; 
        border-color: #2ecc71; 
    }
    .analysis-box { 
        background-color: #141414; 
        padding: 18px; 
        border-radius: 10px; 
        border: 2px solid #2ecc71; 
        margin-top: 15px; 
        color: #ffffff;
    }
    .analysis-box h4 { color: #2ecc71 !important; font-size: 20px; }
    .standby-box { 
        background-color: #141414; 
        padding: 18px; 
        border-radius: 10px; 
        border: 2px solid #ff4444; 
        margin-top: 15px; 
        text-align: left; 
        color: #ffffff; 
    }
    .signal-buy { color: #2ecc71; font-weight: bold; font-size: 22px; }
    .signal-sell { color: #ff4444; font-weight: bold; font-size: 22px; }
    </style>
    """, 
    unsafe_allow_html=True,
)

st.title("⚡ AURA PRO ⚡")

mercato_tipo = st.radio("Seleziona Modalità:", ["🚀 Scanner Globale", "Forex Reale", "Asset OTC Valute", "Crypto OTC"], horizontal=True)

# Coppie Forex Reali (Rimosse EUR/AUD e NZD/USD)
forex_dict = {
    "🇪🇺🇺🇸 EUR/USD": {"symbol": "EURUSD=X"},
    "🇬🇧🇺🇸 GBP/USD": {"symbol": "GBPUSD=X"},
    "🇺🇸🇯🇵 USD/JPY": {"symbol": "USDJPY=X"},
    "🇦🇺🇺🇸 AUD/USD": {"symbol": "AUDUSD=X"},
    "🇺🇸🇨🇦 USD/CAD": {"symbol": "USDCAD=X"},
    "🇺🇸🇨🇭 USD/CHF": {"symbol": "USDCHF=X"},
    "🇬🇧🇯🇵 GBP/JPY": {"symbol": "GBPJPY=X"},
    "🇪🇺🇯🇵 EUR/JPY": {"symbol": "EURJPY=X"},
    "🇪🇺🇬🇧 EUR/GBP": {"symbol": "EURGBP=X"},
    "🇦🇺🇯🇵 AUD/JPY": {"symbol": "AUDJPY=X"},
    "🇬🇧🇦🇺 GBP/AUD": {"symbol": "GBPAUD=X"},
    "🇪🇺🇨🇦 EUR/CAD": {"symbol": "EURCAD=X"},
    "🇬🇧🇨🇦 GBP/CAD": {"symbol": "GBPCAD=X"},
    "🇦🇺🇨🇦 AUD/CAD": {"symbol": "AUDCAD=X"},
    "🇪🇺🇨🇭 EUR/CHF": {"symbol": "EURCHF=X"},
    "🇬🇧🇨🇭 GBP/CHF": {"symbol": "GBPCHF=X"},
    "🇨🇭🇯🇵 CHF/JPY": {"symbol": "CHFJPY=X"}
}

# Coppie OTC Valute
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
    "🇳🇿🇺🇸 NZD/USD OTC": {"symbol": "NZDUSD=X"},
    "🇨🇦🇨🇭 CAD/CHF OTC": {"symbol": "CADCHF=X"},
    "🇦🇺🇨🇦 AUD/CAD OTC": {"symbol": "AUDCAD=X"}
}

# Crypto OTC
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
    now = datetime.utcnow() + timedelta(hours=1)
    total_secs = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    rem = total_secs % seconds
    sec_to_wait = seconds - rem
    return max(1, int(round(sec_to_wait)))

def get_next_candle_time(seconds):
    now = datetime.utcnow() + timedelta(hours=1)
    secs_left = get_seconds_to_next_candle(seconds)
    target_time = now + timedelta(seconds=secs_left)
    total_epoch_secs = int(target_time.timestamp())
    aligned_epoch_secs = total_epoch_secs - (total_epoch_secs % seconds)
    aligned_time = datetime.fromtimestamp(aligned_epoch_secs)
    return aligned_time.strftime("%H:%M:%S")

def calculate_adx(df, period=14):
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)

    df['+DM'] = np.where((df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']), 
                         np.maximum(df['High'] - df['High'].shift(1), 0), 0)
    df['-DM'] = np.where((df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)), 
                         np.maximum(df['Low'].shift(1) - df['Low'], 0), 0)

    tr_smooth = df['TR'].rolling(window=period).sum()
    plus_di = 100 * (df['+DM'].rolling(window=period).sum() / tr_smooth)
    minus_di = 100 * (df['-DM'].rolling(window=period).sum() / tr_smooth)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    return adx.iloc[-1]

def ultimate_institutional_analysis(ticker, timeframe_choice, tf_sec):
    try:
        interval_map = {
            "M1 (60s)": ("1m", "5m"),
            "M3 (180s)": ("2m", "15m"),
            "M5 (300s)": ("5m", "15m"),
            "M10 (600s)": ("5m", "30m"),
            "M15 (900s)": ("15m", "1h")
        }
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
        macro_ema9 = macro_close.ewm(span=9, adjust=False).mean()
        macro_ema21 = macro_close.ewm(span=21, adjust=False).mean()
        macro_bullish = float(macro_ema9.iloc[-1].item()) > float(macro_ema21.iloc[-1].item())

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1].item())

        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)
        curr_lower = float(lower_band.iloc[-1].item())
        curr_upper = float(upper_band.iloc[-1].item())

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

        base_score = 80.0
        if "BUY" in direction:
            rsi_bonus = max(0.0, (46.0 - current_rsi) * 0.9)
            base_score += rsi_bonus
            if curr_price <= curr_lower: base_score += 5.0
            if adx_val >= 25.0: base_score += 4.0
        else:
            rsi_bonus = max(0.0, (current_rsi - 54.0) * 0.9)
            base_score += rsi_bonus
            if curr_price >= curr_upper: base_score += 5.0
            if adx_val >= 25.0: base_score += 4.0

        final_score = min(max(base_score, 81.0), 97.5)
        confidence_str = f"{final_score:.1f}% (Institutional MTF Confluence)"

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
    if mercato_tipo == "🚀 Scanner Globale":
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
    if mercato_tipo == "🚀 Scanner Globale":
        st.success("Scanner completato!")
        st.markdown("### 🎯 VALUTE CON SEGNALE ATTIVO")
        if len(st.session_state.scanner_results) > 0:
            for res in st.session_state.scanner_results:
                dir_class = "signal-buy" if "BUY" in res['direction'] else "signal-sell"
                st.markdown(f"""
                <div class="analysis-box">
                    <h4 style="color:#ffffff;">{res['asset']} &rarr; <span class="{dir_class}">{res['direction']}</span></h4>
                    <p style="color:#ffffff;"><b>Timeframe:</b> <span style="color:#2ecc71;">{res['timeframe']}</span> | <b>Confidence:</b> <span style="color:#2ecc71;">{res['confidence']}</span> | <b>RSI:</b> {res['rsi']} | <b>Entry:</b> <span style="color:#2ecc71;">{res['entry_time']}</span></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="standby-box" style="border: 2px solid #ff4444; text-align: center;">
                <h4 style="color: #ff4444;">🛑 NESSUN SEGNALE IN QUESTO MOMENTO</h4>
                <p style="color:#ffffff;">Nessun asset soddisfa i filtri di allineamento Macro-Trend e ADX.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("Analysis complete!")
        st.markdown("### SIGNAL RESULT")
        dir_display = st.session_state.cached_direction_snp
        dir_html = f"<span class='signal-buy'>{dir_display}</span>" if "BUY" in dir_display else f"<span class='signal-sell'>{dir_display}</span>" if "SELL" in dir_display else f"<span style='color: #ff4444; font-weight: bold;'>{dir_display}</span>"
        
        st.markdown(f"""
        * **Asset:** `{st.session_state.cached_asset_display_snp}`
        * **Timeframe:** `{st.session_state.cached_tf_choice_snp}`
        * **Signal Direction:** {dir_html}
        * **Entry Time (Candle Close):** `{st.session_state.cached_time_snp}`
        * **Dynamic AI Confidence:** `{st.session_state.cached_win_rate_snp}`
        * **Filter Status:** `{st.session_state.cached_confidence_snp}`
        """)

        details = st.session_state.cached_details_snp
        if details:
            if "STAND BY" in st.session_state.cached_direction_snp:
                st.markdown(f"""
                <div class="standby-box">
                    <h4 style="color: #ff4444; margin-top: 0;">🛑 STAND BY: FILTRI NON SUPERATI</h4>
                    <p style="color:#ffffff; margin-bottom: 10px;"><b>Asset:</b> {st.session_state.cached_asset_display_snp} | <b>Timeframe:</b> {st.session_state.cached_tf_choice_snp}</p>
                    <hr style="border-color: #333333; margin: 10px 0;">
                    <p style="color: #ffffff; text-align: left; margin: 5px 0;"><b>Motivo:</b> Mercato laterale o disallineamento (Stato: {st.session_state.cached_confidence_snp})</p>
                    <p style="color: #ffffff; text-align: left; margin: 5px 0;"><b>RSI:</b> {details.get('RSI', 'N/A')}</p>
                    <p style="color: #ffffff; text-align: left; margin: 5px 0;"><b>Trend Macro:</b> {details.get('Trend Macro', 'N/A')}</p>
                    <p style="color: #ffffff; text-align: left; margin: 5px 0;"><b>Forza ADX:</b> {details.get('ADX Strength', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="analysis-box">
                    <h4>🎯 CONFLUENZA ISTITUZIONALE VERIFICATA</h4>
                    <p style="color:#ffffff;"><b>RSI (14):</b> <span style="color:#2ecc71;">{details.get('RSI', 'N/A')}</span></p>
                    <p style="color:#ffffff;"><b>Trend Macro:</b> {details.get('Trend Macro', 'N/A')}</p>
                    <p style="color:#ffffff;"><b>Forza ADX:</b> <span style="color:#2ecc71;">{details.get('ADX Strength', 'N/A')}</span></p>
                    <p style="color:#ffffff;"><b>Posizione Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### ⏳ Current Candle Countdown (Pocket Option Sync)")
        initial_left = get_seconds_to_next_candle(st.session_state.cached_tf_seconds_snp)

        timer_html = f"""
        <div style="font-size: 28px; font-weight: bold; color: #2ecc71; text-align: center; background-color: #141414; padding: 15px; border-radius: 8px; border: 2px solid #2ecc71;" id="countdown_snp">
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
