import time
from datetime import datetime
import pytz
import requests

BOT_TOKEN = "8626042409:AAHElsiJD8_Jk9R7r5VHUj8fPjcl8Meacp4"
CHAT_ID = "706694019"

# Crypto Symbols
CRYPTO_SYMBOLS = ["BTC-USD", "ETH-USD"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=payload, timeout=10)

def get_data(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=2d"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
    return res['chart']['result'][0]

def scanner():
    ist = pytz.timezone('Asia/Kolkata')
    alerts = []

    for sym in CRYPTO_SYMBOLS:
        try:
            data = get_data(sym)
            quotes = data['indicators']['quote'][0]
            vols = [v for v in quotes['volume'] if v is not None]
            closes = quotes['close']
            opens = quotes['open']
            highs = quotes['high']
            lows = quotes['low']

            if len(vols) < 22: continue

            # Current candle logic
            c_vol = vols[-1]
            avg_vol = sum(vols[-21:-1]) / 20
            
            # Previous Day High/Low
            # (Daily data fetch for prev day high/low)
            url_1d = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
            res_1d = requests.get(url_1d, headers={"User-Agent": "Mozilla/5.0"}).json()
            d1 = res_1d['chart']['result'][0]['indicators']['quote'][0]
            prev_high = d1['high'][-2]
            prev_low = d1['low'][-2]

            # Criteria: 2x Volume + High/Low interaction
            if c_vol >= 2 * avg_vol:
                ltp = closes[-1]
                # Price is near Prev High or Prev Low (within 0.1%)
                is_near_level = (abs(ltp - prev_high) / ltp < 0.001) or (abs(ltp - prev_low) / ltp < 0.001)
                
                if is_near_level:
                    signal = "🟢 BUY" if closes[-1] > opens[-1] else "🔴 SELL"
                    alerts.append(f"• *{sym}* | {signal} | Vol: {c_vol/avg_vol:.1f}x | Price: {ltp:.2f}")

        except Exception: continue

    if alerts:
        msg = f"🚀 *CRYPTO ALERT ({datetime.now(ist).strftime('%H:%M')})*\n\n" + "\n".join(alerts)
        send_telegram(msg)

if __name__ == "__main__":
    scanner()
