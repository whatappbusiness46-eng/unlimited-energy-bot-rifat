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
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
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

        # ==========================
        # BASIC
        # ==========================

        "user_id": user_id,
        "banned": False,

        # ==========================
        # WALLET
        # ==========================

        "balance": 0,
        "bonus_balance": 0,
        "premium_balance": 0,

        # ==========================
        # EARNING
        # ==========================

        "total_earned": 0,
        "offer_completed": 0,
        "shortlink_completed": 0,

        # ==========================
        # DAILY BONUS
        # ==========================

        "last_daily": 0,
        "daily_streak": 0,

        # ==========================
        # SPIN
        # ==========================

        "spin_ticket": 0,
        "last_spin": 0,
        "spin_wins": 0,

        # ==========================
        # LUCKY BOX
        # ==========================

        "lucky_box": 0,
        "last_lucky_box": 0,
        "lucky_box_wins": 0,

        # ==========================
        # SCRATCH CARD
        # ==========================

        "scratch_card": 0,
        "last_scratch": 0,
        "scratch_wins": 0,

        # ==========================
        # ENERGY
        # ==========================

        "energy": 100,
        "max_energy": 100,
        "last_energy_update": now,

        # ==========================
        # XP / LEVEL
        # ==========================

        "xp": 0,
        "level": 1,
        "rank": "🔰 Beginner",

        # ==========================
        # REFERRAL
        # ==========================

        "referrals": 0,
        "referred_by": None,
        "referral_earn": 0,
        "referral_xp": 0,
        # ==========================
        # PREMIUM
        # ==========================

        "premium": False,
        "premium_expire": 0,
        "vip": False,

        # ==========================
        # GROUP REWARD
        # ==========================

        "group_reward": False,

        # ==========================
        # WITHDRAW
        # ==========================

        "withdraw_pending": 0,
        "total_withdraw": 0,
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
        # NOTIFICATION
        # ==========================

        "notifications": True,

        # ==========================
        # COUPON
        # ==========================

        "used_coupons": [],

        # ==========================
        # GIFT
        # ==========================

        "gift_claimed": [],

        # ==========================
        # JACKPOT
        # ==========================

        "jackpot_ticket": 0,

        # ==========================
        # SECURITY
        # ==========================

        "last_ip": "",
        "device_id": "",

        # ==========================
        # LANGUAGE
        # ==========================

        "language": "en",

        # ==========================
        # LOGIN
        # ==========================

        "last_login": now,

        # ==========================
        # CREATED
        # ==========================

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
        {"$set": data}
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
                "total_earned": amount,
            }
        }
    )


# ==========================
# ADD BONUS BALANCE
# ==========================

def add_bonus(user_id, amount):

    users.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "bonus_balance": amount,
                "total_earned": amount,
            }
        }
    )


# ==========================
# REMOVE BALANCE
# ==========================

def remove_balance(user_id, amount):

    user = get_user(user_id)

    balance = user.get(
        "balance",
        0
    )

    if amount <= 0:
        return 0

    if balance < amount:
        return 0

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

    old_xp = user.get(
        "xp",
        0
    )

    old_level = user.get(
        "level",
        1
    )

    new_xp = old_xp + amount

    # Every 100 XP = 1 level
    new_level = (new_xp // 100) + 1

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

    return {
        "xp": new_xp,
        "level": new_level,
        "level_up": new_level > old_level,
    }


# ==========================
# ADD ACTIVITY
# ==========================

def add_activity(
    user_id,
    action,
    amount=0
):

    activity = {
        "action": action,
        "amount": amount,
        "time": int(time.time()),
    }

    users.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "activity": {
                    "$each": [activity],
                    "$slice": -20,
                }
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
                "spin_ticket": -1
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
                "lucky_box": -1
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
                "scratch_card": -1
            }
        }
    )

    return result.modified_count > 0


# ==========================
# ENERGY UPDATE
# ==========================

def update_energy(user_id):

    user = get_user(user_id)

    now = int(time.time())

    energy = user.get(
        "energy",
        100
    )

    max_energy = user.get(
        "max_energy",
        100
    )

    last_update = user.get(
        "last_energy_update",
        now
    )

    elapsed = now - last_update

    # 1 energy every 60 seconds
    recovered = elapsed // 60

    if recovered <= 0:
        return energy

    new_energy = min(
        max_energy,
        energy + recovered
    )

    new_update_time = (
        last_update
        + recovered * 60
    )

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "energy": new_energy,
                "last_energy_update": new_update_time,
            }
        }
    )

    return new_energy


# ==========================
# USE ENERGY
# ==========================

def use_energy(
    user_id,
    amount=1
):

    update_energy(user_id)

    result = users.update_one(
        {
            "user_id": user_id,
            "energy": {
                "$gte": amount
            }
        },
        {
            "$inc": {
                "energy": -amount
            }
        }
    )

    return result.modified_count > 0


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
    
