import os
import json
import time
import threading
from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


# ==========================
# CONFIG
# ==========================

TOKEN = os.getenv("BOT_TOKEN")

DB_FILE = "users.json"

GROUP1 = "@whatsAppsellboy"
GROUP2 = "@wsfreeincomesite67"

ADMIN_ID = 7713476833


# ==========================
# DATABASE
# ==========================

def load_users():

    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)

    except:
        return {}


def save_users(users):

    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)


def get_user(user_id):

    users = load_users()

    uid = str(user_id)

    if uid not in users:

        users[uid] = {
            "balance": 0,
            "referrals": 0,
            "last_daily": 0,
            "group_reward": False,
            "referred_by": None
        }

        save_users(users)

    return users


def get_balance(user_id):

    users = get_user(user_id)

    return users[str(user_id)]["balance"]


def add_balance(user_id, amount):

    users = get_user(user_id)

    users[str(user_id)]["balance"] += amount

    save_users(users)
    # ==========================
# MAIN MENU
# ==========================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Earn",
                callback_data="earn"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Balance",
                callback_data="balance"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Referral",
                callback_data="refer"
            )
        ],

        [
            InlineKeyboardButton(
                "💸 Withdraw",
                callback_data="withdraw"
            )
        ],

        [
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


# ==========================
# START COMMAND
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    users = get_user(user.id)

    uid = str(user.id)


    # ==========================
    # AUTO REFERRAL
    # ==========================

    if context.args:

        referrer = context.args[0]


        if (
            referrer != uid
            and referrer in users
            and users[uid].get("referred_by") is None
        ):

            users[uid]["referred_by"] = referrer

            users[referrer]["balance"] += 10

            users[referrer]["referrals"] += 1

            save_users(users)


            try:

                await context.bot.send_message(

                    chat_id=int(referrer),

                    text=(
                        "🎉 New Referral Joined!\n\n"
                        "✅ +10 Points Added."
                    )

                )

            except:

                pass


    # ==========================
    # WELCOME MESSAGE
    # ==========================

    await update.message.reply_text(

        "👋 Welcome to Unlimited Energy Bot!\n\n"
        "Choose an option below:",

        reply_markup=main_menu()

    )
    # ==========================
# CALLBACK SYSTEM
# ==========================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    # ==========================
    # EARN MENU
    # ==========================

    if query.data == "earn":

        keyboard = [

            [
                InlineKeyboardButton(
                    "📢 Join Group 1",
                    url="https://t.me/whatsAppsellboy"
                )
            ],

            [
                InlineKeyboardButton(
                    "📢 Join Group 2",
                    url="https://t.me/wsfreeincomesite67"
                )
            ],

            [
                InlineKeyboardButton(
                    "✅ Verify Join (+2)",
                    callback_data="verify"
                )
            ],

            [
                InlineKeyboardButton(
                    "🎁 Daily Bonus (+5)",
                    callback_data="daily"
                )
            ],

            [
                InlineKeyboardButton(
                    "👥 Referral",
                    callback_data="refer"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                )
            ]

        ]


        await query.edit_message_text(

            "💰 Earn Points\n\n"
            "Complete the tasks below.",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )


    # ==========================
    # BALANCE
    # ==========================

    elif query.data == "balance":

        balance = get_balance(
            query.from_user.id
        )


        await query.edit_message_text(

            f"💳 Your Balance\n\n"
            f"💰 {balance} Points",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )
                ]

            ])

        )


    # ==========================
    # BACK
    # ==========================

    elif query.data == "back":

        await query.edit_message_text(

            "👋 Welcome to Unlimited Energy Bot!\n\n"
            "Choose an option below:",

            reply_markup=main_menu()

        )
            # ==========================
    # DAILY BONUS
    # ==========================

    elif query.data == "daily":

        users = get_user(
            query.from_user.id
        )

        uid = str(
            query.from_user.id
        )

        now = int(time.time())

        last = users[uid]["last_daily"]


        if now - last >= 86400:

            users[uid]["last_daily"] = now

            users[uid]["balance"] += 5

            save_users(users)


            text = (
                "🎉 Daily Bonus Claimed!\n\n"
                "✅ +5 Points Added."
            )


        else:

            remaining = 86400 - (now - last)

            hours = remaining // 3600

            minutes = (remaining % 3600) // 60


            text = (
                "⏳ Daily Bonus Already Claimed.\n\n"
                f"Try Again After {hours}h {minutes}m."
            )


        await query.edit_message_text(

            text,

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )
                ]

            ])

        )


    # ==========================
    # GROUP VERIFY
    # ==========================

    elif query.data == "verify":

        users = get_user(
            query.from_user.id
        )

        uid = str(
            query.from_user.id
        )


        if users[uid]["group_reward"]:

            text = (
                "✅ You already claimed "
                "the Join Reward."
            )


        else:

            try:

                member1 = await context.bot.get_chat_member(

                    GROUP1,

                    query.from_user.id

                )


                member2 = await context.bot.get_chat_member(

                    GROUP2,

                    query.from_user.id

                )


                joined1 = member1.status not in [
                    "left",
                    "kicked"
                ]


                joined2 = member2.status not in [
                    "left",
                    "kicked"
                ]


                if joined1 and joined2:

                    users[uid]["group_reward"] = True

                    users[uid]["balance"] += 2

                    save_users(users)


                    text = (
                        "🎉 Verification Successful!\n\n"
                        "✅ +2 Points Added."
                    )


                else:

                    text = (
                        "❌ Please Join Both Groups First."
                    )


            except:

                text = (
                    "⚠️ Verification Failed.\n\n"
                    "Make sure bot is Admin in both groups."
                )


        await query.edit_message_text(

            text,

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )
                ]

            ])

        )
            # ==========================
    # REFERRAL SYSTEM
    # ==========================

    elif query.data == "refer":

        bot = await context.bot.get_me()

        link = (
            f"https://t.me/{bot.username}"
            f"?start={query.from_user.id}"
        )


        users = get_user(
            query.from_user.id
        )

        uid = str(
            query.from_user.id
        )

        referrals = users[uid]["referrals"]


        await query.edit_message_text(

            "👥 Referral System\n\n"

            f"👤 Total Referrals : {referrals}\n\n"

            "🔗 Your Referral Link:\n\n"

            f"{link}\n\n"

            "🎁 Reward : +10 Points per referral.",


            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )

                ]

            ])

        )


    # ==========================
    # WITHDRAW MENU
    # ==========================

    elif query.data == "withdraw":

        balance = get_balance(
            query.from_user.id
        )


        if balance >= 100:

            status = (
                "✅ You can withdraw.\n"
                "Use /withdraw command."
            )

        else:

            need = 100 - balance

            status = (
                f"❌ Need {need} more points."
            )


        await query.edit_message_text(

            "💸 Withdraw\n\n"

            f"💰 Balance : {balance} Points\n\n"

            "💵 Minimum Withdraw : 100 Points\n\n"

            f"{status}",


            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )

                ]

            ])

        )


    # ==========================
    # HELP MENU
    # ==========================

    elif query.data == "help":

        await query.edit_message_text(

            "❓ Help Menu\n\n"

            "💰 Earn = Complete Tasks\n"

            "🎁 Daily Bonus = Every 24 Hours\n"

            "👥 Referral = Invite Friends\n"

            "💳 Balance = Check Points\n"

            "💸 Withdraw = Minimum 100 Points",


            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )

                ]

            ])

        )
        # ==========================
