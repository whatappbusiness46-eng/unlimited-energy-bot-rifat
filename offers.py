# ============================================================
# OFFERS SYSTEM
# ============================================================

import logging
import time
from typing import Any, Dict, Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_user,
    update_user,
    add_balance,
    add_activity,
)

logger = logging.getLogger(__name__)

OFFERS: Dict[str, Dict[str, Any]] = {}


def _now():
    return int(time.time())


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_user(user_id):
    try:
        return get_user(user_id, create=False)
    except TypeError:
        return get_user(user_id)


def _blocked(user):
    return bool(
        not user
        or user.get("banned", False)
        or user.get("blacklisted", False)
    )


def register_offer(
    offer_id: str,
    title: str,
    description: str = "",
    reward: int = 0,
    url: Optional[str] = None,
    enabled: bool = True,
    cooldown: int = 86400,
):
    offer_id = str(offer_id).strip()
    reward = _safe_int(reward, 0)

    if not offer_id or reward < 0:
        return False

    OFFERS[offer_id] = {
        "id": offer_id,
        "title": str(title or offer_id),
        "description": str(description or ""),
        "reward": reward,
        "url": url,
        "enabled": bool(enabled),
        "cooldown": max(0, _safe_int(cooldown, 86400)),
    }
    return True


def get_offer(offer_id):
    offer = OFFERS.get(str(offer_id))
    return dict(offer) if offer else None


def get_offers(include_disabled=False):
    return [
        dict(offer)
        for offer in OFFERS.values()
        if include_disabled or offer.get("enabled", True)
    ]


def _claims(user):
    value = user.get("offer_claims", {})
    return dict(value) if isinstance(value, dict) else {}


def offer_available(user_id, offer_id):
    user = _get_user(user_id)
    offer = get_offer(offer_id)

    if _blocked(user) or not offer or not offer["enabled"]:
        return False

    claims = _claims(user)
    last = _safe_int(claims.get(str(offer_id), 0), 0)

    if last <= 0:
        return True

    cooldown = max(
        0,
        _safe_int(offer.get("cooldown", 86400), 86400),
    )
    return _now() - last >= cooldown


def claim_offer(user_id, offer_id):
    user = _get_user(user_id)
    offer = get_offer(offer_id)

    if _blocked(user) or not offer or not offer["enabled"]:
        return False

    if not offer_available(user_id, offer_id):
        return False

    claims = _claims(user)
    claims[str(offer_id)] = _now()

    try:
        result = update_user(
            user_id,
            {"offer_claims": claims},
        )
        if result is False:
            return False

        reward = _safe_int(offer["reward"], 0)

        if reward > 0:
            result = add_balance(
                user_id,
                reward,
            )
            if result is False:
                return False

            try:
                add_activity(
                    user_id,
                    f"🎁 Offer claimed: {offer['title']}",
                    reward,
                )
            except Exception:
                logger.exception(
                    "Offer activity failed | user=%s offer=%s",
                    user_id,
                    offer_id,
                )

        return True

    except Exception:
        logger.exception(
            "Offer claim failed | user=%s offer=%s",
            user_id,
            offer_id,
        )
        return False


def offers_menu(user_id=None):
    keyboard = []

    for offer in get_offers():
        available = (
            True
            if user_id is None
            else offer_available(user_id, offer["id"])
        )

        label = (
            f"🎁 {offer['title']}"
            if available
            else f"⏳ {offer['title']}"
        )

        keyboard.append([
            InlineKeyboardButton(
                label,
                callback_data=f"offer_{offer['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton("🏠 Home", callback_data="home")
    ])
    return InlineKeyboardMarkup(keyboard)


async def offers_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return

    db_user = _get_user(user.id)

    if _blocked(db_user):
        await message.reply_text("🚫 Your account is restricted.")
        return

    offers = get_offers()

    if not offers:
        text = "🎁 **OFFERS**\n\nNo offers are available right now."
    else:
        lines = ["🎁 **OFFERS**", ""]
        for offer in offers:
            status = (
                "🟢 Available"
                if offer_available(user.id, offer["id"])
                else "🔴 Cooldown"
            )
            lines.append(
                f"{status} — {offer['title']} (+{offer['reward']})"
            )
        text = "\n".join(lines)

    await message.reply_text(
        text,
        reply_markup=offers_menu(user.id),
        parse_mode="Markdown",
    )


async def offer_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    data = str(query.data or "")
    if not data.startswith("offer_"):
        return

    offer_id = data[6:]
    offer = get_offer(offer_id)

    if not offer:
        await query.edit_message_text(
            "⚠️ Offer not found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Offers", callback_data="offers")],
                [InlineKeyboardButton("🏠 Home", callback_data="home")],
            ]),
        )
        return

    keyboard = []

    if offer.get("url"):
        keyboard.append([
            InlineKeyboardButton(
                "🚀 Open Offer",
                url=offer["url"],
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "✅ Claim Reward",
            callback_data=f"offer_claim_{offer_id}",
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            "🏠 Home",
            callback_data="home",
        )
    ])

    await query.edit_message_text(
        "🎁 **OFFER**\n\n"
        f"📌 {offer['title']}\n\n"
        f"{offer['description']}\n\n"
        f"💰 Reward: {offer['reward']} Points",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def offer_claim_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    data = str(query.data or "")
    if not data.startswith("offer_claim_"):
        return

    offer_id = data[len("offer_claim_"):]
    offer = get_offer(offer_id)

    if not offer:
        await query.edit_message_text("⚠️ Offer not found.")
        return

    success = claim_offer(
        query.from_user.id,
        offer_id,
    )

    if success:
        text = (
            "🎉 **OFFER CLAIMED!**\n\n"
            f"🎁 {offer['title']}\n"
            f"💰 +{offer['reward']} Points"
        )
    else:
        text = (
            "❌ **OFFER UNAVAILABLE**\n\n"
            "The offer is already claimed or on cooldown."
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Offers", callback_data="offers")],
            [InlineKeyboardButton("🏠 Home", callback_data="home")],
        ]),
        parse_mode="Markdown",
    )


HANDLER_FUNCTIONS = {
    "offers": offers_page,
    "offer_callback": offer_callback,
    "offer_claim_callback": offer_claim_callback,
}

__all__ = [
    "OFFERS",
    "register_offer",
    "get_offer",
    "get_offers",
    "offer_available",
    "claim_offer",
    "offers_menu",
    "offers_page",
    "offer_callback",
    "offer_claim_callback",
    "HANDLER_FUNCTIONS",
  ]
                  
