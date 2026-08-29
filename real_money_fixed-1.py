# real_money.py
# Manual real-money Premium/VIP purchase flow.
#
# This module intentionally leaves premium.py, vip.py, callbacks.py,
# and database.py unchanged. bot.py only needs to register the handlers.
#
# Payment methods: bKash, Nagad, Bybit
# Flow:
#   existing Premium/VIP button -> choose payment method
#   -> instructions -> user sends TxID
#   -> pending order saved in MongoDB
#   -> admin receives Approve/Reject buttons
#   -> approve -> activate membership
#
# Set these environment variables in Render:
#   PAYMENT_ADMIN_ID=your_telegram_admin_id
#   BKASH_NUMBER=...
#   NAGAD_NUMBER=...
#   BYBIT_UID=...
#   PREMIUM_CASH_PRICE=...
#   VIP1_CASH_PRICE=...
#   VIP2_CASH_PRICE=...
#   VIP3_CASH_PRICE=...
#   VIP4_CASH_PRICE=...
#   VIP5_CASH_PRICE=...
#
# This is MANUAL verification. Do not auto-approve from a user-submitted TxID.

import logging
import os
import time
import uuid

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from database import (
    db,
    get_user,
    activate_premium,
    activate_vip,
    record_transaction,
)

logger = logging.getLogger(__name__)

PAYMENT_ADMIN_ID = int(os.getenv("PAYMENT_ADMIN_ID", "0") or 0)

PAYMENT_METHODS = {
    "bkash": os.getenv("BKASH_NUMBER", "").strip(),
    "nagad": os.getenv("NAGAD_NUMBER", "").strip(),
    "bybit": os.getenv("BYBIT_UID", "").strip(),
}

PREMIUM_PRICE = os.getenv("PREMIUM_CASH_PRICE", "0").strip()

VIP_PRICES = {
    1: os.getenv("VIP1_CASH_PRICE", "0").strip(),
    2: os.getenv("VIP2_CASH_PRICE", "0").strip(),
    3: os.getenv("VIP3_CASH_PRICE", "0").strip(),
    4: os.getenv("VIP4_CASH_PRICE", "0").strip(),
    5: os.getenv("VIP5_CASH_PRICE", "0").strip(),
}

PREMIUM_DAYS = int(os.getenv("PREMIUM_PAYMENT_DAYS", "30") or 30)
VIP_DAYS = int(os.getenv("VIP_PAYMENT_DAYS", "30") or 30)

orders = db["membership_payment_orders"]


def _price(kind, level=0):
    value = PREMIUM_PRICE if kind == "premium" else VIP_PRICES.get(level, "0")
    return str(value).strip()


def _valid_user(uid):
    user = get_user(uid, create=False)
    if not user:
        return False
    return not user.get("banned", False) and not user.get("blacklisted", False)


def _order(kind, level, user_id):
    return {
        "order_id": "PAY-" + uuid.uuid4().hex[:14].upper(),
        "user_id": int(user_id),
        "kind": kind,
        "level": int(level),
        "days": PREMIUM_DAYS if kind == "premium" else VIP_DAYS,
        "price": _price(kind, level),
        "currency": "BDT",
        "status": "pending",
        "payment_method": "",
        "txid": "",
        "created_at": int(time.time()),
    }


def _method_keyboard(kind, level):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📱 bKash",
                callback_data=f"realpay_method_bkash_{kind}_{level}",
            ),
            InlineKeyboardButton(
                "📱 Nagad",
                callback_data=f"realpay_method_nagad_{kind}_{level}",
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 Bybit",
                callback_data=f"realpay_method_bybit_{kind}_{level}",
            ),
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="realpay_cancel"),
        ],
    ])


