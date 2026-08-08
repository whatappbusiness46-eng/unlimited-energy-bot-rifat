import time
import logging

from pymongo import MongoClient
from config import (
    MONGO_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
)

# ==========================
# LOGGING
# ==========================

logger = logging.getLogger(__name__)


# ==========================
# MONGODB CONNECTION
# ==========================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=20000,
    socketTimeoutMS=20000,
)

db = client[DATABASE_NAME]

users = db[COLLECTION_NAME]


# ==========================
# CREATE USER
# ==========================

def create_user(user_id, referred_by=None):

    user = users.find_one({
        "user_id": user_id
    })

    if user:
        return user

    now = int(time.time())

    new_user = {

        # ==========================
        # BASIC
        # ==========================

        "user_id": user_id,
        "created_at": now,
        "last_login": now,

        # ==========================
        # WALLET
        # ==========================

        "balance": 0,
        "bonus_balance": 0,
        "premium_balance": 0,

        "total_earned": 0,
        "total_withdraw": 0,

        # ==========================
        # REFERRAL
        # ==========================

        "referrals": 0,
        "referred_by": referred_by,
        "referral_earn": 0,

        # ==========================
        # PREMIUM / VIP
        # ==========================

        "premium": False,
        "vip": False,
        "premium_expire": 0,

        # ==========================
        # USER STATUS
        # ==========================

        "banned": False,

        # ==========================
        # XP / LEVEL / RANK
        # ==========================

        "xp": 0,
        "level": 1,
        "rank": "🔰 Beginner",

        # ==========================
        # DAILY
        # ==========================

        "last_daily": 0,
        "daily_streak": 0,

        # ==========================
        # GROUP REWARD
        # ==========================

        "group_reward": False,

        # ==========================
        # SPIN
        # ==========================

        "spin_ticket": 0,
        "spin_used": 0,

        # ==========================
        # LUCKY BOX
        # ==========================

        "lucky_box": 0,
        "lucky_box_opened": 0,

        # ==========================
        # SCRATCH CARD
        # ==========================

        "scratch_card": 0,
        "scratch_used": 0,

        # ==========================
        # JACKPOT
        # ==========================

        "jackpot_ticket": 0,

        # ==========================
        # ENERGY
        # ==========================

        "energy": 100,
        "max_energy": 100,
        "last_energy_update": now,

        # ==========================
        # EARN STATISTICS
        # ==========================

        "offer_completed": 0,
        "shortlink_completed": 0,
        "task_completed": 0,

        # ==========================
        # WITHDRAW
        # ==========================

        "withdraw_pending": 0,
        "withdraw_history": [],

        # ==========================
        # ACTIVITY
        # ==========================

        "activity": [],

        # ==========================
        # ACHIEVEMENTS
        # ==========================

        "badges": [],

        # ==========================
        # NOTIFICATIONS
        # ==========================

        "notifications": True,

        # ==========================
        # SECURITY
        # ==========================

        "last_ip": "",
        "device_id": "",

        # ==========================
        # COUPON
        # ==========================

        "used_coupons": [],

        # ==========================
        # GIFTS
        # ==========================

        "gift_claimed": [],

        # ==========================
        # LANGUAGE
        # ==========================

        "language": "en",

    }

    users.insert_one(new_user)

    logger.info(
        "New user created | user_id=%s",
        user_id
    )

    return new_user


# ==========================
# GET USER
# ==========================

def get_user(user_id):

    user = users.find_one({
        "user_id": user_id
    })

    if not user:
        user = create_user(user_id)

    return user


# ==========================
# UPDATE USER
# ==========================

def update_user(user_id, data):

    users.update_one(
        {"user_id": user_id},
        {"$set": data}
    )


# ==========================
# ADD BALANCE
# ==========================

def add_balance(user_id, amount):

    if amount <= 0:
        return False

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": amount,
                "total_earned": amount,
            }
        }
    )

    return True


# ==========================
# ADD BONUS BALANCE
# ==========================

def add_bonus(user_id, amount):

    if amount <= 0:
        return False

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "bonus_balance": amount,
            }
        }
    )

    return True


# ==========================
# ADD PREMIUM BALANCE
# ==========================

def add_premium_balance(user_id, amount):

    if amount <= 0:
        return False

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "premium_balance": amount,
            }
        }
    )

    return True


# ==========================
# REMOVE BALANCE
# ==========================

def remove_balance(user_id, amount):

    if amount <= 0:
        return False

    user = get_user(user_id)

    balance = user.get(
        "balance",
        0
    )

    if balance < amount:
        return False

    users.update_one(
        {
            "user_id": user_id,
            "balance": {
                "$gte": amount
            }
        },
        {
            "$inc": {
                "balance": -amount
            }
        }
    )

    return True


