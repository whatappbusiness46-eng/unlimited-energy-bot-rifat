import random
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from config import (
    DAILY_BONUS,
    SPIN_MIN,
    SPIN_MAX,
    SCRATCH_MIN,
    SCRATCH_MAX,
    LUCKYBOX_MIN,
    LUCKYBOX_MAX,
)

from database import (
    get_user,
    update_user,
    add_balance,
    add_bonus,
    add_xp,
    add_activity,
    update_energy,
    use_energy,
    use_spin_ticket,
    use_lucky_box,
    use_scratch_card,
)


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
                "🎡 Spin Wheel",
                callback_data="spin"
            ),
            InlineKeyboardButton(
                "🎁 Lucky Box",
                callback_data="lucky_box"
            )
        ],

        [
            InlineKeyboardButton(
                "🪙 Scratch Card",
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
        ],

    ]

    return InlineKeyboardMarkup(keyboard)


# ==========================
# BACK TO EARN
# ==========================

def back_earn_menu():

    return InlineKeyboardMarkup([
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
    ])


# ==========================
# EARN PAGE
# ==========================

async def earn_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user_id = query.from_user.id

    user = get_user(user_id)

    energy = update_energy(user_id)

    spin_ticket = user.get(
        "spin_ticket",
        0
    )

    lucky_box = user.get(
        "lucky_box",
        0
    )

    scratch_card = user.get(
        "scratch_card",
        0
    )

    await query.edit_message_text(

        "💰 EARN CENTER\n\n"

        "🎁 Daily Bonus\n"
        "🎡 Spin Wheel\n"
        "🎁 Lucky Box\n"
        "🪙 Scratch Card\n"
        "⚡ Energy System\n\n"

        f"🎟 Spin Tickets: {spin_ticket}\n"
        f"🎁 Lucky Boxes: {lucky_box}\n"
        f"🪙 Scratch Cards: {scratch_card}\n"
        f"⚡ Energy: {energy}/100\n\n"

        "👇 Choose your reward:",

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

    user_id = query.from_user.id

    user = get_user(user_id)

    now = int(time.time())

    last_daily = user.get(
        "last_daily",
        0
    )

    # 24 hour cooldown
    if last_daily:

        remaining = (
            86400
            - (now - last_daily)
        )

        if remaining > 0:

            hours = remaining // 3600
            minutes = (
                remaining % 3600
            ) // 60

            await query.edit_message_text(

                "⏳ DAILY BONUS\n\n"

                "You already claimed today's bonus.\n\n"

                f"🕐 Try again in "
                f"{hours}h {minutes}m.",

                reply_markup=back_earn_menu()
            )

            return

    old_streak = user.get(
        "daily_streak",
        0
    )

    # Consecutive daily check
    if last_daily:

        days_passed = (
            now - last_daily
        ) // 86400

        if days_passed <= 1:
            streak = old_streak + 1
        else:
            streak = 1

    else:
        streak = 1

    # Streak bonus
    streak_bonus = min(
        streak,
        7
    )

    reward = (
        DAILY_BONUS
        + streak_bonus
    )

    update_user(
        user_id,
        {
            "last_daily": now,
            "daily_streak": streak,
        }
    )

    add_bonus(
        user_id,
        reward
    )

    xp_result = add_xp(
        user_id,
        5
    )

    add_activity(
        user_id,
        "🎁 Daily Bonus",
        reward
    )

    message = (
        "🎉 DAILY BONUS CLAIMED!\n\n"

        f"💰 Reward: +{reward} Points\n"
        f"🔥 Streak: {streak} Day(s)\n"
        f"⭐ XP: +5\n"
    )

    if xp_result["level_up"]:

        message += (
            "\n🎊 LEVEL UP!\n"
            f"🏆 Level: "
            f"{xp_result['level']}\n"
        )

    message += (
        "\nCome back tomorrow for another reward! 🚀"
    )

    await query.edit_message_text(
        message,
        reply_markup=back_earn_menu()
    )


# ==========================
# SPIN WHEEL
# ==========================

async def spin_wheel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user_id = query.from_user.id

    user = get_user(user_id)

    tickets = user.get(
        "spin_ticket",
        0
    )

    if tickets <= 0:

        await query.edit_message_text(

            "🎡 SPIN WHEEL\n\n"

            "❌ You don't have any Spin Ticket.\n\n"

            "🎟 Spin Tickets can be earned "
            "from future tasks and rewards.",

            reply_markup=back_earn_menu()
        )

        return

    if not use_spin_ticket(user_id):

        await query.edit_message_text(
            "❌ Unable to use Spin Ticket.",
            reply_markup=back_earn_menu()
        )

        return

    reward = random.randint(
        SPIN_MIN,
        SPIN_MAX
    )

    add_balance(
        user_id,
        reward
    )

    add_xp(
        user_id,
        3
    )

    add_activity(
        user_id,
        "🎡 Spin Wheel",
        reward
    )

    await query.edit_message_text(

        "🎡 SPIN WHEEL\n\n"

        "🎉 Congratulations!\n\n"

        f"💰 You won: +{reward} Points\n"
        "⭐ XP: +3\n\n"

        "🎟 One Spin Ticket used.",

        reply_markup=back_earn_menu()
    )


# ==========================
# LUCKY BOX
# ==========================

async def lucky_box(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user_id = query.from_user.id

    user = get_user(user_id)

    boxes = user.get(
        "lucky_box",
        0
    )

    if boxes <= 0:

        await query.edit_message_text(

            "🎁 LUCKY BOX\n\n"

            "❌ You don't have a Lucky Box.\n\n"

            "Complete tasks to receive "
            "Lucky Boxes.",

            reply_markup=back_earn_menu()
        )

        return

    if not use_lucky_box(user_id):

        await query.edit_message_text(
            "❌ Unable to open Lucky Box.",
            reply_markup=back_earn_menu()
        )

        return

    reward = random.randint(
        LUCKYBOX_MIN,
        LUCKYBOX_MAX
    )

    add_balance(
        user_id,
        reward
    )

    add_xp(
        user_id,
        5
    )

    add_activity(
        user_id,
        "🎁 Lucky Box",
        reward
    )

    await query.edit_message_text(

        "🎁 LUCKY BOX OPENED!\n\n"

        "✨ Amazing!\n\n"

        f"💰 Reward: +{reward} Points\n"
        "⭐ XP: +5\n\n"

        "🎁 Lucky Box used.",

        reply_markup=back_earn_menu()
    )


# ==========================
# SCRATCH CARD
# ==========================

async def scratch_card(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user_id = query.from_user.id

    user = get_user(user_id)

    cards = user.get(
        "scratch_card",
        0
    )

    if cards <= 0:

        await query.edit_message_text(

            "🪙 SCRATCH CARD\n\n"

            "❌ You don't have a Scratch Card.\n\n"

            "Complete tasks to receive "
            "Scratch Cards.",

            reply_markup=back_earn_menu()
        )

        return

    if not use_scratch_card(user_id):

        await query.edit_message_text(
            "❌ Unable to use Scratch Card.",
            reply_markup=back_earn_menu()
        )

        return

    reward = random.randint(
        SCRATCH_MIN,
        SCRATCH_MAX
    )

    add_bonus(
        user_id,
        reward
    )

    add_xp(
        user_id,
        4
    )

    add_activity(
        user_id,
        "🪙 Scratch Card",
        reward
    )

    await query.edit_message_text(

        "🪙 SCRATCH CARD\n\n"

        "✨ You scratched the card!\n\n"

        f"🎁 Reward: +{reward} Bonus Points\n"
        "⭐ XP: +4\n\n"

        "🪙 Scratch Card used.",

        reply_markup=back_earn_menu()
    )


# ==========================
# ENERGY PAGE
# ==========================

async def energy_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user_id = query.from_user.id

    energy = update_energy(
        user_id
    )

    user = get_user(user_id)

    max_energy = user.get(
        "max_energy",
        100
    )

    await query.edit_message_text(

        "⚡ ENERGY SYSTEM\n\n"

        f"⚡ Energy: {energy}/{max_energy}\n\n"

        "🔋 Energy automatically regenerates.\n"
        "⏱️ Recovery: 1 Energy / minute\n\n"

        "Energy will be used by selected "
        "future earning tasks.",

        reply_markup=back_earn_menu()
    )


# ==========================
# HANDLER EXPORTS
# ==========================

EARN_FUNCTIONS = {

    "earn": earn_page,

    "daily_bonus": daily_bonus,

    "spin": spin_wheel,

    "lucky_box": lucky_box,

    "scratch": scratch_card,

    "energy": energy_page,

  }
