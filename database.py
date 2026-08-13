# ============================================================
# database.py
# Unlimited Energy Bot V2
# FINAL DATABASE LAYER
# PART 1/8
# ============================================================

import time
import uuid
import logging

from pymongo import (
    MongoClient,
    ASCENDING,
    DESCENDING,
)

from pymongo.errors import (
    DuplicateKeyError,
)

from config import (
    MONGO_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
    MAX_ENERGY,
    ENERGY_REGEN_SECONDS,
    XP_PER_LEVEL,
    LEADERBOARD_LIMIT,
    ACTIVITY_LIMIT,
)


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE CONNECTION
# ============================================================

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI environment variable is not configured."
    )


client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
)


db = client[DATABASE_NAME]


# ============================================================
# COLLECTIONS
# ============================================================

users = db[COLLECTION_NAME]

transactions = db[
    "transactions"
]

withdrawals = db[
    "withdrawals"
]

security_logs = db[
    "security_logs"
]

daily_statistics = db[
    "daily_statistics"
]

bot_settings = db[
    "bot_settings"
]


# ============================================================
# DATABASE INDEXES
# ============================================================

def ensure_indexes():
    """
    Create required MongoDB indexes safely.

    Existing indexes are checked first to avoid
    IndexOptionsConflict during repeated deployments.
    """

    try:

        # ----------------------------------------------------
        # USERS
        # ----------------------------------------------------

        existing_indexes = (
            users.index_information()
        )

        user_id_index_exists = False

        for (
            index_name,
            index_info,
        ) in existing_indexes.items():

            key_list = index_info.get(
                "key",
                [],
            )

            if key_list == [
                (
                    "user_id",
                    ASCENDING,
                )
            ]:

                user_id_index_exists = True
                break

        if not user_id_index_exists:

            users.create_index(
                [
                    (
                        "user_id",
                        ASCENDING,
                    )
                ],
                unique=True,
                name="user_id_unique",
            )

        users.create_index(
            [
                (
                    "balance",
                    DESCENDING,
                )
            ],
            name="balance_desc",
        )

        users.create_index(
            [
                (
                    "last_login",
                    DESCENDING,
                )
            ],
            name="last_login_desc",
        )

        users.create_index(
            [
                (
                    "banned",
                    ASCENDING,
                )
            ],
            name="banned_index",
        )

        # ----------------------------------------------------
        # TRANSACTIONS
        # ----------------------------------------------------

        transactions.create_index(
            [
                (
                    "transaction_id",
                    ASCENDING,
                )
            ],
            unique=True,
            name="transaction_id_unique",
        )

        transactions.create_index(
            [
                (
                    "user_id",
                    ASCENDING,
                ),
                (
                    "created_at",
                    DESCENDING,
                ),
            ],
            name="user_transactions",
        )

        # ----------------------------------------------------
        # WITHDRAWALS
        # ----------------------------------------------------

        withdrawals.create_index(
            [
                (
                    "withdrawal_id",
                    ASCENDING,
                )
            ],
            unique=True,
            name="withdrawal_id_unique",
        )

        withdrawals.create_index(
            [
                (
                    "user_id",
                    ASCENDING,
                ),
                (
                    "created_at",
                    DESCENDING,
                ),
            ],
            name="user_withdrawals",
        )

        withdrawals.create_index(
            [
                (
                    "status",
                    ASCENDING,
                ),
                (
                    "created_at",
                    DESCENDING,
                ),
            ],
            name="withdrawal_status",
        )

        # ----------------------------------------------------
        # SECURITY LOGS
        # ----------------------------------------------------

        security_logs.create_index(
            [
                (
                    "user_id",
                    ASCENDING,
                ),
                (
                    "created_at",
                    DESCENDING,
                ),
            ],
            name="user_security_logs",
        )

        # ----------------------------------------------------
        # DAILY STATISTICS
        # ----------------------------------------------------

        daily_statistics.create_index(
            [
                (
                    "date",
                    ASCENDING,
                )
            ],
            unique=True,
            name="statistics_date_unique",
        )

    except Exception as error:

        logger.warning(
            "Database index setup warning: %s",
            error,
        )


# ============================================================
# DEFAULT USER DOCUMENT
# ============================================================

