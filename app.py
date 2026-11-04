import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Bot Analisi Forex & OTC", layout="centered")

st.title("🤖 Bot di Analisi Tecnica (Forex & OTC)")
st.write("Analisi automatica con RSI, EMA, Bande di Bollinger e MACD.")

# Menu laterale per la scelta
st.sidebar.header("Configurazione")
modalita = st.sidebar.selectbox("Seleziona Mercato", ["Forex Reale (yfinance)", "OTC WebSocket"])

# Funzione comune di calcolo indicatori (corretta per le maiuscole di yfinance)
def calculate_indicators(df):
    # Pulisce eventuali multi-indice e normalizza i nomi delle colonne in minuscolo
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df.columns = [str(col).lower() for col in df.columns]
    
    if 'close' not in df.columns:
        return None, f"Colonna 'close' non trovata. Colonne disponibili: {list(df.columns)}"
        
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

# ==================== MODALITA FOREX ====================
if modalita == "Forex Reale (yfinance)":
    symbol = st.sidebar.text_input("Simbolo Forex", value="EURUSD=X")
    
    if st.button("Analizza Forex"):
        with st.spinner("Scaricamento dati in corso..."):
            df = yf.download(symbol, period="5d", interval="1m", progress=False)
            if df.empty:
                st.error("Nessun dato ricevuto da yfinance.")
            else:
                analysis, err = calculate_indicators(df)
                if analysis:
                    st.success("Analisi completata!")
                    st.metric(label="Prezzo Attuale", value=analysis['close'])
                    st.metric(label="RSI (14)", value=analysis['rsi'])
                    st.markdown(f"### Segnale: {analysis['signal']}")
                    st.info(f"**Motivo:** {analysis['reason']}")
                else:
                    st.warning(err)

# ==================== MODALITA OTC ====================
elif modalita == "OTC WebSocket":
    st.sidebar.warning("Nota: I WebSocket OTC sui server cloud (come Streamlit) potrebbero subire restrizioni IP.")
    ssid_input = st.sidebar.text_input("Inserisci il tuo SSID", type="password")
    asset_otc = st.sidebar.selectbox("Asset OTC", ["EURUSD_otc", "GBPUSD_otc", "Bitcoin_otc", "Ethereum_otc"])
    
    st.write(f"Asset selezionato per i test WebSocket: **{asset_otc}**")


