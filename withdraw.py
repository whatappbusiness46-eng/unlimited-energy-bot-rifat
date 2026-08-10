import time

from config import MIN_WITHDRAW
from database import (
    get_user,
    reserve_withdrawal,
    get_withdrawals,
)


METHODS = {
    "bkash": "bKash",
    "nagad": "Nagad",
    "bybit": "Bybit",
}


def available_balance(user_id):
    user = get_user(user_id, create=False)

    if not user:
        return 0

    return int(user.get("balance", 0))


def pending_balance(user_id):
    user = get_user(user_id, create=False)

    if not user:
        return 0

    return int(user.get("withdraw_pending", 0))


def validate_amount(user_id, amount):
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return False, "Withdrawal amount must be a number."

    if amount < MIN_WITHDRAW:
        return False, (
            f"Minimum withdrawal is {MIN_WITHDRAW} points."
        )

    balance = available_balance(user_id)

    if amount > balance:
        return False, "Insufficient balance."

    return True, amount


def validate_method(method):
    method = str(method).lower().strip()

    if method not in METHODS:
        return False, "Invalid payment method."

    return True, method


def create_withdrawal(
    user_id,
    amount,
    method,
    account,
):
    valid, result = validate_amount(
        user_id,
        amount,
    )

    if not valid:
        return False, result

    valid, method_result = validate_method(method)

    if not valid:
        return False, method_result

    account = str(account).strip()

    if not account:
        return False, "Payment account cannot be empty."

    withdrawal = reserve_withdrawal(
        user_id,
        int(result),
    )

    if not withdrawal:
        return False, "Unable to reserve the withdrawal amount."

    withdrawal["method"] = method_result
    withdrawal["method_name"] = METHODS[method_result]
    withdrawal["account"] = account

    return True, withdrawal


def pending_withdrawals(
    limit=50,
):
    return get_withdrawals(
        status="pending",
        limit=limit,
    )


def withdrawal_history(
    user_id,
    limit=50,
):
    records = get_withdrawals(
        limit=limit,
    )

    return [
        item
        for item in records
        if int(item.get("user_id", 0)) == int(user_id)
    ]


def format_withdrawal(withdrawal):
    if not withdrawal:
        return "Withdrawal not found."

    amount = int(withdrawal.get("amount", 0))
    status = withdrawal.get("status", "unknown")
    withdrawal_id = withdrawal.get(
        "withdrawal_id",
        "N/A",
    )

    method = withdrawal.get(
        "method_name",
        withdrawal.get("method", "N/A"),
    )

    account = withdrawal.get(
        "account",
        "N/A",
    )

    return (
        "💸 Withdrawal\n\n"
        f"🆔 {withdrawal_id}\n"
        f"💰 Amount: {amount} Points\n"
        f"💳 Method: {method}\n"
        f"👤 Account: {account}\n"
        f"📌 Status: {status}"
    )
  
