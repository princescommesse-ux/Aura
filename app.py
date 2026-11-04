import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Bot Analisi Forex & OTC Pro", layout="centered")

st.title("🤖 Bot di Analisi Tecnica - Pro Edition")
st.write("Seleziona il mercato, il timeframe (5m, 10m, 15m) e avvia l'analisi.")

# --- LISTE COMPLETE CON BANDIERE ---
FOREX_LIST = [
    "🇪🇺🇺🇸 EUR/USD (EURUSD=X)", "🇬🇧🇺🇸 GBP/USD (GBPUSD=X)", "🇯🇵🇺🇸 USD/JPY (USDJPY=X)", "🇦🇺🇺🇸 AUD/USD (AUDUSD=X)",
    "🇨🇦🇺🇸 USD/CAD (USDCAD=X)", "🇳🇿🇺🇸 NZD/USD (NZDUSD=X)", "🇨🇭🇺🇸 USD/CHF (USDCHF=X)", "🇪🇺🇬🇧 EUR/GBP (EURGBP=X)",
    "🇪🇺🇯🇵 EUR/JPY (EURJPY=X)", "🇬🇧🇯🇵 GBP/JPY (GBPJPY=X)", "🇦🇺🇯🇵 AUD/JPY (AUDJPY=X)", "🇪🇺🇦🇺 EUR/AUD (EURAUD=X)",
    "🇬🇧🇦🇺 GBP/AUD (GBPAUD=X)", "🇪🇺🇨🇦 EUR/CAD (EURCAD=X)", "🇬🇧🇨🇦 GBP/CAD (GBPCAD=X)", "🇦🇺🇨🇦 AUD/CAD (AUDCAD=X)",
    "🇳🇿🇯🇵 NZD/JPY (NZDJPY=X)", "🇪🇺🇳🇿 EUR/NZD (EURNZD=X)", "🇬🇧🇳🇿 GBP/NZD (GBPNZD=X)", "🇸🇪🇺🇸 USD/SEK (USDSEK=X)"
]

OTC_VALUTE_LIST = [
    "🇪🇺🇺🇸 EUR/USD OTC", "🇬🇧🇺🇸 GBP/USD OTC", "🇯🇵🇺🇸 USD/JPY OTC", "🇦🇺🇺🇸 AUD/USD OTC", "🇨🇦🇺🇸 USD/CAD OTC",
    "🇳🇿🇺🇸 NZD/USD OTC", "🇨🇭🇺🇸 USD/CHF OTC", "🇪🇺🇬🇧 EUR/GBP OTC", "🇪🇺🇯🇵 EUR/JPY OTC", "🇬🇧🇯🇵 GBP/JPY OTC",
    "🇦🇺🇯🇵 AUD/JPY OTC", "🇪🇺🇦🇺 EUR/AUD OTC", "🇬🇧🇦🇺 GBP/AUD OTC", "🇪🇺🇨🇦 EUR/CAD OTC", "🇬🇧🇨🇦 GBP/CAD OTC",
    "🇦🇺🇨🇦 AUD/CAD OTC", "🇳🇿🇯🇵 NZD/JPY OTC", "🇪🇺🇳🇿 EUR/NZD OTC", "🇬🇧🇳🇿 GBP/NZD OTC", "🇸🇪🇺🇸 USD/SEK OTC",
    "🇸🇪🇪🇺 EUR/SEK OTC", "🇳🇴🇺🇸 USD/NOK OTC", "🇳🇴🇪🇺 EUR/NOK OTC", "🇩🇰🇺🇸 USD/DKK OTC", "🇵🇱🇺🇸 USD/PLN OTC",
    "🇵🇱🇪🇺 EUR/PLN OTC", "🇿🇦🇺🇸 USD/ZAR OTC", "🇿🇦🇪🇺 EUR/ZAR OTC", "🇹🇷🇺🇸 USD/TRY OTC", "🇹🇷🇪🇺 EUR/TRY OTC",
    "🇲🇽🇺🇸 USD/MXN OTC", "🇧🇷🇺🇸 USD/BRL OTC", "🇦🇷🇺🇸 USD/ARS OTC", "🇨🇱🇺🇸 USD/CLP OTC", "🇨🇴🇺🇸 USD/COP OTC",
    "🇮🇳🇺🇸 USD/INR OTC", "🇮🇩🇺🇸 USD/IDR OTC", "🇵🇭🇺🇸 USD/PHP OTC", "🇸🇬🇺🇸 USD/SGD OTC", "🇹🇭🇺🇸 USD/THB OTC",
    "🇲🇾🇺🇸 USD/MYR OTC", "🇻🇳🇺🇸 USD/VND OTC", "🇰🇷🇺🇸 USD/KRW OTC", "🇹🇼🇺🇸 USD/TWD OTC", "🇭🇰🇺🇸 USD/HKD OTC",
    "🇳🇿🇦🇺 AUD/NZD OTC", "🇨🇭🇦🇺 AUD/CHF OTC", "🇯🇵🇨🇦 CAD/JPY OTC", "🇯🇵🇨🇭 CHF/JPY OTC", "🇨🇦🇳🇿 NZD/CAD OTC",
    "🇨🇭🇳🇿 NZD/CHF OTC", "🇨🇭🇬🇧 GBP/CHF OTC", "🇨🇭🇪🇺 EUR/CHF OTC", "🇨🇭🇨🇦 CAD/CHF OTC", "🇯🇵🇸🇬 SGD/JPY OTC",
    "🇯🇵🇿🇦 ZAR/JPY OTC", "🇸🇪🇳🇴 NOK/SEK OTC", "🇯🇵🇵🇱 PLN/JPY OTC", "🇯🇵🇭🇺 HUF/JPY OTC", "🇯🇵🇨🇿 CZK/JPY OTC"
]

