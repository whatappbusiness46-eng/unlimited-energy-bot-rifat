import time
import time
import logging

logger = logging.getLogger(__name__)

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
)

from database import (
    create_user,
    get_user,
    update_user,
    leaderboard,
)

from config import GROUPS


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
            ),
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Referral",
                callback_data="refer"
            ),
            InlineKeyboardButton(
                "🏆 Rank",
                callback_data="rank"
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
                "👑 Premium",
                callback_data="premium"
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
# FORCE JOIN MENU
# ==========================

def force_join_menu():

    keyboard = []

    for index, group in enumerate(GROUPS, start=1):

        keyboard.append(

            [

                InlineKeyboardButton(

                    f"📢 Join Group {index}",

                    url=f"https://t.me/{group.replace('@','')}"

                )

            ]

        )

    keyboard.append(

        [

            InlineKeyboardButton(

                "✅ Verify Join",

                callback_data="verify_join"

            )

        ]

    )

    return InlineKeyboardMarkup(keyboard)
    
# ==========================
# START COMMAND
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    create_user(user.id)

    # ==========================
    # FORCE JOIN CHECK
    # ==========================

    not_joined = []

    for group in GROUPS:

        try:

            member = await context.bot.get_chat_member(
                group,
                user.id
            )

            if member.status in ["left", "kicked"]:

                not_joined.append(group)

        except:

            not_joined.append(group)

    if not_joined:

        await update.message.reply_text(

            "🔒 Before using this bot,\n"
            "please join all our Official Groups.",

            reply_markup=force_join_menu()

        )

        return

    # ==========================
    # HOME PAGE
    # ==========================

    await update.message.reply_text(

        f"👋 Welcome {user.first_name}!\n\n"

        "🚀 Welcome to Unlimited Energy Bot V2\n\n"

        "💰 Earn Points\n"
        "🎁 Complete Tasks\n"
        "👥 Invite Friends\n"
        "💸 Withdraw Rewards\n\n"

        "👇 Choose an option below.",

        reply_markup=main_menu()

    )
    
# ==========================
# PROFILE COMMAND
# ==========================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user = get_user(user_id)

    balance = user.get("balance", 0)
    bonus_balance = user.get("bonus_balance", 0)
    premium_balance = user.get("premium_balance", 0)

    referrals = user.get("referrals", 0)
    xp = user.get("xp", 0)
    level = user.get("level", 1)
    rank = user.get("rank", "🔰 Beginner")

    premium = user.get("premium", False)
    vip = user.get("vip", False)

    premium_status = "✅ Active" if premium else "❌ Inactive"
    vip_status = "✅ Active" if vip else "❌ Inactive"

    await update.message.reply_text(

        "👤 YOUR PROFILE\n\n"

        f"🆔 ID : {user_id}\n\n"

        f"💰 Balance : {balance} Points\n"
        f"🎁 Bonus Balance : {bonus_balance} Points\n"
        f"💎 Premium Balance : {premium_balance} Points\n\n"

        f"👥 Referrals : {referrals}\n"
        f"⭐ XP : {xp}\n"
        f"🏆 Level : {level}\n"
        f"🎖 Rank : {rank}\n\n"

        f"👑 Premium : {premium_status}\n"
        f"💎 VIP : {vip_status}"

    )


# ==========================
# BALANCE COMMAND
# ==========================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user = get_user(user_id)

    balance = user.get("balance", 0)
    bonus = user.get("bonus_balance", 0)
    premium_balance = user.get("premium_balance", 0)

    total = balance + bonus + premium_balance

    await update.message.reply_text(

        "💰 YOUR WALLET\n\n"

        f"💰 Earn Balance : {balance} Points\n"
        f"🎁 Bonus Balance : {bonus} Points\n"
        f"💎 Premium Balance : {premium_balance} Points\n\n"

        f"💵 Total Balance : {total} Points"

    )


# ==========================
# RANK COMMAND
# ==========================

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user = get_user(user_id)

    balance = user.get("balance", 0)

    if balance >= 10000:
        user_rank = "💎 Diamond"

    elif balance >= 6000:
        user_rank = "🥇 Gold"

    elif balance >= 2000:
        user_rank = "🥈 Silver"

    elif balance >= 600:
        user_rank = "🥉 Bronze"

    else:
        user_rank = "🔰 Beginner"

    if user.get("rank") != user_rank:

        update_user(
            user_id,
            {"rank": user_rank}
        )

    await update.message.reply_text(

        "🏆 YOUR RANK\n\n"

        f"💰 Balance : {balance} Points\n"
        f"🎖 Rank : {user_rank}"

    )


# ==========================
# HELP COMMAND
# ==========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "❓ HELP CENTER\n\n"

        "💰 /balance - Check your balance\n"
        "👤 /profile - View your profile\n"
        "🏆 /rank - Check your rank\n"
        "📊 /stats - View statistics\n"
        "🏅 /leaderboard - Top users\n"
        "📜 /activity - Recent activity\n"
        "🎁 /dailystatus - Daily bonus status\n"
        "🆔 /myid - Your Telegram ID\n\n"

        "💡 Use the buttons in the main menu "
        "to access earning, premium and withdrawal features."

    )

