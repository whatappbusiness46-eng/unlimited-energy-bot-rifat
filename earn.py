import random
import time
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import DAILY_BONUS

from database import (
    get_user,
    add_balance,
    add_bonus,
    add_xp,
    add_activity,
    update_user,
    use_energy,
    use_spin_ticket,
    use_lucky_box,
    use_scratch_card,
)


logger = logging.getLogger(__name__)


# ==================================================
# EARN MENU
# ==================================================

def earn_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🎁 Daily Bonus",
                callback_data="daily_bonus",
            )
        ],

        [
            InlineKeyboardButton(
                "📋 Tasks",
                callback_data="tasks",
            ),
            InlineKeyboardButton(
                "🔗 Shortlinks",
                callback_data="shortlinks",
            ),
        ],

        [
            InlineKeyboardButton(
                "🎡 Spin Wheel",
                callback_data="spin",
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 Lucky Box",
                callback_data="lucky_box",
            ),
            InlineKeyboardButton(
                "🎫 Scratch Card",
                callback_data="scratch",
            ),
        ],

        [
            InlineKeyboardButton(
                "⚡ Energy",
                callback_data="energy",
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# BACK MENU
# ==================================================

def earn_back_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Earn",
                callback_data="earn",
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# EARN PAGE
# ==================================================

async def earn(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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

        reply_markup=earn_menu(),
    )


# ==================================================
# DAILY BONUS
# ==================================================

async def daily_bonus(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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
        0,
    )

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

                reply_markup=earn_back_menu(),
            )

            return

    streak = user.get(
        "daily_streak",
        0,
    )

    if last_daily:

        if now - last_daily <= 172800:

            streak += 1

        else:

            streak = 1

    else:

        streak = 1

    streak_bonus = min(
        streak - 1,
        10,
    )

    reward = DAILY_BONUS + streak_bonus

    add_bonus(
        user_id,
        reward,
    )

    xp_result = add_xp(
        user_id,
        10,
    )

    update_user(
        user_id,
        {
            "last_daily": now,
            "daily_streak": streak,
        },
    )

    add_activity(
        user_id,
        "🎁 Daily Bonus",
        reward,
    )

    level_text = ""

    if xp_result["level_up"]:

        level_text = (
            "\n🎉 LEVEL UP!\n"
            f"🏆 New Level: "
            f"{xp_result['level']}\n"
        )

    await query.edit_message_text(

        "🎁 DAILY BONUS CLAIMED!\n\n"

        f"💰 Reward: +{reward} Points\n"
        f"🔥 Daily Streak: {streak} Days\n"
        "⭐ XP: +10\n"

        f"{level_text}\n"

        "Come back tomorrow for another bonus! 🚀",

        reply_markup=earn_back_menu(),
    )


# ==================================================
# TASKS
# ==================================================

async def tasks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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

    keyboard = [

        [
            InlineKeyboardButton(
                "🎯 Complete Test Task",
                callback_data="claim_test_task",
            )
        ],

        [
            InlineKeyboardButton(
                "💰 Earn",
                callback_data="earn",
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ],
    ]

    await query.edit_message_text(

        "📋 TASK CENTER\n\n"

        "🎯 Test Task\n"
        "💰 Reward: +10 Points\n"
        "⚡ Energy Required: 1\n"
        "⭐ XP: +5\n\n"

        "Complete the task to receive "
        "your reward.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# ==================================================
# TEST TASK
# ==================================================

async def claim_test_task(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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
        1,
    ):

        await query.edit_message_text(

            "⚡ NOT ENOUGH ENERGY\n\n"

            "You need at least "
            "1 Energy to complete this task.",

            reply_markup=earn_back_menu(),
        )

        return

    reward = 10

    add_balance(
        user_id,
        reward,
    )

    xp_result = add_xp(
        user_id,
        5,
    )

    add_activity(
        user_id,
        "📋 Test Task Completed",
        reward,
    )

    update_user(
        user_id,
        {
            "offer_completed": (
                user.get(
                    "offer_completed",
                    0,
                )
                + 1
            )
        },
    )

    level_text = ""

    if xp_result["level_up"]:

        level_text = (
            "\n🎉 LEVEL UP!\n"
            f"🏆 New Level: "
            f"{xp_result['level']}\n"
        )

    await query.edit_message_text(

        "✅ TASK COMPLETED!\n\n"

        f"💰 Reward: +{reward} Points\n"
        "⚡ Energy Used: 1\n"
        "⭐ XP: +5\n"

        f"{level_text}",

        reply_markup=earn_back_menu(),
    )


# ==================================================
# SHORTLINKS
# ==================================================

async def shortlinks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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

        reply_markup=earn_back_menu(),
    )


# ==================================================
# ENERGY
# ==================================================

async def energy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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
        100,
    )

    max_energy = user.get(
        "max_energy",
        100,
    )

    await query.edit_message_text(

        "⚡ ENERGY\n\n"

        f"⚡ Energy: "
        f"{energy_value}/{max_energy}\n\n"

        "Energy automatically regenerates "
        "over time.\n\n"

        "💡 Some earning activities use Energy.",

        reply_markup=earn_back_menu(),
    )


# ==================================================
# SPIN WHEEL
# ==================================================

async def spin_wheel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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

    tickets = user.get(
        "spin_ticket",
        0,
    )

    if tickets <= 0:

        await query.edit_message_text(

            "🎡 SPIN WHEEL\n\n"

            "❌ You don't have a Spin Ticket.\n\n"

            "🎟 Spin Tickets can be added by "
            "Admin/reward systems.",

            reply_markup=earn_back_menu(),
        )

        return

    if not use_spin_ticket(user_id):

        await query.edit_message_text(
            "❌ Unable to use Spin Ticket.",
            reply_markup=earn_back_menu(),
        )

        return

    rewards = [
        5,
        10,
        15,
        20,
        25,
        50,
    ]

    reward = random.choice(
        rewards
    )

    add_balance(
        user_id,
        reward,
    )

    xp_result = add_xp(
        user_id,
        3,
    )

    update_user(
        user_id,
        {
            "last_spin": int(time.time()),
            "spin_wins": (
                user.get(
                    "spin_wins",
                    0,
                )
                + 1
            ),
        },
    )

    add_activity(
        user_id,
        "🎡 Spin Wheel",
        reward,
    )

    level_text = ""

    if xp_result["level_up"]:

        level_text = (
            "\n🎉 LEVEL UP!\n"
            f"🏆 New Level: "
            f"{xp_result['level']}\n"
        )

    await query.edit_message_text(

        "🎡 SPIN COMPLETE!\n\n"

        f"🎁 You won: +{reward} Points\n"
        "⭐ XP: +3\n"

        f"{level_text}",

        reply_markup=earn_back_menu(),
    )


# ==================================================
# LUCKY BOX
# ==================================================

async def lucky_box(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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

    boxes = user.get(
        "lucky_box",
        0,
    )

    if boxes <= 0:

        await query.edit_message_text(

            "🎁 LUCKY BOX\n\n"

            "❌ You don't have a Lucky Box.\n\n"

            "🎁 Lucky Boxes can be added "
            "by Admin/reward systems.",

            reply_markup=earn_back_menu(),
        )

        return

    if not use_lucky_box(user_id):

        await query.edit_message_text(
            "❌ Unable to open Lucky Box.",
            reply_markup=earn_back_menu(),
        )

        return

    rewards = [
        10,
        20,
        30,
        50,
        100,
    ]

    reward = random.choice(
        rewards
    )

    add_balance(
        user_id,
        reward,
    )

    xp_result = add_xp(
        user_id,
        5,
    )

    update_user(
        user_id,
        {
            "last_lucky_box": int(time.time()),
            "lucky_box_wins": (
                user.get(
                    "lucky_box_wins",
                    0,
                )
                + 1
            ),
        },
    )

    add_activity(
        user_id,
        "🎁 Lucky Box",
        reward,
    )

    level_text = ""

    if xp_result["level_up"]:

        level_text = (
            "\n🎉 LEVEL UP!\n"
            f"🏆 New Level: "
            f"{xp_result['level']}\n"
        )

    await query.edit_message_text(

        "🎁 LUCKY BOX OPENED!\n\n"

        f"💰 You won: +{reward} Points\n"
        "⭐ XP: +5\n"

        f"{level_text}",

        reply_markup=earn_back_menu(),
    )


# ==================================================
# SCRATCH CARD
# ==================================================

async def scratch_card(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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

    cards = user.get(
        "scratch_card",
        0,
    )

    if cards <= 0:

        await query.edit_message_text(

            "🎫 SCRATCH CARD\n\n"

            "❌ You don't have a Scratch Card.\n\n"

            "🎫 Scratch Cards can be added "
            "by Admin/reward systems.",

            reply_markup=earn_back_menu(),
        )

        return

    if not use_scratch_card(user_id):

        await query.edit_message_text(
            "❌ Unable to use Scratch Card.",
            reply_markup=earn_back_menu(),
        )

        return

    rewards = [
        5,
        10,
        15,
        25,
        50,
    ]

    reward = random.choice(
        rewards
    )

    add_balance(
        user_id,
        reward,
    )

    xp_result = add_xp(
        user_id,
        4,
    )

    update_user(
        user_id,
        {
            "last_scratch": int(time.time()),
            "scratch_wins": (
                user.get(
                    "scratch_wins",
                    0,
                )
                + 1
            ),
        },
    )

    add_activity(
        user_id,
        "🎫 Scratch Card",
        reward,
    )

    level_text = ""

    if xp_result["level_up"]:

        level_text = (
            "\n🎉 LEVEL UP!\n"
            f"🏆 New Level: "
            f"{xp_result['level']}\n"
        )

    await query.edit_message_text(

        "🎫 SCRATCH COMPLETE!\n\n"

        f"💰 You won: +{reward} Points\n"
        "⭐ XP: +4\n"

        f"{level_text}",

        reply_markup=earn_back_menu(),
    )


# ==================================================
# HANDLER EXPORTS
# ==================================================

EARN_HANDLERS = {

    "earn": earn,
    "daily_bonus": daily_bonus,
    "tasks": tasks,
    "shortlinks": shortlinks,
    "energy": energy,
    "claim_test_task": claim_test_task,
    "spin": spin_wheel,
    "lucky_box": lucky_box,
    "scratch": scratch_card,

    }
