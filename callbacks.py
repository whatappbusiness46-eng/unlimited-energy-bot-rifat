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
    earn,
    daily_bonus,
    tasks,
    shortlinks,
    energy,
    claim_test_task,
    spin_wheel,
    lucky_box,
    scratch_card,
)


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
        ],

    ]

    await query.edit_message_text(

        "💰 YOUR WALLET\n\n"

        f"💰 Earn Balance: {balance} Points\n"
        f"🎁 Bonus Balance: {bonus} Points\n"
        f"💎 Premium Balance: "
        f"{premium_balance} Points\n\n"

        f"💵 Total Balance: {total} Points",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
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

        "👤 YOUR PROFILE\n\n"

        f"🆔 ID: {user_id}\n\n"

        f"💰 Balance: {balance}\n"
        f"🎁 Bonus: {bonus}\n"
        f"💎 Premium Balance: "
        f"{premium_balance}\n"
        f"👥 Referrals: {referrals}\n\n"

        f"⭐ XP: {xp}\n"
        f"🏆 Level: {level}\n"
        f"🎖 Rank: {rank}\n\n"

        f"👑 Premium: {premium_status}\n"
        f"💎 VIP: {vip_status}",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
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

        "👥 REFERRAL CENTER\n\n"

        "🎁 Invite friends and earn rewards!\n\n"

        f"👥 Total Referrals: {referrals}\n"
        f"💰 Referral Earnings: "
        f"{referral_earn} Points\n"
        f"⭐ Referral XP: {referral_xp}\n\n"

        "🔗 Your Referral Link:\n"
        f"{referral_link}\n\n"

        "📢 Share your link with your friends.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
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

    await query.edit_message_text(

        "🏆 YOUR RANK\n\n"

        f"🎖 Rank: {rank}\n"
        f"🏆 Level: {level}\n"
        f"⭐ XP: {xp}\n\n"

        "Keep earning to reach "
        "the next rank! 🚀",

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
    )


# ==================================================
# HELP PAGE
# ==================================================

async def show_help(
    query,
):

    await query.edit_message_text(

        "❓ HELP CENTER\n\n"

        "💰 Earn — Complete available tasks\n"
        "💳 Balance — Check your wallet\n"
        "👤 Profile — View your account\n"
        "👥 Referral — Invite friends\n"
        "🏆 Rank — Check your progress\n"
        "💸 Withdraw — Request withdrawal\n"
        "👑 Premium — Premium features\n\n"

        "🆘 Need help?\n"
        "Contact the Admin.",

        reply_markup=InlineKeyboardMarkup(

            [

                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ],

            ]

        ),
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

    if user.get(
        "banned",
        False,
    ):

        await query.edit_message_text(
            "🚫 Your account has been banned."
        )

        return

    data = query.data

    # ==================================================
    # HOME
    # ==================================================

    if data == "home":

        await query.edit_message_text(

            "🏠 MAIN MENU\n\n"
            "👇 Choose an option:",

            reply_markup=main_menu(),
        )

        return

    # ==================================================
    # EARN
    # ==================================================

    if data == "earn":

        await earn(
            update,
            context,
        )

        return

    # ==================================================
    # DAILY BONUS
    # ==================================================

    if data == "daily_bonus":

        await daily_bonus(
            update,
            context,
        )

        return

    # ==================================================
    # TASKS
    # ==================================================

    if data == "tasks":

        await tasks(
            update,
            context,
        )

        return

    # ==================================================
    # SHORTLINKS
    # ==================================================

    if data == "shortlinks":

        await shortlinks(
            update,
            context,
        )

        return

    # ==================================================
    # ENERGY
    # ==================================================

    if data == "energy":

        await energy(
            update,
            context,
        )

        return

    # ==================================================
    # TEST TASK
    # ==================================================

    if data == "claim_test_task":

        await claim_test_task(
            update,
            context,
        )

        return

    # ==================================================
    # SPIN
    # ==================================================

    if data == "spin":

        await spin_wheel(
            update,
            context,
        )

        return

    # ==================================================
    # LUCKY BOX
    # ==================================================

    if data == "lucky_box":

        await lucky_box(
            update,
            context,
        )

        return

    # ==================================================
    # SCRATCH
    # ==================================================

    if data == "scratch":

        await scratch_card(
            update,
            context,
        )

        return

    # ==================================================
    # BALANCE
    # ==================================================

    if data == "balance":

        await show_balance(
            query,
            user_id,
        )

        return

    # ==================================================
    # PROFILE
    # ==================================================

    if data == "profile":

        await show_profile(
            query,
            user_id,
        )

        return

    # ==================================================
    # REFERRAL
    # ==================================================

    if data == "refer":

        await show_referral(
            query,
            context,
            user_id,
        )

        return

    # ==================================================
    # RANK
    # ==================================================

    if data == "rank":

        await show_rank(
            query,
            user_id,
        )

        return

    # ==================================================
    # HELP
    # ==================================================

    if data == "help":

        await show_help(
            query,
        )

        return

    # ==================================================
    # VERIFY JOIN
    # ==================================================

    if data == "verify_join":

        await verify_join_callback(
            update,
            context,
        )

        return

    # ==================================================
    # UNKNOWN CALLBACK
    # ==================================================

    await query.edit_message_text(

        "⚠️ This option is not available yet.\n\n"
        "🚀 More features are coming soon!",

        reply_markup=InlineKeyboardMarkup(

            [

                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ],

            ]

        ),
    )


# ==================================================
# VERIFY JOIN
# ==================================================

async def verify_join_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

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

        except Exception:

            not_joined.append(
                group
            )

    if not_joined:

        await query.edit_message_text(

            "❌ You haven't joined all "
            "required groups yet.\n\n"

            "Please join all groups and "
            "press ✅ Verify again.",

            reply_markup=force_join_menu(),
        )

        return

    await query.edit_message_text(

        "✅ VERIFICATION SUCCESSFUL!\n\n"

        "🎉 You can now use "
        "Unlimited Energy Bot.",

        reply_markup=main_menu(),
    )


# ==================================================
# CALLBACK EXPORTS
# ==================================================

CALLBACK_FUNCTIONS = {
    "button_callback": button_callback,
    "verify_join_callback": verify_join_callback,
        }
