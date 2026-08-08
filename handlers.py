import time
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database import (
    create_user,
    get_user,
    update_user,
    leaderboard,
)

from config import (
    GROUPS,
    DAILY_BONUS,
    DAILY_XP,
    REFERRAL_REWARD,
    REFERRAL_XP,
    GROUP_JOIN_REWARD,
    XP_PER_LEVEL,
    BRONZE_REQUIRED,
    SILVER_REQUIRED,
    GOLD_REQUIRED,
    DIAMOND_REQUIRED,
    MAX_ENERGY,
    ACTIVITY_LIMIT,
)


# ==================================================
# LOGGING
# ==================================================

logger = logging.getLogger(__name__)


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def add_activity(user_id, action):
    """
    Add a small activity entry to user's history.
    """

    user = get_user(user_id)

    activities = user.get("activity", [])

    activities.append(
        {
            "action": action,
            "time": int(time.time()),
        }
    )

    activities = activities[-ACTIVITY_LIMIT:]

    update_user(
        user_id,
        {
            "activity": activities,
            "last_login": int(time.time()),
        },
    )


def calculate_rank(balance):
    """
    Calculate rank from balance.
    """

    if balance >= DIAMOND_REQUIRED:
        return "💎 Diamond"

    if balance >= GOLD_REQUIRED:
        return "🥇 Gold"

    if balance >= SILVER_REQUIRED:
        return "🥈 Silver"

    if balance >= BRONZE_REQUIRED:
        return "🥉 Bronze"

    return "🔰 Beginner"


def calculate_level(xp):
    """
    Calculate user level from XP.
    """

    level = (xp // XP_PER_LEVEL) + 1

    return max(level, 1)


def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Earn",
                callback_data="earn",
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Balance",
                callback_data="balance",
            ),
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile",
            ),
        ],

        [
            InlineKeyboardButton(
                "👥 Referral",
                callback_data="refer",
            ),
            InlineKeyboardButton(
                "🏆 Rank",
                callback_data="rank",
            ),
        ],

        [
            InlineKeyboardButton(
                "💸 Withdraw",
                callback_data="withdraw",
            )
        ],

        [
            InlineKeyboardButton(
                "👑 Premium",
                callback_data="premium",
            )
        ],

        [
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help",
            )
        ],

    ]

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# FORCE JOIN MENU
# ==================================================

def force_join_menu():

    keyboard = []

    for index, group in enumerate(
        GROUPS,
        start=1,
    ):

        keyboard.append(

            [
                InlineKeyboardButton(
                    f"📢 Join Group {index}",
                    url=(
                        "https://t.me/"
                        f"{group.replace('@', '')}"
                    ),
                )
            ]

        )

    keyboard.append(

        [
            InlineKeyboardButton(
                "✅ Verify Join",
                callback_data="verify_join",
            )
        ]

    )

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# CHECK FORCE JOIN
# ==================================================

async def check_force_join(
    user_id,
    context,
):

    not_joined = []

    for group in GROUPS:

        try:

            member = await context.bot.get_chat_member(
                group,
                user_id,
            )

            if member.status in (
                "left",
                "kicked",
            ):

                not_joined.append(group)

        except Exception as error:

            logger.error(
                "Force join check failed | group=%s | user=%s | error=%s",
                group,
                user_id,
                error,
            )

            not_joined.append(group)

    return not_joined


