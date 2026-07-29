from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "8605792055:AAEZft5Cpj4qlzeGDSdU54kxp6aWuKkfgzg"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Earn", callback_data="earn")],
        [InlineKeyboardButton("💳 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to Unlimited Energy Bot!\n\nChoose an option:",
        reply_markup=reply_markup,
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "earn":
        text = (
            "💰 Earn Rewards\n\n"
            "✅ Join our Telegram Channel\n"
            "✅ Invite Friends\n"
            "✅ Complete Daily Tasks\n\n"
            "🎁 More tasks coming soon!"
        )

    elif query.data == "balance":
        text = (
            "💳 Balance\n\n"
            "💰 Your Balance: 0 Points"
        )

    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        user_id = query.from_user.id

        text = (
            "👥 Referral Program\n\n"
            f"🔗 Your Link:\nhttps://t.me/{bot_username}?start={user_id}\n\n"
            "🎁 Invite friends and earn rewards!"
        )

    elif query.data == "withdraw":
        text = (
            "💸 Withdraw\n\n"
            "Minimum Withdraw: 100 Points\n"
            "Send your payment details to the admin."
        )

    elif query.data == "help":
        text = (
            "❓ Help\n\n"
            "Use the buttons below to navigate.\n"
            "If you need help, contact the admin."
        )

    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💰 Earn", callback_data="earn")],
        [InlineKeyboardButton("💳 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ]

    await query.edit_message_text(
        "👋 Welcome to Unlimited Energy Bot!\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "back":
        await back(update, context)
    else:
        await button(update, context)


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callbacks))

print("✅ Bot is running...")
app.run_polling()
