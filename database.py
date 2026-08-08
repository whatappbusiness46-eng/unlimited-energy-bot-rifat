import time
from pymongo import MongoClient

from config import (
    MONGO_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
)


# ==========================
# DATABASE CONNECTION
# ==========================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=30000,
)

db = client[DATABASE_NAME]

users = db[COLLECTION_NAME]


# ==========================
# CREATE USER
# ==========================

def create_user(user_id):

    user = users.find_one({
        "user_id": user_id
    })

    if user:
        return user

    now = int(time.time())

    new_user = {

        # ==================
        # BASIC
        # ==================

        "user_id": user_id,
        "banned": False,

        # ==================
        # WALLET
        # ==================

        "balance": 0,
        "bonus_balance": 0,
        "premium_balance": 0,

        # ==================
        # REFERRAL
        # ==================

        "referrals": 0,
        "referred_by": None,
        "referral_earn": 0,

        # ==================
        # PREMIUM / VIP
        # ==================

        "premium": False,
        "vip": False,
        "premium_expire": 0,

        # ==================
        # LEVEL / RANK
        # ==================

        "xp": 0,
        "level": 1,
        "rank": "🔰 Beginner",

        # ==================
        # DAILY
        # ==================

        "last_daily": 0,
        "daily_streak": 0,

        # ==================
        # EARNING
        # ==================

        "total_earned": 0,
        "offer_completed": 0,
        "shortlink_completed": 0,

        # ==================
        # REWARDS / GAMES
        # ==================

        "group_reward": False,
        "spin_ticket": 0,
        "lucky_box": 0,
        "jackpot_ticket": 0,

        # ==================
        # ENERGY
        # ==================

        "energy": 100,

        # ==================
        # WITHDRAW
        # ==================

        "withdraw_pending": 0,
        "total_withdraw": 0,
        "withdraw_history": [],

        # ==================
        # ACTIVITY
        # ==================

        "activity": [],

        # ==================
        # ACHIEVEMENTS
        # ==================

        "badges": [],

        # ==================
        # COUPONS / GIFTS
        # ==================

        "used_coupons": [],
        "gift_claimed": [],

        # ==================
        # NOTIFICATION
        # ==================

        "notifications": True,

        # ==================
        # SECURITY
        # ==================

        "last_ip": "",
        "device_id": "",

        # ==================
        # LANGUAGE
        # ==================

        "language": "en",

        # ==================
        # TIME
        # ==================

        "last_login": now,
        "created_at": now,
    }

    users.insert_one(new_user)

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
        {"$set": data},
        upsert=True,
    )

    return get_user(user_id)


# ==========================
# ADD BALANCE
# ==========================

def add_balance(user_id, amount):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": amount,
                "total_earned": amount,
            }
        },
        upsert=True,
    )


# ==========================
# REMOVE BALANCE
# ==========================

def remove_balance(user_id, amount):

    user = get_user(user_id)

    balance = user.get("balance", 0)

    if balance <= 0:
        return 0

    amount = min(amount, balance)

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": -amount
            }
        }
    )

    return amount


# ==========================
# ADD XP
# ==========================

def add_xp(user_id, amount):

    user = get_user(user_id)

    current_xp = user.get("xp", 0)

    new_xp = current_xp + amount

    # Simple level system
    new_level = (new_xp // 100) + 1

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "xp": new_xp,
                "level": new_level,
            }
        }
    )

    return new_xp, new_level


# ==========================
# ACTIVITY
# ==========================

def add_activity(user_id, action):

    activity = {
        "action": action,
        "time": int(time.time()),
    }

    users.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "activity": {
                    "$each": [activity],
                    "$slice": -50,
                }
            }
        },
        upsert=True,
    )


# ==========================
# TOTAL USERS
# ==========================

def total_users():

    return users.count_documents({})


# ==========================
# LEADERBOARD
# ==========================

def leaderboard():

    return list(
        users.find().sort(
            "balance",
            -1
        ).limit(10)
    )


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
# CHECK BAN
# ==========================

def is_banned(user_id):

    user = get_user(user_id)

    return user.get(
        "banned",
        False
    )


# ==========================
# DAILY UPDATE
# ==========================

def update_daily(
    user_id,
    streak
):

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "last_daily": int(time.time()),
                "daily_streak": streak,
            }
        }
    )


# ==========================
# REFERRAL UPDATE
# ==========================

def add_referral(
    user_id,
    amount=0
):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "referrals": 1,
                "referral_earn": amount,
                "balance": amount,
                "total_earned": amount,
            }
        }
    )


# ==========================
# WITHDRAW RECORD
# ==========================

def add_withdrawal(
    user_id,
    amount,
    method,
    status="pending"
):

    withdrawal = {
        "amount": amount,
        "method": method,
        "status": status,
        "time": int(time.time()),
    }

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "withdraw_pending": amount
            },
            "$push": {
                "withdraw_history": withdrawal
            }
        }
    )


# ==========================
# DATABASE TEST
# ==========================

def database_test():

    try:
        client.admin.command("ping")
        return True

    except Exception:
        return False