# --- PANNELLO DI CONFIGURAZIONE ---
st.sidebar.header("⚙️ Impostazioni")
mercato_tipo = st.sidebar.radio("Mercato:", ["Forex Reale (20 coppie)", "Asset OTC Valute (60+)"])
# Timeframe richiesti: solo 5m, 10m, 15m
timeframe = st.sidebar.selectbox("⏱️ Timeframe:", ["5m", "10m", "15m"], index=0)
auto_refresh = st.sidebar.checkbox("Abilita Countdown / Auto-Refresh", value=False)

symbol_to_fetch = "EURUSD=X"
display_name = "EUR/USD"

if mercato_tipo == "Forex Reale (20 coppie)":
    forex_scelta = st.selectbox("Scegli la coppia Forex:", FOREX_LIST)
    symbol_to_fetch = forex_scelta.split("(")[1].replace(")", "").strip()
    display_name = forex_scelta
else:
    asset_scelta = st.selectbox("Scegli l'asset OTC di valuta:", OTC_VALUTE_LIST)
    display_name = asset_scelta
    base_clean = asset_scelta.split(" ")[1].replace("/", "")
    symbol_to_fetch = f"{base_clean}=X"
    if base_clean not in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF", "EURGBP", "EURJPY", "GBPJPY"]:
        symbol_to_fetch = "EURUSD=X"

# Funzione di calcolo indicatori
def calculate_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df.columns = [str(col).lower() for col in df.columns]
    
    if 'close' not in df.columns:
        return None, f"Colonna 'close' non trovata. Colonne: {list(df.columns)}"
        
    if len(df) < 30:
        return None, "Dati insufficienti per il calcolo (< 30 candele)"
    
    df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['BB_Middle'] = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (std * 2)
    
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    last = df.iloc[-1]
    rsi_val = last['RSI']
    
    signal = "STAND BY"
    reason = f"RSI neutrale ({round(rsi_val, 2)})."
    
    if rsi_val < 45 or last['close'] <= last['BB_Lower']:
        signal = "BUY 🟢"
        reason = f"RSI in zona vantaggiosa ({round(rsi_val, 2)}) o prezzo sotto la banda inferiore."
    elif rsi_val > 55 or last['close'] >= last['BB_Upper']:
        signal = "SELL 🔴"
        reason = f"RSI in zona vantaggiosa ({round(rsi_val, 2)}) o prezzo sopra la banda superiore."
            
    return {
        "time": str(df.index[-1] if hasattr(df.index, '__getitem__') else "Live"),
        "close": round(float(last['close']), 5),
        "rsi": round(float(rsi_val), 2),
        "macd": round(float(last['MACD']), 5),
        "signal": signal,
        "reason": reason
    }, None

# Esecuzione Analisi
st.markdown("---")
if st.button("🚀 Avvia Analisi di Mercato", type="primary"):
    with st.spinner(f"Scaricamento e adattamento dati ({timeframe}) per {display_name}..."):
        # Scarichiamo a 1m per poter ricampionare in modo pulito anche a 10m
        df = yf.download(symbol_to_fetch, period="5d", interval="1m", progress=False)
        
        if df.empty:
            st.error("Nessun dato ricevuto dal server di mercato.")
        else:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [str(col).lower() for col in df.columns]
            
            # Ricampionamento in base al timeframe scelto (5m, 10m, 15m)
            rule_map = {"5m": "5min", "10m": "10min", "15m": "15min"}
            rule = rule_map.get(timeframe, "5min")
            
            df = df.resample(rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            analysis, err = calculate_indicators(df)
            if analysis:
                st.success(f"Analisi completata per {display_name} [{timeframe}]!")
                
                # Metriche principali
                col1, col2, col3 = st.columns(3)
                col1.metric("Prezzo", analysis['close'])
                col2.metric("RSI (14)", analysis['rsi'])
                col3.metric("MACD", analysis['macd'])
                
                st.markdown(f"### Segnale: {analysis['signal']}")
                st.info(f"**Motivo:** {analysis['reason']}")
            else:
                st.warning(err)

# Gestione Countdown / Auto-Refresh visivo
if auto_refresh:
    st.markdown("---")
    placeholder = st.empty()
    for seconds in range(60, 0, -1):
        placeholder.markdown(f"⏳ **Prossimo aggiornamento automatico tra:** `{seconds} secondi`")
        time.sleep(1)
    st.rerun()
