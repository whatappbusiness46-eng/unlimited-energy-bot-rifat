# ============================================================
# SHORTLINKS / USEFUL LINKS - POLICY-SAFE VERSION
# ============================================================
# ShrtFly links are NOT reward tasks.
# Users receive NO points/cash/gifts for opening a shortlink.
# Existing public function names are kept for compatibility with
# admin.py/callbacks.py, but completion never credits balance.
# ============================================================

import logging
import time
from typing import Any, Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_user, db

logger = logging.getLogger(__name__)

SHORTLINKS: Dict[str, Dict[str, Any]] = {}
SHORTLINK_COLLECTION = db["shortlinks"]
TOKENS: Dict[str, Dict[str, Any]] = {}

DEFAULT_TOKEN_TTL = 3600
DEFAULT_COOLDOWN = 86400


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


def register_shortlink(
    shortlink_id: str,
    name: str,
    base_url: str,
    reward: int = 0,
    enabled: bool = True,
    cooldown: int = DEFAULT_COOLDOWN,
    token_ttl: int = DEFAULT_TOKEN_TTL,
):
    """Register a useful link. reward is intentionally forced to 0."""
    shortlink_id = str(shortlink_id or "").strip()
    base_url = str(base_url or "").strip()

    if not shortlink_id or not base_url:
        return False

    item = {
        "id": shortlink_id,
        "name": str(name or shortlink_id),
        "base_url": base_url,
        # Kept for compatibility with the existing admin schema.
        # Never used to reward a click.
        "reward": 0,
        "enabled": bool(enabled),
        "cooldown": max(0, _safe_int(cooldown, DEFAULT_COOLDOWN)),
        "token_ttl": max(60, _safe_int(token_ttl, DEFAULT_TOKEN_TTL)),
        "updated_at": _now(),
    }

    try:
        SHORTLINK_COLLECTION.create_index(
            "id", unique=True, name="shortlink_id_unique"
        )
        SHORTLINK_COLLECTION.update_one(
            {"id": shortlink_id},
            {"$set": item},
            upsert=True,
        )
    except Exception:
        logger.exception("Could not persist useful link | id=%s", shortlink_id)
        return False

    SHORTLINKS[shortlink_id] = dict(item)
    return True


def get_shortlink(shortlink_id):
    key = str(shortlink_id)
    item = SHORTLINKS.get(key)
    if item:
        return dict(item)

    try:
        item = SHORTLINK_COLLECTION.find_one({"id": key}, {"_id": 0})
    except Exception:
        item = None

    if item:
        SHORTLINKS[key] = dict(item)
        return dict(item)
    return None


def get_shortlinks(include_disabled=False):
    try:
        query = {} if include_disabled else {"enabled": True}
        items = [
            dict(x)
            for x in SHORTLINK_COLLECTION.find(query, {"_id": 0}).sort("id", 1)
        ]
        for item in items:
            SHORTLINKS[item["id"]] = dict(item)
        return items
    except Exception:
        return [
            dict(item)
            for item in SHORTLINKS.values()
            if include_disabled or item.get("enabled", True)
        ]


def set_shortlink_enabled(shortlink_id, enabled):
    key = str(shortlink_id)
    try:
        result = SHORTLINK_COLLECTION.update_one(
            {"id": key},
            {"$set": {"enabled": bool(enabled), "updated_at": _now()}},
        )
        if result.matched_count <= 0:
            return False
    except Exception:
        logger.exception("Could not update useful link | id=%s", key)
        return False

    if key in SHORTLINKS:
        SHORTLINKS[key]["enabled"] = bool(enabled)
    return True


def delete_shortlink(shortlink_id):
    key = str(shortlink_id)
    try:
        result = SHORTLINK_COLLECTION.delete_one({"id": key})
    except Exception:
        logger.exception("Could not delete useful link | id=%s", key)
        return False

    SHORTLINKS.pop(key, None)
    return result.deleted_count > 0


