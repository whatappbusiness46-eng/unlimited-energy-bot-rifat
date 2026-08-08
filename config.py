import os

# ==================================================
# BOT CONFIG
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==================================================
# DATABASE
# ==================================================

MONGO_URI = os.getenv("MONGO_URI")

DATABASE_NAME = "UnlimitedEnergy"
COLLECTION_NAME = "users"

# ==================================================
# ADMIN
# ==================================================

ADMIN_ID = 7713476833

# ==================================================
# FORCE JOIN GROUPS
# ==================================================

GROUPS = [
    "@UnlimitedEnergyTasks",
    "@UnlimitedEnergyRewards",
    "@UnlimitedEnergyCommunity",
    "@UnlimitedEnergyOfficial",
]

# ==================================================
# WITHDRAW
# ==================================================

MIN_WITHDRAW = 200

BKASH_NUMBER = "017XXXXXXXX"
NAGAD_NUMBER = "018XXXXXXXX"
BYBIT_UID = "YOUR_BYBIT_UID"

# ==================================================
# DAILY REWARD
# ==================================================

DAILY_BONUS = 5

DAILY_XP = 5

# ==================================================
# REFERRAL
# ==================================================

REFERRAL_REWARD = 10
REFERRAL_XP = 10

# ==================================================
# GROUP JOIN REWARD
# ==================================================

GROUP_JOIN_REWARD = 20

# ==================================================
# ENERGY
# ==================================================

MAX_ENERGY = 100
ENERGY_REGEN_SECONDS = 300

# ==================================================
# SPIN WHEEL
# ==================================================

SPIN_MIN = 1
SPIN_MAX = 20

SPIN_TICKET_REWARD = 1

# ==================================================
# LUCKY BOX
# ==================================================

LUCKYBOX_MIN = 5
LUCKYBOX_MAX = 30

LUCKYBOX_TICKET_REWARD = 1

# ==================================================
# SCRATCH CARD
# ==================================================

SCRATCH_MIN = 2
SCRATCH_MAX = 15

SCRATCH_CARD_REWARD = 1

# ==================================================
# JACKPOT
# ==================================================

JACKPOT_MIN = 10
JACKPOT_MAX = 100

JACKPOT_TICKET_REWARD = 1

# ==================================================
# XP / LEVEL
# ==================================================

XP_PER_LEVEL = 100

# ==================================================
# RANK REQUIREMENTS
# ==================================================

BRONZE_REQUIRED = 600
SILVER_REQUIRED = 2000
GOLD_REQUIRED = 6000
DIAMOND_REQUIRED = 10000

# ==================================================
# PREMIUM
# ==================================================

PREMIUM_PRICE = 199

PREMIUM_DAYS = 30

FIRST_PREMIUM_WINNERS = 5

# ==================================================
# VIP
# ==================================================

VIP_PRICE = 499

VIP_DAYS = 30

# ==================================================
# EARN REWARDS
# ==================================================

TASK_REWARD_MIN = 5
TASK_REWARD_MAX = 50

OFFER_REWARD_MIN = 10
OFFER_REWARD_MAX = 100

SHORTLINK_REWARD_MIN = 5
SHORTLINK_REWARD_MAX = 50

# ==================================================
# GAME COOLDOWN
# ==================================================

SPIN_COOLDOWN = 0
LUCKYBOX_COOLDOWN = 0
SCRATCH_COOLDOWN = 0
JACKPOT_COOLDOWN = 0

# ==================================================
# WITHDRAW STATUS
# ==================================================

WITHDRAW_PENDING = "pending"
WITHDRAW_APPROVED = "approved"
WITHDRAW_REJECTED = "rejected"

# ==================================================
# BOT INFORMATION
# ==================================================

BOT_NAME = "Unlimited Energy Bot"
BOT_VERSION = "V2"

# ==================================================
# NOTIFICATION
# ==================================================

ENABLE_NOTIFICATIONS = True

# ==================================================
# SECURITY
# ==================================================

MAX_REFERRAL_REWARD_PER_USER = 1000

# ==================================================
# PAGINATION
# ==================================================

LEADERBOARD_LIMIT = 10

ACTIVITY_LIMIT = 10
