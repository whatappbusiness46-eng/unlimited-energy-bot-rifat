# ============================================================
# callbacks.py
# Unlimited Energy Bot V2
# PART 4 - FINAL CALLBACK ROUTER
# ============================================================

import logging
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import GROUPS

from database import get_user

from withdraw import (
    withdraw_page,
    select_method,
    confirm_withdrawal,
    cancel_withdrawal,
    withdrawal_history_page,
)

from handlers import (
    main_menu,
    force_join_menu,
)
from earn import (
    earn_page,
    daily_bonus,
    tasks,
    shortlinks,
    spin_wheel,
    lucky_box,
    scratch_card,
    energy_page,
    claim_test_task,
)


logger = logging.getLogger(__name__)


# ============================================================
# COMMON KEYBOARDS
# ============================================================

def home_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home",
                )
            ]
        ]
    )


def back_earn_keyboard():

    return InlineKeyboardMarkup(
        [
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
    )


def back_profile_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👤 Profile",
                    callback_data="profile",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home",
                )
            ],
        ]
    )


# ============================================================
# BALANCE
# ============================================================

async def show_balance(
    query,
    user_id,
):

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found.",
            reply_markup=home_keyboard(),
        )

        return

    balance = user.get(
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
        balance
        + bonus
        + premium_balance
    )

    await query.edit_message_text(

        "💰 **YOUR WALLET**\n\n"

        f"💰 Earn Balance: "
        f"{balance} Points\n"

        f"🎁 Bonus Balance: "
        f"{bonus} Points\n"

        f"💎 Premium Balance: "
        f"{premium_balance} Points\n\n"

        f"💵 **Total Balance: "
        f"{total} Points**",

        reply_markup=home_keyboard(),

        parse_mode="Markdown",
    )


# ============================================================
# PROFILE
# ============================================================

