from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes
from config import GROUPS
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

    # ==========================
    # BAN CHECK
    # ==========================

    if user.get("banned", False):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    data = query.data

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

        keyboard = [
            [
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(

            "💰 YOUR WALLET\n\n"

            f"💰 Earn Balance: {balance} Points\n"
            f"🎁 Bonus Balance: {bonus} Points\n"
            f"💎 Premium Balance: "
            f"{premium_balance} Points\n\n"

            f"💵 Total Balance: {total} Points",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )

        )

        return

    # ==========================
    # PROFILE
    # ==========================

    if data == "profile":

        user_id = user.get("user_id")

        balance = user.get(
            "balance",
            0
        )

        bonus = user.get(
            "bonus_balance",
            0
        )

        referrals = user.get(
            "referrals",
            0
        )

        xp = user.get(
            "xp",
            0
        )

        level = user.get(
            "level",
            1
        )

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
                    "🏆 Rank",
                    callback_data="rank"
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

        return

    # ==========================
    # RANK
    # ==========================

    if data == "rank":

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
                            "👤 Profile",
                            callback_data="profile"
                        )
                    ],
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
    # HELP
    # ==========================

    if data == "help":

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

        return

    # ==========================
    # UNKNOWN CALLBACK
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


# ==========================
# VERIFY JOIN CALLBACK
# ==========================

async def verify_join_callback(
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

    not_joined = []

    for group in GROUPS:

        try:

            member = await context.bot.get_chat_member(
                group,
                user_id
            )

            if member.status in [
                "left",
                "kicked"
            ]:

                not_joined.append(group)

        except Exception:

            not_joined.append(group)

    if not_joined:

        await query.edit_message_text(

            "❌ You haven't joined all "
            "required groups yet.\n\n"

            "Please join all groups and "
            "press ✅ Verify again.",

            reply_markup=force_join_menu()

        )

        return

    await query.edit_message_text(

        "✅ Verification successful!\n\n"

        "🎉 You can now use "
        "Unlimited Energy Bot.",

        reply_markup=main_menu()

        )
    
