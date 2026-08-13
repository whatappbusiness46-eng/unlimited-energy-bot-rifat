import time
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import ADMIN_ID

from database import (
    get_user,
    update_user,
    add_balance,
    remove_balance,
    users,
    db,
    get_withdrawals,
    approve_withdrawal,
    reject_withdrawal,
    pending_withdrawals_count,
    total_withdrawals,
)


logger = logging.getLogger(__name__)


# ==================================================
# ADMIN CHECK
# ==================================================

def is_admin(user_id):
    try:
        return int(user_id) == int(ADMIN_ID)
    except (TypeError, ValueError):
        return False


def admin_only(user_id):
    return is_admin(user_id)


# ==================================================
# COMMON KEYBOARDS
# ==================================================

def admin_back():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 Admin Panel",
                    callback_data="admin",
                )
            ]
        ]
    )


def admin_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "👥 Users",
                callback_data="admin_users",
            ),
            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="admin_stats",
            ),
        ],

        [
            InlineKeyboardButton(
                "💰 Manage Balance",
                callback_data="admin_balance",
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 Manage Rewards",
                callback_data="admin_rewards",
            )
        ],

        [
            InlineKeyboardButton(
                "🎯 Manage Tasks",
                callback_data="admin_tasks",
            )
        ],

        [
            InlineKeyboardButton(
                "🎡 Wheel Settings",
                callback_data="admin_wheel",
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 Lucky Box",
                callback_data="admin_lucky",
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Referral Settings",
                callback_data="admin_referral",
            )
        ],
        [
            InlineKeyboardButton(
                "💸 Withdrawals",
                callback_data="admin_withdrawals",
            )
        ],

        [
            InlineKeyboardButton(
                "🔒 Ban / Unban",
                callback_data="admin_ban",
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Broadcast",
                callback_data="admin_broadcast",
            )
        ],

        [
            InlineKeyboardButton(
                "⚙️ Bot Settings",
                callback_data="admin_settings",
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


def user_info_keyboard(user_id):

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "💰 Add Balance",
                    callback_data=f"admin_add_{user_id}",
                )
            ],

            [
                InlineKeyboardButton(
                    "➖ Remove Balance",
                    callback_data=f"admin_remove_{user_id}",
                )
            ],

            [
                InlineKeyboardButton(
                    "🔒 Ban / Unban",
                    callback_data=f"admin_toggleban_{user_id}",
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 Users",
                    callback_data="admin_users",
                )
            ],

        ]
    )


# ==================================================
# ADMIN PANEL
# ==================================================

async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    user_id = update.effective_user.id

    if not admin_only(user_id):

        if update.callback_query:

            await update.callback_query.answer(
                "🚫 Admin only.",
                show_alert=True,
            )

        elif update.message:

            await update.message.reply_text(
                "🚫 You are not an Admin."
            )

        return

    text = (
        "🛡️ **ADMIN CONTROL PANEL**\n\n"
        "Welcome Admin.\n\n"
        "Choose an option below:"
    )

    if update.callback_query:

        query = update.callback_query

        await query.answer()

        await query.edit_message_text(
            text,
            reply_markup=admin_menu(),
            parse_mode="Markdown",
        )

    elif update.message:

        await update.message.reply_text(
            text,
            reply_markup=admin_menu(),
            parse_mode="Markdown",
        )


# ==================================================
# USERS
# ==================================================

async def admin_users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    total = users.count_documents({})

    active_24h = users.count_documents(
        {
            "last_login": {
                "$gte": int(time.time()) - 86400
            }
        }
    )

    banned = users.count_documents(
        {
            "banned": True
        }
    )

    await query.edit_message_text(

        "👥 **USER MANAGEMENT**\n\n"

        f"👥 Total Users: {total}\n"
        f"🟢 Active 24h: {active_24h}\n"
        f"🔒 Banned: {banned}\n\n"

        "Use the buttons below to manage users.",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "🔍 Find User",
                        callback_data="admin_find_user",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin",
                    )
                ],

            ]
        ),

        parse_mode="Markdown",
    )


# ==================================================
# FIND USER
# ==================================================

async def admin_find_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    context.user_data["admin_action"] = "find_user"

    await query.edit_message_text(

        "🔍 **FIND USER**\n\n"

        "Send the Telegram User ID.\n\n"

        "Example:\n"
        "`123456789`",

        reply_markup=admin_back(),

        parse_mode="Markdown",
    )


# ==================================================
# SHOW USER
# ==================================================