async def show_profile(
    query,
    user_id,
):

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found.",
            reply_markup=home_keyboard(),
        )

        return

    balance = user.get(
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
        "🔰 Beginner",
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

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance",
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Referral",
                callback_data="refer",
            )
        ],

        [
            InlineKeyboardButton(
                "🏆 Rank",
                callback_data="rank",
            )
        ],

        [
            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="user_stats",
            )
        ],

        [
            InlineKeyboardButton(
                "📜 Activity",
                callback_data="user_activity",
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

        "👤 **YOUR PROFILE**\n\n"

        f"🆔 ID: `{user_id}`\n\n"

        f"💰 Balance: "
        f"{balance} Points\n"

        f"🎁 Bonus: "
        f"{bonus} Points\n"

        f"💎 Premium Balance: "
        f"{premium_balance} Points\n\n"

        f"👥 Referrals: "
        f"{referrals}\n"

        f"⭐ XP: "
        f"{xp}\n"

        f"🏆 Level: "
        f"{level}\n"

        f"🎖 Rank: "
        f"{rank}\n\n"

        f"👑 Premium: "
        f"{premium_status}\n"

        f"💎 VIP: "
        f"{vip_status}",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ============================================================
# REFERRAL
# ============================================================

async def show_referral(
    query,
    context,
    user_id,
):

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found.",
            reply_markup=home_keyboard(),
        )

        return

    referrals = user.get(
        "referrals",
        0,
    )

    referral_earn = user.get(
        "referral_earn",
        0,
    )

    referral_xp = user.get(
        "referral_xp",
        0,
    )

    try:

        bot_info = await context.bot.get_me()

        bot_username = bot_info.username

    except Exception as error:

        logger.exception(
            "Could not get bot info: %s",
            error,
        )

        await query.edit_message_text(
            "⚠️ Unable to generate referral link.",
            reply_markup=home_keyboard(),
        )

        return

    referral_link = (
        f"https://t.me/{bot_username}"
        f"?start=ref_{user_id}"
    )

    share_url = (
        "https://t.me/share/url"
        f"?url={referral_link}"
        "&text=Join%20Unlimited%20Energy%20Bot%20and%20earn%20rewards!"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "📤 Share Referral Link",
                url=share_url,
            )
        ],

        [
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile",
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

        "👥 **REFERRAL CENTER**\n\n"

        "🎁 Invite friends and earn rewards!\n\n"

        f"👥 Total Referrals: "
        f"{referrals}\n"

        f"💰 Referral Earnings: "
        f"{referral_earn} Points\n"

        f"⭐ Referral XP: "
        f"{referral_xp}\n\n"

        "🔗 **Your Referral Link:**\n"

        f"`{referral_link}`\n\n"

        "📢 Share your link with your friends.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ============================================================
# RANK
# ============================================================

async def show_rank(
    query,
    user_id,
):

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found.",
            reply_markup=home_keyboard(),
        )

        return

    rank = user.get(
        "rank",
        "🔰 Beginner",
    )

    level = user.get(
        "level",
        1,
    )

    xp = user.get(
        "xp",
        0,
    )

    await query.edit_message_text(

        "🏆 **YOUR RANK**\n\n"

        f"🎖 Rank: "
        f"{rank}\n"

        f"🏆 Level: "
        f"{level}\n"

        f"⭐ XP: "
        f"{xp}\n\n"

        "🚀 Keep earning to reach "
        "the next rank!",

        reply_markup=InlineKeyboardMarkup(

            [

                [
                    InlineKeyboardButton(
                        "👤 Profile",
                        callback_data="profile",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ],

            ]

        ),

        parse_mode="Markdown",
    )


# ============================================================
# USER STATISTICS
# ============================================================

async def show_user_stats(
    query,
    user_id,
):

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found.",
            reply_markup=home_keyboard(),
        )

        return

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

    referral_earn = user.get(
        "referral_earn",
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

    daily_streak = user.get(
        "daily_streak",
        0,
    )

    wheel_data = user.get(
        "wheel_data",
        {},
    )

    lucky_box_data = user.get(
        "lucky_box_data",
        {},
    )

    task_data = user.get(
        "task_data",
        {},
    )

    if not isinstance(
        wheel_data,
        dict,
    ):
        wheel_data = {}

    if not isinstance(
        lucky_box_data,
        dict,
    ):
        lucky_box_data = {}

    if not isinstance(
        task_data,
        dict,
    ):
        task_data = {}

    wheel_spins = wheel_data.get(
        "spins",
        0,
    )

    lucky_boxes = lucky_box_data.get(
        "opened",
        0,
    )

    tasks_completed = task_data.get(
        "completed",
        0,
    )

    await query.edit_message_text(

        "📊 **YOUR STATISTICS**\n\n"

        f"💰 Total Earned: "
        f"{total_earned} Points\n"

        f"💸 Total Withdrawn: "
        f"{total_withdraw} Points\n"

        f"👥 Referrals: "
        f"{referrals}\n"

        f"🎁 Referral Earnings: "
        f"{referral_earn} Points\n\n"

        f"🎯 Tasks Completed: "
        f"{tasks_completed}\n"

        f"🎡 Wheel Spins: "
        f"{wheel_spins}\n"

        f"🎁 Lucky Boxes: "
        f"{lucky_boxes}\n\n"

        f"🔥 Daily Streak: "
        f"{daily_streak}\n"

        f"⭐ XP: "
        f"{xp}\n"

        f"🏆 Level: "
        f"{level}",

        reply_markup=back_profile_keyboard(),

        parse_mode="Markdown",
    )


# ============================================================
# USER ACTIVITY
# ============================================================

async def show_user_activity(
    query,
    user_id,
):

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found.",
            reply_markup=home_keyboard(),
        )

        return

    activities = user.get(
        "activity",
        [],
    )

    if not isinstance(
        activities,
        list,
    ):
        activities = []

    activities = activities[-10:]

    if not activities:

        await query.edit_message_text(

            "📜 **RECENT ACTIVITY**\n\n"
            "No activity recorded yet.",

            reply_markup=back_profile_keyboard(),

            parse_mode="Markdown",
        )

        return

    text = (
        "📜 **RECENT ACTIVITY**\n\n"
    )

    for item in reversed(
        activities
    ):

        if not isinstance(
            item,
            dict,
        ):
            continue

        action = item.get(
            "action",
            "Unknown action",
        )

        timestamp = item.get(
            "time",
            "",
        )

        text += (
            f"• {action}\n"
            f"  🕒 {timestamp}\n\n"
        )

    await query.edit_message_text(

        text,

        reply_markup=back_profile_keyboard(),

        parse_mode="Markdown",
    )


# ============================================================
# HELP
# ============================================================

async def show_help(
    query,
):

    await query.edit_message_text(

        "❓ **HELP CENTER**\n\n"

        "💰 Earn — Complete available tasks\n"
        "💳 Balance — Check your wallet\n"
        "👤 Profile — View your account\n"
        "👥 Referral — Invite friends\n"
        "🏆 Rank — Check your progress\n"
        "🎁 Daily — Claim daily reward\n"
        "🎡 Games — Spin, Lucky Box & Scratch\n"
        "💸 Withdraw — Request withdrawal\n"
        "👑 Premium — Premium features\n"
        "💎 VIP — VIP features\n"
        "📊 Statistics — View your progress\n"
        "📜 Activity — View recent activity\n\n"

        "🆘 Need help?\n"
        "Contact the Admin.",

        reply_markup=home_keyboard(),

        parse_mode="Markdown",
    )


