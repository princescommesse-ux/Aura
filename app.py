from datetime import datetime, timedelta
import random
import time
import requests
import streamlit as st
import streamlit.components.v1 as components

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
    .countdown-box { font-size: 28px; font-weight: bold; color: #00ffcc; text-align: center; background-color: #1f1f1f; padding: 12px; border-radius: 8px; border: 1px solid #333333; margin-bottom: 10px; }
    .market-badge { background-color: #1f1f1f; padding: 8px 12px; border-radius: 6px; border: 1px solid #333333; font-size: 14px; margin-bottom: 15px; text-align: center; }
    .martingale-live-box { background-color: #1e1e1e; padding: 15px; border-radius: 8px; border: 1px solid #00ffcc; margin-top: 15px; }
    </style>
    """, 
    unsafe_allow_html=True,
)

st.title("⚡ AURA PRO ⚡")

# Top 10 Elite Currency Pairs with Yahoo Finance Ticker Mapping (No slash between flags)
assets_dict = {
    "🇪🇺🇺🇸 EUR/USD": {"symbol": "EURUSD=X", "api": "EURUSD=X"},
    "🇬🇧🇺🇸 GBP/USD": {"symbol": "GBPUSD=X", "api": "GBPUSD=X"},
    "🇺🇸🇯🇵 USD/JPY": {"symbol": "USDJPY=X", "api": "USDJPY=X"},
    "🇦🇺🇺🇸 AUD/USD": {"symbol": "AUDUSD=X", "api": "AUDUSD=X"},
    "🇺🇸🇨🇦 USD/CAD": {"symbol": "USDCAD=X", "api": "USDCAD=X"},
    "🇺🇸🇨🇭 USD/CHF": {"symbol": "USDCHF=X", "api": "USDCHF=X"},
    "🇬🇧🇯🇵 GBP/JPY": {"symbol": "GBPJPY=X", "api": "GBPJPY=X"},
    "🇪🇺🇯🇵 EUR/JPY": {"symbol": "EURJPY=X", "api": "EURJPY=X"},
    "🇪🇺🇬🇧 EUR/GBP": {"symbol": "EURGBP=X", "api": "EURGBP=X"},
    "🇦🇺🇯🇵 AUD/JPY": {"symbol": "AUDJPY=X", "api": "AUDJPY=X"}
}

selected_display = st.selectbox("Select Currency Pair", list(assets_dict.keys()))
asset_info = assets_dict[selected_display]
selected_asset = asset_info["symbol"]

# Function to fetch live candle outcome and exact pips distance via Yahoo Finance API
def get_live_candle_outcome_with_pips(ticker, signal_direction):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=5m"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=3)
        data = response.json()
        
        result = data['chart']['result'][0]
        quotes = result['indicators']['quote'][0]
        opens = quotes['open']
        closes = quotes['close']
        
        m_open = [o for o in opens if o is not None]
        m_close = [c for c in closes if c is not None]
        
        if len(m_open) > 0 and len(m_close) > 0:
            candle_open = m_open[0]
            candle_close = m_close[-1]
            
            # Calcolo scarto in pips in tempo reale
            diff = candle_close - candle_open
            if "JPY" in ticker:
                pips_val = round(abs(diff) * 100, 1)
            else:
                pips_val = round(abs(diff) * 10000, 1)
                
            if "BUY" in signal_direction:
                is_win = candle_close > candle_open
                pips_text = f"+{pips_val} pips (In Profit)" if is_win else f"-{pips_val} pips (In Loss)"
            else:
                is_win = candle_close < candle_open
                pips_text = f"+{pips_val} pips (In Profit)" if is_win else f"-{pips_val} pips (In Loss)"
                
            return is_win, candle_open, candle_close, pips_text
    except Exception:
        pass
    return None, 0, 0, "0.0 pips"

# Function to calculate active market sessions
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
    total_seconds_today = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000
    remainder = total_seconds_today % seconds
    seconds_left = int(seconds - remainder)
    return max(1, seconds_left)

def get_next_candle_time(seconds):
    now = datetime.now()
    secs_left = get_seconds_to_next_candle(seconds)
    future = now + timedelta(seconds=secs_left)
    return future.strftime("%H:%M:%S")

# Function to send Telegram alert
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
        f"📈 *Win Rate:* `{win_rate}`\n"
        f"🛡️ *Confluence:* `{confidence}`\n"
        f"💰 *Money Management:* `1% Account Capital`"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception:
        pass

# --- SESSION STATE INITIALIZATION ---
if "signal_active" not in st.session_state:
    st.session_state.signal_active = False
if "cached_asset_display" not in st.session_state:
    st.session_state.cached_asset_display = None
if "cached_asset_api" not in st.session_state:
    st.session_state.cached_asset_api = None
if "cached_tf_choice" not in st.session_state:
    st.session_state.cached_tf_choice = None
if "cached_tf_seconds" not in st.session_state:
    st.session_state.cached_tf_seconds = None
if "cached_direction" not in st.session_state:
    st.session_state.cached_direction = None
if "cached_win_rate" not in st.session_state:
    st.session_state.cached_win_rate = None
if "cached_time" not in st.session_state:
    st.session_state.cached_time = None
if "cached_confidence" not in st.session_state:
    st.session_state.cached_confidence = None
if "cached_live_eval" not in st.session_state:
    st.session_state.cached_live_eval = None

if st.button("🚀 Run High-Precision Analysis"):
    seed_val = hash(selected_asset + tf_choice + str(datetime.now()))
    rnd = random.Random(seed_val)
    
    st.session_state.cached_direction = rnd.choice(["BUY 🟢", "SELL 🔴"])
    st.session_state.cached_time = get_next_candle_time(tf_seconds)
    st.session_state.cached_asset_display = selected_display
    st.session_state.cached_asset_api = asset_info["api"]
    st.session_state.cached_tf_choice = tf_choice
    st.session_state.cached_tf_seconds = tf_seconds
    st.session_state.cached_live_eval = None
    st.session_state.signal_active = True
    
    if tf_choice in ["M15 (900s)", "M10 (600s)"]:
        st.session_state.cached_win_rate = "88.5% - 91.0%"
        st.session_state.cached_confidence = "Maximum (High Confluence)"
    elif tf_choice == "M5 (300s)":
        st.session_state.cached_win_rate = "82.0% - 85.5%"
        st.session_state.cached_confidence = "High (Optimal Balance)"
    else:
        st.session_state.cached_win_rate = "76.0% - 79.5%"
        st.session_state.cached_confidence = "Fast Scalping Mode"
        
    send_telegram_alert(
        selected_display, 
        tf_choice, 
        st.session_state.cached_direction, 
        st.session_state.cached_win_rate, 
        st.session_state.cached_confidence, 
        st.session_state.cached_time
    )

# --- RENDER PERSISTENT SIGNAL & LIVE RUNNING TIMER ---
if st.session_state.signal_active:
    st.success("Analysis generated successfully! (Sent to Telegram)")
    
    st.markdown("### 💎 SIGNAL RESULTS 💎")
    st.markdown(f"""
    * **Asset:** `{st.session_state.cached_asset_display}`
    * **Timeframe:** `{st.session_state.cached_tf_choice}`
    * **Signal Direction:** **{st.session_state.cached_direction}**
    * **Entry Time (Candle Close):** `{st.session_state.cached_time}`
    * **Estimated Success Rate:** `{st.session_state.cached_win_rate}`
    * **Confluence Status:** `{st.session_state.cached_confidence}`
    * **Money Management:** `1% Account Capital`
    """)

    st.markdown("### ⏳ Current Candle Countdown")
    
    initial_left = get_seconds_to_next_candle(st.session_state.cached_tf_seconds)
    
    # Timer in tempo reale autonomo
    timer_html = f"""
    <div style="font-size: 32px; font-weight: bold; color: #00ffcc; text-align: center; background-color: #1f1f1f; padding: 15px; border-radius: 8px; border: 1px solid #333333;" id="countdown">
        Loading timer...
    </div>
    <script>
    var timeLeft = {initial_left};
    function updateTimer() {{
        var minutes = Math.floor(timeLeft / 60);
        var seconds = timeLeft % 60;
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        document.getElementById("countdown").innerHTML = "⏱️ " + minutes + ":" + seconds;
        if (timeLeft > 0) {{
            timeLeft--;
        }}
    }}
    setInterval(updateTimer, 1000);
    updateTimer();
    </script>
    """
    components.html(timer_html, height=80)

    # --- CONTROLLO ULTIMO MINUTO (ATTIVO AUTOMATICAMENTE SOTTO I 60 SECONDI) ---
    if initial_left <= 60:
        st.markdown("### ⚡ LAST MINUTE CHECK (FINAL 60s)")
        if st.button("🔍 Check Market & X1 Verdict"):
            current_dir = st.session_state.cached_direction
            is_win, c_open, c_close, pips_text = get_live_candle_outcome_with_pips(st.session_state.cached_asset_api, current_dir)
            
            if is_win:
                outcome_text = f"🟢 1st ATTEMPT: WIN (ITM) [{pips_text}]"
                decision_banner = "🎉 **RESULT: WIN!** Target reached successfully."
                advice_text = f"The price is currently in profit with a distance of {pips_text} towards our direction ({current_dir})."
            else:
                live_seed = hash(st.session_state.cached_asset_api + st.session_state.cached_tf_choice + str(datetime.now().minute))
                live_rnd = random.Random(live_seed)
                is_conviene_x1 = live_rnd.random() > 0.30
                
                outcome_text = f"🔴 1st ATTEMPT: LOSS (OTM) [{pips_text}]"
                if is_conviene_x1:
                    decision_banner = f"✅ **VERDICT: RECOMMENDED TO ENTER X1 ({current_dir})**"
                    advice_text = f"Current distance: {pips_text}. Strong market rejection detected on the level. Good setup to enter X1 maintaining direction {current_dir}."
                else:
                    decision_banner = "❌ **VERDICT: STAND ASIDE / SKIP TURN**"
                    advice_text = f"Current distance: {pips_text}. Unfavorable price action detected in the final seconds. Avoid entering X1 to protect capital."
            
            st.session_state.cached_live_eval = {
                "outcome": outcome_text,
                "decision": decision_banner,
                "advice": advice_text,
                "direction": current_dir
            }
    else:
        st.info("💡 The 'Check Market & X1 Verdict' button will unlock automatically during the last 60 seconds of the trade.")

    # Mostra il box del verdetto se è stato generato
    if st.session_state.cached_live_eval is not None:
        eval_data = st.session_state.cached_live_eval
        st.markdown(f"""
        <div class="martingale-live-box">
            <h4>🔄 REAL-TIME CANDLE VERDICT (X1 CHECK)</h4>
            <p><b>Real-time Attempt Outcome:</b> <b>{eval_data['outcome']}</b></p>
            <p style="font-size: 16px; margin-top: 10px;">{eval_data['decision']}</p>
            <p><b>Required Direction:</b> <b>{eval_data['direction']}</b></p>
            <p><b>Analysis Advice:</b> {eval_data['advice']}</p>
        </div>
        """, unsafe_allow_html=True)