# ==========================
# ADD XP
# ==========================

def add_xp(user_id, amount):

    if amount <= 0:
        return False

    user = get_user(user_id)

    current_xp = user.get(
        "xp",
        0
    )

    current_level = user.get(
        "level",
        1
    )

    new_xp = current_xp + amount

    new_level = (
        new_xp // 100
    ) + 1

    if new_level < 1:
        new_level = 1

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "xp": new_xp,
                "level": new_level,
            }
        }
    )

    return True


# ==========================
# ADD ACTIVITY
# ==========================

def add_activity(
    user_id,
    action,
    extra=None
):

    item = {
        "action": action,
        "time": int(time.time()),
    }

    if extra:
        item["extra"] = extra

    users.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "activity": {
                    "$each": [item],
                    "$slice": -50,
                }
            }
        }
    )


# ==========================
# ADD REFERRAL
# ==========================

def add_referral(
    referrer_id,
    reward
):

    users.update_one(
        {"user_id": referrer_id},
        {
            "$inc": {
                "referrals": 1,
                "referral_earn": reward,
                "balance": reward,
                "total_earned": reward,
            }
        }
    )


# ==========================
# SET REFERRER
# ==========================

def set_referrer(
    user_id,
    referrer_id
):

    users.update_one(
        {
            "user_id": user_id,
            "referred_by": None,
        },
        {
            "$set": {
                "referred_by": referrer_id
            }
        }
    )


# ==========================
# ADD SPIN TICKET
# ==========================

def add_spin_ticket(
    user_id,
    amount=1
):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "spin_ticket": amount
            }
        }
    )


# ==========================
# USE SPIN TICKET
# ==========================

def use_spin_ticket(user_id):

    result = users.update_one(
        {
            "user_id": user_id,
            "spin_ticket": {
                "$gt": 0
            }
        },
        {
            "$inc": {
                "spin_ticket": -1,
                "spin_used": 1,
            }
        }
    )

    return result.modified_count > 0


# ==========================
# ADD LUCKY BOX
# ==========================

def add_lucky_box(
    user_id,
    amount=1
):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "lucky_box": amount
            }
        }
    )


# ==========================
# USE LUCKY BOX
# ==========================

def use_lucky_box(user_id):

    result = users.update_one(
        {
            "user_id": user_id,
            "lucky_box": {
                "$gt": 0
            }
        },
        {
            "$inc": {
                "lucky_box": -1,
                "lucky_box_opened": 1,
            }
        }
    )

    return result.modified_count > 0


# ==========================
# ADD SCRATCH CARD
# ==========================

def add_scratch_card(
    user_id,
    amount=1
):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "scratch_card": amount
            }
        }
    )


# ==========================
# USE SCRATCH CARD
# ==========================

def use_scratch_card(user_id):

    result = users.update_one(
        {
            "user_id": user_id,
            "scratch_card": {
                "$gt": 0
            }
        },
        {
            "$inc": {
                "scratch_card": -1,
                "scratch_used": 1,
            }
        }
    )

    return result.modified_count > 0


# ==========================
# ADD JACKPOT TICKET
# ==========================

def add_jackpot_ticket(
    user_id,
    amount=1
):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "jackpot_ticket": amount
            }
        }
    )


# ==========================
# TOTAL USERS
# ==========================

def total_users():

    return users.count_documents({})


# ==========================
# TOP USERS
# ==========================

def leaderboard():

    return list(
        users.find(
            {},
            {
                "user_id": 1,
                "balance": 1,
                "xp": 1,
                "level": 1,
                "rank": 1,
            }
        )
        .sort(
            "balance",
            -1
        )
        .limit(10)
    )


# ==========================
# GET USER COUNT BY FIELD
# ==========================

def count_users(field, value):

    return users.count_documents({
        field: value
    })


# ==========================
# BAN USER
# ==========================

def ban_user(user_id):

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "banned": True
            }
        }
    )


# ==========================
# UNBAN USER
# ==========================

def unban_user(user_id):

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "banned": False
            }
        }
    )


# ==========================
# ADD BADGE
# ==========================

def add_badge(
    user_id,
    badge
):

    users.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {
                "badges": badge
            }
        }
    )


# ==========================
# MARK COUPON USED
# ==========================

def mark_coupon_used(
    user_id,
    coupon
):

    users.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {
                "used_coupons": coupon
            }
        }
    )


# ==========================
# MARK GIFT CLAIMED
# ==========================

def mark_gift_claimed(
    user_id,
    gift_id
):

    users.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {
                "gift_claimed": gift_id
            }
        }
    )
    
