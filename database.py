from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME

# ==========================
# CONNECT DATABASE
# ==========================

client = MongoClient(MONGO_URI)

db = client[DATABASE_NAME]

users = db[COLLECTION_NAME]

# ==========================
# CREATE USER
# ==========================

def create_user(user_id):

    user = users.find_one({"user_id": user_id})

    if user:
        return user

    new_user = {
    "user_id": user_id,

    # Wallet
    "balance": 0,
    "bonus_balance": 0,
    "premium_balance": 0,

    # Referral
    "referrals": 0,
    "referred_by": None,

    # Premium
    "premium": False,
    "vip": False,

    # User Status
    "banned": False,

    # Statistics
    "total_earned": 0,
    "total_withdraw": 0,

    # Level System
    "xp": 0,
    "level": 1,
    "rank": "🔰 Beginner",

    # Daily
    "last_daily": 0,
    "daily_streak": 0,

    # Rewards
    "group_reward": False,

    # Spin & Games
    "spin_ticket": 0,
    "lucky_box": 0,

    # History
    "activity": [],
    # Withdraw
    "withdraw_pending": 0,
    "withdraw_history": [],

    # Premium
    "premium_expire": 0,

    # Earn
    "offer_completed": 0,
    "shortlink_completed": 0,

    # Referral
    "referral_earn": 0,

    # Login
    "last_login": int(time.time()),

    # Achievement
    "badges": [],

    # Notification
    "notifications": True,

    # Security
    "last_ip": "",
    "device_id": "",

    # Coupon
    "used_coupons": [],

    # Gift
    "gift_claimed": [],

    # Jackpot
    "jackpot_ticket": 0,

    # Energy
    "energy": 100,

    # Settings
    "language": "en",

    # Time
    "created_at": int(time.time()),
    }

    users.insert_one(new_user)

    return new_user

# ==========================
# GET USER
# ==========================

def get_user(user_id):

    user = users.find_one({"user_id": user_id})

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

        {"$inc": {"balance": amount}}

    )

# ==========================
# REMOVE BALANCE
# ==========================

def remove_balance(user_id, amount):

    user = get_user(user_id)

    balance = user["balance"]

    if balance < amount:

        amount = balance

    users.update_one(

        {"user_id": user_id},

        {"$inc": {"balance": -amount}}

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

        users.find().sort(

            "balance",

            -1

        ).limit(10)

  )
