import asyncio
import time
import pandas as pd
import ccxt
from telegram import Bot
from datetime import datetime
import logging

# --- Config utilisateur ---
API_KEY = "8683629e-376a-4f8f-8aa3-b1393f184d70"
API_SECRET = "CBD17C85B60BCFA86B9E2F9E9F6E5789"
API_PASSPHRASE = "Trading_Bot2026"
TELEGRAM_TOKEN = "6590523947:AAE_FakDtTLOIKUoCL2opb1FHDyKk4UosA8"
CHAT_ID = 6669494469
SYMBOLS = ['BTC/USDT', 'XAU/USDT']
INTERVAL = '15m'
DELAY = 60 * 15  # toutes les 15 minutes

# --- Initialisation bot Telegram ---
bot = Bot(token=TELEGRAM_TOKEN)

# --- Initialisation OKX ---
exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# --- Fonctions d'analyse ---
def analyse_technique(df):
    df['ema'] = df['close'].ewm(span=20).mean()
    df['rsi'] = compute_rsi(df['close'], 14)
    df['macd'], df['signal'] = compute_macd(df['close'])
    df['upper_bb'], df['lower_bb'] = compute_bollinger(df['close'])

    last = df.iloc[-1]

    if last['macd'] > last['signal'] and last['rsi'] < 60 and last['close'] < last['lower_bb']:
        return "📈 Achat (Buy)"
    elif last['macd'] < last['signal'] and last['rsi'] > 40 and last['close'] > last['upper_bb']:
        return "📉 Vente (Sell)"
    else:
        return "⏸️ Aucun signal clair"

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, short=12, long=26, signal=9):
    ema_short = series.ewm(span=short).mean()
    ema_long = series.ewm(span=long).mean()
    macd = ema_short - ema_long
    signal_line = macd.ewm(span=signal).mean()
    return macd, signal_line

def compute_bollinger(series, period=20, std=2):
    ma = series.rolling(window=period).mean()
    stddev = series.rolling(window=period).std()
    upper = ma + std * stddev
    lower = ma - std * stddev
    return upper, lower

# --- Récupération des données ---
def get_ohlcv(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=INTERVAL, limit=50)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# --- Bot principal ---
async def bot_main():
    await bot.send_message(chat_id=CHAT_ID, text="🤖 Bot de trading lancé avec succès.")

    while True:
        try:
            for symbol in SYMBOLS:
                df = get_ohlcv(symbol)
                signal = analyse_technique(df)
                await bot.send_message(chat_id=CHAT_ID, text=f"💹 {symbol}\nSignal : {signal}\n🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
            await asyncio.sleep(DELAY)
        except Exception as e:
            await bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Erreur : {e}")
            await asyncio.sleep(30)

# --- Démarrage ---
if __name__ == "__main__":
    asyncio.run(bot_main())