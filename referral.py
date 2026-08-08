import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import REFERRAL_REWARD
from database import (
    get_user,
    update_user,
    add_balance,
    add_activity,
)


logger = logging.getLogger(__name__)


# ==========================
# REFERRAL MENU
# ==========================

def referral_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🔗 Get Referral Link",
                callback_data="referral_link"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 My Referrals",
                callback_data="referral_stats"
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
# REFERRAL PAGE
# ==========================

async def referral(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    referrals = user.get(
        "referrals",
        0
    )

    referral_earn = user.get(
        "referral_earn",
        0
    )

    bot_username = context.bot.username

    referral_link = (
        f"https://t.me/{bot_username}"
        f"?start=ref_{user_id}"
    )

    await update.message.reply_text(

        "👥 REFERRAL PROGRAM\n\n"

        "🎁 Invite your friends and earn rewards!\n\n"

        f"💰 Reward per referral: "
        f"{REFERRAL_REWARD} Points\n\n"

        f"👥 Total Referrals: {referrals}\n"
        f"💵 Referral Earnings: "
        f"{referral_earn} Points\n\n"

        "🔗 Your Referral Link:\n"
        f"{referral_link}\n\n"

        "📢 Share your link with your friends!",

        reply_markup=referral_menu()

    )


# ==========================
# REFERRAL LINK CALLBACK
# ==========================

async def referral_link_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    bot_username = context.bot.username

    referral_link = (
        f"https://t.me/{bot_username}"
        f"?start=ref_{user_id}"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "📊 Referral Stats",
                callback_data="referral_stats"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Referral Menu",
                callback_data="refer"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        ]

    ]

    await query.edit_message_text(

        "🔗 YOUR REFERRAL LINK\n\n"

        f"{referral_link}\n\n"

        f"🎁 You earn "
        f"{REFERRAL_REWARD} Points "
        "for every valid referral.\n\n"

        "📢 Share this link with your friends!",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )

    )


# ==========================
# REFERRAL STATISTICS
# ==========================

async def referral_stats_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    referrals = user.get(
        "referrals",
        0
    )

    referral_earn = user.get(
        "referral_earn",
        0
    )

    referred_by = user.get(
        "referred_by",
        None
    )

    if referred_by:

        referred_text = (
            f"👤 Referred By: {referred_by}"
        )

    else:

        referred_text = (
            "👤 Referred By: None"
        )

    keyboard = [

        [
            InlineKeyboardButton(
                "🔗 Referral Link",
                callback_data="referral_link"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        ]

    ]

    await query.edit_message_text(

        "📊 REFERRAL STATISTICS\n\n"

        f"👥 Total Referrals: {referrals}\n"
        f"💰 Referral Earnings: "
        f"{referral_earn} Points\n\n"

        f"{referred_text}\n\n"

        f"🎁 Reward per referral: "
        f"{REFERRAL_REWARD} Points",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )

    )


# ==========================
# PROCESS REFERRAL
# ==========================

def process_referral(
    new_user_id,
    referral_id
):

    # ==========================
    # INVALID REFERRAL
    # ==========================

    if not referral_id:

        return False

    # ==========================
    # SELF REFERRAL BLOCK
    # ==========================

    if new_user_id == referral_id:

        logger.warning(
            "Self referral blocked | user=%s",
            new_user_id
        )

        return False

    # ==========================
    # GET USERS
    # ==========================

    new_user = get_user(
        new_user_id
    )

    referrer = get_user(
        referral_id
    )

    # ==========================
    # ALREADY REFERRED
    # ==========================

    if new_user.get(
        "referred_by"
    ) is not None:

        logger.info(
            "Duplicate referral blocked | user=%s",
            new_user_id
        )

        return False

    # ==========================
    # REFERRED USER CHECK
    # ==========================

    if not referrer:

        return False

    # ==========================
    # SAVE REFERRAL
    # ==========================

    update_user(

        new_user_id,

        {
            "referred_by": referral_id
        }

    )

    # ==========================
    # REFERRER REWARD
    # ==========================

    add_balance(
        referral_id,
        REFERRAL_REWARD
    )

    # ==========================
    # UPDATE REFERRAL COUNT
    # ==========================

    current_referrals = referrer.get(
        "referrals",
        0
    )

    current_earn = referrer.get(
        "referral_earn",
        0
    )

    update_user(

        referral_id,

        {
            "referrals":
                current_referrals + 1,

            "referral_earn":
                current_earn + REFERRAL_REWARD,
        }

    )

    # ==========================
    # ACTIVITY
    # ==========================

    add_activity(

        referral_id,

        "👥 Referral reward received",

        REFERRAL_REWARD

    )

    logger.info(

        "Referral successful | "
        "new_user=%s | referrer=%s | reward=%s",

        new_user_id,
        referral_id,
        REFERRAL_REWARD

    )

    return True


# ==========================
# HANDLER EXPORTS
# ==========================

HANDLER_FUNCTIONS = {

    "referral": referral,

    "referral_link_callback":
        referral_link_callback,

    "referral_stats_callback":
        referral_stats_callback,

    "process_referral":
        process_referral,

  }