async def purchase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    data = str(q.data or "")

    if data == "premium_buy":
        kind, level = "premium", 0
    elif data.startswith("vip_level_"):
        try:
            level = int(data.rsplit("_", 1)[1])
        except ValueError:
            return
        if level not in range(1, 6):
            return
        kind = "vip"
    else:
        return

    await q.answer()

    if not _valid_user(q.from_user.id):
        await q.edit_message_text("❌ Your account cannot make purchases.")
        return

    price = _price(kind, level)
    if not price or price == "0":
        await q.edit_message_text(
            "⚠️ Real-money price is not configured yet.\n"
            "Please contact Admin."
        )
        return

    title = "Premium" if kind == "premium" else f"VIP {level}"

    await q.edit_message_text(
        f"💎 **{title} — Real Money Purchase**\n\n"
        f"💰 Price: **৳{price}**\n"
        f"⏳ Duration: **{PREMIUM_DAYS if kind == 'premium' else VIP_DAYS} days**\n\n"
        "Choose your payment method:",
        reply_markup=_method_keyboard(kind, level),
        parse_mode="Markdown",
    )


async def method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return

    parts = str(q.data or "").split("_")
    # realpay_method_<method>_<kind>_<level>
    if len(parts) != 5:
        return

    method = parts[2]
    kind = parts[3]
    try:
        level = int(parts[4])
    except ValueError:
        return

    if method not in PAYMENT_METHODS or kind not in ("premium", "vip"):
        await q.answer("Invalid payment option.", show_alert=True)
        return

    await q.answer()

    destination = PAYMENT_METHODS.get(method, "")
    if not destination:
        await q.edit_message_text(
            "⚠️ This payment method is not configured yet.\n"
            "Please contact Admin."
        )
        return

    price = _price(kind, level)
    title = "Premium" if kind == "premium" else f"VIP {level}"

    context.user_data["real_payment_draft"] = {
        "kind": kind,
        "level": level,
        "method": method,
        "price": price,
    }

    if method in ("bkash", "nagad"):
        instructions = (
            f"Send **৳{price}** to:\n\n"
            f"📱 **{destination}**\n\n"
            "After sending the money, reply to this message with "
            "your **Transaction ID (TxID)**."
        )
    else:
        instructions = (
            f"Send the equivalent of **৳{price}** via Bybit to:\n\n"
            f"🌐 **{destination}**\n\n"
            "After payment, reply with your **Bybit TxID/order ID**."
        )

    await q.edit_message_text(
        f"💳 **{title} Payment**\n\n"
        f"{instructions}\n\n"
        "⚠️ Do not send your password, OTP, PIN, or private key.\n"
        "Only send the payment transaction ID.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="realpay_cancel")]
        ]),
    )


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or q.data != "realpay_cancel":
        return
    await q.answer()
    context.user_data.pop("real_payment_draft", None)
    await q.edit_message_text("❌ Payment cancelled.")


