import time

from config import (
    VIP_PRICE,
    VIP_DAYS,
)
from database import (
    get_user,
    remove_balance,
    update_user,
    add_activity,
)


VIP_LEVELS = {
    1: {
        "name": "VIP 1",
        "multiplier": 1.10,
    },
    2: {
        "name": "VIP 2",
        "multiplier": 1.20,
    },
    3: {
        "name": "VIP 3",
        "multiplier": 1.30,
    },
    4: {
        "name": "VIP 4",
        "multiplier": 1.40,
    },
    5: {
        "name": "VIP 5",
        "multiplier": 1.50,
    },
}


def vip_active(user_id):
    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return False

    if not user.get("vip", False):
        return False

    expires = int(
        user.get(
            "vip_expire",
            0,
        )
    )

    if expires <= int(time.time()):
        update_user(
            user_id,
            {
                "vip": False,
                "vip_expire": 0,
            },
        )
        return False

    return True


def vip_expiry(user_id):
    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        return 0

    return int(
        user.get(
            "vip_expire",
            0,
        )
    )


def purchase_vip(
    user_id,
    level=1,
):
    level = int(level)

    if level not in VIP_LEVELS:
        return False, "Invalid VIP level."

    if vip_active(user_id):
        return False, "VIP is already active."

    removed = remove_balance(
        user_id,
        VIP_PRICE,
    )

    if not removed:
        return False, "Insufficient balance."

    now = int(time.time())
    expires = (
        now
        + VIP_DAYS * 86400
    )

    update_user(
        user_id,
        {
            "vip": True,
            "vip_expire": expires,
            "vip_level": level,
        },
    )

    add_activity(
        user_id,
        f"vip_{level}_purchase",
        VIP_PRICE,
    )

    return True, {
        "level": level,
        "name": VIP_LEVELS[level]["name"],
        "price": VIP_PRICE,
        "days": VIP_DAYS,
        "expires": expires,
        "multiplier": VIP_LEVELS[level]["multiplier"],
    }


def vip_status(user_id):
    if not vip_active(user_id):
        return {
            "active": False,
            "level": 0,
            "expires": 0,
        }

    user = get_user(
        user_id,
        create=False,
    )

    return {
        "active": True,
        "level": int(
            user.get(
                "vip_level",
                1,
            )
        ),
        "expires": vip_expiry(user_id),
    }