# ADMIN PANEL
# ==========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        return


    users = load_users()


    total_users = len(users)


    total_points = sum(
        users[uid]["balance"]
        for uid in users
    )


    await update.message.reply_text(

        "👑 Admin Panel\n\n"

        f"👥 Total Users : {total_users}\n"

        f"💰 Total Points : {total_points}"

    )


# ==========================
# ADD BALANCE ADMIN
# ==========================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        return


    if len(context.args) != 2:

        await update.message.reply_text(

            "Usage:\n/add USER_ID AMOUNT"

        )

        return


    user_id = context.args[0]

    amount = int(context.args[1])


    users = load_users()


    if user_id not in users:

        await update.message.reply_text(

            "❌ User Not Found."

        )

        return


    users[user_id]["balance"] += amount


    save_users(users)


    await update.message.reply_text(

        "✅ Balance Added Successfully."

    )


# ==========================
# REMOVE BALANCE ADMIN
# ==========================

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        return


    if len(context.args) != 2:

        await update.message.reply_text(

            "Usage:\n/remove USER_ID AMOUNT"

        )

        return


    user_id = context.args[0]

    amount = int(context.args[1])


    users = load_users()


    if user_id not in users:

        await update.message.reply_text(

            "❌ User Not Found."

        )

        return


    users[user_id]["balance"] -= amount


    if users[user_id]["balance"] < 0:

        users[user_id]["balance"] = 0


    save_users(users)


    await update.message.reply_text(

        "✅ Balance Removed Successfully."

    )
    # ==========================