def shortlink_available(user_id, shortlink_id):
    user = _get_user(user_id)
    item = get_shortlink(shortlink_id)
    return bool(item and item.get("enabled", True) and not _blocked(user))


def create_shortlink_token(user_id, shortlink_id):
    """Compatibility helper; no reward verification token is needed."""
    return None


def validate_shortlink_token(token, user_id=None, shortlink_id=None):
    # Completion verification is intentionally disabled.
    return False


def build_shortlink_url(shortlink_id, token=None):
    item = get_shortlink(shortlink_id)
    if not item:
        return None
    return str(item.get("base_url", "")).strip() or None


def complete_shortlink(user_id, shortlink_id, token=None):
    """Compatibility helper; deliberately never credits balance."""
    return False


def shortlinks_menu(user_id=None):
    keyboard = []

    for item in get_shortlinks():
        name = str(item.get("name", item.get("id", "Link")))[:45]
        keyboard.append([
            InlineKeyboardButton(
                f"🔗 {name}",
                callback_data=f"shortlink_{item['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton("🏠 Home", callback_data="home")
    ])
    return InlineKeyboardMarkup(keyboard)


async def shortlinks_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return

    db_user = _get_user(user.id)
    if _blocked(db_user):
        await message.reply_text("🚫 Your account is restricted.")
        return

    items = get_shortlinks()
    if not items:
        text = "🔗 **USEFUL LINKS**\n\nNo useful links are available right now."
    else:
        lines = [
            "🔗 **USEFUL LINKS**",
            "",
            "Explore the resources below:",
            "",
        ]
        for item in items:
            lines.append(f"• {item.get('name', item['id'])}")
        text = "\n".join(lines)

    await message.reply_text(
        text,
        reply_markup=shortlinks_menu(user.id),
        parse_mode="Markdown",
    )


async def shortlink_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = str(query.data or "")
    if not data.startswith("shortlink_"):
        return

    shortlink_id = data[len("shortlink_"):]
    item = get_shortlink(shortlink_id)

    if not item or not item.get("enabled", True):
        await query.edit_message_text(
            "⚠️ This link is currently unavailable.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Useful Links", callback_data="shortlinks")],
                [InlineKeyboardButton("🏠 Home", callback_data="home")],
            ]),
        )
        return

    url = build_shortlink_url(shortlink_id)
    if not url:
        await query.edit_message_text(
            "⚠️ Link is not configured correctly.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Useful Links", callback_data="shortlinks")],
            ]),
        )
        return

    await query.edit_message_text(
        "🔗 **USEFUL LINK**\n\n"
        f"📌 {item.get('name', shortlink_id)}\n\n"
        "This link may contain an advertising step before the destination opens.\n\n"
        "Open it only if you want to view the linked content.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Open Link", url=url)],
            [InlineKeyboardButton("⬅️ Useful Links", callback_data="shortlinks")],
            [InlineKeyboardButton("🏠 Home", callback_data="home")],
        ]),
        parse_mode="Markdown",
    )


async def shortlink_verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy callback kept so existing callbacks.py routing does not break."""
    query = update.callback_query
    if not query:
        return
    await query.answer(
        "Useful links do not give rewards for clicks.",
        show_alert=True,
    )


HANDLER_FUNCTIONS = {
    "shortlinks": shortlinks_page,
    "shortlink_callback": shortlink_callback,
    "shortlink_verify_callback": shortlink_verify_callback,
}


__all__ = [
    "SHORTLINKS",
    "TOKENS",
    "register_shortlink",
    "get_shortlink",
    "get_shortlinks",
    "shortlink_available",
    "create_shortlink_token",
    "validate_shortlink_token",
    "build_shortlink_url",
    "complete_shortlink",
    "shortlinks_menu",
    "shortlinks_page",
    "shortlink_callback",
    "shortlink_verify_callback",
    "HANDLER_FUNCTIONS",
]
