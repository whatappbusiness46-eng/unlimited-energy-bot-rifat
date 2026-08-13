# ============================================================
# VIP SYSTEM
# ============================================================

import logging
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_user,
    get_vip_status,
    get_membership_status,
    get_membership_multiplier,
    get_extra_spins,
    activate_vip,
    remove_vip,
    add_activity,
)


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

DAY_SECONDS = 86400

VIP_LEVELS = {
    1: {
        "daily_multiplier": 1.30,
        "extra_spins": 1,
    },
    2: {
        "daily_multiplier": 1.40,
        "extra_spins": 2,
    },
    3: {
        "daily_multiplier": 1.50,
        "extra_spins": 2,
    },
    4: {
        "daily_multiplier": 1.75,
        "extra_spins": 3,
    },
    5: {
        "daily_multiplier": 2.00,
        "extra_spins": 4,
    },
}


# ============================================================
# TIME HELPER
# ============================================================

def _now():
    return int(time.time())


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=1.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_user(user_id):
    try:
        return get_user(
            user_id,
            create=False,
        )
    except TypeError:
        return get_user(user_id)


def _safe_vip_status(user_id):
    try:
        status = get_vip_status(user_id)
    except Exception:
        logger.exception(
            "Failed to get VIP status | user=%s",
            user_id,
        )
        return {}

    return status if isinstance(status, dict) else {}


# ============================================================
# VALIDATION
# ============================================================

def is_valid_vip_level(level):
    try:
        level = int(level)
    except (TypeError, ValueError):
        return False

    return level in VIP_LEVELS


# ============================================================
# VIP STATUS
# ============================================================

def vip_active(user_id):
    """
    Return True when VIP is currently active.
    """

    status = _safe_vip_status(user_id)

    active = bool(
        status.get(
            "active",
            False,
        )
    )

    expire = _safe_int(
        status.get(
            "expire",
            0,
        ),
        0,
    )

    if expire > 0 and expire <= _now():
        return False

    return active


def vip_level(user_id):
    """
    Return active VIP level.

    Returns 0 when VIP is inactive.
    """

    if not vip_active(user_id):
        return 0

    status = _safe_vip_status(user_id)

    level = _safe_int(
        status.get(
            "level",
            0,
        ),
        0,
    )

    return (
        level
        if is_valid_vip_level(level)
        else 0
    )


def vip_expiry(user_id):
    """
    Return VIP expiry timestamp.
    """

    status = _safe_vip_status(user_id)

    return _safe_int(
        status.get(
            "expire",
            0,
        ),
        0,
    )


# ============================================================
# REMAINING TIME
# ============================================================

def vip_remaining_seconds(user_id):
    expire = vip_expiry(
        user_id
    )

    if expire <= 0:
        return 0

    return max(
        0,
        expire - _now(),
    )


def vip_remaining_days(user_id):
    seconds = vip_remaining_seconds(
        user_id
    )

    if seconds <= 0:
        return 0

    return (
        seconds + DAY_SECONDS - 1
    ) // DAY_SECONDS


# ============================================================
# VIP BENEFITS
# ============================================================

def get_vip_benefits(level):
    """
    Return benefits for VIP level 1-5.
    """

    level = _safe_int(
        level,
        0,
    )

    benefits = VIP_LEVELS.get(
        level
    )

    if not benefits:
        return {
            "daily_multiplier": 1.0,
            "extra_spins": 0,
        }

    return dict(
        benefits
    )


def vip_multiplier(user_id):
    """
    Return the currently effective Premium/VIP
    reward multiplier.
    """

    try:
        return _safe_float(
            get_membership_multiplier(
                user_id
            ),
            1.0,
        )
    except Exception:
        logger.exception(
            "Failed to get membership multiplier | user=%s",
            user_id,
        )
        return 1.0


def vip_extra_spins(user_id):
    """
    Return currently available Premium/VIP extra spins.
    """

    try:
        return max(
            0,
            _safe_int(
                get_extra_spins(
                    user_id
                ),
                0,
            ),
        )
    except Exception:
        logger.exception(
            "Failed to get extra spins | user=%s",
            user_id,
        )
        return 0


# ============================================================
# VIP SUMMARY
# ============================================================

