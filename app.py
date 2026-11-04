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

# LISTA ASSET
ASSET_LIST = {
    "1": {"name": "EUR/USD (Reale - yfinance)", "symbol": "EURUSD=X", "type": "forex"},
    "2": {"name": "EUR/USD OTC", "symbol": "EURUSD_otc", "type": "otc"},
    "3": {"name": "GBP/USD OTC", "symbol": "GBPUSD_otc", "type": "otc"},
    "4": {"name": "Bitcoin (BTC) OTC", "symbol": "Bitcoin_otc", "type": "otc"},
    "5": {"name": "Ethereum (ETH) OTC", "symbol": "Ethereum_otc", "type": "otc"},
}

def calculate_indicators(df):
    if len(df) < 30:
        return None, f"Dati insufficienti ({len(df)} candele, ne servono almeno 30)"
    
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

def run_forex_analysis(symbol, name):
    print(f"\n[FOREX] Scaricamento dati reali per {name}...")
    try:
        df = yf.download(symbol, period="5d", interval="1m", progress=False)
        if df.empty:
            print("[ERRORE] yfinance ha restituito un DataFrame vuoto.")
            return
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        analysis, err = calculate_indicators(df)
        if analysis:
            print(f"\n[{analysis['time']}] Prezzo: {analysis['close']} | RSI: {analysis['rsi']}")
            print(f"-> Segnale: {analysis['signal']}")
            print(f"   Motivo: {analysis['reason']}\n" + "-"*50)
        else:
            print(f"[ATTENZIONE] {err}")
    except Exception as e:
        print(f"[ERRORE FOREX] {e}")

async def run_otc_analysis(asset_target, name):
    candles_df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://pocketoption.com"
    }
    
    print(f"\n[OTC] Tentativo di connessione WebSocket per {name} ({asset_target})...")
    
    try:
        # Aggiungiamo un timeout di connessione di 10 secondi per evitare blocchi infiniti
        async with websockets.connect(WEBSOCKET_URL, extra_headers=headers, ping_interval=20) as ws:
            print("[DEBUG] Connessione WebSocket stabilita. Invio handshake...")
            await ws.send('40')
            
            print(f"[DEBUG] Invio autenticazione con SSID...")
            auth_msg = f'42["auth", {{"session": "{SSID}", "isDemo": 1}}]'
            await ws.send(auth_msg)
            
            print(f"[DEBUG] Sottoscrizione all'asset {asset_target}...")
            sub_msg = f'42["changeSymbol", "{asset_target}"]'
            await ws.send(sub_msg)
            
            print(f"[SUCCESSO] In ascolto dei flussi live. Premi Ctrl+C per uscire.\n")
            
            while True:
                try:
                    # Timeout di 15 secondi sul singolo pacchetto per evitare il freeze totale
                    response = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    
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
                                print(f"-> Segnale: {analysis['signal']} | Motivo: {analysis['reason']}\n" + "-"*50)
                
                except asyncio.TimeoutError:
                    print("[AVVISO] Nessun pacchetto ricevuto dal server negli ultimi 15 secondi (connessione inattiva o SSID non valido).")
                    break
                    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"[ERRORE WEBSOCKET] Status code non valido: {e.status_code}. Il server ha rifiutato la connessione.")
    except Exception as e:
        print(f"[ERRORE WEBSOCKET CRITICO] {e}")

if __name__ == "__main__":
    print("==========================================")
    print("   BOT UNIFICATO: FOREX & OTC (DEBUG)")
    print("==========================================")
    print("Seleziona l'asset da monitorare:\n")
    
    for key, data in ASSET_LIST.items():
        print(f" [{key}] {data['name']}")
        
    scelta = input("\nInserisci il numero dell'asset: ").strip()
    
    if scelta in ASSET_LIST:
        selected = ASSET_LIST[scelta]
        if selected["type"] == "forex":
            run_forex_analysis(selected["symbol"], selected["name"])
        else:
            try:
                asyncio.run(run_otc_analysis(selected["symbol"], selected["name"]))
            except KeyboardInterrupt:
                print("\n[STOP] Monitoraggio interrotto.")
    else:
        print("[ERRORE] Scelta non valida.") 