async def show_admin_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
):

    query = update.callback_query

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "❌ User not found.",
            reply_markup=admin_back(),
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

    xp = user.get(
        "xp",
        0,
    )

    level = user.get(
        "level",
        1,
    )

    referrals = user.get(
        "referrals",
        0,
    )

    banned = user.get(
        "banned",
        False,
    )

    status = (
        "🔒 BANNED"
        if banned
        else "🟢 ACTIVE"
    )

    await query.edit_message_text(

        "👤 **USER INFORMATION**\n\n"

        f"🆔 ID: `{user_id}`\n"
        f"📌 Status: {status}\n\n"

        f"💰 Balance: {balance}\n"
        f"🎁 Bonus: {bonus}\n"
        f"💎 Premium Balance: {premium_balance}\n\n"

        f"⭐ XP: {xp}\n"
        f"🏆 Level: {level}\n"
        f"👥 Referrals: {referrals}\n",

        reply_markup=user_info_keyboard(
            user_id
        ),

        parse_mode="Markdown",
    )


# ==================================================
# BALANCE MENU
# ==================================================

async def admin_balance(
    update,
    context,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    context.user_data["admin_action"] = "find_user"

    await query.edit_message_text(

        "💰 **MANAGE BALANCE**\n\n"

        "Send the User ID whose balance "
        "you want to manage.",

        reply_markup=admin_back(),

        parse_mode="Markdown",
    )


# ==================================================
# ADD BALANCE
# ==================================================

async def admin_add_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    user_id = int(
        query.data.replace(
            "admin_add_",
            "",
            1,
        )
    )

    context.user_data["admin_action"] = "add_balance"

    context.user_data["admin_target"] = user_id

    await query.edit_message_text(

        "💰 **ADD BALANCE**\n\n"

        f"User ID: `{user_id}`\n\n"

        "Send the amount to add.\n\n"

        "Example: `100`",

        reply_markup=admin_back(),

        parse_mode="Markdown",
    )


# ==================================================
# REMOVE BALANCE
# ==================================================

async def admin_remove_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    user_id = int(
        query.data.replace(
            "admin_remove_",
            "",
            1,
        )
    )

    context.user_data["admin_action"] = "remove_balance"

    context.user_data["admin_target"] = user_id

    await query.edit_message_text(

        "➖ **REMOVE BALANCE**\n\n"

        f"User ID: `{user_id}`\n\n"

        "Send amount to remove.\n\n"

        "Example: `50`",

        reply_markup=admin_back(),

        parse_mode="Markdown",
    )


# ==================================================
# BAN MENU
# ==================================================

async def admin_ban(
    update,
    context,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    context.user_data["admin_action"] = "find_user"

    await query.edit_message_text(

        "🔒 **BAN / UNBAN USER**\n\n"

        "Send the Telegram User ID.",

        reply_markup=admin_back(),

        parse_mode="Markdown",
    )


# ==================================================
# BAN / UNBAN
# ==================================================

async def admin_toggle_ban(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    user_id = int(
        query.data.replace(
            "admin_toggleban_",
            "",
            1,
        )
    )

    user = get_user(user_id)

    if not user:

        await query.edit_message_text(
            "❌ User not found.",
            reply_markup=admin_back(),
        )

        return

    current = user.get(
        "banned",
        False,
    )

    new_status = not current

    update_user(
        user_id,
        {
            "banned": new_status,
        },
    )

    status = (
        "🔒 BANNED"
        if new_status
        else "🟢 UNBANNED"
    )

    await query.edit_message_text(

        f"✅ User `{user_id}` is now {status}.",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "👤 User Info",
                        callback_data=f"admin_view_{user_id}",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin",
                    )
                ],

            ]
        ),

        parse_mode="Markdown",
    )
# ==================================================
# WITHDRAWAL MANAGEMENT
# ==================================================

async def admin_withdrawals(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    if not admin_only(query.from_user.id):
        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )
        return

    await query.answer()

    pending = get_withdrawals(
        status="pending",
        limit=30,
    )

    pending_count = pending_withdrawals_count()
    approved_total = total_withdrawals()

    if not pending:
        await query.edit_message_text(
            "💸 **WITHDRAWAL MANAGEMENT**\n\n"
            f"🟡 Pending: {pending_count}\n"
            f"🟢 Approved Total: {approved_total} Points\n\n"
            "✅ No pending withdrawals.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh",
                            callback_data="admin_withdrawals",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 Admin Panel",
                            callback_data="admin",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )
        return

    buttons = []

    for item in pending[:20]:
        withdrawal_id = item.get(
            "withdrawal_id",
            "N/A",
        )

        amount = int(
            item.get(
                "amount",
                0,
            )
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    f"💸 {withdrawal_id} • {amount}",
                    callback_data=(
                        f"admin_withdraw_view_{withdrawal_id}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="admin_withdrawals",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔙 Admin Panel",
                callback_data="admin",
            )
        ]
    )

    await query.edit_message_text(
        "💸 **WITHDRAWAL MANAGEMENT**\n\n"
        f"🟡 Pending: {pending_count}\n"
        f"🟢 Approved Total: {approved_total} Points\n\n"
        "Select a pending withdrawal:",
        reply_markup=InlineKeyboardMarkup(
            buttons
        ),
        parse_mode="Markdown",
    )