def build_default_user(user_id):

    now = int(
        time.time()
    )

    return {

        # ====================================================
        # BASIC
        # ====================================================

        "user_id": int(user_id),

        "username": "",

        "first_name": "",

        "last_name": "",

        "banned": False,

        "blacklisted": False,


        # ====================================================
        # WALLET
        # ====================================================

        "balance": 0,

        "bonus_balance": 0,

        "premium_balance": 0,

        "total_earned": 0,

        "total_spent": 0,


        # ====================================================
        # EARNING
        # ====================================================

        "offer_completed": 0,

        "shortlink_completed": 0,

        "daily_task_count": 0,

        "last_task_reset": 0,


        # ====================================================
        # DAILY
        # ====================================================

        "last_daily": 0,

        "daily_streak": 0,


        # ====================================================
        # SPIN
        # ====================================================

        "spin_ticket": 0,

        "last_spin": 0,

        "spin_wins": 0,

        "spin_count": 0,


        # ====================================================
        # LUCKY BOX
        # ====================================================

        "lucky_box": 0,

        "last_lucky_box": 0,

        "lucky_box_wins": 0,

        "lucky_box_count": 0,


        # ====================================================
        # SCRATCH CARD
        # ====================================================

        "scratch_card": 0,

        "last_scratch": 0,

        "scratch_wins": 0,

        "scratch_count": 0,


        # ====================================================
        # JACKPOT
        # ====================================================

        "jackpot_ticket": 0,

        "last_jackpot": 0,

        "jackpot_wins": 0,

        "jackpot_count": 0,


        # ====================================================
        # ENERGY
        # ====================================================

        "energy": MAX_ENERGY,

        "max_energy": MAX_ENERGY,

        "last_energy_update": now,


        # ====================================================
        # XP / LEVEL
        # ====================================================

        "xp": 0,

        "level": 1,

        "rank": "🔰 Beginner",


        # ====================================================
        # REFERRAL
        # ====================================================

        "referrals": 0,

        "referred_by": None,

        "referral_earn": 0,

        "referral_xp": 0,

        "referral_reward_given": False,

        "referral_ids": [],


        # ====================================================
        # PREMIUM
        # ====================================================

        "premium": False,

        "premium_expire": 0,

        "premium_balance": 0,


        # ====================================================
        # VIP
        # ====================================================

        "vip": False,

        "vip_expire": 0,


        # ====================================================
        # FORCE JOIN
        # ====================================================

        "group_reward": False,

        "groups_verified": False,

        "verified_at": 0,


        # ====================================================
        # WITHDRAW
        # ====================================================

        "withdraw_pending": 0,

        "total_withdraw": 0,

        "withdraw_history": [],


        # ====================================================
        # ACTIVITY
        # ====================================================

        "activity": [],


        # ====================================================
        # TRANSACTIONS
        # ====================================================

        "transactions": [],


        # ====================================================
        # ACHIEVEMENTS
        # ====================================================

        "badges": [],

        "achievements": [],


        # ====================================================
        # NOTIFICATIONS
        # ====================================================

        "notifications": True,


        # ====================================================
        # COUPONS
        # ====================================================

        "used_coupons": [],


        # ====================================================
        # GIFTS
        # ====================================================

        "gift_claimed": [],


        # ====================================================
        # TASK PROTECTION
        # ====================================================

        "completed_tasks": [],

        "completed_offers": [],

        "completed_shortlinks": [],


        # ====================================================
        # SECURITY
        # ====================================================

        "last_ip": "",

        "device_id": "",

        "suspicious_activity": False,

        "suspicious_count": 0,

        "security_flags": [],


        # ====================================================
        # COOLDOWN / ABUSE
        # ====================================================

        "last_reward": 0,

        "last_task": 0,

        "last_offer": 0,

        "last_shortlink": 0,


        # ====================================================
        # LANGUAGE
        # ====================================================

        "language": "en",


        # ====================================================
        # LOGIN / ACTIVITY TIME
        # ====================================================

        "last_login": now,

        "last_active": now,


        # ====================================================
        # CREATED
        # ====================================================

        "created_at": now,

    }


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    user_id,
    username="",
    first_name="",
    last_name="",
):

    user_id = int(
        user_id
    )

    existing = users.find_one(
        {
            "user_id": user_id
        }
    )

    if existing:

        update_data = {}

        if username:
            update_data[
                "username"
            ] = username

        if first_name:
            update_data[
                "first_name"
            ] = first_name

        if last_name:
            update_data[
                "last_name"
            ] = last_name

        if update_data:

            update_data[
                "last_active"
            ] = int(
                time.time()
            )

            users.update_one(
                {
                    "user_id": user_id
                },
                {
                    "$set": update_data
                },
            )

        return get_user(
            user_id,
            create=False,
        )

    new_user = build_default_user(
        user_id
    )

    if username:
        new_user[
            "username"
        ] = username

    if first_name:
        new_user[
            "first_name"
        ] = first_name

    if last_name:
        new_user[
            "last_name"
        ] = last_name

    try:

        users.insert_one(
            new_user
        )

    except DuplicateKeyError:

        return get_user(
            user_id,
            create=False,
        )

    return new_user


