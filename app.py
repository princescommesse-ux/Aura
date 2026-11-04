import time
import pandas as pd
import numpy as np
import yfinance as yf

# ==========================================
# CONFIGURAZIONE BOT (STANDARD / BALANCED)
# ==========================================
# Puoi cambiare la coppia Forex in base alle tue preferenze
SYMBOL = "EURUSD=X" 
INTERVAL = "1m"     # Intervallo delle candele (1 minuto)

def fetch_data(symbol):
    """Scarica i dati reali da yfinance"""
    df = yf.download(symbol, period="1d", interval=INTERVAL, progress=False)
    if df.empty:
        return None
    # Pulisce eventuali multi-indice di yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def calculate_indicators(df):
    """Calcola la logica tecnica: RSI, EMA, Bollinger, MACD"""
    if len(df) < 30:
        return None, "Dati insufficienti"
    
    # 1. EMA 9 e 21
    df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    # 2. RSI 14
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 3. Bande di Bollinger (20, 2)
    df['BB_Middle'] = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (std * 2)
    
    # 4. MACD (12, 26, 9)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    last = df.iloc[-1]
    
    # Logica di Segnale Bilanciata
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
        "time": str(df.index[-1]),
        "close": round(float(last['close']), 5),
        "rsi": round(float(last['RSI']), 2),
        "macd": round(float(last['MACD']), 5),
        "signal": signal,
        "reason": reason
    }, None

def main():
    print(f"=== AVVIO BOT FOREX (app.py) su {SYMBOL} ===")
    print("Monitoraggio attivo dei dati reali. Premi Ctrl+C per uscire.\n")
    
    while True:
        try:
            df = fetch_data(SYMBOL)
            if df is not None:
                analysis, err = calculate_indicators(df)
                if analysis:
                    print(f"[{analysis['time']}] Prezzo: {analysis['close']} | RSI: {analysis['rsi']}")
                    print(f"-> Segnale: {analysis['signal']}")
                    print(f"   Motivo: {analysis['reason']}")
                    print("-" * 60)
            
            # Attende 60 secondi prima della candela successiva
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n[STOP] Bot interrotto manualmente.")
            break
        except Exception as e:
            print(f"[ERRORE] {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
