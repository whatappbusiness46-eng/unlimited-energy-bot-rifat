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
# DAILY REWARD
# ==========================

DAILY_BONUS = 5

DAILY_COOLDOWN = 86400


# ==========================
# REFERRAL
# ==========================

REFERRAL_REWARD = 10

REFERRAL_XP = 20


# ==========================
# GROUP JOIN REWARD
# ==========================

GROUP_JOIN_REWARD = 20


# ==========================
# XP / LEVEL
# ==========================

XP_PER_LEVEL = 100

OFFER_XP = 10

SHORTLINK_XP = 15

DAILY_XP = 5

REFERRAL_XP = 20


# ==========================
# ENERGY SYSTEM
# ==========================

MAX_ENERGY = 100

ENERGY_PER_TASK = 10

ENERGY_RESTORE_TIME = 3600


# ==========================
# SPIN / WHEEL 🎡
# ==========================

SPIN_MIN = 1

SPIN_MAX = 20

SPIN_TICKET_COST = 1


# ==========================
# SCRATCH CARD 🎫
# ==========================

SCRATCH_MIN = 2

SCRATCH_MAX = 15

SCRATCH_TICKET_COST = 1


# ==========================
# LUCKY BOX 🎁
# ==========================

LUCKYBOX_MIN = 5

LUCKYBOX_MAX = 30

LUCKYBOX_COST = 1


# ==========================
# JACKPOT 🎰
# ==========================

JACKPOT_MIN = 10

JACKPOT_MAX = 100

JACKPOT_TICKET_COST = 1


# ==========================
# PREMIUM 👑
# ==========================

PREMIUM_PRICE = 199

PREMIUM_DURATION = 30 * 86400

FIRST_PREMIUM_WINNERS = 5


# ==========================
# VIP 💎
# ==========================

VIP_PRICE = 499

VIP_DURATION = 30 * 86400


# ==========================
# EARNING LIMITS
# ==========================

MAX_DAILY_EARN = 500

MAX_REFERRAL_EARN = 10000


# ==========================
# TASK SETTINGS
# ==========================

OFFER_REWARD_MIN = 5

OFFER_REWARD_MAX = 50

SHORTLINK_REWARD_MIN = 5

SHORTLINK_REWARD_MAX = 30


# ==========================
# SECURITY
# ==========================

MAX_WITHDRAW_PER_DAY = 3

MAX_DAILY_TASKS = 50


# ==========================
# BOT SETTINGS
# ==========================

BOT_NAME = "Unlimited Energy Bot V2"

SUPPORT_USERNAME = "@UnlimitedEnergyOfficial"

CURRENCY_NAME = "Points"
