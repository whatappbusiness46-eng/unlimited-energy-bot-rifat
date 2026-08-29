import logging, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from database import get_user, activate_premium, activate_vip, record_transaction, add_activity

logger = logging.getLogger(__name__)

PREMIUM_DAYS = 30
VIP_DAYS = 30
PREMIUM_STARS = int(os.getenv("PREMIUM_STARS", "100"))
VIP_STARS = {
    1: int(os.getenv("VIP1_STARS", "50")),
    2: int(os.getenv("VIP2_STARS", "100")),
    3: int(os.getenv("VIP3_STARS", "150")),
    4: int(os.getenv("VIP4_STARS", "225")),
    5: int(os.getenv("VIP5_STARS", "300")),
}

def _allowed(uid):
    u = get_user(uid, create=False)
    if not u: return False, "User account not found."
    if u.get("banned", False): return False, "Your account is banned."
    if u.get("blacklisted", False): return False, "Your account is restricted."
    return True, u

def _plan(payload):
    p = str(payload or "").split(":")
    if len(p) == 2 and p[0] == "premium" and int(p[1]) > 0:
        return "premium", 0, int(p[1])
    if len(p) == 3 and p[0] == "vip":
        level, days = int(p[1]), int(p[2])
        if level in VIP_STARS and days > 0: return "vip", level, days
    return None

def _price(kind, level):
    return PREMIUM_STARS if kind == "premium" else VIP_STARS.get(level, 0)

async def membership_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q: return
    await q.answer()
    data, uid = str(q.data or ""), q.from_user.id
    ok, result = _allowed(uid)
    if not ok:
        await q.edit_message_text(f"❌ {result}"); return

    if data == "membership_pay_premium":
        kind, level, days, title = "premium", 0, PREMIUM_DAYS, "Premium 30 Days"
    elif data.startswith("membership_pay_vip_"):
        try: level = int(data.rsplit("_", 1)[1])
        except ValueError:
            await q.edit_message_text("⚠️ Invalid VIP level."); return
        if level not in VIP_STARS:
            await q.edit_message_text("⚠️ Invalid VIP level."); return
        kind, days, title = "vip", VIP_DAYS, f"VIP {level} — 30 Days"
    else:
        await q.edit_message_text("⚠️ Invalid payment option."); return

    stars = _price(kind, level)
    payload = f"premium:{days}" if kind == "premium" else f"vip:{level}:{days}"
    if stars <= 0:
        await q.edit_message_text("⚠️ Payment price is not configured."); return

    try:
        await context.bot.send_invoice(
            chat_id=uid, title=title,
            description="Unlimited Energy Bot digital membership.",
            payload=payload, provider_token="", currency="XTR",
            prices=[LabeledPrice(title, stars)],
            start_parameter=f"membership_{kind}_{level or 'premium'}",
        )
        await q.edit_message_text(
            f"💳 Payment invoice sent below.\n\n⭐ Price: {stars} Stars\n⏳ Duration: {days} days",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]]),
        )
    except Exception:
        logger.exception("Invoice creation failed")
        await q.edit_message_text("⚠️ Could not create the payment invoice.")

async def membership_precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.pre_checkout_query
    if not q: return
    try: plan = _plan(q.invoice_payload)
    except (TypeError, ValueError): plan = None
    if not plan:
        await q.answer(ok=False, error_message="Invalid membership order."); return
    ok, _ = _allowed(q.from_user.id)
    expected = _price(plan[0], plan[1])
    if not ok or expected <= 0 or int(q.total_amount) != expected:
        await q.answer(ok=False, error_message="Order validation failed."); return
    await q.answer(ok=True)

async def membership_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    if not m or not m.successful_payment: return
    p = m.successful_payment
    try: plan = _plan(p.invoice_payload)
    except (TypeError, ValueError): plan = None
    if not plan: return

    uid = m.from_user.id
    ok, _ = _allowed(uid)
    expected = _price(plan[0], plan[1])
    if not ok or int(p.total_amount) != expected: return

    try:
        if plan[0] == "premium":
            activated = activate_premium(uid, days=plan[2])
            name = "Premium"
        else:
            activated = activate_vip(uid, level=plan[1], days=plan[2])
            name = f"VIP {plan[1]}"
        if not activated:
            await m.reply_text("⚠️ Payment received, but activation failed. Please contact support.")
            return
        record_transaction(
            user_id=uid, transaction_type="membership_stars_purchase",
            amount=p.total_amount, source="telegram_stars", status="completed",
            metadata={"membership": name, "payload": p.invoice_payload,
                      "telegram_payment_charge_id": p.telegram_payment_charge_id,
                      "currency": p.currency},
        )
        add_activity(uid, "membership_stars_purchase", p.total_amount)
        await m.reply_text(
            f"🎉 **PAYMENT SUCCESSFUL!**\n\n👑 {name}\n⏳ {plan[2]} days\n⭐ Paid: {p.total_amount} Stars\n\n✅ Membership activated.",
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Membership payment processing failed")
        await m.reply_text("⚠️ Payment received, but processing failed. Please contact support.")

def membership_payment_handlers():
    return [
        PreCheckoutQueryHandler(membership_precheckout),
        MessageHandler(filters.SUCCESSFUL_PAYMENT, membership_successful_payment),
    ]

__all__ = ["membership_payment_callback", "membership_precheckout",
           "membership_successful_payment", "membership_payment_handlers"]
