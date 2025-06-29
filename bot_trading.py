import pandas as pd
import ccxt
import ta
import time
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

# === CONFIGURATION ===
TELEGRAM_TOKEN = "8032643176:AAG3yOXI0czomp4T0GSyapXANU33E88Be8Q"
CHAT_ID = 6669494469
symbols = ['BTC/USDT', 'XAU/USDT']
timeframe = '5m'
limit = 100

exchange = ccxt.okx({'enableRateLimit': True})  # Pas besoin d'API pour les données publiques

TP_SL_MARGIN = {
    'BTC/USDT': {'tp': 50, 'sl': 30},
    'XAU/USDT': {'tp': 0.3, 'sl': 0.2}
}

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
                f"🧠 (RSI < 65, MACD croisé, proche BB inférieure)\n"
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
                f"🧠 (RSI > 40, MACD croisé, proche BB supérieure)\n"
                f"🕐 Analyse en M5"
            )

        return signal
    except Exception as e:
        return f"❌ Erreur analyse {symbol} : <code>{str(e)}</code>"

def send_all_signals(update=None, context=None):
    for sym in symbols:
        signal = get_signal(sym)
        if signal:
            context.bot.send_message(chat_id=CHAT_ID, text=signal, parse_mode=ParseMode.HTML)

def start(update, context):
    context.bot.send_message(chat_id=CHAT_ID, text="🤖 <b>Bot lancé avec succès !</b>\nEnvoyez /signal pour une analyse manuelle.", parse_mode=ParseMode.HTML)

def signal(update, context):
    send_all_signals(update, context)

def periodic_signals(context):
    send_all_signals(context=context)

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("signal", signal))

    job_queue = updater.job_queue
    job_queue.run_repeating(periodic_signals, interval=300, first=5)  # toutes les 5 min

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()