import time
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import ADMIN_ID

from shortlinks import (
    get_shortlinks,
    register_shortlink,
    set_shortlink_enabled,
    delete_shortlink,
)

from database import (
    get_user,
    update_user,
    add_balance,
    remove_balance,
    reset_all_balances,
    users,
    db,
    get_withdrawals,
    approve_withdrawal,
    reject_withdrawal,
    pending_withdrawals_count,
    total_withdrawals,
    is_vip_purchase_enabled,
    set_vip_purchase_enabled,
)
from tasks import (
    get_tasks,
    get_task,
    register_task,
    update_task,
    delete_task,
    set_task_enabled,
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
async def admin_reset_all_balances(update, context):
    query = update.callback_query

    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer("🚫 Admin only.", show_alert=True)
        return

    await query.answer()

    await query.edit_message_text(
        "⚠️ *RESET ALL BALANCES*\n\n"
        "This will set EVERY user's main balance to 0.\n\n"
        "Premium/VIP status, bonus balance, XP, level, "
        "and transaction history will NOT be changed.\n\n"
        "Are you absolutely sure?",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⚠️ YES, RESET ALL",
                    callback_data="admin_confirm_reset_balances",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="admin",
                )
            ],
        ]),
        parse_mode="Markdown",
    )


async def admin_confirm_reset_balances(update, context):
    query = update.callback_query

    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer("🚫 Admin only.", show_alert=True)
        return

    await query.answer()

    result = reset_all_balances()

    await query.edit_message_text(
        "✅ *ALL BALANCES RESET*\n\n"
        f"👥 Matched: {result['matched']}\n"
        f"🔄 Modified: {result['modified']}\n\n"
        "Every user's main balance is now 0.",
        reply_markup=admin_back(),
        parse_mode="Markdown",
    )

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
    vip_status = (
    "🟢 ON"
    if is_vip_purchase_enabled()
    else "🔴 OFF"
    )
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
                "🧹 Reset All Balances",
                callback_data="admin_reset_balances",
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
                "🔗 Shortlinks",
                callback_data="admin_shortlinks",
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
                "💎 VIP Purchase ON/OFF",
                callback_data="admin_vip_toggle",
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
# SHORTLINK MANAGEMENT
# ==================================================

async def admin_shortlinks(update, context):
    query = update.callback_query
    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer("🚫 Admin only.", show_alert=True)
        return

    await query.answer()
    items = get_shortlinks(include_disabled=True)
    buttons = [[InlineKeyboardButton("➕ Add Shortlink", callback_data="admin_add_shortlink")]]

    for item in items[:30]:
        status = "🟢" if item.get("enabled", True) else "🔴"
        sid = str(item.get("id"))
        buttons.append([
            InlineKeyboardButton(
                f"{status} {item.get('name', sid)} | {item.get('reward', 0)}",
                callback_data=f"admin_shortlink_toggle_{sid}",
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                f"🗑 Delete {sid}",
                callback_data=f"admin_shortlink_delete_{sid}",
            )
        ])

    buttons.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin")])
    await query.edit_message_text(
        "🔗 **SHORTLINK MANAGEMENT**\n\n"
        f"Configured: {len(items)}\n\n"
        "Add format: `id|name|url|reward|cooldown`\n"
        "Example: `sl1|Example|https://example.com/go|10|86400`",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def admin_add_shortlink(update, context):
    query = update.callback_query
    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer("🚫 Admin only.", show_alert=True)
        return
    await query.answer()
    context.user_data["admin_action"] = "add_shortlink"
    await query.edit_message_text(
        "🔗 **ADD SHORTLINK**\n\n"
        "Send: `id|name|url|reward|cooldown`\n\n"
        "Example: `sl1|Example|https://example.com/go|10|86400`",
        reply_markup=admin_back(),
        parse_mode="Markdown",
    )


async def admin_shortlink_toggle(update, context):
    query = update.callback_query
    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer("🚫 Admin only.", show_alert=True)
        return
    sid = str(query.data).replace("admin_shortlink_toggle_", "", 1)
    item = next((x for x in get_shortlinks(include_disabled=True) if str(x.get("id")) == sid), None)
    if not item:
        await query.answer("Shortlink not found.", show_alert=True)
        return
    new_state = not bool(item.get("enabled", True))
    if set_shortlink_enabled(sid, new_state):
        await query.answer("🟢 Enabled" if new_state else "🔴 Disabled")
    else:
        await query.answer("Update failed.", show_alert=True)
    await admin_shortlinks(update, context)


async def admin_shortlink_delete(update, context):
    query = update.callback_query
    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer("🚫 Admin only.", show_alert=True)
        return
    sid = str(query.data).replace("admin_shortlink_delete_", "", 1)
    if delete_shortlink(sid):
        await query.answer("🗑 Deleted")
    else:
        await query.answer("Shortlink not found.", show_alert=True)
    await admin_shortlinks(update, context)


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

    success = approve_withdrawal(withdrawal_id)

    if not success:
        await query.answer(
            "Withdrawal not found or already processed.",
            show_alert=True,
        )
        return

    records = get_withdrawals(status="approved", limit=100)
    withdrawal = next(
        (item for item in records if item.get("withdrawal_id") == withdrawal_id),
        None,
    )

    await query.answer("🟢 Withdrawal approved.")

    if withdrawal:
        user_id = int(withdrawal.get("user_id", 0))
        amount = int(withdrawal.get("amount", 0))
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🟢 **WITHDRAWAL APPROVED**\n\n"
                    f"🆔 ID: `{withdrawal_id}`\n"
                    f"💰 Amount: {amount} Points\n\n"
                    "Your withdrawal has been approved by Admin."
                ),
                parse_mode="Markdown",
            )
        except Exception:
            logger.exception(
                "Withdrawal approval notification failed | user=%s",
                user_id,
            )

    await admin_withdrawals(update, context)


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
# TASK MANAGEMENT
# ==================================================

