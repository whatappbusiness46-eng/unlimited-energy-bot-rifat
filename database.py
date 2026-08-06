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
        "balance": 0,
        "referrals": 0,
        "referred_by": None,
        "last_daily": 0,
        "group_reward": False,
        "premium": False,
        "vip": False,
        "banned": False,
        "total_earned": 0,
        "total_withdraw": 0,
        "created_at": 0,
        "activity": []
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
