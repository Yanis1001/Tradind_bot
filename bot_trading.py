import pandas as pd
import ccxt
import ta
import time
import threading
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# === CONFIGURATION ===
TELEGRAM_TOKEN = "8032643176:AAG3yOXI0czomp4T0GSyapXANU33E88Be8Q"
CHAT_ID = 6669494469
bot = Bot(token=TELEGRAM_TOKEN)

symbols = ['BTC/USDT', 'XAU/USDT']
timeframe = '5m'
limit = 100

exchange = ccxt.okx({'enableRateLimit': True})  # Données publiques

TP_SL_MARGIN = {
    'BTC/USDT': {'tp': 50, 'sl': 30},
    'XAU/USDT': {'tp': 0.3, 'sl': 0.2}
}

def send_telegram_message(text):
    bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")

def get_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()

        last = df.iloc[-1]
        price = last['close']
        signal = None

        if last['macd'] > last['macd_signal'] and last['rsi'] < 65 and price < last['bb_lower']:
            entry_min = round(price * 0.998, 2)
            entry_max = round(price * 1.002, 2)
            tp = round(price + TP_SL_MARGIN[symbol]['tp'], 2)
            sl = round(price - TP_SL_MARGIN[symbol]['sl'], 2)
            signal = (
                f"📢 <b>Signal ACHAT</b> 🟢\n\n"
                f"📊 <b>Actif :</b> <code>{symbol}</code>\n"
                f"💰 <b>Entrée :</b> entre <code>{entry_min}</code> et <code>{entry_max}</code>\n"
                f"🎯 <b>TP :</b> <code>{tp}</code>\n"
                f"🛑 <b>SL :</b> <code>{sl}</code>\n"
                f"🧠 <i>(RSI < 65, MACD croisé, proche BB inférieure)</i>\n"
                f"🕐 Analyse en M5"
            )

        elif last['macd'] < last['macd_signal'] and last['rsi'] > 40 and price > last['bb_upper']:
            entry_min = round(price * 0.998, 2)
            entry_max = round(price * 1.002, 2)
            tp = round(price - TP_SL_MARGIN[symbol]['tp'], 2)
            sl = round(price + TP_SL_MARGIN[symbol]['sl'], 2)
            signal = (
                f"📢 <b>Signal VENTE</b> 🔴\n\n"
                f"📊 <b>Actif :</b> <code>{symbol}</code>\n"
                f"💰 <b>Entrée :</b> entre <code>{entry_min}</code> et <code>{entry_max}</code>\n"
                f"🎯 <b>TP :</b> <code>{tp}</code>\n"
                f"🛑 <b>SL :</b> <code>{sl}</code>\n"
                f"🧠 <i>(RSI > 40, MACD croisé, proche BB supérieure)</i>\n"
                f"🕐 Analyse en M5"
            )

        return signal
    except Exception as e:
        return f"❌ <b>Erreur analyse {symbol} :</b> <code>{str(e)}</code>"

# === COMMANDE /signal ===
def signal_command(update: Update, context: CallbackContext):
    update.message.reply_text("🔍 Analyse en cours...")
    for sym in symbols:
        signal = get_signal(sym)
        if signal:
            context.bot.send_message(chat_id=CHAT_ID, text=signal, parse_mode="HTML")
        else:
            context.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Aucun signal clair pour {sym}", parse_mode="HTML")

# === LANCEMENT AUTOMATIQUE TOUTES LES 5 MINUTES ===
def auto_loop():
    send_telegram_message("🤖 <b>Bot lancé</b> avec succès.\n📊 Analyse toutes les 5 min\n⌛️ M5 / RSI + MACD + BB\n")
    while True:
        for sym in symbols:
            signal = get_signal(sym)
            if signal:
                send_telegram_message(signal)
        time.sleep(120)

# === MAIN ===
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("signal", signal_command))
    threading.Thread(target=auto_loop).start()
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()