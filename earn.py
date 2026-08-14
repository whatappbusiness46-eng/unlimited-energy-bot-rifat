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

