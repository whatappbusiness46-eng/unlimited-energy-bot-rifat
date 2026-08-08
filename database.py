import time
from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME


# ==========================
# DATABASE CONNECTION
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

def create_user(user_id):
    user = users.find_one({"user_id": user_id})

    if user:
        return user

    now = int(time.time())

    new_user = {
        "user_id": user_id,

        # Wallet
        "balance": 0,
        "bonus_balance": 0,
        "premium_balance": 0,

        # Referral
        "referrals": 0,
        "referred_by": None,
        "referral_earn": 0,

        # Premium / VIP
        "premium": False,
        "vip": False,
        "premium_expire": 0,

        # Account
        "banned": False,

        # Statistics
        "total_earned": 0,
        "total_withdraw": 0,
        "offer_completed": 0,
        "shortlink_completed": 0,

        # Level / Rank
        "xp": 0,
        "level": 1,
        "rank": "🔰 Beginner",

        # Daily
        "last_daily": 0,
        "daily_streak": 0,

        # Rewards
        "group_reward": False,

        # Games
        "spin_ticket": 0,
        "lucky_box": 0,
        "jackpot_ticket": 0,

        # Withdraw
        "withdraw_pending": 0,
        "withdraw_history": [],

        # Activity
        "activity": [],

        # Achievements
        "badges": [],

        # Notifications
        "notifications": True,

        # Security
        "last_ip": "",
        "device_id": "",

        # Coupons
        "used_coupons": [],

        # Gifts
        "gift_claimed": [],

        # Energy
        "energy": 100,

        # Language
        "language": "en",

        # Login / Time
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
        upsert=True
    )


# ==========================
# ADD BALANCE
# ==========================

def add_balance(user_id, amount):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": amount,
                "total_earned": amount
            }
        },
        upsert=True
    )


# ==========================
# REMOVE BALANCE
# ==========================

def remove_balance(user_id, amount):

    user = get_user(user_id)

    balance = user.get("balance", 0)

    if amount <= 0:
        return False

    if balance < amount:
        return False

    users.update_one(
        {"user_id": user_id},
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
        return

    user = get_user(user_id)

    current_xp = user.get("xp", 0)

    new_xp = current_xp + amount

    level = (new_xp // 100) + 1

    if level < 1:
        level = 1

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "xp": new_xp,
                "level": level
            }
        }
    )


# ==========================
# ADD ACTIVITY
# ==========================

def add_activity(user_id, action):

    activity = {
        "action": action,
        "time": int(time.time())
    }

    users.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "activity": {
                    "$each": [activity],
                    "$slice": -50
                }
            }
        },
        upsert=True
    )


# ==========================
# REFERRAL
# ==========================

def set_referrer(user_id, referrer_id):

    if user_id == referrer_id:
        return False

    user = get_user(user_id)

    if user.get("referred_by") is not None:
        return False

    referrer = get_user(referrer_id)

    if not referrer:
        return False

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "referred_by": referrer_id
            }
        }
    )

    return True


def add_referral(referrer_id, reward=0):

    users.update_one(
        {"user_id": referrer_id},
        {
            "$inc": {
                "referrals": 1,
                "referral_earn": reward,
                "balance": reward,
                "total_earned": reward
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
            {
                "banned": {
                    "$ne": True
                }
            },
            {
                "user_id": 1,
                "balance": 1,
                "xp": 1,
                "level": 1,
                "rank": 1,
            }
        )
        .sort("balance", -1)
        .limit(10)
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
# DAILY BONUS
# ==========================

def claim_daily(user_id, reward):

    user = get_user(user_id)

    now = int(time.time())

    last_daily = user.get(
        "last_daily",
        0
    )

    if last_daily:

        if now - last_daily < 86400:
            return False

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "last_daily": now
            },
            "$inc": {
                "daily_streak": 1,
                "balance": reward,
                "bonus_balance": reward,
                "total_earned": reward
            }
        }
    )

    add_activity(
        user_id,
        f"🎁 Daily bonus +{reward} Points"
    )

    return True


# ==========================
# WITHDRAW RECORD
# ==========================

def add_withdrawal(
    user_id,
    amount,
    method,
    account
):

    withdrawal = {
        "amount": amount,
        "method": method,
        "account": account,
        "status": "pending",
        "time": int(time.time())
    }

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": -amount,
                "withdraw_pending": amount
            },
            "$push": {
                "withdraw_history": withdrawal
            }
        }
    )

    return withdrawal


# ==========================
# COMPLETE WITHDRAWAL
# ==========================

def complete_withdrawal(
    user_id,
    amount
):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "withdraw_pending": -amount,
                "total_withdraw": amount
            }
        }
    )


# ==========================
# INDEXES
# ==========================

try:

    users.create_index(
        "user_id",
        unique=True
    )

    users.create_index(
        [
            ("balance", -1)
        ]
    )

except Exception:
    pass
    
