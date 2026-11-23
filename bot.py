import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.request import HTTPXRequest

logging.basicConfig(level=logging.INFO)

waiting_user: int | None = None
active_pairs: dict[int, int] = {}

async def baglan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user
    user_id = update.effective_user.id

    if user_id in active_pairs:
        await update.message.reply_text("Zaten bir bağlantınız var. Çıkmak için /ayril yazın.")
        return

    if waiting_user is None:
        waiting_user = user_id
        await update.message.reply_text("Bağlantı için eş bekleniyor...")
    elif waiting_user == user_id:
        await update.message.reply_text("Zaten bekleme sırasındasınız.")
    else:
        partner_id = waiting_user
        waiting_user = None
        active_pairs[user_id] = partner_id
        active_pairs[partner_id] = user_id
        await context.bot.send_message(partner_id, "Bağlantı kuruldu! Mesaj gönderebilirsiniz.")
        await update.message.reply_text("Bağlantı kuruldu! Mesaj gönderebilirsiniz.")

async def ayril(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user
    user_id = update.effective_user.id
    if waiting_user == user_id:
        waiting_user = None
        await update.message.reply_text("Bekleme sırasından çıkıldı.")
        return

    partner_id = active_pairs.pop(user_id, None)
    if partner_id:
        active_pairs.pop(partner_id, None)
        await context.bot.send_message(partner_id, "Karşı taraf bağlantıyı sonlandırdı.")
        await update.message.reply_text("Bağlantı sonlandırıldı.")
    else:
        await update.message.reply_text("Aktif bir bağlantınız yok.")

async def mesaj_ilet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = active_pairs.get(user_id)
    if partner_id and update.message.text:
        await context.bot.send_message(partner_id, update.message.text)

def main():
    token = os.environ["BOT_TOKEN"]
    request = HTTPXRequest(
        connection_pool_size=20,
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
    )
    app = (
        ApplicationBuilder()
        .token(token)
        .request(request)
        .get_updates_request(request)
        .build()
    )
    app.add_handler(CommandHandler("baglan", baglan))
    app.add_handler(CommandHandler("ayril", ayril))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj_ilet))
    print("Bot baslatildi!")
    app.run_polling(poll_interval=2.0, timeout=30)

if __name__ == "__main__":
    main()
