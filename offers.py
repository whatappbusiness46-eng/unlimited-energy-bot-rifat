# ============================================================
# OFFERS SYSTEM
# CPAGrip based
# ============================================================

import logging
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database import (
    get_user,
)

from cpagrip import (
    build_cpa_link,
    CPA_REWARD_POINTS,
    CPA_DAILY_LIMIT,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# EXISTING ADVERTSREWARD
# ------------------------------------------------------------

ADVERTSREWARD_WIDGET_ID = os.getenv(
    "ADVERTSREWARD_WIDGET_ID",
    "rsDaKm6BnQ9WP9OnfxLmKn2hrSmX3SBA",
)

ADVERTSREWARD_BASE_URL = (
    "https://advertsreward.com/w/"
)


def advertsreward_url(user_id: int) -> str:

    return (
        f"{ADVERTSREWARD_BASE_URL}"
        f"{ADVERTSREWARD_WIDGET_ID}"
        f"?uid={int(user_id)}"
    )


def advertsreward_button(user_id: int):

    return InlineKeyboardButton(
        "🎯 AdvertsReward Offers",
        url=advertsreward_url(user_id),
    )


# ------------------------------------------------------------
# USER
# ------------------------------------------------------------

def _get_user(user_id):

    try:
        return get_user(
            user_id,
            create=False,
        )

    except TypeError:

        return get_user(
            user_id
        )


def _blocked(user):

    return bool(
        not user
        or user.get(
            "banned",
            False,
        )
        or user.get(
            "blacklisted",
            False,
        )
    )


# ------------------------------------------------------------
# CPA LINK
# ------------------------------------------------------------

def cpagrip_url(
    user_id: int,
) -> str:

    return build_cpa_link(
        user_id
    )


def cpagrip_button(
    user_id: int,
):

    return InlineKeyboardButton(
        "🎁 CPA Offers",
        url=cpagrip_url(
            user_id
        ),
    )


# ------------------------------------------------------------
# CPA STATUS
# ------------------------------------------------------------

def _today_count(user_id: int):

    from database import (
        cpa_conversions
    )

    from datetime import datetime, timezone

    today = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d"
    )

    return cpa_conversions.count_documents(
        {
            "user_id": int(user_id),
            "day": today,
            "status": "credited",
        }
    )


# ------------------------------------------------------------
# OFFERS MENU
# ------------------------------------------------------------

def offers_menu(
    user_id=None,
):

    keyboard = []

    if user_id is not None:

        keyboard.append(
            [
                cpagrip_button(
                    user_id
                )
            ]
        )

        keyboard.append(
            [
                advertsreward_button(
                    user_id
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# ------------------------------------------------------------
# OFFERS PAGE
# ------------------------------------------------------------

async def offers_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not message:
        return

    db_user = _get_user(
        user.id
    )

    if _blocked(db_user):

        await message.reply_text(
            "🚫 Your account is restricted."
        )

        return

    completed_today = _today_count(
        user.id
    )

    remaining = max(
        0,
        CPA_DAILY_LIMIT
        - completed_today,
    )

    text = (
        "🎁 **EARN POINTS**\n\n"
        "Complete available CPA offers "
        "to earn points.\n\n"
        f"💰 Reward per valid conversion: "
        f"+{CPA_REWARD_POINTS} points\n"
        f"📊 Daily limit: "
        f"{CPA_DAILY_LIMIT}\n"
        f"✅ Completed today: "
        f"{completed_today}\n"
        f"🎯 Remaining today: "
        f"{remaining}\n\n"
        "⚠️ Points are credited only after "
        "CPAGrip confirms a valid conversion."
    )

    await message.reply_text(
        text,
        reply_markup=offers_menu(
            user.id
        ),
        parse_mode="Markdown",
    )


# ------------------------------------------------------------
# CALLBACK COMPATIBILITY
# ------------------------------------------------------------

async def offer_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    await query.edit_message_text(
        "🎁 **CPA OFFERS**\n\n"
        "Open the CPA Offers button below "
        "to see the offers available for "
        "your country/device.\n\n"
        f"💰 Reward: +{CPA_REWARD_POINTS} "
        "points per valid conversion.\n"
        f"📊 Daily limit: {CPA_DAILY_LIMIT}.",
        reply_markup=offers_menu(
            query.from_user.id
        ),
        parse_mode="Markdown",
    )


# ------------------------------------------------------------
# OLD CLAIM CALLBACK DISABLED
# ------------------------------------------------------------

async def offer_claim_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer(
        "Reward is credited automatically after CPAGrip confirms the offer.",
        show_alert=True,
    )


# ------------------------------------------------------------
# HANDLERS
# ------------------------------------------------------------

HANDLER_FUNCTIONS = {
    "offers": offers_page,
    "offer_callback": offer_callback,
    "offer_claim_callback":
        offer_claim_callback,
}


__all__ = [
    "offers_page",
    "offers_menu",
    "offer_callback",
    "offer_claim_callback",
    "cpagrip_url",
    "cpagrip_button",
    "advertsreward_url",
    "advertsreward_button",
    "HANDLER_FUNCTIONS",
    ]
