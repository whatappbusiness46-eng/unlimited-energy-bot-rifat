# ============================================================
# VIP SYSTEM
# ============================================================

import time

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

    status = get_vip_status(user_id)

    return bool(
        status.get(
            "active",
            False,
        )
    )


def vip_level(user_id):
    """
    Return active VIP level.

    Returns 0 when VIP is inactive.
    """

    status = get_vip_status(user_id)

    if not status.get(
        "active",
        False,
    ):
        return 0

    try:
        return int(
            status.get(
                "level",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


def vip_expiry(user_id):
    """
    Return VIP expiry timestamp.
    """

    status = get_vip_status(user_id)

    try:
        return int(
            status.get(
                "expire",
                0,
            )
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


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

    try:
        level = int(level)
    except (
        TypeError,
        ValueError,
    ):
        return {
            "daily_multiplier": 1.0,
            "extra_spins": 0,
        }

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
        return float(
            get_membership_multiplier(
                user_id
            )
        )
    except Exception:
        return 1.0


def vip_extra_spins(user_id):
    """
    Return currently available Premium/VIP extra spins.
    """

    try:
        return int(
            get_extra_spins(
                user_id
            )
        )
    except Exception:
        return 0


# ============================================================
# VIP SUMMARY
# ============================================================

def get_vip_summary(user_id):
    """
    Return complete VIP information.
    """

    status = get_vip_status(
        user_id
    )

    level = int(
        status.get(
            "level",
            0,
        )
        or 0
    )

    active = bool(
        status.get(
            "active",
            False,
        )
    )

    expire = int(
        status.get(
            "expire",
            0,
        )
        or 0
    )

    benefits = get_vip_benefits(
        level
    )

    return {
        "active": active,
        "level": (
            level
            if active
            else 0
        ),
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
            (
                float(
                    status.get(
                        "daily_multiplier",
                        benefits[
                            "daily_multiplier"
                        ],
                    )
                )
                if active
                else 1.0
            ),
        "extra_spins":
            (
                int(
                    status.get(
                        "extra_spins",
                        benefits[
                            "extra_spins"
                        ],
                    )
                )
                if active
                else 0
            ),
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

    try:
        level = int(level)
        days = int(days)
    except (
        TypeError,
        ValueError,
    ):
        return False

    if not is_valid_vip_level(
        level
    ):
        return False

    if days <= 0:
        return False

    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return False

    success = activate_vip(
        user_id,
        level=level,
        days=days,
    )

    if not success:
        return False

    try:
        add_activity(
            user_id,
            "vip_granted",
            0,
        )
    except Exception:
        pass

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

    try:
        days = int(days)
    except (
        TypeError,
        ValueError,
    ):
        return False

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

    try:
        level = int(level)
    except (
        TypeError,
        ValueError,
    ):
        return False

    if not is_valid_vip_level(
        level
    ):
        return False

    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return False

    success = activate_vip(
        user_id,
        level=level,
        days=days,
    )

    if not success:
        return False

    try:
        add_activity(
            user_id,
            "vip_extended",
            0,
        )
    except Exception:
        pass

    return True


# ============================================================
# ADMIN REVOKE
# ============================================================

def revoke_vip(user_id):
    """
    Immediately remove VIP.
    """

    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return False

    success = remove_vip(
        user_id
    )

    if success:
        try:
            add_activity(
                user_id,
                "vip_revoked",
                0,
            )
        except Exception:
            pass

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

    status = get_membership_status(
        user_id
    )

    return {
        "premium":
            bool(
                status.get(
                    "premium",
                    False,
                )
            ),
        "premium_expire":
            int(
                status.get(
                    "premium_expire",
                    0,
                )
                or 0
            ),
        "vip":
            bool(
                status.get(
                    "vip",
                    False,
                )
            ),
        "vip_level":
            int(
                status.get(
                    "vip_level",
                    0,
                )
                or 0
            ),
        "vip_expire":
            int(
                status.get(
                    "vip_expire",
                    0,
                )
                or 0
            ),
        "multiplier":
            vip_multiplier(
                user_id
            ),
        "extra_spins":
            vip_extra_spins(
                user_id
            ),
    }
    async def vip_page(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    summary = get_vip_summary(user_id)

    if summary["active"]:
        text = (
            "💎 **VIP MEMBERSHIP**\n\n"
            f"🏆 Level: VIP {summary['level']}\n"
            f"⏳ Remaining: {summary['remaining_days']} days\n"
            f"⚡ Multiplier: {summary['daily_multiplier']}x\n"
            f"🎡 Extra Spins: {summary['extra_spins']}\n\n"
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
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode="Markdown",
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
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
                ]
