import os

# ==========================
# BOT CONFIG
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==========================
# MONGODB
# ==========================

MONGO_URI = os.getenv("MONGO_URI")

DATABASE_NAME = "UnlimitedEnergy"

COLLECTION_NAME = "users"

# ==========================
# ADMIN
# ==========================

ADMIN_ID = 8473514178

# ==========================
# FORCE JOIN GROUPS
# ==========================

GROUPS = [
    "@UnlimitedEnergyTasks",
    "@UnlimitedEnergyRewards",
    "@UnlimitedEnergyCommunity",
    "@UnlimitedEnergyOfficial",
]

# ==========================
# WITHDRAW SETTINGS
# ==========================

MIN_WITHDRAW = 200

BKASH_NUMBER = "017XXXXXXXX"

NAGAD_NUMBER = "018XXXXXXXX"

BYBIT_UID = "YOUR_BYBIT_UID"

# ==========================
# REWARDS
# ==========================

DAILY_BONUS = 5

REFERRAL_REWARD = 10

GROUP_JOIN_REWARD = 20

SPIN_MIN = 1
SPIN_MAX = 20

SCRATCH_MIN = 2
SCRATCH_MAX = 15

LUCKYBOX_MIN = 5
LUCKYBOX_MAX = 30

# ==========================
# PREMIUM
# ==========================

PREMIUM_PRICE = 199

FIRST_PREMIUM_WINNERS = 5
