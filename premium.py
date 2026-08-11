# ============================================================
# PREMIUM SYSTEM
# ============================================================

import time

from config import (
    PREMIUM_PRICE,
    PREMIUM_DAYS,
)

from database import (
    get_user,
    remove_balance,
    activate_premium,
    remove_premium,
    get_premium_status,
    get_membership_status,
    get_membership_multiplier,
    add_activity,
    record_transaction,
)


# ============================================================
# HELPERS
# ============================================================

DAY_SECONDS = 86400


def _now():
    return int(time.time())


# ============================================================
# PREMIUM STATUS
# ============================================================

def premium_active(user_id):
    """
    Return True when Premium is currently active.

    Expired Premium is automatically treated as inactive.
    """

    status = get_premium_status(user_id)

    return bool(
        status.get("active", False)
    )


def premium_expiry(user_id):
    """
    Return Premium expiry timestamp.
    """

    status = get_premium_status(user_id)

    return int(
        status.get(
            "expire",
            0,
        )
        or 0
    )


def premium_status(user_id):
    """
    Return complete Premium status.
    """

    status = get_premium_status(
        user_id
    )

    expire = int(
        status.get(
            "expire",
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

    return {
        "active": active,
        "expires": expire,
        "expire": expire,
    }


# ============================================================
# PREMIUM REMAINING TIME
# ============================================================

def premium_remaining_seconds(user_id):
    """
    Return remaining Premium time in seconds.
    """

    expire = premium_expiry(
        user_id
    )

    if expire <= 0:
        return 0

    return max(
        0,
        expire - _now(),
    )


def premium_remaining_days(user_id):
    """
    Return remaining Premium time in whole days.
    """

    seconds = premium_remaining_seconds(
        user_id
    )

    if seconds <= 0:
        return 0

    return (
        seconds + DAY_SECONDS - 1
    ) // DAY_SECONDS


# ============================================================
# PREMIUM PURCHASE
# ============================================================

def purchase_premium(user_id):
    """
    Purchase Premium using the user's main balance.

    Returns:
        (False, message)
        or
        (True, details)
    """

    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return (
            False,
            "User not found.",
        )

    if premium_active(
        user_id
    ):
        return (
            False,
            "Premium is already active.",
        )

    try:
        price = int(
            PREMIUM_PRICE
        )
    except (
        TypeError,
        ValueError,
    ):
        return (
            False,
            "Premium price is not configured correctly.",
        )

    if price <= 0:
        return (
            False,
            "Premium price is invalid.",
        )

    # --------------------------------------------------------
    # REMOVE BALANCE
    # --------------------------------------------------------

    removed = remove_balance(
        user_id,
        price,
    )

    if not removed:
        return (
            False,
            "Insufficient balance.",
        )

    # --------------------------------------------------------
    # ACTIVATE PREMIUM
    # --------------------------------------------------------

    try:
        activated = activate_premium(
            user_id,
            days=PREMIUM_DAYS,
        )
    except Exception:

        # Best-effort refund if activation fails.
        try:
            from database import add_balance

            add_balance(
                user_id,
                price,
            )
        except Exception:
            pass

        return (
            False,
            "Premium activation failed. Your balance was not charged.",
        )

    if not activated:

        try:
            from database import add_balance

            add_balance(
                user_id,
                price,
            )
        except Exception:
            pass

        return (
            False,
            "Premium activation failed. Your balance was not charged.",
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    expires = premium_expiry(
        user_id
    )

    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    try:
        add_activity(
            user_id,
            "premium_purchase",
            price,
        )
    except Exception:
        pass

    return (
        True,
        {
            "price": price,
            "days": int(
                PREMIUM_DAYS
            ),
            "expires": expires,
            "remaining_days":
                premium_remaining_days(
                    user_id
                ),
        },
    )


# ============================================================
# PREMIUM RENEWAL
# ============================================================

def renew_premium(user_id):
    """
    Renew Premium by purchasing another Premium period.

    If Premium is already active, this function extends the
    existing expiry through database.activate_premium().
    """

    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return (
            False,
            "User not found.",
        )

    try:
        price = int(
            PREMIUM_PRICE
        )
    except (
        TypeError,
        ValueError,
    ):
        return (
            False,
            "Premium price is invalid.",
        )

    removed = remove_balance(
        user_id,
        price,
    )

    if not removed:
        return (
            False,
            "Insufficient balance.",
        )

    try:
        activated = activate_premium(
            user_id,
            days=PREMIUM_DAYS,
        )
    except Exception:

        try:
            from database import add_balance

            add_balance(
                user_id,
                price,
            )
        except Exception:
            pass

        return (
            False,
            "Premium renewal failed.",
        )

    if not activated:

        try:
            from database import add_balance

            add_balance(
                user_id,
                price,
            )
        except Exception:
            pass

        return (
            False,
            "Premium renewal failed.",
        )

    expires = premium_expiry(
        user_id
    )

    try:
        add_activity(
            user_id,
            "premium_renewal",
            price,
        )
    except Exception:
        pass

    return (
        True,
        {
            "price": price,
            "days": int(
                PREMIUM_DAYS
            ),
            "expires": expires,
            "remaining_days":
                premium_remaining_days(
                    user_id
                ),
        },
    )


# ============================================================
# ADMIN GRANT
# ============================================================

def grant_premium(
    user_id,
    days=30,
):
    """
    Grant or extend Premium without charging balance.

    Intended for admin/reward systems.
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

    return bool(
        activate_premium(
            user_id,
            days=days,
        )
    )


# ============================================================
# ADMIN REVOKE
# ============================================================

def revoke_premium(user_id):
    """
    Immediately remove Premium.
    """

    return bool(
        remove_premium(
            user_id
        )
    )


# ============================================================
# PREMIUM BENEFITS
# ============================================================

def premium_daily_multiplier(user_id):
    """
    Return Premium/VIP-aware daily multiplier.

    Database membership logic remains the source of truth.
    """

    try:
        return float(
            get_membership_multiplier(
                user_id
            )
        )
    except Exception:
        return 1.0


def premium_is_benefit_active(user_id):
    """
    Convenience helper for reward systems.
    """

    return premium_active(
        user_id
    )


# ============================================================
# PREMIUM SUMMARY
# ============================================================

def get_premium_summary(user_id):
    """
    Return a user-friendly Premium summary.
    """

    status = premium_status(
        user_id
    )

    return {
        "active":
            status["active"],

        "expires":
            status["expires"],

        "remaining_seconds":
            premium_remaining_seconds(
                user_id
            ),

        "remaining_days":
            premium_remaining_days(
                user_id
            ),

        "price":
            int(PREMIUM_PRICE),

        "days":
            int(PREMIUM_DAYS),

        "daily_multiplier":
            premium_daily_multiplier(
                user_id
            ),
    }


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "premium_active",
    "premium_expiry",
    "premium_status",
    "premium_remaining_seconds",
    "premium_remaining_days",
    "purchase_premium",
    "renew_premium",
    "grant_premium",
    "revoke_premium",
    "premium_daily_multiplier",
    "premium_is_benefit_active",
    "get_premium_summary",
]
