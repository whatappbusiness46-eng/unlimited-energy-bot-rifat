from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database import get_user

from handlers import (
    main_menu,
    force_join_menu,
)


# ==========================
# CALLBACK ROUTER
# ==========================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user.get("banned", False):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    data = query.data

    # ==========================
    # MAIN MENU
    # ==========================

    if data == "home":

        await query.edit_message_text(
            "🏠 MAIN MENU\n\n"
            "👇 Choose an option:",
            reply_markup=main_menu()
        )

        return

    # ==========================
    # BALANCE
    # ==========================

    if data == "balance":

        balance = user.get("balance", 0)
        bonus = user.get("bonus_balance", 0)
        premium_balance = user.get(
            "premium_balance",
            0
        )

        total = (
            balance
            + bonus
            + premium_balance
        )

        await query.edit_message_text(

            "💰 YOUR WALLET\n\n"

            f"💰 Earn Balance: {balance}\n"
            f"🎁 Bonus Balance: {bonus}\n"
            f"💎 Premium Balance: "
            f"{premium_balance}\n\n"

            f"💵 Total: {total} Points",

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home"
                        )
                    ]
                ]
            )

        )

        return
      
