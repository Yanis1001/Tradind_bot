
import ccxt
import pandas as pd
import time
import requests

# Identifiants OKX
api_key = '8683629e-376a-4f8f-8aa3-b1393f184d70'
api_secret = 'CBD17C85B60BCFA86B9E2F9E9F6E5789'
api_passphrase = 'Trading_Bot2026'

# Telegram
telegram_token = '6669494469:AAHpPWqE-vJMNkMZPeoU_4Y32bqOJHtNODc'
chat_id = '6669494469'

exchange = ccxt.okx({
    'apiKey': api_key,
    'secret': api_secret,
    'password': api_passphrase,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

symbols = {
    'BTC': 'BTC/USDT:USDT',
    'GOLD': 'XAU/USDT:USDT'
}

def send_telegram(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{telegram_token}/sendMessage",
            data={"chat_id": chat_id, "text": message}
        )
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def fetch_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def add_indicators(df):
    df['SMA7'] = df['close'].rolling(7).mean()
    df['SMA25'] = df['close'].rolling(25).mean()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA12'] = df['close'].ewm(span=12).mean()
    df['EMA26'] = df['close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    return df

def analyze(df):
    last = df.iloc[-1]
    if last['SMA7'] > last['SMA25'] and last['MACD'] > last['Signal'] and last['RSI'] < 70:
        return 'buy'
    elif last['SMA7'] < last['SMA25'] and last['MACD'] < last['Signal'] and last['RSI'] > 30:
        return 'sell'
    else:
        return 'hold'

def place_order(symbol_name, symbol):
    try:
        df = fetch_data(symbol)
        df = add_indicators(df)
        signal = analyze(df)
        balance = exchange.fetch_balance()
        price = exchange.fetch_ticker(symbol)['last']
        usdt = balance['total']['USDT']
        amount = round(usdt * 0.3 / price, 3)

        if signal == 'buy':
            exchange.create_market_buy_order(symbol, amount)
            send_telegram(f"✅ [{symbol_name}] Achat de {amount} à {price} USD")
        elif signal == 'sell':
            exchange.create_market_sell_order(symbol, amount)
            send_telegram(f"🔻 [{symbol_name}] Vente de {amount} à {price} USD")
        else:
            send_telegram(f"🤔 [{symbol_name}] Pas d’opportunité")
    except Exception as e:
        send_telegram(f"❌ [{symbol_name}] Erreur : {e}")

send_telegram("🚀 Bot de trading automatique lancé.")
while True:
    for name, symbol in symbols.items():
        place_order(name, symbol)
    time.sleep(300)