# BROADCAST SYSTEM
# ==========================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        return


    if not context.args:

        await update.message.reply_text(

            "Usage:\n/broadcast Your Message"

        )

        return


    message = " ".join(context.args)


    users = load_users()


    success = 0

    failed = 0


    for uid in users:

        try:

            await context.bot.send_message(

                chat_id=int(uid),

                text=message

            )

            success += 1


        except:

            failed += 1


    await update.message.reply_text(

        "📢 Broadcast Completed\n\n"

        f"✅ Sent : {success}\n"

        f"❌ Failed : {failed}"

    )


# ==========================
# USER STATS
# ==========================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(
        update.effective_user.id
    )


    users = get_user(uid)


    data = users[uid]


    await update.message.reply_text(

        "📊 Your Statistics\n\n"

        f"🆔 ID : {uid}\n"

        f"💰 Balance : {data['balance']}\n"

        f"👥 Referrals : {data['referrals']}\n"

        f"🎁 Group Reward : {data['group_reward']}"

    )
    # ==========================
# WITHDRAW REQUEST SYSTEM
# ==========================

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(
        update.effective_user.id
    )


    users = get_user(uid)


    balance = users[uid]["balance"]


    if balance < 100:

        await update.message.reply_text(

            "❌ Minimum Withdraw is 100 Points."

        )

        return


    if len(context.args) != 1:

        await update.message.reply_text(

            "Usage:\n/withdraw YOUR_NUMBER"

        )

        return


    number = context.args[0]


    await context.bot.send_message(

        chat_id=ADMIN_ID,

        text=(

            "💸 New Withdraw Request\n\n"

            f"👤 User ID : {uid}\n"

            f"📱 Number : {number}\n"

            f"💰 Amount : {balance} Points"

        )

    )


    users[uid]["balance"] = 0


    save_users(users)


    await update.message.reply_text(

        "✅ Withdraw Request Sent.\n\n"

        "Please wait for Admin Approval."

    )


# ==========================
# USER INFO ADMIN
# ==========================

async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        return


    if len(context.args) != 1:

        await update.message.reply_text(

            "Usage:\n/userinfo USER_ID"

        )

        return


    user_id = context.args[0]


    users = load_users()


    if user_id not in users:

        await update.message.reply_text(

            "❌ User Not Found."

        )

        return


    user = users[user_id]


    await update.message.reply_text(

        "👤 User Information\n\n"

        f"🆔 ID : {user_id}\n"

        f"💰 Balance : {user['balance']}\n"

        f"👥 Referrals : {user['referrals']}\n"

        f"🎁 Group Reward : {user['group_reward']}"

        )
        # ==========================
