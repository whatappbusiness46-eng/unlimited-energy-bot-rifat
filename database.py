import time
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from config import (
    MONGO_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
)


# ==========================
# MONGODB CONNECTION
# ==========================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=20000,
    retryWrites=True,
)

db = client[DATABASE_NAME]
users = db[COLLECTION_NAME]


# ==========================
# DATABASE CHECK
# ==========================

def database_ping():

    try:
        client.admin.command("ping")
        return True

    except PyMongoError:
        return False


# ==========================
# INDEX
# ==========================

try:

    users.create_index(
        [("user_id", ASCENDING)],
        unique=True
    )

    users.create_index(
        [("balance", DESCENDING)]
    )

except PyMongoError:
    pass


# ==========================
# DEFAULT USER DATA
# ==========================

def default_user(user_id):

    now = int(time.time())

    return {

        # ======================
        # BASIC
        # ======================

        "user_id": user_id,

        # ======================
        # WALLET
        # ======================

        "balance": 0,
        "bonus_balance": 0,
        "premium_balance": 0,

        # ======================
        # REFERRAL
        # ======================

        "referrals": 0,
        "referred_by": None,
        "referral_earn": 0,

        # ======================
        # PREMIUM / VIP
        # ======================

        "premium": False,
        "premium_expire": 0,
        "vip": False,

        # ======================
        # STATUS
        # ======================

        "banned": False,

        # ======================
        # STATISTICS
        # ======================

        "total_earned": 0,
        "total_withdraw": 0,
        "offer_completed": 0,
        "shortlink_completed": 0,

        # ======================
        # LEVEL SYSTEM
        # ======================

        "xp": 0,
        "level": 1,
        "rank": "🔰 Beginner",

        # ======================
        # DAILY
        # ======================

        "last_daily": 0,
        "daily_streak": 0,

        # ======================
        # GROUP REWARD
        # ======================

        "group_reward": False,

        # ======================
        # WHEEL / SPIN
        # ======================

        "spin_ticket": 0,
        "spin_count": 0,
        "last_spin": 0,

        # ======================
        # LUCKY BOX
        # ======================

        "lucky_box": 0,
        "luckybox_opened": 0,

        # ======================
        # SCRATCH CARD
        # ======================

        "scratch_ticket": 0,
        "scratch_played": 0,

        # ======================
        # JACKPOT
        # ======================

        "jackpot_ticket": 0,
        "jackpot_played": 0,

        # ======================
        # ENERGY
        # ======================

        "energy": 100,
        "max_energy": 100,

        # ======================
        # WITHDRAW
        # ======================

        "withdraw_pending": 0,
        "withdraw_history": [],

        # ======================
        # ACTIVITY
        # ======================

        "activity": [],

        # ======================
        # TRANSACTIONS
        # ======================

        "transactions": [],

        # ======================
        # ACHIEVEMENTS
        # ======================

        "badges": [],

        # ======================
        # COUPONS
        # ======================

        "used_coupons": [],

        # ======================
        # GIFTS
        # ======================

        "gift_claimed": [],

        # ======================
        # NOTIFICATIONS
        # ======================

        "notifications": True,

        # ======================
        # SECURITY
        # ======================

        "last_ip": "",
        "device_id": "",

        # ======================
        # LOGIN
        # ======================

        "last_login": now,
        "login_count": 1,

        # ======================
        # SETTINGS
        # ======================

        "language": "en",

        # ======================
        # TIME
        # ======================

        "created_at": now,
        "updated_at": now,
    }


# ==========================
# CREATE USER
# ==========================

def create_user(user_id):

    user = users.find_one(
        {"user_id": user_id}
    )

    if user:
        return user

    new_user = default_user(user_id)

    try:

        users.insert_one(new_user)

    except PyMongoError:

        # Another request may have
        # created the same user.

        existing = users.find_one(
            {"user_id": user_id}
        )

        if existing:
            return existing

        raise

    return new_user


# ==========================
# GET USER
# ==========================

def get_user(user_id):

    user = users.find_one(
        {"user_id": user_id}
    )

    if not user:

        user = create_user(user_id)

    return user


# ==========================
# UPDATE USER
# ==========================

def update_user(user_id, data):

    data["updated_at"] = int(time.time())

    users.update_one(

        {"user_id": user_id},

        {
            "$set": data
        }

    )

    return get_user(user_id)


# ==========================
# ADD BALANCE
# ==========================

