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
    .history-box { background-color: #181818; padding: 10px; border-radius: 6px; border: 1px solid #444444; margin-top: 10px; font-size: 13px; }
    </style>
    """, 
    unsafe_allow_html=True,
)

st.title("⚡ AURA PRO (ULTIMATE EDITION) ⚡")

mercato_tipo = st.radio("Seleziona Modalità:", ["🚀 Scanner Globale (Full Elite + Log)", "Forex Reale (20 coppie)", "Asset OTC Valute (Reali)", "Crypto OTC (Top 3)"], horizontal=True)

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

if mercato_tipo != "🚀 Scanner Globale (Full Elite + Log)":
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

st.markdown("### ⏰ Timeframe & Risk Management")
col_tf, col_risk = st.columns(2)
with col_tf:
    scadenze = {
        "M1 (60s)": 60,
        "M3 (180s)": 180,
        "M5 (300s)": 300,
        "M10 (600s)": 600,
        "M15 (900s)": 900
    }
    tf_choice = st.radio("Choose from time basket:", list(scadenze.keys()), horizontal=True, key="snp_tf")
    tf_seconds = scadenze[tf_choice]

with col_risk:
    account_balance = st.number_input("Capitale Account ($)", min_value=10.0, value=1000.0, step=50.0)
    risk_pct = st.slider("Rischio per Operazione (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

calculated_stake = round(account_balance * (risk_pct / 100.0), 2)
st.info(f"💰 **Stake Consigliata (Money Management):** ${calculated_stake} ({risk_pct}% del capitale)")

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

        high = df['High']
        low = df['Low']
        close = df['Close']
        open_p = df['Open']
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        true_range = max(tr1, tr2, tr3) if isinstance(tr1, float) else pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean()
        atr_sma = atr.rolling(window=10).mean()
        
        current_atr = float(atr.iloc[-1].item()) if not atr.empty else 0.0
        avg_atr = float(atr_sma.iloc[-1].item()) if not atr_sma.empty else 0.0
        is_volatility_active = current_atr >= avg_atr * 0.9

        prev_is_green = float(close.iloc[-2].item()) > float(open_p.iloc[-2].item())
        prev_is_red = float(close.iloc[-2].item()) < float(open_p.iloc[-2].item())

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

        higher_iv = "15m" if iv in ["1m", "2m", "5m"] else "1h"
        df_higher = yf.download(ticker, period="5d", interval=higher_iv, progress=False)
        macro_bullish = True
        if not df_higher.empty and len(df_higher) >= 25:
            h_close = df_higher['Close']
            h_ema9 = h_close.ewm(span=9, adjust=False).mean()
            h_ema21 = h_close.ewm(span=21, adjust=False).mean()
            macro_bullish = float(h_ema9.iloc[-1].item()) > float(h_ema21.iloc[-1].item())

        details = {
            "RSI": f"{current_rsi:.1f}",
            "ATR Dinamico": "OK 🟢" if is_volatility_active else "Basso 🔴",
            "Candela Prev. Spinta": "Green 🟢" if prev_is_green else "Red 🔴",
            "Trend Macro (Multi-TF)": "BULLISH 🟢" if macro_bullish else "BEARISH 🔴",
            "Bollinger Position": "Near Lower Support" if curr_price <= curr_lower * 1.005 else ("Near Upper Resistance" if curr_price >= curr_upper * 0.995 else "Mid-Channel"),
            "MACD Cross": "BULLISH 🟢" if is_macd_bullish else "BEARISH 🔴"
        }

        if current_rsi <= 40 and (is_bullish_trend or curr_price <= curr_lower * 1.005) and macro_bullish and is_volatility_active and prev_is_green:
            direction = "BUY 🟢"
        elif current_rsi >= 60 and (not is_bullish_trend or curr_price >= curr_upper * 0.995) and not macro_bullish and is_volatility_active and prev_is_red:
            direction = "SELL 🔴"
        else:
            return "STAND BY / NO TRADE", "N/A", "Market in Equilibrium or Momentum Mismatch", details

        score = 65.0
        if "BUY" in direction:
            if current_rsi <= 35: score += 10.0
            if curr_price <= curr_lower * 1.005: score += 10.0
            if is_macd_bullish: score += 5.0
        elif "SELL" in direction:
            if current_rsi >= 65: score += 10.0
            if curr_price >= curr_upper * 0.995: score += 10.0
            if not is_macd_bullish: score += 5.0

        final_score = min(score, 98.0)
        confidence_str = f"{final_score:.1f}% (Elite Momentum Confirmed)"

        return direction, confidence_str, "Institutional Elite Confluence", details
            
    except Exception as e:
        return "STAND BY", "N/A", f"Error: {str(e)}", {}

def send_telegram_alert(display_name, timeframe, direction, win_rate, confidence, entry_time, stake):
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
        f"💰 *Consigliato Stake:* `${stake}`\n"
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
if "session_history" not in st.session_state: st.session_state.session_history = []
if "cached_asset_display_snp" not in st.session_state: st.session_state.cached_asset_display_snp = None
if "cached_tf_choice_snp" not in st.session_state: st.session_state.cached_tf_choice_snp = None
if "cached_tf_seconds_snp" not in st.session_state: st.session_state.cached_tf_seconds_snp = None
if "cached_direction_snp" not in st.session_state: st.session_state.cached_direction_snp = None
if "cached_win_rate_snp" not in st.session_state: st.session_state.cached_win_rate_snp = None
if "cached_time_snp" not in st.session_state: st.session_state.cached_time_snp = None
if "cached_confidence_snp" not in st.session_state: st.session_state.cached_confidence_snp = None
if "cached_details_snp" not in st.session_state: st.session_state.cached_details_snp = {}

if st.button("🚀 RUN SCANNER / ANALYSIS"):
    if mercato_tipo == "🚀 Scanner Globale (Full Elite + Log)":
        st.session_state.scanner_results = []
        combined_dict = {**forex_dict, **otc_dict}
        
        progress_bar = st.progress(0)
        total_items = len(combined_dict)
        i = 0
        
        for name, data in combined_dict.items():
            direction, win_rate, conf, details = ultimate_institutional_analysis(data["symbol"], tf_choice)
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
                st.session_state.session_history.insert(0, {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "asset": name,
                    "tf": tf_choice,
                    "dir": direction,
                    "conf": win_rate
                })
            i += 1
            progress_bar.progress(i / total_items)
            
        progress_bar.empty()
        st.session_state.signal_active_snp = True
    else:
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
            st.session_state.session_history.insert(0, {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "asset": selected_display,
                "tf": tf_choice,
                "dir": direction,
                "conf": win_rate
            })
            send_telegram_alert(
                selected_display, 
                tf_choice, 
                st.session_state.cached_direction_snp, 
                st.session_state.cached_win_rate_snp, 
                st.session_state.cached_confidence_snp, 
                st.session_state.cached_time_snp,
                calculated_stake
            )

if st.session_state.signal_active_snp:
    if mercato_tipo == "🚀 Scanner Globale (Full Elite + Log)":
        st.success("Scanner completato!")
        st.markdown("### 🎯 VALUTE CON SEGNALE ELITE CONFERMATO")
        if len(st.session_state.scanner_results) > 0:
            for res in st.session_state.scanner_results:
                st.markdown(f"""
                <div class="analysis-box">
                    <h4>{res['asset']} &rarr; <b>{res['direction']}</b></h4>
                    <p><b>Timeframe:</b> {res['timeframe']} | <b>Confidence:</b> {res['confidence']} | <b>RSI:</b> {res['rsi']} | <b>Entry:</b> {res['entry_time']}</p>
                    <p style="color: #00ffcc; font-size: 13px;">💡 <b>Stake Consigliata:</b> ${calculated_stake}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="standby-box">
                <h4>🛑 NESSUN SEGNALE ELITE</h4>
                <p>Nessun asset soddisfa contemporaneamente i requisiti di momentum della candela e volatilità dinamica.</p>
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
        * **Stake Consigliata:** `${calculated_stake} ({risk_pct}% del capitale)`
        """)
        
        details = st.session_state.cached_details_snp
        if details:
            if "STAND BY" in st.session_state.cached_direction_snp:
                st.markdown(f"""
                <div class="standby-box">
                    <h4>🛑 STAND BY: FILTRI ELITE ATTIVI</h4>
                    <p>Il mercato non rispetta i criteri rigorosi di spinta o volatilità.</p>
                    <hr style="border-color: #ff4444;">
                    <p style="color: #ffffff; text-align: left;"><b>RSI:</b> {details.get('RSI', 'N/A')}</p>
                    <p style="color: #ffffff; text-align: left;"><b>ATR Dinamico:</b> {details.get('ATR Dinamico', 'N/A')}</p>
                    <p style="color: #ffffff; text-align: left;"><b>Candela Prev. Spinta:</b> {details.get('Candela Prev. Spinta', 'N/A')}</p>
                    <p style="color: #ffffff; text-align: left;"><b>Trend Macro (Multi-TF):</b> {details.get('Trend Macro (Multi-TF)', 'N/A')}</p>
                    <p style="color: #ffffff; text-align: left;"><b>Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                    <p style="color: #ffffff; text-align: left;"><b>MACD:</b> {details.get('MACD Cross', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="analysis-box">
                    <h4>🎯 ELITE MOMENTUM CONFLUENCE ALIGNED</h4>
                    <p><b>RSI (14):</b> {details.get('RSI', 'N/A')}</p>
                    <p><b>ATR Dinamico:</b> {details.get('ATR Dinamico', 'N/A')}</p>
                    <p><b>Candela Prev. Spinta:</b> {details.get('Candela Prev. Spinta', 'N/A')}</p>
                    <p><b>Trend Macro (Multi-TF):</b> {details.get('Trend Macro (Multi-TF)', 'N/A')}</p>
                    <p><b>Posizione Bollinger:</b> {details.get('Bollinger Position', 'N/A')}</p>
                    <p><b>Momento MACD:</b> {details.get('MACD Cross', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### ⏳ Current Candle Countdown")
        initial_left = get_seconds_to_next_candle(st.session_state.cached_tf_seconds_snp)
        
        # Timer HTML robusto senza f-string conflittuali
        timer_html = (
            '<div style="font-size: 28px; font-weight: bold; color: #00ffcc; text-align: center; '
            'background-color: #1f1f1f; padding: 15px; border-radius: 8px; border: 1px solid #333333;" '
            'id="countdown_snp">Loading timer...</div>'
            '<script>'
            'var timeLeftSnp = ' + str(initial_left) + ';                       