# LEADERBOARD SYSTEM
# ==========================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    users = load_users()


    top_users = sorted(

        users.items(),

        key=lambda x: x[1]["balance"],

        reverse=True

    )[:10]


    text = "🏆 Top 10 Users\n\n"


    rank = 1


    for uid, data in top_users:


        text += (

            f"{rank}. 👤 {uid}\n"

            f"💰 {data['balance']} Points\n\n"

        )


        rank += 1


    await update.message.reply_text(text)



# ==========================
# USER LIST ADMIN
# ==========================

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        return


    data = load_users()


    text = "👥 Registered Users\n\n"


    count = 0


    for uid in data:


        count += 1


        text += f"{count}. {uid}\n"


        if count == 50:

            break



    text += f"\n📊 Total Users : {len(data)}"



    await update.message.reply_text(text)



# ==========================
# DELETE USER ADMIN
# ==========================

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        return


    if len(context.args) != 1:


        await update.message.reply_text(

            "Usage:\n/delete USER_ID"

        )

        return



    user_id = context.args[0]


    data = load_users()



    if user_id not in data:


        await update.message.reply_text(

            "❌ User Not Found."

        )

        return



    del data[user_id]


    save_users(data)



    await update.message.reply_text(

        "✅ User Deleted Successfully."

    )
    # ==========================
# BOT INFO
# ==========================

async def botinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    users = load_users()


    total_users = len(users)


    total_points = sum(

        user["balance"]

        for user in users.values()

    )


    await update.message.reply_text(

        "🤖 Unlimited Energy Bot\n\n"

        f"👥 Total Users : {total_users}\n"

        f"💰 Total Points : {total_points}\n\n"

        "🎁 Daily Bonus : +5\n"

        "👥 Referral Reward : +10\n"

        "📢 Group Reward : +2\n"

        "💸 Minimum Withdraw : 100 Points"

    )



# ==========================
# MY ID COMMAND
# ==========================

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "🆔 Your Telegram ID:\n\n"

        f"{update.effective_user.id}"

    )



# ==========================
# BACKUP SYSTEM ADMIN
# ==========================

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        return


    users = load_users()


    with open("users_backup.json", "w") as f:

        json.dump(

            users,

            f,

            indent=4

        )


    await update.message.reply_text(

        "✅ Backup Created Successfully."

    )
    # ==========================
# PING COMMAND
# ==========================

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):

    start_time = time.time()


    msg = await update.message.reply_text(

        "🏓 Pinging..."

    )


    end_time = time.time()


    ms = round(

        (end_time - start_time) * 1000

    )


    await msg.edit_text(

        "🏓 Pong!\n\n"

        f"⚡ Speed : {ms} ms"

    )



# ==========================
# UPTIME SYSTEM
# ==========================

BOT_START = time.time()



async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):

    seconds = int(

        time.time() - BOT_START

    )


    days = seconds // 86400

    hours = (seconds % 86400) // 3600

    minutes = (seconds % 3600) // 60

    seconds = seconds % 60



    await update.message.reply_text(

        "⏳ Bot Uptime\n\n"

        f"📅 Days : {days}\n"

        f"🕐 Hours : {hours}\n"

        f"⏰ Minutes : {minutes}\n"

        f"⏱ Seconds : {seconds}"

    )



# ==========================
# PROFILE SYSTEM
# ==========================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(

        update.effective_user.id

    )


    users = get_user(uid)


    data = users[uid]



    await update.message.reply_text(

        "👤 Your Profile\n\n"

        f"🆔 ID : {uid}\n"

        f"💰 Balance : {data['balance']} Points\n"

        f"👥 Referrals : {data['referrals']}\n"

        f"🎁 Group Reward : {data['group_reward']}"

    )
    # ==========================
# USER RANK SYSTEM
# ==========================

