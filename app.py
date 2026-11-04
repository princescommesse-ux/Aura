import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Bot Analisi Forex & OTC", layout="centered")

st.title("🤖 Bot di Analisi Tecnica")
st.write("Seleziona il mercato, scegli la valuta o l'asset OTC e avvia l'analisi.")

# --- MENU PRINCIPALE IN EVIDENZA ---
mercato_tipo = st.radio("Seleziona la tipologia di mercato:", ["Forex Reale (yfinance)", "Asset OTC"])

symbol = None
asset_name = None

if mercato_tipo == "Forex Reale (yfinance)":
    # Scelta rapida delle valute Forex
    forex_scelta = st.selectbox("Scegli la coppia Forex:", [
        "EUR/USD (EURUSD=X)",
        "GBP/USD (GBPUSD=X)",
        "USD/JPY (USDJPY=X)",
        "AUD/USD (AUDUSD=X)"
    ])
    # Estrae il simbolo pulito per yfinance
    symbol = forex_scelta.split("(")[1].replace(")", "").strip()

else:
    # Scelta degli asset OTC
    asset_scelta = st.selectbox("Scegli l'asset OTC:", [
        "EUR/USD OTC",
        "GBP/USD OTC",
        "Bitcoin (BTC) OTC",
        "Ethereum (ETH) OTC",
        "Dash OTC",
        "Chainlink OTC"
    ])
    asset_name = asset_scelta

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
    if mercato_tipo == "Forex Reale (yfinance)":
        with st.spinner(f"Scaricamento dati reali per {symbol}..."):
            df = yf.download(symbol, period="5d", interval="1m", progress=False)
            if df.empty:
                st.error("Nessun dato ricevuto da yfinance.")
            else:
                analysis, err = calculate_indicators(df)
                if analysis:
                    st.success("Analisi Forex completata!")
                    st.metric(label="Prezzo Attuale", value=analysis['close'])
                    st.metric(label="RSI (14)", value=analysis['rsi'])
                    st.markdown(f"### Segnale: {analysis['signal']}")
                    st.info(f"**Motivo:** {analysis['reason']}")
                else:
                    st.warning(err)
    else:
        st.info(f"Hai selezionato l'asset OTC: **{asset_name}**")
        st.warning("Nota: sui server cloud di Streamlit i flussi WebSocket diretti dei broker OTC subiscono restrizioni di rete. Per gli OTC puri ti conviene testare la logica direttamente in locale se necessario, oppure puoi usare i dati reali del Forex qui sopra.")



