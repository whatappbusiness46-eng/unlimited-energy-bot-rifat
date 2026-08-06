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
    