async def admin_tasks(update, context):
    query = update.callback_query

    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer(
                "🚫 Admin only.",
                show_alert=True,
            )
        return

    await query.answer()

    items = get_tasks(include_disabled=True)

    buttons = [
        [
            InlineKeyboardButton(
                "➕ Add Task",
                callback_data="admin_task_add",
            )
        ]
    ]

    for task in items[:30]:
        task_id = str(task.get("id"))
        title = str(task.get("title", task_id))[:28]
        status = "🟢" if task.get("enabled", True) else "🔴"

        buttons.append([
            InlineKeyboardButton(
                f"{status} {title}",
                callback_data=f"admin_task_view_{task_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🔙 Admin Panel",
            callback_data="admin",
        )
    ])

    await query.edit_message_text(
        "🎯 **TASK MANAGEMENT**\n\n"
        f"📋 Total Tasks: {len(items)}\n\n"
        "Create, edit, enable, disable or delete tasks.",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def admin_task_add(update, context):
    query = update.callback_query

    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer(
                "🚫 Admin only.",
                show_alert=True,
            )
        return

    await query.answer()

    context.user_data["admin_action"] = "add_task"

    await query.edit_message_text(
        "➕ **ADD TASK**\n\n"
        "Send:\n\n"
        "`id|title|description|reward|url|cooldown`\n\n"
        "Example:\n"
        "`task1|Join Channel|Join our channel|20|https://t.me/example|86400`\n\n"
        "Use `-` for no URL.",
        reply_markup=admin_back(),
        parse_mode="Markdown",
    )


async def admin_task_view(update, context):
    query = update.callback_query

    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer(
                "🚫 Admin only.",
                show_alert=True,
            )
        return

    task_id = str(
        query.data.replace(
            "admin_task_view_",
            "",
            1,
        )
    )

    task = get_task(task_id)

    if not task:
        await query.answer(
            "❌ Task not found.",
            show_alert=True,
        )
        return

    await query.answer()

    enabled = bool(task.get("enabled", True))
    status = "🟢 ENABLED" if enabled else "🔴 DISABLED"

    buttons = [
        [
            InlineKeyboardButton(
                "✏️ Edit",
                callback_data=f"admin_task_edit_{task_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔴 Disable" if enabled else "🟢 Enable",
                callback_data=f"admin_task_toggle_{task_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Delete",
                callback_data=f"admin_task_delete_{task_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Tasks",
                callback_data="admin_tasks",
            )
        ],
    ]

    await query.edit_message_text(
        "🎯 **TASK DETAILS**\n\n"
        f"🆔 ID: `{task_id}`\n"
        f"📌 Title: {task.get('title', task_id)}\n"
        f"📝 Description: {task.get('description', '')}\n"
        f"💰 Reward: {task.get('reward', 0)}\n"
        f"🔗 URL: {task.get('url') or 'None'}\n"
        f"⏳ Cooldown: {task.get('cooldown', 0)}s\n"
        f"📊 Status: {status}",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def admin_task_edit(update, context):
    query = update.callback_query

    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer(
                "🚫 Admin only.",
                show_alert=True,
            )
        return

    task_id = str(
        query.data.replace(
            "admin_task_edit_",
            "",
            1,
        )
    )

    if not get_task(task_id):
        await query.answer(
            "❌ Task not found.",
            show_alert=True,
        )
        return

    await query.answer()

    context.user_data["admin_action"] = "edit_task"
    context.user_data["admin_task_id"] = task_id

    await query.edit_message_text(
        "✏️ **EDIT TASK**\n\n"
        f"Task ID: `{task_id}`\n\n"
        "Send:\n\n"
        "`title|description|reward|url|cooldown`\n\n"
        "Use `-` for no URL.",
        reply_markup=admin_back(),
        parse_mode="Markdown",
    )


async def admin_task_toggle(update, context):
    query = update.callback_query

    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer(
                "🚫 Admin only.",
                show_alert=True,
            )
        return

    task_id = str(
        query.data.replace(
            "admin_task_toggle_",
            "",
            1,
        )
    )

    task = get_task(task_id)

    if not task:
        await query.answer(
            "❌ Task not found.",
            show_alert=True,
        )
        return

    new_state = not bool(
        task.get("enabled", True)
    )

    if set_task_enabled(task_id, new_state):
        await query.answer(
            "🟢 Task enabled."
            if new_state
            else "🔴 Task disabled."
        )
    else:
        await query.answer(
            "❌ Update failed.",
            show_alert=True,
        )

    await admin_task_view(update, context)


async def admin_task_delete(update, context):
    query = update.callback_query

    if not query or not admin_only(query.from_user.id):
        if query:
            await query.answer(
                "🚫 Admin only.",
                show_alert=True,
            )
        return

    task_id = str(
        query.data.replace(
            "admin_task_delete_",
            "",
            1,
        )
    )

    if delete_task(task_id):
        await query.answer("🗑 Task deleted.")
    else:
        await query.answer(
            "❌ Task not found.",
            show_alert=True,
        )

    await admin_tasks(update, context)
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
    
# ==================================================
# LUCKY BOX
# ==================================================

async def admin_lucky(
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
        "lucky_min",
        5,
    )

    maximum = settings.get(
        "lucky_max",
        30,
    )

    await query.edit_message_text(

        "🎁 **LUCKY BOX SETTINGS**\n\n"

        f"🔽 Minimum Reward: {minimum}\n"
        f"🔼 Maximum Reward: {maximum}",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "🔽 Set Minimum",
                        callback_data="admin_set_lucky_min",
                    ),

                    InlineKeyboardButton(
                        "🔼 Set Maximum",
                        callback_data="admin_set_lucky_max",
                    ),
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


async def admin_set_lucky_min(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_lucky_min"
    )

    await query.edit_message_text(
        "🎁 Send new Lucky Box minimum:",
        reply_markup=admin_back(),
    )


async def admin_set_lucky_max(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_lucky_max"
    )

    await query.edit_message_text(
        "🎁 Send new Lucky Box maximum:",
        reply_markup=admin_back(),
    )

# ==================================================
# REFERRAL SETTINGS
# ==================================================

async def admin_referral(
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
        "referral_reward",
        10,
    )

    xp = settings.get(
        "referral_xp",
        10,
    )

    await query.edit_message_text(

        "👥 **REFERRAL SETTINGS**\n\n"

        f"💰 Referral Reward: {reward}\n"
        f"⭐ Referral XP: {xp}",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "💰 Change Reward",
                        callback_data="admin_set_ref_reward",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "⭐ Change XP",
                        callback_data="admin_set_ref_xp",
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


async def admin_set_ref_reward(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_ref_reward"
    )

    await query.edit_message_text(
        "👥 Send new Referral Reward:",
        reply_markup=admin_back(),
    )


async def admin_set_ref_xp(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "set_ref_xp"
    )

    await query.edit_message_text(
        "👥 Send new Referral XP:",
        reply_markup=admin_back(),
    )

# ==================================================
# BOT SETTINGS
# ==================================================

async def admin_settings(
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

    maintenance = settings.get(
        "maintenance",
        False,
    )

    notifications = settings.get(
        "notifications",
        True,
    )

    await query.edit_message_text(

        "⚙️ **BOT SETTINGS**\n\n"

        f"🔧 Maintenance: "
        f"{'ON' if maintenance else 'OFF'}\n"

        f"🔔 Notifications: "
        f"{'ON' if notifications else 'OFF'}",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "🔧 Toggle Maintenance",
                        callback_data=(
                            "admin_toggle_maintenance"
                        ),
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔔 Toggle Notifications",
                        callback_data=(
                            "admin_toggle_notifications"
                        ),
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
# BROADCAST
# ==================================================

async def admin_broadcast(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(

        "📢 **BROADCAST CENTER**\n\n"

        "Choose broadcast type:",

        reply_markup=InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "👥 All Users",
                        callback_data="admin_bc_all",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🟢 Active 24h",
                        callback_data="admin_bc_active",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "👤 Specific User",
                        callback_data="admin_bc_specific",
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


async def admin_bc_all(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "broadcast_all"
    )

    await query.edit_message_text(
        "📢 Send the message you want to broadcast.",
        reply_markup=admin_back(),
    )


async def admin_bc_active(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "broadcast_active"
    )

    await query.edit_message_text(
        "📢 Send the message for active users.",
        reply_markup=admin_back(),
    )


async def admin_bc_specific(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    context.user_data["admin_action"] = (
        "broadcast_specific"
    )

    await query.edit_message_text(

        "👤 **SPECIFIC USER BROADCAST**\n\n"

        "Send User ID first.\n\n"
        "Example:\n"
        "`123456789`",

        reply_markup=admin_back(),

        parse_mode="Markdown",
    )

# ==================================================
# ADMIN TEXT HANDLER
# ==================================================

async def admin_text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return False

    if not update.message:
        return False

    user_id = update.effective_user.id

    if not admin_only(user_id):
        return False

    action = context.user_data.get(
        "admin_action"
    )

    if not action:
        return False

    text = (
        update.message.text or ""
    ).strip()

    # ==================================================
    # FIND USER
    # ==================================================

    if action == "find_user":

        try:
            target_id = int(text)

        except ValueError:

            await update.message.reply_text(
                "❌ Invalid User ID."
            )

            return True

        context.user_data.clear()

        user = get_user(
            target_id
        )

        if not user:

            await update.message.reply_text(
                "❌ User not found.",
                reply_markup=admin_back(),
            )

            return True

        balance = user.get(
            "balance",
            0,
        )

        bonus = user.get(
            "bonus_balance",
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

        await update.message.reply_text(

            "👤 **USER INFORMATION**\n\n"

            f"🆔 ID: `{target_id}`\n"
            f"💰 Balance: {balance}\n"
            f"🎁 Bonus: {bonus}\n"
            f"⭐ XP: {xp}\n"
            f"🏆 Level: {level}\n"
            f"👥 Referrals: {referrals}\n"
            f"🔒 Banned: {banned}",

            reply_markup=user_info_keyboard(
                target_id
            ),

            parse_mode="Markdown",
        )

        return True

    # ==================================================
    # WITHDRAWAL REJECTION REASON
    # ==================================================

    if action == "withdrawal_reject_reason":

        withdrawal_id = (
            context.user_data.get(
                "withdrawal_reject_id"
            )
        )

        reason = (
            update.message.text or ""
        ).strip()

        if not withdrawal_id:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ Withdrawal session expired.",
                reply_markup=admin_back(),
            )

            return True

        if not reason:

            await update.message.reply_text(
                "❌ Please send a rejection reason.",
                reply_markup=admin_back(),
            )

            return True

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

            context.user_data.clear()

            await update.message.reply_text(
                "❌ Withdrawal not found.",
                reply_markup=admin_back(),
            )

            return True

        target_user_id = int(
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

        success = reject_withdrawal(
            withdrawal_id,
            reason,
        )

        if not success:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ Withdrawal was already processed.",
                reply_markup=admin_back(),
            )

            return True

# ----------------------------------------------
        # USER NOTIFICATION
        # ----------------------------------------------

        try:

            await context.bot.send_message(

                chat_id=target_user_id,

                text=(

                    "🔴 **WITHDRAWAL REJECTED**\n\n"

                    f"🆔 ID: `{withdrawal_id}`\n"
                    f"💰 Amount: {amount} Points\n\n"

                    f"📝 Reason: {reason}\n\n"

                    "💰 The amount has been "
                    "returned to your balance."
                ),

                parse_mode="Markdown",
            )

        except Exception as error:

            logger.warning(

                "Withdrawal rejection "
                "notification failed | "
                "user=%s | error=%s",

                target_user_id,
                error,
            )

        context.user_data.clear()

        await update.message.reply_text(

            "🔴 **WITHDRAWAL REJECTED**\n\n"

            f"🆔 ID: `{withdrawal_id}`\n"
            f"👤 User: `{target_user_id}`\n"
            f"💰 Refunded: {amount} Points\n"
            f"📝 Reason: {reason}",

            reply_markup=admin_back(),

            parse_mode="Markdown",
        )

        return True

# ==================================================
    # BALANCE
    # ==================================================

    if action in (
        "add_balance",
        "remove_balance",
    ):

        target_id = (
            context.user_data.get(
                "admin_target"
            )
        )

        try:

            amount = int(text)

        except ValueError:

            await update.message.reply_text(
                "❌ Amount must be a number."
            )

            return True

        if amount <= 0:

            await update.message.reply_text(
                "❌ Amount must be greater than 0."
            )

            return True

        target_user = get_user(
            target_id
        )

        if not target_user:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ User not found.",
                reply_markup=admin_back(),
            )

            return True

        if action == "add_balance":

            add_balance(
                target_id,
                amount,
            )

            message = (
                f"✅ Added {amount} Points "
                f"to {target_id}."
            )

        else:

            removed = remove_balance(
                target_id,
                amount,
            )

            if removed <= 0:

                await update.message.reply_text(
                    "❌ Insufficient balance."
                )

                return True

            message = (
                f"✅ Removed {removed} Points "
                f"from {target_id}."
            )

        context.user_data.clear()

        await update.message.reply_text(

            message,

            reply_markup=admin_back(),

            parse_mode="Markdown",
        )

        return True
        

    # ==================================================
    # SPECIFIC BROADCAST USER ID
    # ==================================================

    if action == "broadcast_specific":

        try:

            target_id = int(text)

        except ValueError:

            await update.message.reply_text(
                "❌ Invalid User ID."
            )

            return True

        target_user = get_user(
            target_id
        )

        if not target_user:

            await update.message.reply_text(
                "❌ User not found."
            )

            return True

        context.user_data[
            "admin_action"
        ] = "broadcast_specific_message"

        context.user_data[
            "admin_target"
        ] = target_id

        await update.message.reply_text(

            "📢 Now send the message.",

            reply_markup=admin_back(),
        )

        return True
        # ==================================================
    # SPECIFIC BROADCAST MESSAGE
    # ==================================================

    if action == "add_shortlink":
        parts = [part.strip() for part in (update.message.text or "").split("|")]
        if len(parts) != 5:
            await update.message.reply_text(
                "❌ Invalid format. Use: id|name|url|reward|cooldown",
                reply_markup=admin_back(),
            )
            return True
        sid, name, url, reward_text, cooldown_text = parts
        try:
            reward = int(reward_text)
            cooldown = int(cooldown_text)
        except ValueError:
            await update.message.reply_text("❌ Reward and cooldown must be numbers.", reply_markup=admin_back())
            return True
        if reward < 0 or cooldown < 0 or not sid or not url:
            await update.message.reply_text("❌ Invalid shortlink values.", reply_markup=admin_back())
            return True
        if not register_shortlink(sid, name, url, reward=reward, cooldown=cooldown):
            await update.message.reply_text("❌ Could not save shortlink.", reply_markup=admin_back())
            return True
        context.user_data.clear()
        await update.message.reply_text(
            f"✅ Shortlink `{sid}` saved.\n\n"
            "⚠️ The URL must be a provider/gateway URL that preserves the token query parameter; the bot does not invent a shortening API.",
            reply_markup=admin_back(),
            parse_mode="Markdown",
        )
        return True

    if action == "broadcast_specific_message":

        target_id = (
            context.user_data.get(
                "admin_target"
            )
        )

        message_text = (
            update.message.text or ""
        )

        try:

            await context.bot.send_message(

                chat_id=target_id,

                text=message_text,
            )

            result_text = (
                "📢 BROADCAST COMPLETE\n\n"
                "✅ Message sent successfully."
            )

        except Exception as error:

            logger.warning(

                "Specific broadcast failed | "
                "user=%s | error=%s",

                target_id,
                error,
            )

            result_text = (
                "📢 BROADCAST FAILED\n\n"
                "❌ Could not send the message."
            )

        context.user_data.clear()

        await update.message.reply_text(

            result_text,

            reply_markup=admin_back(),

            parse_mode="Markdown",
        )

        return True
        # ==================================================
    # SETTINGS
    # ==================================================

    setting_map = {

        "set_daily":
            "daily_bonus",

        "set_group":
            "group_reward",

        "set_task_reward":
            "task_reward",

        "set_task_limit":
            "daily_task_limit",

        "set_spin_min":
            "spin_min",

        "set_spin_max":
            "spin_max",

        "set_spin_cd":
            "spin_cooldown",

        "set_lucky_min":
            "lucky_min",

        "set_lucky_max":
            "lucky_max",

        "set_ref_reward":
            "referral_reward",

        "set_ref_xp":
            "referral_xp",
    }

    if action in setting_map:

        try:

            value = int(text)

        except ValueError:

            await update.message.reply_text(
                "❌ Please send a number."
            )

            return True

        if value < 0:

            await update.message.reply_text(
                "❌ Value cannot be negative."
            )

            return True

        field = setting_map[
            action
        ]

        db["bot_settings"].update_one(

            {
                "_id": "main"
            },

            {
                "$set": {
                    field: value
                }
            },

            upsert=True,
        )

        context.user_data.clear()

        await update.message.reply_text(

            "✅ SETTING UPDATED\n\n"

            f"⚙️ {field} = {value}",

            reply_markup=admin_back(),

            parse_mode="Markdown",
        )

        return True

    # ==================================================
    # BROADCAST ALL / ACTIVE
    # ==================================================

    if action in (
        "broadcast_all",
        "broadcast_active",
    ):

        message_text = (
            update.message.text or ""
        )

        if action == "broadcast_all":

            cursor = users.find(
                {},
                {
                    "user_id": 1
                },
            )

        else:

            cursor = users.find(

                {
                    "last_login": {
                        "$gte": (
                            int(time.time())
                            - 86400
                        )
                    }
                },

                {
                    "user_id": 1
                },
            )

        success = 0
        failed = 0

        for user in cursor:

            target_id = user.get(
                "user_id"
            )

            if not target_id:
                continue

            try:

                await context.bot.send_message(

                    chat_id=target_id,

                    text=message_text,
                )

                success += 1

            except Exception as error:

                failed += 1

                logger.warning(

                    "Broadcast failed | "
                    "user=%s | error=%s",

                    target_id,
                    error,
                )

        context.user_data.clear()

        await update.message.reply_text(

            "📢 BROADCAST COMPLETE\n\n"

            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}",

            reply_markup=admin_back(),

            parse_mode="Markdown",
        )

        return True

    return False
# ==================================================
# VIP PURCHASE ON/OFF
# ==================================================

async def admin_vip_toggle(
    update,
    context,
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

    try:
        current = is_vip_purchase_enabled()

        new_status = not current

        success = set_vip_purchase_enabled(
            new_status
        )

        if not success:
            await query.answer(
                "❌ Failed to change VIP status.",
                show_alert=True,
            )
            return

        status = (
            "🟢 ON"
            if new_status
            else "🔴 OFF"
        )

        await query.answer(
            f"VIP Purchase: {status}"
        )

        await admin_panel(
            update,
            context,
        )

    except Exception:
        logger.exception(
            "VIP purchase toggle failed"
        )

        await query.answer(
            "⚠️ VIP setting failed.",
            show_alert=True,
    )
# ==================================================
# ADMIN CALLBACK ROUTER
# ==================================================

async def admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query or not query.from_user:
        return

    if not admin_only(query.from_user.id):
        await query.answer(
            "🚫 Admin only.",
            show_alert=True,
        )
        return

    data = query.data or ""

    try:
        await query.answer()
    except Exception:
        pass

    if data in ("admin", "admin_panel"):
        await admin_panel(update, context)
        return

    routes = {
        "admin_users": admin_users,
        "admin_find_user": admin_find_user,
        "admin_balance": admin_balance,
        "admin_reset_balances": admin_reset_all_balances,
        "admin_confirm_reset_balances": admin_confirm_reset_balances,
        "admin_ban": admin_ban,
        "admin_stats": admin_statistics,
        "admin_rewards": admin_rewards,
        "admin_tasks": admin_tasks,
        "admin_wheel": admin_wheel,
        "admin_lucky": admin_lucky,
        "admin_referral": admin_referral,
        "admin_settings": admin_settings,
        "admin_broadcast": admin_broadcast,
        "admin_bc_all": admin_bc_all,
        "admin_bc_active": admin_bc_active,
        "admin_bc_specific": admin_bc_specific,
        "admin_set_daily": admin_set_daily,
        "admin_set_group": admin_set_group,
        "admin_set_task_reward": admin_set_task_reward,
        "admin_set_task_limit": admin_set_task_limit,
        "admin_set_spin_min": admin_set_spin_min,
        "admin_set_spin_max": admin_set_spin_max,
        "admin_set_spin_cd": admin_set_spin_cd,
        "admin_set_lucky_min": admin_set_lucky_min,
        "admin_set_lucky_max": admin_set_lucky_max,
        "admin_set_ref_reward": admin_set_ref_reward,
        "admin_set_ref_xp": admin_set_ref_xp,
        "admin_shortlinks": admin_shortlinks,
        "admin_add_shortlink": admin_add_shortlink,
        "admin_withdrawals": admin_withdrawals,
        "admin_vip_toggle": admin_vip_toggle,
    }

    handler = routes.get(data)
    if handler:
        await handler(update, context)
        return

    if data.startswith("admin_shortlink_toggle_"):
        await admin_shortlink_toggle(update, context)
        return

    if data.startswith("admin_shortlink_delete_"):
        await admin_shortlink_delete(update, context)
        return

    if data == "admin_toggle_maintenance":
        settings = db["bot_settings"].find_one({"_id": "main"}) or {}
        current = bool(settings.get("maintenance", False))
        db["bot_settings"].update_one(
            {"_id": "main"},
            {"$set": {"maintenance": not current}},
            upsert=True,
        )
        await admin_settings(update, context)
        return

    if data == "admin_toggle_notifications":
        settings = db["bot_settings"].find_one({"_id": "main"}) or {}
        current = bool(settings.get("notifications", True))
        db["bot_settings"].update_one(
            {"_id": "main"},
            {"$set": {"notifications": not current}},
            upsert=True,
        )
        await admin_settings(update, context)
        return

    if data.startswith("admin_withdraw_view_"):
        await admin_withdrawal_view(update, context)
        return

    if data.startswith("admin_withdraw_approve_"):
        await admin_withdrawal_approve(update, context)
        return

    if data.startswith("admin_withdraw_reject_"):
        await admin_withdrawal_reject(update, context)
        return

    prefixed_handlers = (
        ("admin_add_", admin_add_balance),
        ("admin_remove_", admin_remove_balance),
        ("admin_toggleban_", admin_toggle_ban),
    )

    for prefix_name, handler in prefixed_handlers:
        if data.startswith(prefix_name):
            try:
                int(data.replace(prefix_name, "", 1))
            except ValueError:
                await query.answer(
                    "❌ Invalid user ID.",
                    show_alert=True,
                )
                return

            await handler(update, context)
            return

    if data.startswith("admin_view_"):
        try:
            user_id = int(
                data.replace(
                    "admin_view_",
                    "",
                    1,
                )
            )
        except ValueError:
            await query.answer(
                "❌ Invalid user ID.",
                show_alert=True,
            )
            return

        await show_admin_user(
            update,
            context,
            user_id,
        )
        return

    await query.answer(
        "⚠️ Admin option not available.",
        show_alert=True,
            )

# ==================================================
# EXPORTS
# ==================================================
ADMIN_HANDLERS = {
    "admin": admin_panel,
    "admin_panel": admin_panel,
    "admin_callback": admin_callback,
    "admin_text_handler": admin_text_handler,
}
