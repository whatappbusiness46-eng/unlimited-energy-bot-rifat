# ============================================================
# callbacks.py
# Unlimited Energy Bot V2
# Final Callback Router
# ============================================================

import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import GROUPS

from database import get_user

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
# COMMON
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

        logger.error(
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
        "💎 VIP — VIP features\n\n"

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
                "Force join check failed: "
                "group=%s user=%s error=%s",
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
    from admin import admin_callback
    logger.info(
        "CALLBACK | user=%s | data=%s",
        user_id,
        data,
    )

    # --------------------------------------------------------
    # ADMIN ROUTER
    # --------------------------------------------------------
    if data == "admin" or data.startswith("admin_"):

    await admin_callback(
        update,
        context,
    )

    return

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

    # --------------------------------------------------------
    # NORMAL CALLBACK
    # --------------------------------------------------------

    await query.answer()

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "⚠️ User account not found.\n\n"
            "Please use /start first.",
            reply_markup=home_keyboard(),
        )

        return

    # --------------------------------------------------------
    # BAN CHECK
    # --------------------------------------------------------

    if user.get(
        "banned",
        False,
    ):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    if data == "home":

        await query.edit_message_text(

            "🏠 **MAIN MENU**\n\n"
            "👇 Choose an option:",

            reply_markup=main_menu(),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # EARN
    # --------------------------------------------------------

    if data == "earn":

        await earn_page(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # DAILY
    # --------------------------------------------------------

    if data == "daily_bonus":

        await daily_bonus(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # TASKS
    # --------------------------------------------------------

    if data == "tasks":

        await tasks(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # TEST TASK
    # --------------------------------------------------------

    if data == "claim_test_task":

        await claim_test_task(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # SHORTLINKS
    # --------------------------------------------------------

    if data == "shortlinks":

        await shortlinks(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # SPIN
    # --------------------------------------------------------

    if data == "spin":

        await spin_wheel(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # LUCKY BOX
    # --------------------------------------------------------

    if data == "lucky_box":

        await lucky_box(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # SCRATCH
    # --------------------------------------------------------

    if data == "scratch":

        await scratch_card(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    if data == "energy":

        await energy_page(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # BALANCE
    # --------------------------------------------------------

    if data == "balance":

        await show_balance(
            query,
            user_id,
        )

        return

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    if data == "profile":

        await show_profile(
            query,
            user_id,
        )

        return

    #
    # --------------------------------------------------------
    # REFERRAL
    # --------------------------------------------------------

    if data == "refer":

        await show_referral(
            query,
            context,
            user_id,
        )

        return

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    if data == "rank":

        await show_rank(
            query,
            user_id,
        )

        return

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if data == "help":

        await show_help(
            query,
        )

        return

    # --------------------------------------------------------
    # FORCE JOIN
    # --------------------------------------------------------

    if data == "verify_join":

        await verify_join_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # UNKNOWN CALLBACK
    # --------------------------------------------------------

    await query.edit_message_text(

        "⚠️ This option is not available yet.",

        reply_markup=home_keyboard(),

    )


# ============================================================
# EXPORTS
# ============================================================

CALLBACK_FUNCTIONS = {

    "button_callback":
        button_callback,

    "verify_join_callback":
        verify_join_callback,

}


