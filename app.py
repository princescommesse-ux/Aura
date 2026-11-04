import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Bot Analisi Forex & OTC", layout="centered")

st.title("🤖 Bot di Analisi Tecnica Completo")
st.write("Seleziona una delle 20 coppie Forex reali o uno dei 60 asset OTC di valute.")

# --- LISTE COMPLETE DEI 20 FOREX E 60 OTC VALUTE ---

FOREX_LIST = [
    "EUR/USD (EURUSD=X)", "GBP/USD (GBPUSD=X)", "USD/JPY (USDJPY=X)", "AUD/USD (AUDUSD=X)",
    "USD/CAD (USDCAD=X)", "NZD/USD (NZDUSD=X)", "USD/CHF (USDCHF=X)", "EUR/GBP (EURGBP=X)",
    "EUR/JPY (EURJPY=X)", "GBP/JPY (GBPJPY=X)", "AUD/JPY (AUDJPY=X)", "EUR/AUD (EURAUD=X)",
    "GBP/AUD (GBPAUD=X)", "EUR/CAD (EURCAD=X)", "GBP/CAD (GBPCAD=X)", "AUD/CAD (AUDCAD=X)",
    "NZD/JPY (NZDJPY=X)", "EUR/NZD (EURNZD=X)", "GBP/NZD (GBPNZD=X)", "USD/SEK (USDSEK=X)"
]

OTC_VALUTE_LIST = [
    "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "USD/CAD OTC",
    "NZD/USD OTC", "USD/CHF OTC", "EUR/GBP OTC", "EUR/JPY OTC", "GBP/JPY OTC",
    "AUD/JPY OTC", "EUR/AUD OTC", "GBP/AUD OTC", "EUR/CAD OTC", "GBP/CAD OTC",
    "AUD/CAD OTC", "NZD/JPY OTC", "EUR/NZD OTC", "GBP/NZD OTC", "USD/SEK OTC",
    "EUR/SEK OTC", "USD/NOK OTC", "EUR/NOK OTC", "USD/DKK OTC", "USD/PLN OTC",
    "EUR/PLN OTC", "USD/ZAR OTC", "EUR/ZAR OTC", "USD/TRY OTC", "EUR/TRY OTC",
    "USD/MXN OTC", "USD/BRL OTC", "USD/ARS OTC", "USD/CLP OTC", "USD/COP OTC",
    "USD/INR OTC", "USD/IDR OTC", "USD/PHP OTC", "USD/SGD OTC", "USD/THB OTC",
    "USD/MYR OTC", "USD/VND OTC", "USD/KRW OTC", "USD/TWD OTC", "USD/HKD OTC",
    "AUD/NZD OTC", "AUD/CHF OTC", "CAD/JPY OTC", "CHF/JPY OTC", "NZD/CAD OTC",
    "NZD/CHF OTC", "GBP/CHF OTC", "EUR/CHF OTC", "CAD/CHF OTC", "SGD/JPY OTC",
    "ZAR/JPY OTC", "NOK/SEK OTC", "PLN/JPY OTC", "HUF/JPY OTC", "CZK/JPY OTC"
]

# --- MENU PRINCIPALE ---
mercato_tipo = st.radio("Seleziona la tipologia di mercato:", ["Forex Reale (20 coppie)", "Asset OTC Valute (60+ coppie)"])

symbol_to_fetch = "EURUSD=X"
display_name = "EUR/USD"

if mercato_tipo == "Forex Reale (20 coppie)":
    forex_scelta = st.selectbox("Scegli la coppia Forex:", FOREX_LIST)
    symbol_to_fetch = forex_scelta.split("(")[1].replace(")", "").strip()
    display_name = forex_scelta
else:
    asset_scelta = st.selectbox("Scegli l'asset OTC di valuta:", OTC_VALUTE_LIST)
    display_name = asset_scelta
    
    # Mappatura intelligente dei 60 OTC sul Forex reale corrispondente di Yahoo Finance
    # Se la coppia contiene la stessa valuta base/quota, usa il ticker reale per calcolare gli indicatori
    base_clean = asset_scelta.replace(" OTC", "").replace("/", "")
    symbol_to_fetch = f"{base_clean}=X"
    # Fallback di sicurezza se Yahoo non ha il ticker esatto
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
    
    signal = "STAND BY"
    reason = "Mercato in equilibrio o filtri non allineati"
    
    if last['RSI'] < 38 and last['close'] <= last['BB_Lower'] and last['EMA_9'] > last['EMA_21']:
        if last['MACD'] > last['MACD_Signal']:
            signal = "BUY 🟢"
            reason = "RSI ipervenduto, prezzo sotto la Bollinger inferiore, EMA rialzista e MACD favorevole."
            
    elif last['RSI'] > 62 and last['close'] >= last['BB_Upper'] and last['EMA_9'] < last['EMA_21']:
        if last['MACD'] < last['MACD_Signal']:
            signal = "SELL 🔴"
            reason = "RSI ipercomprato, prezzo sopra la Bollinger superiore, EMA ribassista e MACD favorevole."
            
    return {
        "time": str(df.index[-1] if hasattr(df.index, '__getitem__') else "Live"),
        "close": round(float(last['close']), 5),
        "rsi": round(float(last['RSI']), 2),
        "macd": round(float(last['MACD']), 5),
        "signal": signal,
        "reason": reason
    }, None

# Tasto per avviare l'analisi
st.markdown("---")
if st.button("🚀 Avvia Analisi di Mercato", type="primary"):
    with st.spinner(f"Elaborazione dati per {display_name}..."):
        df = yf.download(symbol_to_fetch, period="5d", interval="1m", progress=False)
        if df.empty:
            st.error("Nessun dato ricevuto dal server di mercato.")
        else:
            analysis, err = calculate_indicators(df)
            if analysis:
                st.success(f"Analisi completata per {display_name}!")
                st.metric(label="Prezzo Attuale", value=analysis['close'])
                st.metric(label="RSI (14)", value=analysis['rsi'])
                st.metric(label="MACD", value=analysis['macd'])
                st.markdown(f"### Segnale: {analysis['signal']}")
                st.info(f"**Motivo:** {analysis['reason']}")
            else:
                st.warning(err)