# ============================================================
# GET USER
# ============================================================

def get_user(
    user_id,
    create=True,
):

    user_id = int(
        user_id
    )

    user = users.find_one(
        {
            "user_id": user_id
        }
    )

    if not user and create:

        return create_user(
            user_id
        )

    return user


# ============================================================
# UPDATE USER
# ============================================================

def update_user(
    user_id,
    data,
):

    if not data:
        return False

    user_id = int(
        user_id
    )

    result = users.update_one(
        {
            "user_id": user_id
        },
        {
            "$set": data
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# TOUCH USER
# ============================================================

def touch_user(
    user_id
):

    now = int(
        time.time()
    )

    result = users.update_one(
        {
            "user_id": int(
                user_id
            )
        },
        {
            "$set": {
                "last_active": now,
                "last_login": now,
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# ADD BALANCE
# ============================================================

def add_balance(
    user_id,
    amount,
):

    amount = int(
        amount
    )

    if amount <= 0:
        return False

    user_id = int(
        user_id
    )

    get_user(
        user_id
    )

    result = users.update_one(
        {
            "user_id": user_id,
            "banned": {
                "$ne": True
            },
            "blacklisted": {
                "$ne": True
            },
        },
        {
            "$inc": {
                "balance": amount,
                "total_earned": amount,
            }
        },
    )

    if result.modified_count > 0:

        record_transaction(
            user_id=user_id,
            transaction_type="credit",
            amount=amount,
            source="balance_reward",
        )

        update_daily_statistic(
            field="total_points_distributed",
            amount=amount,
        )

        return True

    return False


# ============================================================
# ADD BONUS BALANCE
# ============================================================

def add_bonus(
    user_id,
    amount,
):

    amount = int(
        amount
    )

    if amount <= 0:
        return False

    user_id = int(
        user_id
    )

    get_user(
        user_id
    )

    result = users.update_one(
        {
            "user_id": user_id,
            "banned": {
                "$ne": True
            },
            "blacklisted": {
                "$ne": True
            },
        },
        {
            "$inc": {
                "bonus_balance": amount,
                "total_earned": amount,
            }
        },
    )

    if result.modified_count > 0:

        record_transaction(
            user_id=user_id,
            transaction_type="bonus_credit",
            amount=amount,
            source="bonus_reward",
        )

        update_daily_statistic(
            field="total_points_distributed",
            amount=amount,
        )

        return True

    return False


# ============================================================
# REMOVE BALANCE
# ============================================================

def remove_balance(
    user_id,
    amount,
):

    amount = int(
        amount
    )

    if amount <= 0:
        return 0

    user_id = int(
        user_id
    )

    result = users.update_one(
        {
            "user_id": user_id,
            "balance": {
                "$gte": amount
            },
        },
        {
            "$inc": {
                "balance": -amount,
                "total_spent": amount,
            }
        },
    )

    if result.modified_count <= 0:
        return 0

    record_transaction(
        user_id=user_id,
        transaction_type="debit",
        amount=amount,
        source="balance_remove",
    )

    return amount

# ============================================================
# ADD XP
# ============================================================

def add_xp(
    user_id,
    amount,
):

    amount = int(
        amount
    )

    user = get_user(
        user_id
    )

    if amount <= 0:

        return {
            "xp": user.get(
                "xp",
                0,
            ),
            "level": user.get(
                "level",
                1,
            ),
            "level_up": False,
        }

    old_xp = int(
        user.get(
            "xp",
            0,
        )
    )

    old_level = int(
        user.get(
            "level",
            1,
        )
    )

    new_xp = (
        old_xp + amount
    )

    new_level = (
        new_xp
        // XP_PER_LEVEL
    ) + 1

    if new_level < 1:
        new_level = 1

    users.update_one(
        {
            "user_id": int(
                user_id
            )
        },
        {
            "$inc": {
                "xp": amount
            },
            "$set": {
                "level": new_level
            },
        },
    )

    return {
        "xp": new_xp,
        "level": new_level,
        "level_up": (
            new_level
            > old_level
        ),
    }


# ============================================================
# ADD ACTIVITY
# ============================================================

def add_activity(
    user_id,
    action,
    amount=0,
):

    user_id = int(
        user_id
    )

    now = int(
        time.time()
    )

    activity = {
        "action": str(
            action
        ),
        "amount": int(
            amount or 0
        ),
        "time": now,
    }

    get_user(
        user_id
    )

    users.update_one(
        {
            "user_id": user_id
        },
        {
            "$push": {
                "activity": {
                    "$each": [
                        activity
                    ],
                    "$slice": (
                        -ACTIVITY_LIMIT
                    ),
                }
            },
            "$set": {
                "last_active": now,
            },
        },
    )

    return activity


# ============================================================
# TRANSACTION ID
# ============================================================

def generate_transaction_id():

    return (
        "TXN-"
        + uuid.uuid4()
        .hex
        .upper()
    )


# ============================================================
# RECORD TRANSACTION
# ============================================================

def record_transaction(
    user_id,
    transaction_type,
    amount,
    source="unknown",
    status="completed",
    metadata=None,
):

    transaction_id = (
        generate_transaction_id()
    )

    transaction = {

        "transaction_id":
            transaction_id,

        "user_id":
            int(user_id),

        "type":
            str(
                transaction_type
            ),

        "amount":
            int(amount),

        "source":
            str(source),

        "status":
            str(status),

        "metadata":
            metadata or {},

        "created_at":
            int(
                time.time()
            ),

    }

    try:

        transactions.insert_one(
            transaction
        )

    except Exception as error:

        logger.error(
            "Transaction insert failed: %s",
            error,
        )

    try:

        users.update_one(
            {
                "user_id": int(
                    user_id
                )
            },
            {
                "$push": {
                    "transactions": {
                        "$each": [
                            transaction
                        ],
                        "$slice": -100,
                    }
                }
            },
        )

    except Exception as error:

        logger.error(
            "User transaction history update failed: %s",
            error,
        )

    return transaction_id


# ============================================================
# GET TRANSACTIONS
# ============================================================

def get_transactions(
    user_id,
    limit=20,
):

    return list(
        transactions.find(
            {
                "user_id": int(
                    user_id
                )
            }
        )
        .sort(
            "created_at",
            DESCENDING,
        )
        .limit(
            int(limit)
        )
    )


# ============================================================
# ADD SPIN TICKET
# ============================================================

def add_spin_ticket(
    user_id,
    amount=1,
):

    amount = int(
        amount
    )

    if amount <= 0:
        return False

    result = users.update_one(
        {
            "user_id": int(
                user_id
            )
        },
        {
            "$inc": {
                "spin_ticket": amount
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# USE SPIN TICKET
# ============================================================

def use_spin_ticket(
    user_id
):

    result = users.update_one(
        {
            "user_id": int(
                user_id
            ),
            "spin_ticket": {
                "$gt": 0
            },
        },
        {
            "$inc": {
                "spin_ticket": -1
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# ADD LUCKY BOX
# ============================================================

def add_lucky_box(
    user_id,
    amount=1,
):

    amount = int(
        amount
    )

    if amount <= 0:
        return False

    result = users.update_one(
        {
            "user_id": int(
                user_id
            )
        },
        {
            "$inc": {
                "lucky_box": amount
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# USE LUCKY BOX
# ============================================================

def use_lucky_box(
    user_id
):

    result = users.update_one(
        {
            "user_id": int(
                user_id
            ),
            "lucky_box": {
                "$gt": 0
            },
        },
        {
            "$inc": {
                "lucky_box": -1
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# ADD SCRATCH CARD
# ============================================================

def add_scratch_card(
    user_id,
    amount=1,
):

    amount = int(
        amount
    )

    if amount <= 0:
        return False

    result = users.update_one(
        {
            "user_id": int(
                user_id
            )
        },
        {
            "$inc": {
                "scratch_card": amount
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# USE SCRATCH CARD
# ============================================================

def use_scratch_card(
    user_id
):

    result = users.update_one(
        {
            "user_id": int(
                user_id
            ),
            "scratch_card": {
                "$gt": 0
            },
        },
        {
            "$inc": {
                "scratch_card": -1
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# ADD JACKPOT TICKET
# ============================================================

def add_jackpot_ticket(
    user_id,
    amount=1,
):

    amount = int(
        amount
    )

    if amount <= 0:
        return False

    result = users.update_one(
        {
            "user_id": int(
                user_id
            )
        },
        {
            "$inc": {
                "jackpot_ticket": amount
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# USE JACKPOT TICKET
# ============================================================

def use_jackpot_ticket(
    user_id
):

    result = users.update_one(
        {
            "user_id": int(
                user_id
            ),
            "jackpot_ticket": {
                "$gt": 0
            },
        },
        {
            "$inc": {
                "jackpot_ticket": -1
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# UPDATE ENERGY
# ============================================================

def update_energy(
    user_id
):

    user = get_user(
        user_id
    )

    now = int(
        time.time()
    )

    current_energy = int(
        user.get(
            "energy",
            MAX_ENERGY,
        )
    )

    max_energy = int(
        user.get(
            "max_energy",
            MAX_ENERGY,
        )
    )

    last_update = int(
        user.get(
            "last_energy_update",
            now,
        )
    )

    if current_energy >= max_energy:

        users.update_one(
            {
                "user_id": int(
                    user_id
                )
            },
            {
                "$set": {
                    "last_energy_update": now,
                }
            },
        )

        return max_energy

    elapsed = (
        now - last_update
    )

    if elapsed < ENERGY_REGEN_SECONDS:

        return current_energy

    recovered = (
        elapsed
        // ENERGY_REGEN_SECONDS
    )

    if recovered <= 0:

        return current_energy

    new_energy = min(
        max_energy,
        current_energy
        + recovered,
    )

    consumed_time = (
        recovered
        * ENERGY_REGEN_SECONDS
    )

    new_last_update = (
        last_update
        + consumed_time
    )

    users.update_one(
        {
            "user_id": int(
                user_id
            )
        },
        {
            "$set": {
                "energy": new_energy,
                "last_energy_update":
                    new_last_update,
            }
        },
    )

    return new_energy
      # ============================================================
# GET ENERGY
# ============================================================

def get_energy(
    user_id
):

    update_energy(
        user_id
    )

    user = get_user(
        user_id
    )

    return int(
        user.get(
            "energy",
            MAX_ENERGY,
        )
    )


# ============================================================
# USE ENERGY
# ============================================================

def use_energy(
    user_id,
    amount=1,
):

    amount = int(
        amount
    )

    if amount <= 0:

        return True

    update_energy(
        user_id
    )

    result = users.update_one(
        {
            "user_id": int(
                user_id
            ),
            "energy": {
                "$gte": amount
            },
        },
        {
            "$inc": {
                "energy": -amount
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# RESET ENERGY
# ============================================================

def reset_energy(
    user_id
):

    now = int(
        time.time()
    )

    result = users.update_one(
        {
            "user_id": int(
                user_id
            )
        },
        {
            "$set": {
                "energy": MAX_ENERGY,
                "max_energy": MAX_ENERGY,
                "last_energy_update": now,
            }
        },
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# GET BALANCE
# ============================================================

def get_balance(
    user_id
):

    user = get_user(
        user_id
    )

    return int(
        user.get(
            "balance",
            0,
        )
    )


# ============================================================
# GET XP
# ============================================================

def get_xp(
    user_id
):

    user = get_user(
        user_id
    )

    return int(
        user.get(
            "xp",
            0,
        )
    )


# ============================================================
# GET LEVEL
# ============================================================

def get_level(
    user_id
):

    user = get_user(
        user_id
    )

    return int(
        user.get(
            "level",
            1,
        )
    )


# ============================================================
# ENSURE DATABASE READY
# ============================================================

try:

    ensure_indexes()

except Exception as error:

    logger.warning(
        "Database initialization warning: %s",
        error,
    )          
