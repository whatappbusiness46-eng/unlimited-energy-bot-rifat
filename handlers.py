from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
)

from database import (
    create_user,
    get_user,
)

from config import GROUPS


# ==========================
# MAIN MENU
# ==========================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Earn",
                callback_data="earn"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Referral",
                callback_data="refer"
            ),
            InlineKeyboardButton(
                "🏆 Rank",
                callback_data="rank"
            )
        ],

        [
            InlineKeyboardButton(
                "💸 Withdraw",
                callback_data="withdraw"
            )
        ],

        [
            InlineKeyboardButton(
                "👑 Premium",
                callback_data="premium"
            )
        ],

        [
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


# ==========================
# FORCE JOIN MENU
# ==========================

def force_join_menu():

    keyboard = []

    for index, group in enumerate(GROUPS, start=1):

        keyboard.append(

            [

                InlineKeyboardButton(

                    f"📢 Join Group {index}",

                    url=f"https://t.me/{group.replace('@','')}"

                )

            ]

        )

    keyboard.append(

        [

            InlineKeyboardButton(

                "✅ Verify Join",

                callback_data="verify_join"

            )

        ]

    )

    return InlineKeyboardMarkup(keyboard)
    
# ==========================
# START COMMAND
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    create_user(user.id)

    # ==========================
    # FORCE JOIN CHECK
    # ==========================

    not_joined = []

    for group in GROUPS:

        try:

            member = await context.bot.get_chat_member(
                group,
                user.id
            )

            if member.status in ["left", "kicked"]:

                not_joined.append(group)

        except:

            not_joined.append(group)

    if not_joined:

        await update.message.reply_text(

            "🔒 Before using this bot,\n"
            "please join all our Official Groups.",

            reply_markup=force_join_menu()

        )

        return

    # ==========================
    # HOME PAGE
    # ==========================

    await update.message.reply_text(

        f"👋 Welcome {user.first_name}!\n\n"

        "🚀 Welcome to Unlimited Energy Bot V2\n\n"

        "💰 Earn Points\n"
        "🎁 Complete Tasks\n"
        "👥 Invite Friends\n"
        "💸 Withdraw Rewards\n\n"

        "👇 Choose an option below.",

        reply_markup=main_menu()

    )
    
