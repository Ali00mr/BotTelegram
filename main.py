import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from analysis import generate_signals

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TOP_N = int(os.getenv("TOP_N", 100))
NEW_LISTING_DAYS = int(os.getenv("NEW_LISTING_DAYS", 60))
SCHEDULE_HOURS = int(os.getenv("SCHEDULE_EVERY_HOURS", 4))

bot = Bot(token=BOT_TOKEN)

# ارسال سیگنال‌ها
async def send_signals_manual(chat_id=CHANNEL_ID):
    signals = await generate_signals(top_n=TOP_N, new_listing_days=NEW_LISTING_DAYS)
    if not signals:
        await bot.send_message(chat_id=chat_id, text="⏳ هنوز سیگنال مطمئنی پیدا نشد.")
        return

    for s in signals:
        text = (
            f"📊 سیگنال {s['symbol']}\n"
            f"💵 قیمت فعلی: {s['price']}\n"
            f"✅ خرید روی: {s['buy_price']}\n"
            f"🎯 هدف: {s['sell_target']}\n"
            f"🛑 حد ضرر: {s['stop_loss']}\n"
            f"📈 احتمال سود: {s['confidence']}%\n"
            f"ℹ️ {s['note']}"
        )
        await bot.send_message(chat_id=chat_id, text=text)
        await asyncio.sleep(1)  # جلوگیری از بلاک شدن تلگرام

# هندلر دستور /signal
async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_signals_manual(chat_id=update.effective_chat.id)

# برنامه زمان‌بندی‌شده
async def scheduler():
    while True:
        await send_signals_manual(CHANNEL_ID)
        await asyncio.sleep(SCHEDULE_HOURS * 3600)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("signal", signal_command))

    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())

    app.run_polling()

if __name__ == "__main__":
    main()