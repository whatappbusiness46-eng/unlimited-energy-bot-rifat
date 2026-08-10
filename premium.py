import time

from config import (
    PREMIUM_PRICE,
    PREMIUM_DAYS,
)
from database import (
    get_user,
    remove_balance,
    update_user,
    add_activity,
)


def premium_active(user_id):
    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return False

    if not user.get("premium", False):
        return False

    expires = int(
        user.get(
            "premium_expire",
            0,
        )
    )

    if expires <= int(time.time()):
        update_user(
            user_id,
            {
                "premium": False,
                "premium_expire": 0,
            },
        )
        return False

    return True


def premium_expiry(user_id):
    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return 0

    return int(
        user.get(
            "premium_expire",
            0,
        )
    )


def purchase_premium(user_id):
    if premium_active(user_id):
        return False, "Premium is already active."

    removed = remove_balance(
        user_id,
        PREMIUM_PRICE,
    )

    if not removed:
        return False, "Insufficient balance."

    now = int(time.time())
    expires = (
        now
        + PREMIUM_DAYS * 86400
    )

    update_user(
        user_id,
        {
            "premium": True,
            "premium_expire": expires,
        },
    )

    add_activity(
        user_id,
        "premium_purchase",
        PREMIUM_PRICE,
    )

    return True, {
        "price": PREMIUM_PRICE,
        "days": PREMIUM_DAYS,
        "expires": expires,
    }


def premium_status(user_id):
    active = premium_active(user_id)

    if not active:
        return {
            "active": False,
            "expires": 0,
        }

    return {
        "active": True,
        "expires": premium_expiry(user_id),
  }
  