def get_vip_summary(user_id):
    """
    Return complete VIP information.
    """

    status = _safe_vip_status(
        user_id
    )

    level = _safe_int(
        status.get(
            "level",
            0,
        ),
        0,
    )

    expire = _safe_int(
        status.get(
            "expire",
            0,
        ),
        0,
    )

    active = bool(
        status.get(
            "active",
            False,
        )
    )

    if expire > 0 and expire <= _now():
        active = False

    if not is_valid_vip_level(level):
        level = 0

    benefits = get_vip_benefits(
        level
    )

    multiplier = _safe_float(
        status.get(
            "daily_multiplier",
            benefits[
                "daily_multiplier"
            ],
        ),
        benefits[
            "daily_multiplier"
        ],
    )

    extra_spins = max(
        0,
        _safe_int(
            status.get(
                "extra_spins",
                benefits[
                    "extra_spins"
                ],
            ),
            benefits[
                "extra_spins"
            ],
        ),
    )

    if not active:
        level = 0
        multiplier = 1.0
        extra_spins = 0

    return {
        "active": active,
        "level": level,
        "expire": expire,
        "remaining_seconds":
            vip_remaining_seconds(
                user_id
            ),
        "remaining_days":
            vip_remaining_days(
                user_id
            ),
        "daily_multiplier":
            multiplier,
        "extra_spins":
            extra_spins,
    }


# ============================================================
# ACTIVATE / GRANT VIP
# ============================================================

def grant_vip(
    user_id,
    level=1,
    days=30,
):
    """
    Grant or extend VIP.

    This does NOT charge the user's balance.

    Intended for:
        - Admin rewards
        - Promotions
        - Referral milestones
        - Achievement rewards
    """

    level = _safe_int(
        level,
        0,
    )

    days = _safe_int(
        days,
        0,
    )

    if not is_valid_vip_level(
        level
    ):
        return False

    if days <= 0:
        return False

    user = _get_user(
        user_id
    )

    if not user:
        return False

    if (
        user.get("banned", False)
        or user.get("blacklisted", False)
    ):
        return False

    try:
        success = activate_vip(
            user_id,
            level=level,
            days=days,
        )
    except Exception:
        logger.exception(
            "Failed to grant VIP | user=%s | level=%s | days=%s",
            user_id,
            level,
            days,
        )
        return False

    if not success:
        return False

    try:
        add_activity(
            user_id,
            "vip_granted",
            0,
        )
    except Exception:
        logger.exception(
            "Failed to record VIP grant activity | user=%s",
            user_id,
        )

    return True


# ============================================================
# RENEW / UPGRADE VIP
# ============================================================

def extend_vip(
    user_id,
    level=None,
    days=30,
):
    """
    Extend current VIP or change to a specified level.

    No payment is processed here.
    Payment logic should be handled by the
    purchase/payment layer.
    """

    days = _safe_int(
        days,
        0,
    )

    if days <= 0:
        return False

    current_level = vip_level(
        user_id
    )

    if level is None:
        level = (
            current_level
            if current_level > 0
            else 1
        )

    level = _safe_int(
        level,
        0,
    )

    if not is_valid_vip_level(
        level
    ):
        return False

    user = _get_user(
        user_id
    )

    if not user:
        return False

    if (
        user.get("banned", False)
        or user.get("blacklisted", False)
    ):
        return False

    try:
        success = activate_vip(
            user_id,
            level=level,
            days=days,
        )
    except Exception:
        logger.exception(
            "Failed to extend VIP | user=%s | level=%s | days=%s",
            user_id,
            level,
            days,
        )
        return False

    if not success:
        return False

    try:
        add_activity(
            user_id,
            "vip_extended",
            0,
        )
    except Exception:
        logger.exception(
            "Failed to record VIP extension activity | user=%s",
            user_id,
        )

    return True


# ============================================================
# ADMIN REVOKE
# ============================================================

def revoke_vip(user_id):
    """
    Immediately remove VIP.
    """

    user = _get_user(
        user_id
    )

    if not user:
        return False

    try:
        success = remove_vip(
            user_id
        )
    except Exception:
        logger.exception(
            "Failed to revoke VIP | user=%s",
            user_id,
        )
        return False

    if success:
        try:
            add_activity(
                user_id,
                "vip_revoked",
                0,
            )
        except Exception:
            logger.exception(
                "Failed to record VIP revoke activity | user=%s",
                user_id,
            )

    return bool(
        success
    )


# ============================================================
# MEMBERSHIP CHECK
# ============================================================

