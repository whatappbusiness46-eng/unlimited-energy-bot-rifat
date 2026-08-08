import time
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import (
    GROUPS,
    GROUP_JOIN_REWARD,
    DAILY_XP,
)

from database import (
    get_user,
    update_user,
)

from handlers import (
    main_menu,
    force_join_menu,
    calculate_level,
    add_activity,
)

from earn import (
    earn_page,
    daily_bonus,
    spin_wheel,
    lucky_box,
    scratch_card,
    energy_page,
)


# ==================================================
# LOGGING
# ==================================================

logger = logging.getLogger(__name__)


# ==================================================
# BALANCE PAGE
# ==================================================

async def show_balance(
    query,
    user_id,
):

    user = get_user(user_id)

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

    keyboard = [
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ]
    ]

    await query.edit_message_text(

        "💰 **YOUR WALLET**\n\n"

        f"💰 Earn Balance: {balance} Points\n"
        f"🎁 Bonus Balance: {bonus} Points\n"
        f"💎 Premium Balance: "
        f"{premium_balance} Points\n\n"

        f"💵 **Total Balance: {total} Points**",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ==================================================
# PROFILE PAGE
# ==================================================

async def show_profile(
    query,
    user_id,
):

    user = get_user(user_id)

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

        f"💰 Balance: {balance} Points\n"
        f"🎁 Bonus: {bonus} Points\n"
        f"💎 Premium Balance: "
        f"{premium_balance} Points\n\n"

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


# ==================================================
# REFERRAL PAGE
# ==================================================

async def show_referral(
    query,
    context,
    user_id,
):

    user = get_user(user_id)

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

    bot_info = await context.bot.get_me()

    bot_username = bot_info.username

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
                "🏠 Home",
                callback_data="home",
            )
        ],

    ]

    await query.edit_message_text(

        "👥 **REFERRAL CENTER**\n\n"

        "🎁 Invite friends and earn rewards!\n\n"

        f"👥 Total Referrals: {referrals}\n"
        f"💰 Referral Earnings: "
        f"{referral_earn} Points\n"
        f"⭐ Referral XP: {referral_xp}\n\n"

        "🔗 **Your Referral Link:**\n"
        f"`{referral_link}`\n\n"

        "📢 Share your link with your friends.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ==================================================
# RANK PAGE
# ==================================================

async def show_rank(
    query,
    user_id,
):

    user = get_user(user_id)

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

    keyboard = [

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

        "🏆 **YOUR RANK**\n\n"

        f"🎖 Rank: {rank}\n"
        f"🏆 Level: {level}\n"
        f"⭐ XP: {xp}\n\n"

        "🚀 Keep earning to reach "
        "the next rank!",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ==================================================
# HELP PAGE
# ==================================================

async def show_help(
    query,
):

    keyboard = [

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ]

    ]

    await query.edit_message_text(

        "❓ **HELP CENTER**\n\n"

        "💰 Earn — Complete available tasks\n"
        "💳 Balance — Check your wallet\n"
        "👤 Profile — View your account\n"
        "👥 Referral — Invite friends\n"
        "🏆 Rank — Check your progress\n"
        "💸 Withdraw — Request withdrawal\n"
        "👑 Premium — View Premium plans\n\n"

        "🆘 Need help?\n"
        "Contact the Admin.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ==================================================
# WITHDRAW PAGE
# ==================================================

async def show_withdraw(
    query,
    user_id,
):

    user = get_user(user_id)

    balance = user.get(
        "balance",
        0,
    )

    withdraw_pending = user.get(
        "withdraw_pending",
        0,
    )

    total_withdraw = user.get(
        "total_withdraw",
        0,
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "💸 Request Withdraw",
                callback_data="withdraw_request",
            )
        ],

        [
            InlineKeyboardButton(
                "📜 Withdraw History",
                callback_data="withdraw_history",
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

        "💸 **WITHDRAW CENTER**\n\n"

        f"💰 Available Balance: {balance} Points\n"
        f"⏳ Pending: {withdraw_pending} Points\n"
        f"✅ Total Withdrawn: {total_withdraw} Points\n\n"

        "👇 Choose an option below.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ==================================================
# WITHDRAW REQUEST
# ==================================================

async def withdraw_request(
    query,
    user_id,
):

    user = get_user(user_id)

    balance = user.get(
        "balance",
        0,
    )

    if balance <= 0:

        await query.edit_message_text(

            "❌ **INSUFFICIENT BALANCE**\n\n"

            "You don't have enough balance "
            "to request a withdrawal.",

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ]
                ]
            ),

            parse_mode="Markdown",
        )

        return

    await query.edit_message_text(

        "💸 **WITHDRAW REQUEST**\n\n"

        f"💰 Your Balance: {balance} Points\n\n"

        "⚠️ Withdrawal request system is "
        "not configured yet.\n\n"

        "Please wait for the withdrawal "
        "method to be enabled.",

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "💸 Withdraw Center",
                        callback_data="withdraw",
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


# ==================================================
# WITHDRAW HISTORY
# ==================================================

async def withdraw_history(
    query,
    user_id,
):

    user = get_user(user_id)

    history = user.get(
        "withdraw_history",
        [],
    )

    if not history:

        text = (
            "📜 **WITHDRAW HISTORY**\n\n"
            "No withdrawal history found."
        )

    else:

        text = "📜 **WITHDRAW HISTORY**\n\n"

        for item in history[-10:]:

            amount = item.get(
                "amount",
                0,
            )

            status = item.get(
                "status",
                "Unknown",
            )

            created_at = item.get(
                "time",
                0,
            )

            text += (
                f"💰 Amount: {amount} Points\n"
                f"📌 Status: {status}\n"
                f"🕒 {created_at}\n\n"
            )

    keyboard = [

        [
            InlineKeyboardButton(
                "💸 Withdraw Center",
                callback_data="withdraw",
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

        text,

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ==================================================
# VERIFY JOIN CALLBACK
# ==================================================

async def verify_join_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    # ==========================
    # BAN CHECK
    # ==========================

    if user.get(
        "banned",
        False,
    ):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    # ==========================
    # CHECK GROUPS
    # ==========================

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
                "Verify join failed | group=%s | user=%s | error=%s",
                group,
                user_id,
                error,
            )

            not_joined.append(group)

    # ==========================
    # NOT JOINED
    # ==========================

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

    # ==========================
    # GROUP REWARD
    # ==========================

    group_reward_given = user.get(
        "group_reward",
        False,
    )

    reward_text = ""

    if not group_reward_given:

        current_balance = user.get(
            "balance",
            0,
        )

        current_xp = user.get(
            "xp",
            0,
        )

        new_balance = (
            current_balance
            + GROUP_JOIN_REWARD
        )

        new_xp = (
            current_xp
            + DAILY_XP
        )

        update_user(
            user_id,
            {
                "balance": new_balance,

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

    # ==========================
    # SUCCESS
    # ==========================

    await query.edit_message_text(

        "✅ **VERIFICATION SUCCESSFUL!**\n\n"

        "🎉 You can now use "
        "Unlimited Energy Bot."

        f"{reward_text}",

        reply_markup=main_menu(),

        parse_mode="Markdown",
    )


# ==================================================
# MAIN CALLBACK ROUTER
# ==================================================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    # ==========================
    # BAN CHECK
    # ==========================

    if user.get(
        "banned",
        False,
    ):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    data = query.data

    # ==========================
    # HOME
    # ==========================

    if data == "home":

        await query.edit_message_text(

            "🏠 **MAIN MENU**\n\n"
            "👇 Choose an option:",

            reply_markup=main_menu(),

            parse_mode="Markdown",
        )

        return

    # ==========================
    # EARN
    # ==========================

    if data == "earn":

        await earn_page(
            update,
            context,
        )

        return

    # ==========================
    # DAILY BONUS
    # ==========================

    if data == "daily_bonus":

        await daily_bonus(
            update,
            context,
        )

        return

    # ==========================
    # SPIN
    # ==========================

    if data == "spin":

        await spin_wheel(
            update,
            context,
        )

        return

    # ==========================
    # LUCKY BOX
    # ==========================

    if data == "lucky_box":

        await lucky_box(
            update,
            context,
        )

        return

    # ==========================
    # SCRATCH
    # ==========================

    if data == "scratch":

        await scratch_card(
            update,
            context,
        )

        return

    # ==========================
    # ENERGY
    # ==========================

    if data == "energy":

        await energy_page(
            update,
            context,
        )

        return

    # ==========================
    # BALANCE
    # ==========================

    if data == "balance":

        await show_balance(
            query,
            user_id,
        )

        return

    # ==========================
    # PROFILE
    # ==========================

    if data == "profile":

        await show_profile(
            query,
            user_id,
        )

        return

    # ==========================
    # REFERRAL
    # ==========================

    if data == "refer":

        await show_referral(
            query,
            context,
            user_id,
        )

        return

    # ==========================
    # RANK
    # ==========================

    if data == "rank":

        await show_rank(
            query,
            user_id,
        )

        return

    # ==========================
    # WITHDRAW
    # ==========================

    if data == "withdraw":

        await show_withdraw(
            query,
            user_id,
        )

        return

    # ==========================
    # WITHDRAW REQUEST
    # ==========================

    if data == "withdraw_request":

        await withdraw_request(
            query,
            user_id,
        )

        return

    # ==========================
    # WITHDRAW HISTORY
    # ==========================

    if data == "withdraw_history":

        await withdraw_history(
            query,
            user_id,
        )

        return

    # ==========================
    # HELP
    # ==========================

    if data == "help":

        await show_help(
            query,
        )

        return

    # ==========================
    # VERIFY JOIN
    # ==========================

    if data == "verify_join":

        await verify_join_callback(
            update,
            context,
        )

        return

    # ==========================
    # UNKNOWN CALLBACK
    # ==========================

    await query.edit_message_text(

        "⚠️ **OPTION NOT AVAILABLE**\n\n"

        "This option is not available yet.\n\n"
        "🚀 More features are coming soon!",

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ]
            ]
        ),

        parse_mode="Markdown",
    )


# ==================================================
# CALLBACK EXPORT
# ==================================================

CALLBACK_FUNCTIONS = {

    "button_callback": button_callback,

    "verify_join_callback":
        verify_join_callback,

    }
