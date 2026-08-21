import time
from datetime import datetime
import pytz
import requests

BOT_TOKEN = "8626042409:AAHElsiJD8_Jk9R7r5VHUj8fPjcl8Meacp4"
CHAT_ID = "706694019"

CRYPTO_SYMBOLS = ["BTC-USD", "ETH-USD"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=payload, timeout=10)

def get_data(symbol):
    # 5m data for volume, 1d data for High/Low levels
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=2d"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
    return res['chart']['result'][0]

def scanner():
    ist = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(ist).strftime("%Y-%m-%d")
    alerts = []

    for sym in CRYPTO_SYMBOLS:
        try:
            data = get_data(sym)
            quotes = data['indicators']['quote'][0]
            ts_list = data.get('timestamp', [])
            vols = [v for v in quotes['volume'] if v is not None]
            closes = quotes['close']
            opens = quotes['open']
            highs = quotes['high']
            lows = quotes['low']

            if len(vols) < 22: continue

            # Volume criteria
            c_vol = vols[-1]
            avg_vol = sum(vols[-21:-1]) / 20
            
            # Find Today's High/Low and Yesterday's High/Low
            today_highs = []
            today_lows = []
            prev_high = 0
            prev_low = 0
            
            # Yahoo 1d data for prev day levels
            url_1d = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
            res_1d = requests.get(url_1d, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
            d1 = res_1d['chart']['result'][0]['indicators']['quote'][0]
            prev_high = d1['high'][-2]
            prev_low = d1['low'][-2]
            
            # Extract Today's High/Low from intraday
            for i, ts in enumerate(ts_list):
                if datetime.fromtimestamp(ts, ist).strftime("%Y-%m-%d") == today_str:
                    today_highs.append(highs[i])
                    today_lows.append(lows[i])
            
            curr_high = max(today_highs)
            curr_low = min(today_lows)
            ltp = closes[-1]

            # Criteria: 2x Volume AND (Price near Today's H/L OR Prev H/L)
            if c_vol >= 2 * avg_vol:
                # Check proximity (within 0.1%)
                levels = [prev_high, prev_low, curr_high, curr_low]
                is_near = any(abs(ltp - level) / ltp < 0.001 for level in levels)
                
                if is_near:
                    signal = "🟢 BUY" if closes[-1] > opens[-1] else "🔴 SELL"
                    alerts.append(f"• *{sym}* | {signal} | Vol: {c_vol/avg_vol:.1f}x | Price: {ltp:.2f}")

        except Exception: continue

    if alerts:
        msg = f"🚀 *CRYPTO HUNTER ALERT ({datetime.now(ist).strftime('%H:%M')})*\n\n" + "\n".join(alerts)
        send_telegram(msg)

if __name__ == "__main__":
    scanner()
