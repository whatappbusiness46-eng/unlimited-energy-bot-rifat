import time
import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

from config import (
    MIN_WITHDRAW,
    BKASH_NUMBER,
    NAGAD_NUMBER,
    BYBIT_UID,
)

from database import (
    get_user,
    reserve_withdrawal,
    get_withdrawals,
)


logger = logging.getLogger(__name__)


METHODS = {
    "bkash": "bKash",
    "nagad": "Nagad",
    "bybit": "Bybit",
}


def withdraw_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📱 bKash",
                    callback_data="withdraw_method_bkash",
                )
            ],
            [
                InlineKeyboardButton(
                    "📱 Nagad",
                    callback_data="withdraw_method_nagad",
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 Bybit",
                    callback_data="withdraw_method_bybit",
                )
            ],
            [
                InlineKeyboardButton(
                    "📜 Withdrawal History",
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
    )


def cancel_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="withdraw_cancel",
                )
            ]
        ]
    )


def confirm_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Confirm",
                    callback_data="withdraw_confirm",
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="withdraw_cancel",
                ),
            ]
        ]
    )


async def withdraw_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id
    user = get_user(user_id)

    if not user:
        await query.edit_message_text(
            "⚠️ Account not found."
        )
        return

    if user.get("banned", False):
        await query.answer(
            "🚫 Your account is banned.",
            show_alert=True,
        )
        return

    balance = int(
        user.get("balance", 0)
    )

    pending = int(
        user.get(
            "withdraw_pending",
            0,
        )
    )

    await query.answer()

    await query.edit_message_text(
        "💸 **WITHDRAWAL CENTER**\n\n"
        f"💰 Available: {balance} Points\n"
        f"🟡 Pending: {pending} Points\n"
        f"📌 Minimum: {MIN_WITHDRAW} Points\n\n"
        "Select your payment method:",
        reply_markup=withdraw_keyboard(),
        parse_mode="Markdown",
    )