# ============================================================
# FORCE JOIN VERIFICATION
# ============================================================

async def verify_join_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    user = get_user(user_id)

    if not user:

        await query.answer(
            "⚠️ User account not found.",
            show_alert=True,
        )

        return

    if user.get(
        "banned",
        False,
    ):

        await query.answer(
            "🚫 Your account has been banned.",
            show_alert=True,
        )

        return

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

                not_joined.append(
                    group
                )

        except Exception as error:

            logger.warning(
                "Force join check failed | "
                "group=%s | user=%s | error=%s",
                group,
                user_id,
                error,
            )

            not_joined.append(
                group
            )

    if not_joined:

        await query.answer(
            "❌ Join all required groups first.",
            show_alert=True,
        )

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

    await query.answer(
        "✅ Verification successful!"
    )

    await query.edit_message_text(

        "✅ **VERIFICATION SUCCESSFUL!**\n\n"

        "🎉 You can now use "
        "Unlimited Energy Bot.",

        reply_markup=main_menu(),

        parse_mode="Markdown",
    )


# ============================================================
# OPTIONAL FEATURE ROUTER
# ============================================================

async def optional_feature_callback(
    update,
    context,
    module_name,
    function_name,
    unavailable_text,
):

    query = update.callback_query

    try:

        module = __import__(
            module_name
        )

        function = getattr(
            module,
            function_name,
        )

        await function(
            update,
            context,
        )

    except ImportError:

        logger.warning(
            "Optional module unavailable: %s",
            module_name,
        )

        await query.answer(
            unavailable_text,
            show_alert=True,
        )

    except AttributeError:

        logger.exception(
            "Function %s missing in %s",
            function_name,
            module_name,
        )

        await query.answer(
            "⚠️ This feature is not configured yet.",
            show_alert=True,
        )

    except Exception:

        logger.exception(
            "Optional feature error: %s.%s",
            module_name,
            function_name,
        )

        await query.answer(
            "⚠️ Unable to open this feature.",
            show_alert=True,
        )
async def earn_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    data: str,
):
    earn_handlers = {
        "earn": earn_page,
        "daily_bonus": daily_bonus,
        "tasks": tasks,
        "shortlinks": shortlinks,
        "spin": spin_wheel,
        "spin_wheel": spin_wheel,
        "lucky_box": lucky_box,
        "scratch": scratch_card,
        "energy": energy_page,
        "claim_test_task": claim_test_task,
    }

    handler = earn_handlers.get(data)

    if handler is None:
        return False

    await handler(
        update,
        context,
    )

    return True