async def admin_withdrawal_view(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    if not admin_only(query.from_user.id):
        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )
        return

    withdrawal_id = query.data.replace(
        "admin_withdraw_view_",
        "",
        1,
    )

    records = get_withdrawals(
        status="pending",
        limit=100,
    )

    withdrawal = next(
        (
            item
            for item in records
            if item.get(
                "withdrawal_id"
            ) == withdrawal_id
        ),
        None,
    )

    if not withdrawal:
        await query.answer(
            "Withdrawal not found or already processed.",
            show_alert=True,
        )

        await admin_withdrawals(
            update,
            context,
        )

        return

    await query.answer()

    user_id = int(
        withdrawal.get(
            "user_id",
            0,
        )
    )

    amount = int(
        withdrawal.get(
            "amount",
            0,
        )
    )

    method = withdrawal.get(
        "method",
        "N/A",
    )

    account = withdrawal.get(
        "payment_account",
        "N/A",
    )

    created_at = withdrawal.get(
        "created_at",
        0,
    )

    if created_at:
        created_text = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(
                int(created_at)
            ),
        )
    else:
        created_text = "N/A"

    await query.edit_message_text(
        "💸 **WITHDRAWAL REQUEST**\n\n"
        f"🆔 ID: `{withdrawal_id}`\n"
        f"👤 User ID: `{user_id}`\n"
        f"💰 Amount: {amount} Points\n"
        f"💳 Method: {method}\n"
        f"📱 Account: `{account}`\n"
        f"🕒 Created: {created_text}\n"
        "🟡 Status: Pending\n\n"
        "Choose an action:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🟢 Approve",
                        callback_data=(
                            f"admin_withdraw_approve_{withdrawal_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔴 Reject",
                        callback_data=(
                            f"admin_withdraw_reject_{withdrawal_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Pending Withdrawals",
                        callback_data="admin_withdrawals",
                    )
                ],
            ]
        ),
        parse_mode="Markdown",
    )


async def admin_withdrawal_approve(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    if not admin_only(query.from_user.id):
        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )
        return

    withdrawal_id = query.data.replace(
        "admin_withdraw_approve_",
        "",
        1,
    )

    records = get_withdrawals(
        status="pending",
        limit=100,
    )

    withdrawal = next(
        (
            item
            for item in records
            if item.get(
                "withdrawal_id"
            ) == withdrawal_id
        ),
        None,
    )

    if not withdrawal:
        await query.answer(
            "Withdrawal not found.",
            show_alert=True,
        )
        return

  
    context.user_data[
        "withdrawal_reject_id"
    ] = withdrawal_id

    context.user_data[
        "admin_action"
    ] = "withdrawal_reject_reason"

    await query.answer()

    await query.edit_message_text(
        "🔴 **REJECT WITHDRAWAL**\n\n"
        f"🆔 `{withdrawal_id}`\n\n"
        "Send the rejection reason.",
        reply_markup=admin_back(),
        parse_mode="Markdown",
    )

# ==================================================
# STATISTICS
# ==================================================

async def admin_statistics(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    total_users = users.count_documents({})

    active_users = users.count_documents(
        {
            "last_login": {
                "$gte": int(time.time()) - 86400
            }
        }
    )

    banned_users = users.count_documents(
        {
            "banned": True
        }
    )

    pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": "$total_earned"
                },
            }
        }
    ]

    result = list(
        users.aggregate(pipeline)
    )

    total_distributed = 0

    if result:

        total_distributed = result[0].get(
            "total",
            0,
        )

    referral_pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": "$referral_earn"
                },
            }
        }
    ]

    referral_result = list(
        users.aggregate(
            referral_pipeline
        )
    )

    referral_earnings = 0

    if referral_result:

        referral_earnings = referral_result[0].get(
            "total",
            0,
        )

    spin_pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": "$spin_wins"
                },
            }
        }
    ]

    spin_result = list(
        users.aggregate(
            spin_pipeline
        )
    )

    spin_wins = 0

    if spin_result:

        spin_wins = spin_result[0].get(
            "total",
            0,
        )

    await query.edit_message_text(

        "📊 **ADVANCED STATISTICS**\n\n"

        f"👥 Total Users: {total_users}\n"
        f"🟢 Active Users (24h): {active_users}\n"
        f"🔒 Banned Users: {banned_users}\n\n"

        f"💰 Total Points Distributed: "
        f"{total_distributed}\n"

        f"👥 Referral Earnings: "
        f"{referral_earnings}\n"

        f"🎡 Winning Spins: "
        f"{spin_wins}\n",

        reply_markup=admin_back(),

        parse_mode="Markdown",
    )