# ==================================================
# START COMMAND
# ==================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    user = update.effective_user

    user_id = user.id

    logger.info(
        "START COMMAND RECEIVED | user_id=%s",
        user_id,
    )

    # --------------------------------------------------
    # Check whether user already exists
    # --------------------------------------------------

    existing_user = get_user(user_id)

    is_new_user = (
        existing_user.get("created_at") is None
    )

    # create/get user safely
    create_user(user_id)

    # --------------------------------------------------
    # Referral detection
    # --------------------------------------------------

    referral_id = None

    if context.args:

        referral_arg = context.args[0].strip()

        if referral_arg.startswith("ref_"):

            try:

                referral_id = int(
                    referral_arg.replace(
                        "ref_",
                        "",
                        1,
                    )
                )

            except ValueError:

                referral_id = None

    # --------------------------------------------------
    # Apply referral only for a genuinely new user
    # --------------------------------------------------

    if referral_id:

        if referral_id != user_id:

            current_user = get_user(user_id)

            already_referred = current_user.get(
                "referred_by"
            )

            if not already_referred:

                referrer = get_user(referral_id)

                if referrer:

                    update_user(
                        user_id,
                        {
                            "referred_by": referral_id,
                        },
                    )

                    referrer_count = (
                        referrer.get(
                            "referrals",
                            0,
                        )
                        + 1
                    )

                    referrer_earn = (
                        referrer.get(
                            "referral_earn",
                            0,
                        )
                        + REFERRAL_REWARD
                    )

                    referrer_balance = (
                        referrer.get(
                            "balance",
                            0,
                        )
                        + REFERRAL_REWARD
                    )

                    referrer_xp = (
                        referrer.get(
                            "xp",
                            0,
                        )
                        + REFERRAL_XP
                    )

                    referrer_level = calculate_level(
                        referrer_xp
                    )

                    update_user(
                        referral_id,
                        {
                            "referrals": referrer_count,
                            "referral_earn": referrer_earn,
                            "balance": referrer_balance,
                            "total_earned": (
                                referrer.get(
                                    "total_earned",
                                    0,
                                )
                                + REFERRAL_REWARD
                            ),
                            "xp": referrer_xp,
                            "level": referrer_level,
                        },
                    )

                    add_activity(
                        referral_id,
                        f"Referral reward +{REFERRAL_REWARD} Points",
                    )

    # --------------------------------------------------
    # Login update
    # --------------------------------------------------

    update_user(
        user_id,
        {
            "last_login": int(time.time()),
        },
    )

    # --------------------------------------------------
    # Force Join
    # --------------------------------------------------

    not_joined = await check_force_join(
        user_id,
        context,
    )

    if not_joined:

        await update.message.reply_text(

            "🔒 **JOIN REQUIRED**\n\n"

            "Before using Unlimited Energy Bot, "
            "please join all of our official groups.\n\n"

            "After joining all groups, press "
            "✅ Verify Join.",

            reply_markup=force_join_menu(),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------
    # Home
    # --------------------------------------------------

    await update.message.reply_text(

        f"👋 Welcome {user.first_name}!\n\n"

        "🚀 **Unlimited Energy Bot V2**\n\n"

        "💰 Earn Points\n"
        "🎁 Complete Tasks\n"
        "👥 Invite Friends\n"
        "🎡 Play Rewards Games\n"
        "👑 Premium & VIP\n"
        "💸 Withdraw Rewards\n\n"

        "👇 Choose an option below.",

        reply_markup=main_menu(),

        parse_mode="Markdown",
    )

    add_activity(
        user_id,
        "Opened bot",
    )


# ==================================================
# PROFILE COMMAND
# ==================================================

async def profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    balance = user.get("balance", 0)

    bonus = user.get(
        "bonus_balance",
        0,
    )

    premium_balance = user.get(
        "premium_balance",
        0,
    )

    referrals = user.get(
        "referrals",
        0,
    )

    xp = user.get(
        "xp",
        0,
    )

    level = user.get(
        "level",
        1,
    )

    rank = user.get(
        "rank",
        calculate_rank(balance),
    )

    premium = user.get(
        "premium",
        False,
    )

    vip = user.get(
        "vip",
        False,
    )

    premium_status = (
        "✅ Active"
        if premium
        else "❌ Inactive"
    )

    vip_status = (
        "✅ Active"
        if vip
        else "❌ Inactive"
    )

    await update.message.reply_text(

        "👤 **YOUR PROFILE**\n\n"

        f"🆔 ID: `{user_id}`\n\n"

        f"💰 Balance: {balance} Points\n"
        f"🎁 Bonus: {bonus} Points\n"
        f"💎 Premium Balance: {premium_balance} Points\n\n"

        f"👥 Referrals: {referrals}\n"
        f"⭐ XP: {xp}\n"
        f"🏆 Level: {level}\n"
        f"🎖 Rank: {rank}\n\n"

        f"👑 Premium: {premium_status}\n"
        f"💎 VIP: {vip_status}",

        parse_mode="Markdown",
    )


# ==================================================
# BALANCE COMMAND
# ==================================================

async def balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    balance_value = user.get(
        "balance",
        0,
    )

    bonus = user.get(
        "bonus_balance",
        0,
    )

    premium_balance = user.get(
        "premium_balance",
        0,
    )

    total = (
        balance_value
        + bonus
        + premium_balance
    )

    await update.message.reply_text(

        "💰 **YOUR WALLET**\n\n"

        f"💰 Earn Balance: {balance_value} Points\n"
        f"🎁 Bonus Balance: {bonus} Points\n"
        f"💎 Premium Balance: {premium_balance} Points\n\n"

        f"💵 **Total Balance: {total} Points**",

        parse_mode="Markdown",
    )


# ==================================================
# RANK COMMAND
# ==================================================

async def rank(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    balance_value = user.get(
        "balance",
        0,
    )

    xp = user.get(
        "xp",
        0,
    )

    level = calculate_level(xp)

    user_rank = calculate_rank(
        balance_value
    )

    update_user(
        user_id,
        {
            "rank": user_rank,
            "level": level,
        },
    )

    await update.message.reply_text(

        "🏆 **YOUR RANK**\n\n"

        f"💰 Balance: {balance_value} Points\n"
        f"🎖 Rank: {user_rank}\n"
        f"🏆 Level: {level}\n"
        f"⭐ XP: {xp}\n\n"

        "🚀 Keep earning to reach the next rank!",

        parse_mode="Markdown",
    )


# ==================================================
# HELP
# ==================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(

        "❓ **HELP CENTER**\n\n"

        "💰 Earn — Complete available tasks\n"
        "💳 Balance — Check your wallet\n"
        "👤 Profile — View your account\n"
        "👥 Referral — Invite friends\n"
        "🏆 Rank — Check your progress\n"
        "🎁 Daily — Claim daily reward\n"
        "🎡 Games — Spin, Scratch & Lucky Box\n"
        "💸 Withdraw — Request withdrawal\n"
        "👑 Premium — Premium features\n\n"

        "🆘 Need help?\n"
        "Contact the Admin.",

        parse_mode="Markdown",
    )


# ==================================================
# STATS
# ==================================================

async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    total_earned = user.get(
        "total_earned",
        0,
    )

    total_withdraw = user.get(
        "total_withdraw",
        0,
    )

    referrals = user.get(
        "referrals",
        0,
    )

    offers = user.get(
        "offer_completed",
        0,
    )

    shortlinks = user.get(
        "shortlink_completed",
        0,
    )

    streak = user.get(
        "daily_streak",
        0,
    )

    await update.message.reply_text(

        "📊 **YOUR STATISTICS**\n\n"

        f"💰 Total Earned: {total_earned} Points\n"
        f"💸 Total Withdrawn: {total_withdraw} Points\n"
        f"👥 Referrals: {referrals}\n"
        f"🎯 Offers Completed: {offers}\n"
        f"🔗 Shortlinks Completed: {shortlinks}\n"
        f"🔥 Daily Streak: {streak} Days",

        parse_mode="Markdown",
    )


# ==================================================
# LEADERBOARD
# ==================================================

async def leaderboard_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    top_users = leaderboard()

    if not top_users:

        await update.message.reply_text(
            "🏆 Leaderboard is empty."
        )

        return

    text = "🏆 **TOP 10 USERS**\n\n"

    medals = [
        "🥇",
        "🥈",
        "🥉",
    ]

    for position, user in enumerate(
        top_users,
        start=1,
    ):

        user_id = user.get(
            "user_id",
            "Unknown",
        )

        balance_value = user.get(
            "balance",
            0,
        )

        if position <= 3:

            icon = medals[
                position - 1
            ]

        else:

            icon = f"{position}."

        text += (
            f"{icon} "
            f"`{user_id}`\n"
            f"   💰 {balance_value} Points\n\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
    )


# ==================================================
# ACTIVITY
# ==================================================

async def activity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    activities = user.get(
        "activity",
        [],
    )

    if not activities:

        await update.message.reply_text(

            "📜 **YOUR ACTIVITY**\n\n"
            "No activity recorded yet.",

            parse_mode="Markdown",
        )

        return

    text = "📜 **YOUR RECENT ACTIVITY**\n\n"

    for item in activities[-ACTIVITY_LIMIT:]:

        action = item.get(
            "action",
            "Unknown Action",
        )

        activity_time = item.get(
            "time",
            "Unknown Time",
        )

        text += (
            f"• {action}\n"
            f"  🕒 {activity_time}\n\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
    )


# ==================================================
# DAILY STATUS
# ==================================================

async def dailystatus(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    last_daily = user.get(
        "last_daily",
        0,
    )

    if last_daily == 0:

        await update.message.reply_text(

            "🎁 **DAILY BONUS**\n\n"
            f"✅ Your daily bonus is ready!\n\n"
            f"🎁 Reward: {DAILY_BONUS} Points",

            parse_mode="Markdown",
        )

        return

    now = int(time.time())

    remaining = (
        86400
        - (now - last_daily)
    )

    if remaining <= 0:

        await update.message.reply_text(

            "🎁 **DAILY BONUS**\n\n"
            f"✅ Your bonus is ready!\n\n"
            f"🎁 Reward: {DAILY_BONUS} Points",

            parse_mode="Markdown",
        )

        return

    hours = remaining // 3600

    minutes = (
        remaining % 3600
    ) // 60

    await update.message.reply_text(

        "⏳ **DAILY BONUS**\n\n"

        "Your bonus has already been claimed.\n\n"

        f"🕐 Try again after:\n"
        f"{hours} Hours {minutes} Minutes",

        parse_mode="Markdown",
    )


# ==================================================
# MY ID
# ==================================================

async def myid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    await update.message.reply_text(

        "🆔 **YOUR TELEGRAM ID**\n\n"
        f"`{user_id}`",

        parse_mode="Markdown",
    )


# ==================================================
# VERIFY JOIN
# ==================================================

async def verify_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user.get(
        "banned",
        False,
    ):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    not_joined = await check_force_join(
        user_id,
        context,
    )

    if not_joined:

        await query.edit_message_text(

            "❌ **JOIN NOT COMPLETED**\n\n"

            "You still haven't joined all "
            "required groups.\n\n"

            "Join all groups and press "
            "✅ Verify Join again.",

            reply_markup=force_join_menu(),

            parse_mode="Markdown",
        )

        return

    #--------------------------------------------------
    # Group reward
    # --------------------------------------------------

    group_reward_given = user.get(
        "group_reward",
        False,
    )

    if not group_reward_given:

        current_balance = user.get(
            "balance",
            0,
        )

        current_xp = user.get(
            "xp",
            0,
        )

        new_xp = (
            current_xp
            + DAILY_XP
        )

        update_user(
            user_id,
            {
                "balance": (
                    current_balance
                    + GROUP_JOIN_REWARD
                ),
                "total_earned": (
                    user.get(
                        "total_earned",
                        0,
                    )
                    + GROUP_JOIN_REWARD
                ),
                "xp": new_xp,
                "level": calculate_level(
                    new_xp
                ),
                "group_reward": True,
            },
        )

        add_activity(
            user_id,
            f"Group join reward +{GROUP_JOIN_REWARD} Points",
        )

        reward_text = (
            f"\n\n🎁 Group Reward: "
            f"+{GROUP_JOIN_REWARD} Points"
        )

    else:

        reward_text = ""

    await query.edit_message_text(

        "✅ **VERIFICATION SUCCESSFUL!**\n\n"

        "🎉 You can now use "
        "Unlimited Energy Bot."

        f"{reward_text}",

        reply_markup=main_menu(),

        parse_mode="Markdown",
    )


# ==================================================
# HANDLER EXPORTS
# ==================================================

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