# ==========================
# STATS COMMAND
# ==========================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user = get_user(user_id)

    total_earned = user.get("total_earned", 0)
    total_withdraw = user.get("total_withdraw", 0)
    referrals = user.get("referrals", 0)
    offers = user.get("offer_completed", 0)
    shortlinks = user.get("shortlink_completed", 0)
    streak = user.get("daily_streak", 0)

    await update.message.reply_text(

        "📊 YOUR STATISTICS\n\n"

        f"💰 Total Earned : {total_earned} Points\n"
        f"💸 Total Withdrawn : {total_withdraw} Points\n"
        f"👥 Referrals : {referrals}\n"
        f"🎯 Offers Completed : {offers}\n"
        f"🔗 Shortlinks Completed : {shortlinks}\n"
        f"🔥 Daily Streak : {streak} Days"

    )


# ==========================
# LEADERBOARD COMMAND
# ==========================

async def leaderboard_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    top_users = leaderboard()

    if not top_users:

        await update.message.reply_text(
            "🏆 Leaderboard is empty."
        )

        return

    text = "🏆 TOP 10 USERS\n\n"

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for position, user in enumerate(top_users, start=1):

        user_id = user.get("user_id", "Unknown")
        balance_value = user.get("balance", 0)

        if position <= 3:
            icon = medals[position - 1]
        else:
            icon = f"{position}."

        text += (
            f"{icon} "
            f"ID: {user_id}\n"
            f"   💰 {balance_value} Points\n\n"
        )

    await update.message.reply_text(text)


# ==========================
# ACTIVITY COMMAND
# ==========================

async def activity(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user = get_user(user_id)

    activities = user.get("activity", [])

    if not activities:

        await update.message.reply_text(

            "📜 YOUR ACTIVITY\n\n"
            "No activity recorded yet."

        )

        return

    text = "📜 YOUR RECENT ACTIVITY\n\n"

    for item in activities[-10:]:

        action = item.get(
            "action",
            "Unknown Action"
        )

        activity_time = item.get(
            "time",
            "Unknown Time"
        )

        text += (
            f"• {action}\n"
            f"  🕒 {activity_time}\n\n"
        )

    await update.message.reply_text(text)


# ==========================
# DAILY STATUS COMMAND
# ==========================

async def dailystatus(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    last_daily = user.get("last_daily", 0)

    if last_daily == 0:

        await update.message.reply_text(

            "🎁 DAILY BONUS STATUS\n\n"
            "✅ Your daily bonus is ready!"

        )

        return

    now = int(time.time())

    remaining = 86400 - (now - last_daily)

    if remaining <= 0:

        await update.message.reply_text(

            "🎁 DAILY BONUS STATUS\n\n"
            "✅ Your bonus is ready to claim!"

        )

        return

    hours = remaining // 3600

    minutes = (remaining % 3600) // 60

    await update.message.reply_text(

        "⏳ DAILY BONUS STATUS\n\n"

        f"Try again after:\n"
        f"🕐 {hours} Hours "
        f"{minutes} Minutes"

        )
    
# ==========================
# MY ID COMMAND
# ==========================

async def myid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    await update.message.reply_text(
        f"🆔 Your Telegram ID:\n\n"
        f"`{user_id}`",
        parse_mode="Markdown"
    )


# ==========================
# VERIFY JOIN
# ==========================

async def verify_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    not_joined = []

    for group in GROUPS:

        try:

            member = await context.bot.get_chat_member(
                group,
                user_id
            )

            if member.status in ["left", "kicked"]:

                not_joined.append(group)

        except Exception:

            not_joined.append(group)

    if not_joined:

        await query.edit_message_text(

            "❌ You haven't joined all the required groups yet.\n\n"
            "Please join all groups and press "
            "✅ Verify Join again.",

            reply_markup=force_join_menu()

        )

        return

    await query.edit_message_text(

        "✅ Verification successful!\n\n"
        "🎉 You can now use Unlimited Energy Bot.",

        reply_markup=main_menu()

    )

# ==========================
# HANDLER EXPORTS
# ==========================

HANDLER_FUNCTIONS = {
    "start": start,
    "profile": profile,
    "balance": balance,
    "rank": rank,
    "stats": stats,
    "leaderboard": leaderboard_command,
    "activity": activity,
    "dailystatus": dailystatus,
    "help": help_command,
    "myid": myid,
    "verify_join": verify_join,
}