# ==================================================
# REWARD SETTINGS
# ==================================================

async def admin_rewards(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not admin_only(query.from_user.id):

        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )

        return

    await query.answer()

    settings = (
        db["bot_settings"].find_one(
            {"_id": "main"}
        )
        or {}
    )

    daily_bonus = settings.get(
        "daily_bonus",
        5,
    )

    group_reward = settings.get(
        "group_reward",
        20,
    )

    await query.edit_message_text(

        "🎁 **REWARD SETTINGS**\n\n"

        f"🎁 Daily Bonus: {daily_bonus}\n"
        f"👥 Group Join Reward: {group_reward}\n\n"

        "Reward configuration is stored "
        "in MongoDB.",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "🎁 Change Daily Bonus",
                        callback_data="admin_set_daily",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "👥 Change Group Reward",
                        callback_data="admin_set_group",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin",
                    )
                ],

            ]
        ),

        parse_mode="Markdown",
    )

# ==================================================
# DAILY REWARD
# ==================================================

async def admin_set_daily(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = "set_daily"

    await query.edit_message_text(
        "🎁 Send new Daily Bonus amount:",
        reply_markup=admin_back(),
    )


# ==================================================
# GROUP REWARD
# ==================================================

async def admin_set_group(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = "set_group"

    await query.edit_message_text(
        "👥 Send new Group Join Reward:",
        reply_markup=admin_back(),
    )


# ==================================================
# TASK SETTINGS
# ==================================================

async def admin_tasks(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    settings = (
        db["bot_settings"].find_one(
            {"_id": "main"}
        )
        or {}
    )

    reward = settings.get(
        "task_reward",
        10,
    )

    daily_limit = settings.get(
        "daily_task_limit",
        20,
    )

    await query.edit_message_text(

        "🎯 **TASK SETTINGS**\n\n"

        f"💰 Test Task Reward: {reward}\n"
        f"📊 Daily Limit: {daily_limit}\n\n"

        "Task configuration is stored "
        "in MongoDB.",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "💰 Change Reward",
                        callback_data="admin_set_task_reward",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "📊 Change Daily Limit",
                        callback_data="admin_set_task_limit",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin",
                    )
                ],

            ]
        ),

        parse_mode="Markdown",
    )


async def admin_set_task_reward(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_task_reward"
    )

    await query.edit_message_text(
        "🎯 Send new Task Reward:",
        reply_markup=admin_back(),
    )


async def admin_set_task_limit(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_task_limit"
    )

    await query.edit_message_text(
        "🎯 Send new Daily Task Limit:",
        reply_markup=admin_back(),
    )

# ==================================================
# WHEEL SETTINGS
# ==================================================

async def admin_wheel(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    settings = (
        db["bot_settings"].find_one(
            {"_id": "main"}
        )
        or {}
    )

    minimum = settings.get(
        "spin_min",
        1,
    )

    maximum = settings.get(
        "spin_max",
        20,
    )

    cooldown = settings.get(
        "spin_cooldown",
        60,
    )

    await query.edit_message_text(

        "🎡 **WHEEL SETTINGS**\n\n"

        f"🔽 Minimum Reward: {minimum}\n"
        f"🔼 Maximum Reward: {maximum}\n"
        f"⏳ Cooldown: {cooldown}s",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "🔽 Set Minimum",
                        callback_data="admin_set_spin_min",
                    ),

                    InlineKeyboardButton(
                        "🔼 Set Maximum",
                        callback_data="admin_set_spin_max",
                    ),
                ],

                [
                    InlineKeyboardButton(
                        "⏳ Set Cooldown",
                        callback_data="admin_set_spin_cd",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin",
                    )
                ],

            ]
        ),

        parse_mode="Markdown",
    )


async def admin_set_spin_min(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_spin_min"
    )

    await query.edit_message_text(
        "🎡 Send new minimum reward:",
        reply_markup=admin_back(),
    )


async def admin_set_spin_max(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_spin_max"
    )

    await query.edit_message_text(
        "🎡 Send new maximum reward:",
        reply_markup=admin_back(),
    )


async def admin_set_spin_cd(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_spin_cd"
    )

    await query.edit_message_text(
        "🎡 Send new cooldown in seconds:",
        reply_markup=admin_back(),
    )
    
