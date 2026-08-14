# ============================================================
# callbacks.py
# Unlimited Energy Bot V2
# COMPLETE CALLBACK ROUTER
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


def home_main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 Earn",
                    callback_data="earn",
                ),
                InlineKeyboardButton(
                    "💳 Balance",
                    callback_data="balance",
                ),
            ],
            [
                InlineKeyboardButton(
                    "👤 Profile",
                    callback_data="profile",
                ),
                InlineKeyboardButton(
                    "👥 Referral",
                    callback_data="refer",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏆 Rank",
                    callback_data="rank",
                ),
                InlineKeyboardButton(
                    "🎁 Daily",
                    callback_data="daily_bonus",
                ),
            ],
            [
                InlineKeyboardButton(
                    "💸 Withdraw",
                    callback_data="withdraw",
                ),
            ],
            [
                InlineKeyboardButton(
                    "👑 Premium",
                    callback_data="premium",
                ),
                InlineKeyboardButton(
                    "💎 VIP",
                    callback_data="vip",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Statistics",
                    callback_data="user_stats",
                ),
                InlineKeyboardButton(
                    "📜 Activity",
                    callback_data="user_activity",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❓ Help",
                    callback_data="help",
                )
            ],
        ]
    )


# ============================================================
# SAFE HOME PAGE
# ============================================================

async def show_home(
    query,
    user_id,
):

    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        await query.edit_message_text(
            "⚠️ User account not found.\n\n"
            "Please use /start first."
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
        "🏠 **UNLIMITED ENERGY BOT**\n\n"
        "Welcome back! 👋\n\n"
        f"💰 Balance: {total} Points\n"
        f"🎁 Bonus: {bonus} Points\n\n"
        "Choose an option below:",
        reply_markup=home_main_keyboard(),
        parse_mode="Markdown",
    )


# ============================================================
# BALANCE
# ============================================================

