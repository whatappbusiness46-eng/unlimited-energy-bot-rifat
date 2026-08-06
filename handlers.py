from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import GROUPS
from database import get_user


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
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Referral",
                callback_data="refer"
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
                "📊 Profile",
                callback_data="profile"
            )
        ],

        [
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help"
            )
        ],

    ]

    return InlineKeyboardMarkup(keyboard)


# ==========================
# FORCE JOIN BUTTON
# ==========================

def force_join_menu():

    keyboard = []

    for i, group in enumerate(GROUPS, start=1):

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"📢 Join Group {i}",
                    url=f"https://t.me/{group.replace('@','')}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "✅ I've Joined",
                callback_data="verify_join"
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)
  
