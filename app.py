import asyncio
import json
import pandas as pd
import numpy as np
import yfinance as yf
import websockets

# ==========================================
# CONFIGURAZIONE GENERALE BOT UNIFICATO
# ==========================================
SSID = "INSERISCI_QUI_IL_TUO_SSID_DEL_BROWSER"
WEBSOCKET_URL = "wss://api.pocketoption.com/socket.io/?EIO=4&transport=websocket"

# ==========================================
# MOTORE DI INDICATORI COMUNE
# ==========================================
def calculate_indicators(df):
    if len(df) < 30:
        return None, "Dati insufficienti per il calcolo"
    
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
    
    # Logica di Segnale (Bilanciata Standard)
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
        "time": str(last.get('time', 'Live')),
        "close": last['close'],
        "rsi": round(last['RSI'], 2),
        "macd": round(last['MACD'], 5),
        "signal": signal,
        "reason": reason
    }, None

# ==========================================
# MODULO 1: ANALISI FOREX REALE (yfinance)
# ==========================================
def analyze_forex(symbol="EURUSD=X", interval="1m"):
    print(f"\n[FOREX] Analisi in corso per {symbol}...")
    df = yf.download(symbol, period="1d", interval=interval, progress=False)
    if df.empty:
        print("[errore] Nessun dato ricevuto da yfinance.")
        return
    
    # Pulizia colonne multi-indice di yfinance se presenti
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    analysis, err = calculate_indicators(df)
    if analysis:
        print(f"Prezzo: {analysis['close']} | RSI: {analysis['rsi']}")
        print(f"-> Segnale: {analysis['signal']} | Motivo: {analysis['reason']}\n" + "-"*50)

# ==========================================
# MODULO 2: ANALISI OTC (WebSocket)
# ==========================================
async def analyze_otc(asset_target="EURUSD_otc"):
    candles_df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://pocketoption.com"
    }
    
    print(f"\n[OTC] Connessione al flusso WebSocket per: {asset_target}...")
    try:
        async with websockets.connect(WEBSOCKET_URL, extra_headers=headers) as ws:
            await ws.send('40')
            await ws.send(f'42["auth", {{"session": "{SSID}", "isDemo": 1}}]')
            await ws.send(f'42["changeSymbol", "{asset_target}"]')
            print(f"[SUCCESSO] Connesso a {asset_target}! In ascolto dei dati in tempo reale...\n")
            
            while True:
                response = await ws.recv()
                if response == "2":
                    await ws.send("3")
                    continue
                
                if response.startswith("42"):
                    data = json.loads(response[2:])
                    event_type = data[0]
                    payload = data[1]
                    
                    if event_type in ["updateStream", "candleHistory"]:
                        if isinstance(payload, list):
                            candles_df = pd.DataFrame(payload)
                        elif isinstance(payload, dict) and 'close' in payload:
                            new_row = pd.DataFrame([payload])
                            candles_df = pd.concat([candles_df, new_row], ignore_index=True)
                            
                        analysis, err = calculate_indicators(candles_df)
                        if analysis:
                            print(f"[OTC Feed] Prezzo: {analysis['close']} | RSI: {analysis['rsi']}")
                            print(f"-> Segnale: {analysis['signal']} | Motivo: {analysis['reason']}\n" + "-"*50)
                            
    except Exception as e:
        print(f"[ERRORE WEBSOCKET] {e}")

# ==========================================
# MENU PRINCIPALE DEL BOT
# ==========================================
if __name__ == "__main__":
    print("=== BOT UNIFICATO FOREX & OTC ===")
    print("1. Analizza Forex Reale (es. EURUSD=X)")
    print("2. Avvia Monitoraggio WebSocket OTC (es. EURUSD_otc)")
    
    scelta = input("\nScegli la modalità (1 o 2): ").strip()
    
    if scelta == "1":
        symbol_input = input("Inserisci il simbolo Forex (default EURUSD=X): ").strip() or "EURUSD=X"
        analyze_forex(symbol_input)
    elif scelta == "2":
        asset_input = input("Inserisci l'asset OTC (default EURUSD_otc): ").strip() or "EURUSD_otc"
        asyncio.run(analyze_otc(asset_input))
    else:
        print("Scelta non valida.")