async def show_balance(
    query,
    user_id,
):

    user = get_user(
        user_id,
        create=False,
    )

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
        f"💰 Earn Balance: {balance} Points\n"
        f"🎁 Bonus Balance: {bonus} Points\n"
        f"💎 Premium Balance: {premium_balance} Points\n\n"
        f"💵 **Total Balance: {total} Points**",
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

    user = get_user(
        user_id,
        create=False,
    )

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

    premium = bool(
        user.get(
            "premium",
            False,
        )
    )

    vip = bool(
        user.get(
            "vip",
            False,
        )
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
        f"💰 Balance: {balance} Points\n"
        f"🎁 Bonus: {bonus} Points\n"
        f"💎 Premium Balance: {premium_balance} Points\n\n"
        f"👥 Referrals: {referrals}\n"
        f"⭐ XP: {xp}\n"
        f"🏆 Level: {level}\n"
        f"🎖 Rank: {rank}\n\n"
        f"👑 Premium: {premium_status}\n"
        f"💎 VIP: {vip_status}",
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

    user = get_user(
        user_id,
        create=False,
    )

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

    except Exception:
        logger.exception(
            "Could not get bot info"
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
        f"👥 Total Referrals: {referrals}\n"
        f"💰 Referral Earnings: {referral_earn} Points\n"
        f"⭐ Referral XP: {referral_xp}\n\n"
        "🔗 **Your Referral Link:**\n"
        f"`{referral_link}`\n\n"
        "📢 Share this link with your friends.",
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

    user = get_user(
        user_id,
        create=False,
    )

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
        f"🎖 Rank: {rank}\n"
        f"🏆 Level: {level}\n"
        f"⭐ XP: {xp}\n\n"
        "🚀 Keep earning to reach the next rank!",
        reply_markup=back_profile_keyboard(),
        parse_mode="Markdown",
    )


# ============================================================
# USER STATISTICS
# ============================================================

async def show_user_stats(
    query,
    user_id,
):

    user = get_user(
        user_id,
        create=False,
    )

    if not user:
        await query.edit_message_text(
            "⚠️ User account not found.",
            reply_markup=home_keyboard(),
        )
        return

    total_earned = user.get(
        "total_earned",
        user.get(
            "earned",
            0,
        ),
    )

    total_withdraw = user.get(
        "total_withdrawn",
        user.get(
            "withdrawn",
            0,
        ),
    )

    referrals = user.get(
        "referrals",
        0,
    )

    referral_earn = user.get(
        "referral_earn",
        0,
    )

    daily_streak = user.get(
        "daily_streak",
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

    wheel_data = user.get(
        "wheel",
        {},
    )

    lucky_box_data = user.get(
        "lucky_box",
        {},
    )

    task_data = user.get(
        "tasks",
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
        user.get(
            "spin_count",
            0,
        ),
    )

    lucky_boxes = lucky_box_data.get(
        "opened",
        user.get(
            "lucky_box_count",
            0,
        ),
    )

    tasks_completed = task_data.get(
        "completed",
        user.get(
            "offer_completed",
            0,
        ),
    )

    await query.edit_message_text(
        "📊 **YOUR STATISTICS**\n\n"
        f"💰 Total Earned: {total_earned} Points\n"
        f"💸 Total Withdrawn: {total_withdraw} Points\n"
        f"👥 Referrals: {referrals}\n"
        f"🎁 Referral Earnings: {referral_earn} Points\n\n"
        f"🎯 Tasks Completed: {tasks_completed}\n"
        f"🎡 Wheel Spins: {wheel_spins}\n"
        f"🎁 Lucky Boxes: {lucky_boxes}\n\n"
        f"🔥 Daily Streak: {daily_streak}\n"
        f"⭐ XP: {xp}\n"
        f"🏆 Level: {level}",
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

    user = get_user(
        user_id,
        create=False,
    )

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

    lines = [
        "📜 **RECENT ACTIVITY**",
        "",
    ]

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

        lines.append(
            f"• {action}"
        )

        if timestamp:
            lines.append(
                f"  🕒 {timestamp}"
            )

        lines.append("")

    await query.edit_message_text(
        "\n".join(lines),
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

    user = get_user(
        user_id,
        create=False,
    )

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
            "You still haven't joined all required groups.\n\n"
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
        "🎉 You can now use Unlimited Energy Bot.",
        reply_markup=home_main_keyboard(),
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

    if not query:
        return

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


# ============================================================
# EARN ROUTER
# ============================================================

async def earn_callback(
    update,
    context,
    data,
):

    earn_handlers = {
        "earn": earn_page,
        "daily_bonus": daily_bonus,
        "tasks": tasks,
        "shortlinks": shortlinks,
        "spin": spin_wheel,
        "lucky_box": lucky_box,
        "scratch": scratch_card,
        "energy": energy_page,
        "claim_test_task": claim_test_task,
    }

    function = earn_handlers.get(
        data
    )

    if function is None:
        return False

    await function(
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

    data = (
        query.data
        if isinstance(
            query.data,
            str,
        )
        else ""
    )

    logger.info(
        "CALLBACK | user=%s | data=%s",
        user_id,
        data,
    )

    # ========================================================
    # ADMIN ROUTER
    # ========================================================

    if (
        data == "admin"
        or data.startswith("admin_")
    ):

        try:

            from admin import admin_callback

            await admin_callback(
                update,
                context,
            )

        except ImportError:

            logger.exception(
                "admin.py / admin_callback unavailable"
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

    # ========================================================
    # ANSWER CALLBACK
    # ========================================================

    try:
        await query.answer()

    except Exception:
        logger.exception(
            "Callback answer failed."
        )

    # ========================================================
    # USER CHECK
    # ========================================================

    user = get_user(
        user_id,
        create=False,
    )

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found.\n\n"
            "Please use /start first.",
            reply_markup=home_keyboard(),
        )

        return

    # ========================================================
    # BAN CHECK
    # ========================================================

    if user.get(
        "banned",
        False,
    ):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    # ========================================================
    # HOME
    # ========================================================

    if data == "home":

        await show_home(
            query,
            user_id,
        )

        return

    # ========================================================
    # FORCE JOIN
    # ========================================================

    if data in (
        "verify_join",
        "check_join",
        "verify",
    ):

        await verify_join_callback(
            update,
            context,
        )

        return

    # ========================================================
    # EARN SYSTEM
    # ========================================================

    if data in (
        "earn",
        "daily_bonus",
        "tasks",
        "shortlinks",
        "spin",
        "lucky_box",
        "scratch",
        "energy",
        "claim_test_task",
    ):

        try:

            handled = await earn_callback(
                update,
                context,
                data,
            )

            if handled:
                return

        except Exception:

            logger.exception(
                "Earn callback error | data=%s",
                data,
            )

            try:
                await query.answer(
                    "⚠️ Earn feature error.",
                    show_alert=True,
                )
            except Exception:
                pass

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
        "referral_menu",
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
        "user_stats",
        "statistics",
        "stats",
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
        "user_activity",
        "activity",
    ):

        await show_user_activity(
            query,
            user_id,
        )

        return

    # ========================================================
    # HELP
    # ========================================================

    if data in (
        "help",
        "help_center",
    ):

        await show_help(
            query,
        )

        return

    # ========================================================
    # WITHDRAW
    # ========================================================

    if data in (
        "withdraw",
        "withdrawal",
    ):

        try:

            await withdraw_page(
                update,
                context,
            )

        except Exception:

            logger.exception(
                "Withdraw page error"
            )

            await query.answer(
                "⚠️ Withdrawal system error.",
                show_alert=True,
            )

        return

    # ========================================================
    # WITHDRAW METHOD
    # ========================================================

    if data.startswith(
        "withdraw_method_"
    ):

        try:

            await select_method(
                update,
                context,
            )

        except Exception:

            logger.exception(
                "Withdrawal method error"
            )

            await query.answer(
                "⚠️ Unable to select payment method.",
                show_alert=True,
            )

        return

    # ========================================================
    # WITHDRAW CONFIRM
    # ========================================================

    if data == "withdraw_confirm":

        try:

            await confirm_withdrawal(
                update,
                context,
            )

        except Exception:

            logger.exception(
                "Withdrawal confirmation error"
            )

            await query.answer(
                "⚠️ Withdrawal confirmation failed.",
                show_alert=True,
            )

        return

    # ========================================================
    # WITHDRAW CANCEL
    # ========================================================

    if data == "withdraw_cancel":

        try:

            await cancel_withdrawal(
                update,
                context,
            )

        except Exception:

            logger.exception(
                "Withdrawal cancellation error"
            )

        return

    # ========================================================
    # WITHDRAW HISTORY
    # ========================================================

    if data in (
        "withdraw_history",
        "withdrawal_history",
    ):

        try:

            await withdrawal_history_page(
                update,
                context,
            )

        except Exception:

            logger.exception(
                "Withdrawal history error"
            )

            await query.answer(
                "⚠️ Unable to load withdrawal history.",
                show_alert=True,
            )

        return

    # ========================================================
    # PREMIUM
    # ========================================================

    if data in (
        "premium",
        "premium_menu",
    ):

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

    if data in (
        "vip",
        "vip_menu",
    ):

        await optional_feature_callback(
            update,
            context,
            "vip",
            "vip_page",
            "⚠️ VIP system unavailable.",
        )

        return

    # ========================================================
    # PREMIUM PURCHASE
    # ========================================================

    if (
        data.startswith(
            "premium_"
        )
        and not data.startswith(
            "premium_menu"
        )
    ):

        await optional_feature_callback(
            update,
            context,
            "premium",
            "premium_callback",
            "⚠️ Premium system unavailable.",
        )

        return

    # ========================================================
    # VIP ACTIONS
    # ========================================================

    if data.startswith(
        "vip_"
    ):

        await optional_feature_callback(
            update,
            context,
            "vip",
            "vip_callback",
            "⚠️ VIP system unavailable.",
        )

        return

    # ========================================================
    # REFERRAL CALLBACKS
    # ========================================================

    if data == "referral_link":

        await show_referral(
            query,
            context,
            user_id,
        )

        return

    if data == "referral_stats":

        await show_referral(
            query,
            context,
            user_id,
        )

        return

    # ========================================================
    # UNKNOWN CALLBACK
    # ========================================================

    logger.warning(
        "Unknown callback data | user=%s | data=%s",
        user_id,
        data,
    )

    try:

        await query.answer(
            "⚠️ This button is not configured yet.",
            show_alert=True,
        )

    except Exception:
        pass


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "button_callback",
    "verify_join_callback",
    "optional_feature_callback",
    "show_home",
    "show_balance",
    "show_profile",
    "show_referral",
    "show_rank",
    "show_user_stats",
    "show_user_activity",
    "show_help",
    ]