def membership_summary(user_id):
    """
    Return combined Premium/VIP membership status.
    """

    try:
        status = get_membership_status(
            user_id
        )
    except Exception:
        logger.exception(
            "Failed to get membership status | user=%s",
            user_id,
        )
        status = {}

    if not isinstance(status, dict):
        status = {}

    premium_expire = _safe_int(
        status.get(
            "premium_expire",
            0,
        ),
        0,
    )

    vip_expire = _safe_int(
        status.get(
            "vip_expire",
            0,
        ),
        0,
    )

    premium = bool(
        status.get(
            "premium",
            False,
        )
    )

    vip = bool(
        status.get(
            "vip",
            False,
        )
    )

    if (
        premium_expire > 0
        and premium_expire <= _now()
    ):
        premium = False

    if (
        vip_expire > 0
        and vip_expire <= _now()
    ):
        vip = False

    return {
        "premium": premium,
        "premium_expire":
            premium_expire,
        "vip": vip,
        "vip_level":
            (
                vip_level(user_id)
                if vip
                else 0
            ),
        "vip_expire":
            vip_expire,
        "multiplier":
            vip_multiplier(
                user_id
            ),
        "extra_spins":
            vip_extra_spins(
                user_id
            ),
    }


# ============================================================
# VIP PAGE
# ============================================================

async def vip_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    if not user:
        return

    user_id = user.id

    db_user = _get_user(
        user_id
    )

    if not db_user:
        await query.edit_message_text(
            "⚠️ User account not found.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )
        return

    if (
        db_user.get("banned", False)
        or db_user.get("blacklisted", False)
    ):
        await query.edit_message_text(
            "🚫 Your account is restricted.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )
        return

    summary = get_vip_summary(
        user_id
    )

    if summary["active"]:
        text = (
            "💎 **VIP MEMBERSHIP**\n\n"
            f"🏆 Level: VIP {summary['level']}\n"
            f"⏳ Remaining: "
            f"{summary['remaining_days']} days\n"
            f"⚡ Multiplier: "
            f"{summary['daily_multiplier']}x\n"
            f"🎡 Extra Spins: "
            f"{summary['extra_spins']}\n\n"
            "You can extend your VIP membership."
        )
    else:
        text = (
            "💎 **VIP MEMBERSHIP**\n\n"
            "Choose your VIP level:\n\n"
            "🥉 VIP 1 — 1.30x + 1 Spin\n"
            "🥈 VIP 2 — 1.40x + 2 Spins\n"
            "🥇 VIP 3 — 1.50x + 2 Spins\n"
            "💎 VIP 4 — 1.75x + 3 Spins\n"
            "👑 VIP 5 — 2.00x + 4 Spins\n\n"
            "⚠️ VIP pricing will be configured separately."
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "VIP 1",
                callback_data="vip_level_1",
            ),
            InlineKeyboardButton(
                "VIP 2",
                callback_data="vip_level_2",
            ),
        ],
        [
            InlineKeyboardButton(
                "VIP 3",
                callback_data="vip_level_3",
            ),
            InlineKeyboardButton(
                "VIP 4",
                callback_data="vip_level_4",
            ),
        ],
        [
            InlineKeyboardButton(
                "VIP 5",
                callback_data="vip_level_5",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ],
    ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode="Markdown",
    )


# ============================================================
# VIP LEVEL CALLBACK
# ============================================================

async def vip_level_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    if not user:
        return

    user_id = user.id
    data = str(
        query.data or ""
    )

    try:
        level = int(
            data.rsplit(
                "_",
                1,
            )[1]
        )
    except (
        IndexError,
        TypeError,
        ValueError,
    ):
        await query.edit_message_text(
            "⚠️ Invalid VIP level.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💎 VIP",
                            callback_data="vip",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ],
                ]
            ),
        )
        return

    if not is_valid_vip_level(
        level
    ):
        await query.edit_message_text(
            "⚠️ Invalid VIP level.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💎 VIP",
                            callback_data="vip",
                        )
                    ]
                ]
            ),
        )
        return

    benefits = get_vip_benefits(
        level
    )

    await query.edit_message_text(
        "💎 **VIP LEVEL SELECTED**\n\n"
        f"🏆 Level: VIP {level}\n"
        f"⚡ Multiplier: "
        f"{benefits['daily_multiplier']}x\n"
        f"🎡 Extra Spins: "
        f"{benefits['extra_spins']}\n\n"
        "⚠️ VIP pricing is configured "
        "separately from this membership layer.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ VIP Menu",
                        callback_data="vip",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ],
            ]
        ),
        parse_mode="Markdown",
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "DAY_SECONDS",
    "VIP_LEVELS",
    "is_valid_vip_level",
    "vip_active",
    "vip_level",
    "vip_expiry",
    "vip_remaining_seconds",
    "vip_remaining_days",
    "get_vip_benefits",
    "vip_multiplier",
    "vip_extra_spins",
    "get_vip_summary",
    "grant_vip",
    "extend_vip",
    "revoke_vip",
    "membership_summary",
    "vip_page",
    "vip_level_callback",
    ]
        
