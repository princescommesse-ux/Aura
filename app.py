import asyncio
import json
import pandas as pd
import numpy as np
import yfinance as yf
import websockets

# ==========================================
# CONFIGURAZIONE GENERALE
# ==========================================
SSID = "INSERISCI_QUI_IL_TUO_SSID_DEL_BROWSER"
WEBSOCKET_URL = "wss://api.pocketoption.com/socket.io/?EIO=4&transport=websocket"

# LISTA COMPLETA DEGLI ASSET DISPONIBILI NEL BOT
ASSET_LIST = {
    # --- FOREX REALE (Yahoo Finance) ---
    "1": {"name": "EUR/USD (Reale)", "symbol": "EURUSD=X", "type": "forex"},
    "2": {"name": "GBP/USD (Reale)", "symbol": "GBPUSD=X", "type": "forex"},
    "3": {"name": "USD/JPY (Reale)", "symbol": "USDJPY=X", "type": "forex"},
    
    # --- FOREX OTC ---
    "4": {"name": "EUR/USD OTC", "symbol": "EURUSD_otc", "type": "otc"},
    "5": {"name": "GBP/USD OTC", "symbol": "GBPUSD_otc", "type": "otc"},
    "6": {"name": "USD/JPY OTC", "symbol": "USDJPY_otc", "type": "otc"},
    "7": {"name": "AUD/USD OTC", "symbol": "AUDUSD_otc", "type": "otc"},
    
    # --- CRIPTO & ASSET OTC (Dal tuo screenshot) ---
    "8": {"name": "Bitcoin (BTC) OTC", "symbol": "Bitcoin_otc", "type": "otc"},
    "9": {"name": "Ethereum (ETH) OTC", "symbol": "Ethereum_otc", "type": "otc"},
    "10": {"name": "Dash OTC", "symbol": "Dash_otc", "type": "otc"},
    "11": {"name": "Chainlink OTC", "symbol": "Chainlink_otc", "type": "otc"},
    "12": {"name": "BCH/EUR OTC", "symbol": "BCHEUR_otc", "type": "otc"},
    "13": {"name": "BCH/GBP OTC", "symbol": "BCHGBP_otc", "type": "otc"},
    "14": {"name": "BCH/JPY OTC", "symbol": "BCHJPY_otc", "type": "otc"},
    "15": {"name": "BTC/GBP OTC", "symbol": "BTCGBP_otc", "type": "otc"},
    "16": {"name": "BTC/JPY OTC", "symbol": "BTCJPY_otc", "type": "otc"},
}

# ==========================================
# MOTORE DI INDICATORI COMUNE
# ==========================================
def calculate_indicators(df):
    if len(df) < 30:
        return None, "Dati insufficienti per il calcolo"
    
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
        "time": str(last.get('time', 'Live')),
        "close": round(float(last['close']), 5),
        "rsi": round(float(last['RSI']), 2),
        "macd": round(float(last['MACD']), 5),
        "signal": signal,
        "reason": reason
    }, None

# ==========================================
# ANALISI FOREX REALE (yfinance)
# ==========================================
def run_forex_analysis(symbol, name):
    print(f"\n[FOREX REALE] Avvio analisi in corso per {name} ({symbol})...")
    df = yf.download(symbol, period="5d", interval="1m", progress=False)
    if df.empty:
        print("[ERRORE] Nessun dato ricevuto da yfinance.")
        return
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    analysis, err = calculate_indicators(df)
    if analysis:
        print(f"[{analysis['time']}] Prezzo: {analysis['close']} | RSI: {analysis['rsi']}")
        print(f"-> Segnale: {analysis['signal']}\n   Motivo: {analysis['reason']}\n" + "-"*50)

# ==========================================
# ANALISI OTC (WebSocket)
# ==========================================
async def run_otc_analysis(asset_target, name):
    candles_df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://pocketoption.com"
    }
    
    print(f"\n[OTC WEBSOCKET] Connessione al flusso per: {name} ({asset_target})...")
    try:
        async with websockets.connect(WEBSOCKET_URL, extra_headers=headers) as ws:
            await ws.send('40')
            await ws.send(f'42["auth", {{"session": "{SSID}", "isDemo": 1}}]')
            await ws.send(f'42["changeSymbol", "{asset_target}"]')
            print(f"[SUCCESSO] Connesso a {name}! In ascolto dei dati in tempo reale...\n")
            
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
                            print(f"[{name} Live] Prezzo: {analysis['close']} | RSI: {analysis['rsi']}")
                            print(f"-> Segnale: {analysis['signal']}\n   Motivo: {analysis['reason']}\n" + "-"*50)
                            
    except websockets.exceptions.ConnectionClosedError:
        print("[ERRORE] Connessione WebSocket chiusa dal server. Verifica che l'SSID sia corretto.")
    except Exception as e:
        print(f"[ERRORE WEBSOCKET] {e}")

# ==========================================
# MENU PRINCIPALE
# ==========================================
if __name__ == "__main__":
    print("==========================================")
    print("   BOT UNIFICATO: FOREX & OTC ANALYZER")
    print("==========================================")
    print("Seleziona l'asset da monitorare:\n")
    
    for key, data in ASSET_LIST.items():
        print(f" [{key}] {data['name']}")
        
    scelta = input("\nInserisci il numero corrispondente all'asset: ").strip()
    
    if scelta in ASSET_LIST:
        selected = ASSET_LIST[scelta]
        if selected["type"] == "forex":
            run_forex_analysis(selected["symbol"], selected["name"])
        else:
            try:
                asyncio.run(run_otc_analysis(selected["symbol"], selected["name"]))
            except KeyboardInterrupt:
                print("\n[STOP] Monitoraggio interrotto manualmente.")
    else:
        print("[ERRORE] Selezione non valida. Riavvia lo script.")

