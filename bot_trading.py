import pandas as pd
import ccxt
import ta
import time
import asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CONFIGURATION ===
TELEGRAM_TOKEN = "8032643176:AAG3yOXI0czomp4T0GSyapXANU33E88Be8Q"
CHAT_ID = 6669494469
symbols = ['BTC/USDT', 'XAU/USDT']
timeframe = '5m'
limit = 100

# TP / SL réalistes (atteignables en 15-30 min)
TP_SL_MARGIN = {
    'BTC/USDT': {'tp': 30, 'sl': 20},
    'XAU/USDT': {'tp': 0.25, 'sl': 0.15}
}

exchange = ccxt.okx({'enableRateLimit': True})
bot = Bot(token=TELEGRAM_TOKEN)

# === Fonction d'envoi Telegram ===
async def send_telegram_message(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
        print("[✅] Message Telegram envoyé.")
    except Exception as e:
        print(f"[❌] Erreur envoi Telegram : {e}")

# === Analyse d’un actif ===
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

        if last['macd'] > last['macd_signal'] and last['rsi'] < 65 and price <= last['bb_lower']:
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
                f"🕐 <i>Analyse en M5</i>"
            )

        elif last['macd'] < last['macd_signal'] and last['rsi'] > 35 and price >= last['bb_upper']:
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
                f"🧠 <i>(RSI > 35, MACD croisé, proche BB supérieure)</i>\n"
                f"🕐 <i>Analyse en M5</i>"
            )

        return signal
    except Exception as e:
        return f"❌ <b>Erreur analyse {symbol} :</b> <code>{str(e)}</code>"

# === Commande Telegram : /signal ===
async def manual_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_telegram_message("🔍 Analyse manuelle demandée...")
    for sym in symbols:
        signal = get_signal(sym)
        if signal:
            await send_telegram_message(signal)
        else:
            await send_telegram_message(f"❌ Aucun signal clair pour <code>{sym}</code>.")

# === Boucle principale ===
async def main_loop():
    await send_telegram_message("🤖 <b>Bot de signaux lancé !</b>\n📍 RSI, MACD, BBands\n🕐 M5 - Analyse toutes les 5 minutes")
    while True:
        for sym in symbols:
            signal = get_signal(sym)
            if signal:
                await send_telegram_message(signal)
            else:
                print(f"[INFO] Aucun signal pour {sym}")
        await asyncio.sleep(300)

# === Lancement complet ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("signal", manual_signal))

    async def run_all():
        task1 = asyncio.create_task(app.run_polling())
        task2 = asyncio.create_task(main_loop())
        await asyncio.gather(task1, task2)

    asyncio.run(run_all())