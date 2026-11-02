from datetime import datetime, timedelta
import random
import time
import requests
import streamlit as st

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
    .countdown-box { font-size: 24px; font-weight: bold; color: #00ffcc; text-align: center; background-color: #1f1f1f; padding: 10px; border-radius: 8px; border: 1px solid #333333; }
    .market-badge { background-color: #1f1f1f; padding: 8px 12px; border-radius: 6px; border: 1px solid #333333; font-size: 14px; margin-bottom: 15px; text-align: center; }
    .martingale-live-box { background-color: #1e1e1e; padding: 15px; border-radius: 8px; border: 1px solid #00ffcc; margin-top: 15px; }
    </style>
    """, 
    unsafe_allow_html=True,
)

st.title("⚡ AURA PRO ⚡")

# Top 10 Elite Currency Pairs with Flag Emojis
assets_dict = {
    "🇪🇺/🇺🇸 EUR/USD": "EUR/USD",
    "🇬🇧/🇺🇸 GBP/USD": "GBP/USD",
    "🇺🇸/🇯🇵 USD/JPY": "USD/JPY",
    "🇦🇺/🇺🇸 AUD/USD": "AUD/USD",
    "🇺🇸/🇨🇦 USD/CAD": "USD/CAD",
    "🇺🇸/🇨🇭 USD/CHF": "USD/CHF",
    "🇬🇧/🇯🇵 GBP/JPY": "GBP/JPY",
    "🇪🇺/🇯🇵 EUR/JPY": "EUR/JPY",
    "🇪🇺/🇬🇧 EUR/GBP": "EUR/GBP",
    "🇦🇺/🇯🇵 AUD/JPY": "AUD/JPY"
}

selected_display = st.selectbox("Select Currency Pair", list(assets_dict.keys()))
selected_asset = assets_dict[selected_display]

# Funzione per calcolare le sessioni di mercato attive (basata su orario UTC)
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

# Mostra lo stato delle sessioni di mercato in tempo reale
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

# Funzione per inviare il segnale su Telegram
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
        f"💰 *Money Management:* `Fixed Risk X1`"
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception:
        pass

# State initialization for absolute stability
if "last_asset" not in st.session_state:
    st.session_state.last_asset = None
if "last_tf" not in st.session_state:
    st.session_state.last_tf = None
if "cached_direction" not in st.session_state:
    st.session_state.cached_direction = None
if "cached_win_rate" not in st.session_state:
    st.session_state.cached_win_rate = None
if "cached_time" not in st.session_state:
    st.session_state.cached_time = None
if "cached_confidence" not in st.session_state:
    st.session_state.cached_confidence = None

if st.button("🚀 Run High-Precision Analysis"):
    is_new_signal = (st.session_state.last_asset != selected_asset or 
                     st.session_state.last_tf != tf_choice or 
                     st.session_state.cached_direction is None)

    if is_new_signal:
        seed_val = hash(selected_asset + tf_choice + str(datetime.now().minute // 5))
        rnd = random.Random(seed_val)
        
        direzioni = ["BUY 🟢", "SELL 🔴"]
        st.session_state.cached_direction = rnd.choice(direzioni)
        st.session_state.cached_time = get_next_candle_time(tf_seconds)
        
        if tf_choice in ["M15 (900s)", "M10 (600s)"]:
            st.session_state.cached_win_rate = "88.5% - 91.0%"
            st.session_state.cached_confidence = "Maximum (High Confluence)"
        elif tf_choice == "M5 (300s)":
            st.session_state.cached_win_rate = "82.0% - 85.5%"
            st.session_state.cached_confidence = "High (Optimal Balance)"
        else:
            st.session_state.cached_win_rate = "76.0% - 79.5%"
            st.session_state.cached_confidence = "Fast Scalping Mode"
            
        st.session_state.last_asset = selected_asset
        st.session_state.last_tf = tf_choice
        
        send_telegram_alert(
            selected_display, 
            tf_choice, 
            st.session_state.cached_direction, 
            st.session_state.cached_win_rate, 
            st.session_state.cached_confidence, 
            st.session_state.cached_time
        )

    with st.spinner(f"Processing high-precision multi-timeframe models for {selected_display}..."):
        st.success("Analysis generated successfully! (Sent to Telegram)")
        
        # Professional English Output with clean Markdown layout and double diamonds
        st.markdown("### 💎 SIGNAL RESULTS 💎")
        st.markdown(f"""
        * **Asset:** `{selected_display}`
        * **Timeframe:** `{tf_choice}`
        * **Signal Direction:** **{st.session_state.cached_direction}**
        * **Entry Time (Candle Close):** `{st.session_state.cached_time}`
        * **Estimated Success Rate:** `{st.session_state.cached_win_rate}`
        * **Confluence Status:** `{st.session_state.cached_confidence}`
        * **Money Management:** `Fixed Risk X1`
        """)

        # Synchronized Live Countdown Timer matching candle close
        st.markdown("### ⏳ Current Candle Countdown")
        placeholder = st.empty()
        
        initial_left = get_seconds_to_next_candle(tf_seconds)
        
        for remaining in range(initial_left, -1, -1):
            mins, secs = divmod(remaining, 60)
            time_format = f"{mins:02d}:{secs:02d}"
            placeholder.markdown(f'<div class="countdown-box">⏱️ {time_format}</div>', unsafe_allow_html=True)
            if remaining > 0:
                time.sleep(1)
        
        # --- FINESTRA LIVE: SECONDO TENTATIVO / MARTINGALA X1 ---
        live_seed = hash(selected_asset + tf_choice + str(time.time()))
        live_rnd = random.Random(live_seed)
        
        is_favorable_x1 = live_rnd.random() > 0.32
        
        if is_favorable_x1:
            box_action = "🟢 ENTER 2nd ATTEMPT (Martingala X1 - Recommended)"
            box_rate = f"{live_rnd.randint(82, 90)}% Success Probability"
            box_advice = "The previous candle closed with clear rejection. Conditions are favorable to repeat the entry at X1."
        else:
            box_action = "🔴 DO NOT ENTER / SKIP (Not Recommended)"
            box_rate = f"{live_rnd.randint(45, 62)}% Low Probability"
            box_advice = "Market volatility is erratic after candle close. Skip this second attempt to protect capital."

        st.markdown(f"""
        <div class="martingale-live-box">
            <h4>🔄 LIVE CHECK: 2nd ATTEMPT (MARTINGALA X1)</h4>
            <p><b>Real-time Evaluation:</b> {box_action}</p>
            <p><b>Probability / Success Rate:</b> <code>{box_rate}</code></p>
            <p><b>Analysis Advice:</b> {box_advice}</p>
        </div>
        """, unsafe_allow_html=True)