def get_rank(balance):

    if balance >= 10000:

        return "💎 Diamond"


    elif balance >= 5000:

        return "🥇 Gold"


    elif balance >= 1000:

        return "🥈 Silver"


    elif balance >= 500:

        return "🥉 Bronze"


    else:

        return "🔰 Beginner"



# ==========================
# RANK COMMAND
# ==========================

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(

        update.effective_user.id

    )


    users = get_user(uid)


    balance = users[uid]["balance"]


    user_rank = get_rank(balance)



    await update.message.reply_text(

        "🏆 Your Rank\n\n"

        f"💰 Balance : {balance} Points\n"

        f"🎖 Rank : {user_rank}"

    )



# ==========================
# DAILY STATUS
# ==========================

async def dailystatus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(

        update.effective_user.id

    )


    users = get_user(uid)


    last = users[uid]["last_daily"]


    if last == 0:


        await update.message.reply_text(

            "🎁 Daily Bonus Status\n\n"

            "✅ You can claim now."

        )

        return



    now = int(time.time())


    remaining = 86400 - (now - last)



    if remaining <= 0:


        await update.message.reply_text(

            "🎁 Daily Bonus Status\n\n"

            "✅ Your bonus is ready."

        )


    else:


        hours = remaining // 3600


        minutes = (remaining % 3600) // 60



        await update.message.reply_text(

            "⏳ Daily Bonus Status\n\n"

            f"Try again after:\n"

            f"{hours} Hours {minutes} Minutes"

        )



# ==========================
# ACTIVITY LOG
# ==========================

async def activity(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(

        update.effective_user.id

    )


    users = get_user(uid)



    if "activity" not in users[uid]:

        users[uid]["activity"] = []



    users[uid]["activity"].append(

        {

            "action": "Used Bot",

            "time": time.strftime(

                "%d-%m-%Y %H:%M:%S"

            )

        }

    )


    users[uid]["activity"] = users[uid]["activity"][-10:]


    save_users(users)



    text = "📜 Your Recent Activity\n\n"



    for item in users[uid]["activity"]:


        text += (

            f"• {item['action']}\n"

            f"  🕒 {item['time']}\n\n"

        )



    await update.message.reply_text(text)
    # ==========================
# HANDLERS
# ==========================

app = Application.builder().token(TOKEN).build()

# ==========================
# KEEP WEB SERVER FOR RENDER
# ==========================

web = Flask(__name__)

@web.route("/")
def home():
    return "Unlimited Energy Bot is Running!"

def run_web():
    web.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

# USER COMMANDS

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("stats", stats)
)

app.add_handler(
    CommandHandler("profile", profile)
)

app.add_handler(
    CommandHandler("rank", rank)
)

app.add_handler(
    CommandHandler("dailystatus", dailystatus)
)

app.add_handler(
    CommandHandler("activity", activity)
)

app.add_handler(
    CommandHandler("leaderboard", leaderboard)
)

app.add_handler(
    CommandHandler("myid", myid)
)

app.add_handler(
    CommandHandler("ping", ping)
)

app.add_handler(
    CommandHandler("uptime", uptime)
)


# ADMIN COMMANDS

app.add_handler(
    CommandHandler("admin", admin)
)

app.add_handler(
    CommandHandler("add", add)
)

app.add_handler(
    CommandHandler("remove", remove)
)

app.add_handler(
    CommandHandler("broadcast", broadcast)
)

app.add_handler(
    CommandHandler("userinfo", userinfo)
)

app.add_handler(
    CommandHandler("users", users)
)

app.add_handler(
    CommandHandler("delete", delete)
)

app.add_handler(
    CommandHandler("backup", backup)
)


# BUTTON SYSTEM

app.add_handler(
    CallbackQueryHandler(callbacks)
)


# ==========================
# START BOT
# ==========================

print("==============================")
print("✅ Unlimited Energy Bot Started")
print("==============================")

threading.Thread(target=run_web).start()

app.run_polling()