async def select_method(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data

    method = data.replace(
        "withdraw_method_",
        "",
        1,
    )

    if method not in METHODS:
        await query.answer(
            "Invalid payment method.",
            show_alert=True,
        )
        return

    user_id = query.from_user.id
    user = get_user(user_id)

    if not user:
        await query.answer(
            "Account not found.",
            show_alert=True,
        )
        return

    balance = int(
        user.get("balance", 0)
    )

    if balance < MIN_WITHDRAW:
        await query.answer(
            f"Minimum withdrawal is {MIN_WITHDRAW} points.",
            show_alert=True,
        )
        return

    context.user_data[
        "withdraw_method"
    ] = method

    context.user_data[
        "withdraw_step"
    ] = "amount"

    await query.answer()

    await query.edit_message_text(
        "💸 **WITHDRAWAL AMOUNT**\n\n"
        f"💰 Available: {balance} Points\n"
        f"📌 Minimum: {MIN_WITHDRAW} Points\n\n"
        "Send the amount you want to withdraw.\n\n"
        "Example: `1000`",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown",
    )


async def withdraw_text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.message

    if not message:
        return False

    step = context.user_data.get(
        "withdraw_step"
    )

    if not step:
        return False

    user_id = message.from_user.id

    text = (
        message.text or ""
    ).strip()

    if step == "amount":

        try:
            amount = int(text)
        except ValueError:

            await message.reply_text(
                "❌ Please send a valid number.",
                reply_markup=cancel_keyboard(),
            )

            return True

        if amount < MIN_WITHDRAW:

            await message.reply_text(
                f"❌ Minimum withdrawal is "
                f"{MIN_WITHDRAW} points.",
                reply_markup=cancel_keyboard(),
            )

            return True

        user = get_user(user_id)

        if not user:

            await message.reply_text(
                "⚠️ Account not found."
            )

            context.user_data.clear()

            return True

        balance = int(
            user.get("balance", 0)
        )

        if amount > balance:

            await message.reply_text(
                "❌ Insufficient balance.\n\n"
                f"Your balance: {balance} Points",
                reply_markup=cancel_keyboard(),
            )

            return True

        context.user_data[
            "withdraw_amount"
        ] = amount

        context.user_data[
            "withdraw_step"
        ] = "account"

        method = context.user_data.get(
            "withdraw_method",
            "",
        )

        method_name = METHODS.get(
            method,
            method,
        )

        await message.reply_text(
            f"💳 **{method_name} ACCOUNT**\n\n"
            "Send your payment account/number.\n\n"
            "Example:\n"
            "`017XXXXXXXX`",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )

        return True

    if step == "account":

        account = text

        if len(account) < 3:

            await message.reply_text(
                "❌ Invalid payment account.",
                reply_markup=cancel_keyboard(),
            )

            return True

        context.user_data[
            "withdraw_account"
        ] = account

        context.user_data[
            "withdraw_step"
        ] = "confirm"

        method = context.user_data.get(
            "withdraw_method",
            "",
        )

        amount = int(
            context.user_data.get(
                "withdraw_amount",
                0,
            )
        )

        method_name = METHODS.get(
            method,
            method,
        )

        await message.reply_text(
            "🧾 **CONFIRM WITHDRAWAL**\n\n"
            f"💰 Amount: {amount} Points\n"
            f"💳 Method: {method_name}\n"
            f"👤 Account: `{account}`\n\n"
            "Please confirm your withdrawal.",
            reply_markup=confirm_keyboard(),
            parse_mode="Markdown",
        )

        return True

    return False


async def confirm_withdrawal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    method = context.user_data.get(
        "withdraw_method"
    )

    amount = context.user_data.get(
        "withdraw_amount"
    )

    account = context.user_data.get(
        "withdraw_account"
    )

    if not method or not amount or not account:

        await query.answer(
            "⚠️ Withdrawal session expired.",
            show_alert=True,
        )

        context.user_data.clear()

        return

    withdrawal = reserve_withdrawal(
        user_id=user_id,
        amount=int(amount),
        method=method,
        payment_account=account,
    )

    if not withdrawal:

        await query.answer(
            "❌ Withdrawal could not be created.",
            show_alert=True,
        )

        context.user_data.clear()

        return

    context.user_data.clear()

    await query.answer(
        "✅ Withdrawal submitted.",
        show_alert=True,
    )

    await query.edit_message_text(
        "✅ **WITHDRAWAL SUBMITTED**\n\n"
        f"🆔 ID: `{withdrawal['withdrawal_id']}`\n"
        f"💰 Amount: {withdrawal['amount']} Points\n"
        f"💳 Method: {withdrawal['method']}\n"
        f"👤 Account: `{withdrawal['payment_account']}`\n"
        "🟡 Status: Pending\n\n"
        "Admin will review your request.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "💸 Withdraw",
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
    )


async def cancel_withdrawal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    context.user_data.clear()

    if query:

        await query.answer(
            "Withdrawal cancelled."
        )

        await query.edit_message_text(
            "❌ Withdrawal cancelled.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💸 Withdraw",
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
        )


async def withdrawal_history_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    records = get_withdrawals(
        limit=50
    )

    records = [
        item
        for item in records
        if int(
            item.get(
                "user_id",
                0,
            )
        ) == int(user_id)
    ]

    if not records:

        await query.answer()

        await query.edit_message_text(
            "📜 **WITHDRAWAL HISTORY**\n\n"
            "No withdrawal history found.",
            reply_markup=withdraw_keyboard(),
            parse_mode="Markdown",
        )

        return

    lines = [
        "📜 **WITHDRAWAL HISTORY**",
        "",
    ]

    for item in records[:10]:

        lines.append(
            f"🆔 `{item.get('withdrawal_id', 'N/A')}`"
        )

        lines.append(
            f"💰 {item.get('amount', 0)} Points"
        )

        lines.append(
            f"💳 {item.get('method', 'N/A')}"
        )

        lines.append(
            f"📌 {item.get('status', 'unknown')}"
        )

        lines.append("")

    await query.answer()

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=withdraw_keyboard(),
        parse_mode="Markdown",
    )
    