def add_balance(
    user_id,
    amount,
    reason="Balance Added"
):

    if amount <= 0:
        return False

    now = int(time.time())

    result = users.update_one(

        {"user_id": user_id},

        {
            "$inc": {
                "balance": amount,
                "total_earned": amount,
            },

            "$push": {
                "transactions": {
                    "type": "credit",
                    "amount": amount,
                    "reason": reason,
                    "time": now,
                },

                "activity": {
                    "action": reason,
                    "amount": amount,
                    "time": now,
                }
            },

            "$set": {
                "updated_at": now,
            }
        }

    )

    return result.modified_count > 0


# ==========================
# REMOVE BALANCE
# ==========================

def remove_balance(
    user_id,
    amount,
    reason="Balance Removed"
):

    if amount <= 0:
        return False

    now = int(time.time())

    result = users.update_one(

        {
            "user_id": user_id,
            "balance": {
                "$gte": amount
            }
        },

        {
            "$inc": {
                "balance": -amount,
            },

            "$push": {
                "transactions": {
                    "type": "debit",
                    "amount": amount,
                    "reason": reason,
                    "time": now,
                },

                "activity": {
                    "action": reason,
                    "amount": amount,
                    "time": now,
                }
            },

            "$set": {
                "updated_at": now,
            }
        }

    )

    return result.modified_count > 0


# ==========================
# ADD BONUS
# ==========================

def add_bonus(
    user_id,
    amount,
    reason="Bonus Added"
):

    if amount <= 0:
        return False

    now = int(time.time())

    result = users.update_one(

        {"user_id": user_id},

        {
            "$inc": {
                "bonus_balance": amount,
            },

            "$push": {
                "activity": {
                    "action": reason,
                    "amount": amount,
                    "time": now,
                }
            },

            "$set": {
                "updated_at": now,
            }
        }

    )

    return result.modified_count > 0


# ==========================
# ADD XP
# ==========================

def add_xp(user_id, amount):

    if amount <= 0:
        return False

    user = get_user(user_id)

    old_xp = user.get("xp", 0)
    new_xp = old_xp + amount

    new_level = (new_xp // 100) + 1

    users.update_one(

        {"user_id": user_id},

        {
            "$set": {
                "xp": new_xp,
                "level": new_level,
                "updated_at": int(time.time()),
            }
        }

    )

    return True


# ==========================
# SET RANK
# ==========================

def update_rank(user_id):

    user = get_user(user_id)

    balance = user.get(
        "balance",
        0
    )

    if balance >= 10000:

        rank = "💎 Diamond"

    elif balance >= 6000:

        rank = "🥇 Gold"

    elif balance >= 2000:

        rank = "🥈 Silver"

    elif balance >= 600:

        rank = "🥉 Bronze"

    else:

        rank = "🔰 Beginner"

    users.update_one(

        {"user_id": user_id},

        {
            "$set": {
                "rank": rank,
                "updated_at": int(time.time()),
            }
        }

    )

    return rank


# ==========================
# TOTAL USERS
# ==========================

def total_users():

    return users.count_documents({})


# ==========================
# LEADERBOARD
# ==========================

def leaderboard(limit=10):

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
            DESCENDING
        )

        .limit(limit)

    )


# ==========================
# ADD ACTIVITY
# ==========================

def add_activity(
    user_id,
    action,
    amount=0
):

    users.update_one(

        {"user_id": user_id},

        {
            "$push": {
                "activity": {
                    "action": action,
                    "amount": amount,
                    "time": int(time.time()),
                }
            },

            "$set": {
                "updated_at": int(time.time()),
            }
        }

    )


# ==========================
# ADD TRANSACTION
# ==========================

def add_transaction(
    user_id,
    transaction_type,
    amount,
    reason
):

    users.update_one(

        {"user_id": user_id},

        {
            "$push": {
                "transactions": {
                    "type": transaction_type,
                    "amount": amount,
                    "reason": reason,
                    "time": int(time.time()),
                }
            },

            "$set": {
                "updated_at": int(time.time()),
            }
        }

    )


# ==========================
# BAN USER
# ==========================

def ban_user(user_id):

    users.update_one(

        {"user_id": user_id},

        {
            "$set": {
                "banned": True,
                "updated_at": int(time.time()),
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
                "banned": False,
                "updated_at": int(time.time()),
            }
        }

    )


# ==========================
# UPDATE LOGIN
# ==========================

def update_login(user_id):

    now = int(time.time())

    users.update_one(

        {"user_id": user_id},

        {
            "$set": {
                "last_login": now,
                "updated_at": now,
            },

            "$inc": {
                "login_count": 1
            }
        }

    )
    
