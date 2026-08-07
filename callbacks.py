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
      
# ==========================
# PROFILE
# ==========================

async def show_profile(
    query,
    user
):

    user_id = user.get("user_id")

    balance = user.get("balance", 0)
    bonus = user.get("bonus_balance", 0)
    referrals = user.get("referrals", 0)

    xp = user.get("xp", 0)
    level = user.get("level", 1)
    rank = user.get(
        "rank",
        "🔰 Beginner"
    )

    premium = user.get(
        "premium",
        False
    )

    vip = user.get(
        "vip",
        False
    )

    premium_status = (
        "✅ Active"
        if premium
        else "❌ Inactive"
    )

    vip_status = (
        "✅ Active"
        if vip
        else "❌ Inactive"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        ]

    ]

    await query.edit_message_text(

        "👤 YOUR PROFILE\n\n"

        f"🆔 ID: {user_id}\n\n"

        f"💰 Balance: {balance}\n"
        f"🎁 Bonus: {bonus}\n"
        f"👥 Referrals: {referrals}\n\n"

        f"⭐ XP: {xp}\n"
        f"🏆 Level: {level}\n"
        f"🎖 Rank: {rank}\n\n"

        f"👑 Premium: {premium_status}\n"
        f"💎 VIP: {vip_status}",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )

    )


# ==========================
# PROFILE CALLBACK
# ==========================

async def profile_callback(
    query,
    user
):

    await show_profile(
        query,
        user
    )


# ==========================
# RANK
# ==========================

async def rank_callback(
    query,
    user
):

    rank = user.get(
        "rank",
        "🔰 Beginner"
    )

    level = user.get(
        "level",
        1
    )

    xp = user.get(
        "xp",
        0
    )

    await query.edit_message_text(

        "🏆 YOUR RANK\n\n"

        f"🎖 Rank: {rank}\n"
        f"🏆 Level: {level}\n"
        f"⭐ XP: {xp}\n\n"

        "Keep earning to reach "
        "the next rank! 🚀",

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


# ==========================
# HELP
# ==========================

async def help_callback(
    query
):

    await query.edit_message_text(

        "❓ HELP CENTER\n\n"

        "💰 Earn — Complete available tasks\n"
        "💳 Balance — Check your wallet\n"
        "👤 Profile — View your account\n"
        "👥 Referral — Invite friends\n"
        "💸 Withdraw — Request a withdrawal\n"
        "👑 Premium — View Premium plans\n\n"

        "If you need assistance, "
        "contact the Admin.",

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
    # ==========================
# CALLBACK ROUTER — PART 3
# ==========================

async def route_callback(
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
    # PROFILE
    # ==========================

    if data == "profile":

        await show_profile(
            query,
            user
        )

        return

    # ==========================
    # RANK
    # ==========================

    if data == "rank":

        await rank_callback(
            query,
            user
        )

        return

    # ==========================
    # HELP
    # ==========================

    if data == "help":

        await help_callback(
            query
        )

        return

    # ==========================
    # HOME
    # ==========================

    if data == "home":

        await query.edit_message_text(

            "🏠 MAIN MENU\n\n"
            "👇 Choose an option:",

            reply_markup=main_menu()

        )

        return

    # ==========================
    # UNKNOWN BUTTON
    # ==========================

    await query.edit_message_text(

        "⚠️ This option is not available yet.\n\n"
        "🚀 More features are coming soon!",

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
    
