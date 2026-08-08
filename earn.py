import random
import time
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import (
    DAILY_BONUS,
)

from database import (
    get_user,
    add_balance,
    add_bonus,
    add_xp,
    add_activity,
    update_user,
    use_energy,
)


logger = logging.getLogger(__name__)


# ==========================
# EARN MENU
# ==========================

def earn_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🎁 Daily Bonus",
                callback_data="daily_bonus"
            )
        ],

        [
            InlineKeyboardButton(
                "📋 Tasks",
                callback_data="tasks"
            ),

            InlineKeyboardButton(
                "🔗 Shortlinks",
                callback_data="shortlinks"
            )
        ],

        [
            InlineKeyboardButton(
                "🎡 Spin Wheel",
                callback_data="spin"
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 Lucky Box",
                callback_data="lucky_box"
            ),

            InlineKeyboardButton(
                "🎫 Scratch Card",
                callback_data="scratch"
            )
        ],

        [
            InlineKeyboardButton(
                "⚡ Energy",
                callback_data="energy"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


# ==========================
# BACK MENU
# ==========================

def earn_back_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Earn",
                callback_data="earn"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


# ==========================
# EARN PAGE
# ==========================

async def earn(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user.get("banned", False):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    await query.edit_message_text(

        "💰 EARN CENTER\n\n"

        "Choose a way to earn Points:\n\n"

        "🎁 Daily Bonus\n"
        "📋 Complete Tasks\n"
        "🔗 Complete Shortlinks\n"
        "🎡 Spin Wheel\n"
        "🎁 Open Lucky Box\n"
        "🎫 Scratch Card\n\n"

        "⚡ Some activities require Energy.",

        reply_markup=earn_menu()

    )


# ==========================
# DAILY BONUS
# ==========================

async def daily_bonus(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user.get("banned", False):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    now = int(time.time())

    last_daily = user.get(
        "last_daily",
        0
    )

    # 24 hour cooldown
    if last_daily:

        elapsed = now - last_daily

        if elapsed < 86400:

            remaining = 86400 - elapsed

            hours = remaining // 3600

            minutes = (
                remaining % 3600
            ) // 60

            await query.edit_message_text(

                "⏳ DAILY BONUS\n\n"

                "You have already claimed "
                "today's bonus.\n\n"

                f"🕐 Try again in "
                f"{hours}h {minutes}m.",

                reply_markup=earn_back_menu()

            )

            return

    streak = user.get(
        "daily_streak",
        0
    )

    # Continue streak if claimed within
    # 48 hours, otherwise reset.
    if last_daily:

        if now - last_daily <= 172800:

            streak += 1

        else:

            streak = 1

    else:

        streak = 1

    # Streak bonus
    streak_bonus = min(
        streak - 1,
        10
    )

    reward = DAILY_BONUS + streak_bonus

    add_bonus(
        user_id,
        reward
    )

    xp_result = add_xp(
        user_id,
        10
    )

    update_user(
        user_id,
        {
            "last_daily": now,
            "daily_streak": streak,
        }
    )

    add_activity(
        user_id,
        "🎁 Daily Bonus",
        reward
    )

    level_text = ""

    if xp_result["level_up"]:

        level_text = (
            f"\n🎉 LEVEL UP!\n"
            f"🏆 New Level: "
            f"{xp_result['level']}\n"
        )

    await query.edit_message_text(

        "🎁 DAILY BONUS CLAIMED!\n\n"

        f"💰 Reward: +{reward} Points\n"
        f"🔥 Daily Streak: {streak} Days\n"
        f"⭐ XP: +10\n"

        f"{level_text}\n"

        "Come back tomorrow for another bonus! 🚀",

        reply_markup=earn_back_menu()

    )


# ==========================
# TASKS
# ==========================

async def tasks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user.get("banned", False):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    await query.edit_message_text(

        "📋 TASK CENTER\n\n"

        "There are currently no external "
        "tasks available.\n\n"

        "🚀 New tasks will appear here "
        "when they are added by Admin.\n\n"

        "💡 Check back later!",

        reply_markup=earn_back_menu()

    )


# ==========================
# SHORTLINKS
# ==========================

async def shortlinks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user.get("banned", False):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    await query.edit_message_text(

        "🔗 SHORTLINK CENTER\n\n"

        "No shortlinks are currently available.\n\n"

        "🚀 Shortlink offers will appear "
        "here when configured by Admin.",

        reply_markup=earn_back_menu()

    )


# ==========================
# ENERGY
# ==========================

async def energy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user.get("banned", False):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    energy_value = user.get(
        "energy",
        100
    )

    max_energy = user.get(
        "max_energy",
        100
    )

    await query.edit_message_text(

        "⚡ ENERGY\n\n"

        f"⚡ Energy: "
        f"{energy_value}/{max_energy}\n\n"

        "Energy automatically regenerates "
        "over time.\n\n"

        "💡 Some earning activities use Energy.",

        reply_markup=earn_back_menu()

    )


# ==========================
# TEST TASK REWARD
# ==========================

async def claim_test_task(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user.get("banned", False):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    if not use_energy(
        user_id,
        1
    ):

        await query.edit_message_text(

            "⚡ NOT ENOUGH ENERGY\n\n"

            "You need at least "
            "1 Energy to complete this task.",

            reply_markup=earn_back_menu()

        )

        return

    reward = 10

    add_balance(
        user_id,
        reward
    )

    xp_result = add_xp(
        user_id,
        5
    )

    add_activity(
        user_id,
        "📋 Test Task Completed",
        reward
    )

    update_user(
        user_id,
        {
            "offer_completed": (
                user.get(
                    "offer_completed",
                    0
                ) + 1
            )
        }
    )

    level_text = ""

    if xp_result["level_up"]:

        level_text = (
            f"\n🎉 LEVEL UP!\n"
            f"🏆 New Level: "
            f"{xp_result['level']}\n"
        )

    await query.edit_message_text(

        "✅ TASK COMPLETED!\n\n"

        f"💰 Reward: +{reward} Points\n"
        "⚡ Energy Used: 1\n"
        "⭐ XP: +5\n"

        f"{level_text}",

        reply_markup=earn_back_menu()

    )


# ==========================
# HANDLER EXPORTS
# ==========================

EARN_HANDLERS = {

    "earn": earn,

    "daily_bonus": daily_bonus,

    "tasks": tasks,

    "shortlinks": shortlinks,

    "energy": energy,

    "claim_test_task": claim_test_task,

    }