# ============================================================
# MAIN CALLBACK ROUTER
# ============================================================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id
    data = query.data or ""

    logger.info(
        "CALLBACK | user=%s | data=%s",
        user_id,
        data,
    )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if data == "admin" or data.startswith("admin_"):
        try:
            from admin import admin_callback

            await admin_callback(
                update,
                context,
            )

        except ImportError:
            logger.exception(
                "admin_callback unavailable"
            )

            await query.answer(
                "⚠️ Admin system unavailable.",
                show_alert=True,
            )

        except Exception:
            logger.exception(
                "Admin callback error"
            )

            await query.answer(
                "⚠️ Admin action failed.",
                show_alert=True,
            )

        return

    # --------------------------------------------------------
    # ANSWER CALLBACK
    # --------------------------------------------------------

    try:
        await query.answer()
    except Exception:
        logger.exception(
            "Callback answer failed"
        )

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    user = get_user(user_id)

    if not user:
        await query.edit_message_text(
            "⚠️ User account not found.\n\n"
            "Please use /start first.",
            reply_markup=home_keyboard(),
        )
        return

    # --------------------------------------------------------
    # BAN
    # --------------------------------------------------------

    if user.get("banned", False):
        await query.edit_message_text(
            "🚫 Your account has been banned."
        )
        return

    # ========================================================
    # HOME
    # ========================================================

    if data == "home":
        await query.edit_message_text(
            "🏠 **MAIN MENU**\n\n"
            "🚀 **Unlimited Energy Bot V2**\n\n"
            "💰 Earn Points\n"
            "👥 Invite Friends\n"
            "🎁 Complete Tasks\n"
            "🎡 Play Reward Games\n"
            "💸 Withdraw Rewards\n\n"
            "👇 Choose an option below.",
            reply_markup=main_menu(),
            parse_mode="Markdown",
        )
        return

    # ========================================================
    # EARN
    # ========================================================

    if data == "earn":
        await earn_page(
            update,
            context,
        )
        return

    # ========================================================
    # DAILY BONUS
    # ========================================================

    if data == "daily_bonus":
        await daily_bonus(
            update,
            context,
        )
        return

    # ========================================================
    # TASKS
    # ========================================================

    if data == "tasks":
        await tasks(
            update,
            context,
        )
        return

    # ========================================================
    # SHORTLINKS
    # ========================================================

    if data == "shortlinks":
        await shortlinks(
            update,
            context,
        )
        return

    # ========================================================
    # SPIN
    # ========================================================

    if data in (
        "spin",
        "spin_wheel",
    ):
        await spin_wheel(
            update,
            context,
        )
        return

    # ========================================================
    # LUCKY BOX
    # ========================================================

    if data == "lucky_box":
        await lucky_box(
            update,
            context,
        )
        return

    # ========================================================
    # SCRATCH
    # ========================================================

    if data in (
        "scratch",
        "scratch_card",
    ):
        await scratch_card(
            update,
            context,
        )
        return

    # ========================================================
    # ENERGY
    # ========================================================

    if data == "energy":
        await energy_page(
            update,
            context,
        )
        return

    # ========================================================
    # TEST TASK
    # ========================================================

    if data == "claim_test_task":
        await claim_test_task(
            update,
            context,
        )
        return

    # ========================================================
    # BALANCE
    # ========================================================

    if data == "balance":
        await show_balance(
            query,
            user_id,
        )
        return

    # ========================================================
    # PROFILE
    # ========================================================

    if data == "profile":
        await show_profile(
            query,
            user_id,
        )
        return

    # ========================================================
    # REFERRAL
    # ========================================================

    if data in (
        "refer",
        "referral",
    ):
        await show_referral(
            query,
            context,
            user_id,
        )
        return

    # ========================================================
    # RANK
    # ========================================================

    if data == "rank":
        await show_rank(
            query,
            user_id,
        )
        return

    # ========================================================
    # USER STATISTICS
    # ========================================================

    if data in (
        "stats",
        "user_stats",
    ):
        await show_user_stats(
            query,
            user_id,
        )
        return

    # ========================================================
    # USER ACTIVITY
    # ========================================================

    if data in (
        "activity",
        "user_activity",
    ):
        await show_user_activity(
            query,
            user_id,
        )
        return

    # ========================================================
    # HELP
    # ========================================================

    if data == "help":
        await show_help(
            query,
        )
        return

    # ========================================================
    # FORCE JOIN VERIFY
    # ========================================================

    if data in (
        "verify_join",
        "verify",
        "check_join",
    ):
        await verify_join_callback(
            update,
            context,
        )
        return

    # ========================================================
    # WITHDRAW
    # ========================================================

    if data == "withdraw":
        await withdraw_page(
            update,
            context,
        )
        return

    # ========================================================
    # WITHDRAW METHOD
    # ========================================================

    if data.startswith(
        "withdraw_method_"
    ):
        await select_method(
            update,
            context,
        )
        return

    # ========================================================
    # WITHDRAW CONFIRM
    # ========================================================

    if data == "withdraw_confirm":
        await confirm_withdrawal(
            update,
            context,
        )
        return

    # ========================================================
    # WITHDRAW CANCEL
    # ========================================================

    if data == "withdraw_cancel":
        await cancel_withdrawal(
            update,
            context,
        )
        return

    # ========================================================
    # WITHDRAW HISTORY
    # ========================================================

    if data == "withdraw_history":
        await withdrawal_history_page(
            update,
            context,
        )
        return

    # ========================================================
    # PREMIUM
    # ========================================================

    if data == "premium":
        await optional_feature_callback(
            update,
            context,
            "premium",
            "premium_page",
            "⚠️ Premium system unavailable.",
        )
        return

    # ========================================================
    # VIP
    # ========================================================

    if data == "vip":
        await optional_feature_callback(
            update,
            context,
            "vip",
            "vip_page",
            "⚠️ VIP system unavailable.",
        )
        return

    # ========================================================
    # LEADERBOARD
    # ========================================================

    if data == "leaderboard":
        await optional_feature_callback(
            update,
            context,
            "handlers",
            "leaderboard",
            "⚠️ Leaderboard unavailable.",
        )
        return

    # ========================================================
    # UNKNOWN CALLBACK
    # ========================================================

    logger.warning(
        "UNKNOWN CALLBACK | user=%s | data=%s",
        user_id,
        data,
    )

    await query.edit_message_text(
        "⚠️ This button is not configured yet.",
        reply_markup=home_keyboard(),
    )