async def payment_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture a TxID only when the user has an active payment draft."""
    if not update.message or not update.message.text:
        return False

    draft = context.user_data.get("real_payment_draft")
    if not draft:
        return False

    txid = update.message.text.strip()
    if len(txid) < 4 or len(txid) > 200:
        await update.message.reply_text("⚠️ Please send a valid Transaction ID.")
        return True

    uid = update.effective_user.id

    # Prevent reusing an identical TxID.
    if orders.find_one({"txid": txid}):
        await update.message.reply_text(
            "⚠️ This Transaction ID has already been submitted."
        )
        return True

    order = _order(draft["kind"], draft["level"], uid)
    order["payment_method"] = draft["method"]
    order["txid"] = txid

    orders.insert_one(order)
    context.user_data.pop("real_payment_draft", None)

    await update.message.reply_text(
        f"✅ **Payment submitted**\n\n"
        f"🧾 Order: `{order['order_id']}`\n"
        f"💰 Amount: ৳{order['price']}\n"
        f"💳 Method: {draft['method'].upper()}\n"
        f"🔑 TxID: `{txid}`\n\n"
        "⏳ Your payment is pending Admin verification.",
        parse_mode="Markdown",
    )

    if PAYMENT_ADMIN_ID:
        title = "Premium" if order["kind"] == "premium" else f"VIP {order['level']}"
        try:
            await context.bot.send_message(
                chat_id=PAYMENT_ADMIN_ID,
                text=(
                    "💰 **NEW MEMBERSHIP PAYMENT**\n\n"
                    f"🧾 Order: `{order['order_id']}`\n"
                    f"👤 User ID: `{uid}`\n"
                    f"👑 Product: **{title}**\n"
                    f"💵 Amount: **৳{order['price']}**\n"
                    f"💳 Method: **{order['payment_method'].upper()}**\n"
                    f"🔑 TxID: `{txid}`\n\n"
                    "Verify the payment before approving."
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "✅ Approve",
                            callback_data=f"realpay_approve_{order['order_id']}",
                        ),
                        InlineKeyboardButton(
                            "❌ Reject",
                            callback_data=f"realpay_reject_{order['order_id']}",
                        ),
                    ],
                ]),
            )
        except Exception:
            logger.exception("Failed to notify payment admin")

    return True


async def admin_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return

    data = str(q.data or "")
    if not (data.startswith("realpay_approve_") or data.startswith("realpay_reject_")):
        return

    if q.from_user.id != PAYMENT_ADMIN_ID:
        await q.answer("Admin only.", show_alert=True)
        return

    action, order_id = data.split("_", 2)[1], data.split("_", 2)[2]
    order = orders.find_one({"order_id": order_id})

    if not order:
        await q.answer("Order not found.", show_alert=True)
        return

    if order.get("status") != "pending":
        await q.answer("This order was already processed.", show_alert=True)
        return

    if action == "reject":
        orders.update_one(
            {"order_id": order_id, "status": "pending"},
            {"$set": {"status": "rejected", "reviewed_at": int(time.time())}},
        )
        await q.answer("Payment rejected.")
        await q.edit_message_text(
            q.message.text + "\n\n❌ **REJECTED**",
            parse_mode="Markdown",
        )
        try:
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    f"❌ Your payment for "
                    f"{'Premium' if order['kind'] == 'premium' else 'VIP ' + str(order['level'])} "
                    "was rejected. Please contact support if you believe this is an error."
                ),
            )
        except Exception:
            pass
        return

    # Approve only after admin has independently checked the payment.
    if order["kind"] == "premium":
        activated = activate_premium(order["user_id"], days=order["days"])
        product = "Premium"
    else:
        activated = activate_vip(
            order["user_id"],
            level=order["level"],
            days=order["days"],
        )
        product = f"VIP {order['level']}"

    if not activated:
        await q.answer("Activation failed; order remains pending.", show_alert=True)
        return

    result = orders.update_one(
        {"order_id": order_id, "status": "pending"},
        {"$set": {
            "status": "approved",
            "reviewed_at": int(time.time()),
            "reviewed_by": int(q.from_user.id),
        }},
    )

    if result.modified_count != 1:
        logger.error("Payment order race detected: %s", order_id)
        await q.answer("Order state changed; check database.", show_alert=True)
        return

    record_transaction(
        user_id=order["user_id"],
        transaction_type="real_money_membership",
        amount=0,
        source=order["payment_method"],
        status="completed",
        metadata={
            "order_id": order_id,
            "product": product,
            "price_bdt": order["price"],
            "txid": order["txid"],
            "payment_method": order["payment_method"],
            "days": order["days"],
        },
    )

    await q.answer("Approved.")
    await q.edit_message_text(
        q.message.text + f"\n\n✅ **APPROVED — {product} ACTIVATED**",
        parse_mode="Markdown",
    )

    try:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                "🎉 **PAYMENT VERIFIED!**\n\n"
                f"👑 {product}\n"
                f"⏳ Duration: {order['days']} days\n"
                f"💵 Paid: ৳{order['price']}\n\n"
                "✅ Your membership has been activated."
            ),
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Failed to notify user after approval")


def register_real_money_handlers(application):
    # These purchase callbacks intentionally intercept the existing
    # internal-balance purchase buttons before callbacks.py.
    application.add_handler(
        CallbackQueryHandler(
            purchase_callback,
            pattern=r"^(premium_buy|vip_level_[1-5])$",
        ),
        group=0,
    )
    application.add_handler(
        CallbackQueryHandler(
            method_callback,
            pattern=r"^realpay_method_(bkash|nagad|bybit)_(premium|vip)_[0-5]$",
        ),
        group=0,
    )
    application.add_handler(
        CallbackQueryHandler(
            admin_decision_callback,
            pattern=r"^realpay_(approve|reject)_.+$",
        ),
        group=0,
    )
    application.add_handler(
        CallbackQueryHandler(
            cancel_callback,
            pattern=r"^realpay_cancel$",
        ),
        group=0,
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            payment_text_handler,
        ),
        group=-1,
    )
