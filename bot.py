# ============================================================
# bot.py
# Unlimited Energy Bot V2
# FINAL APPLICATION ENTRY POINT
# Render Worker + Flask Health Server
# ============================================================

import logging
import os
import threading

from flask import Flask, request

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN

from handlers import (
    start,
    profile,
    balance,
    rank,
    stats,
    leaderboard_command,
    activity,
    dailystatus,
    help_command,
    myid,
)

from callbacks import (
    button_callback,
)

from admin import (
    admin_panel,
    admin_text_handler,
)

from withdraw import (
    withdraw_text_handler,
)

from real_money import register_real_money_handlers

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format=(
        "%(asctime)s | "
        "%(name)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# ENVIRONMENT VALIDATION
# ============================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is not set."
    )


# ============================================================
# FLASK HEALTH SERVER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Unlimited Energy Bot is running."


@app.route("/health")
def health():
    return {
        "status": "ok",
        "bot": "Unlimited Energy Bot",
    }

# ============================================================
# ADVERTSREWARD POSTBACK
# ============================================================

@app.route(
    "/advertsreward/postback",
    methods=["GET", "POST"],
)
def advertsreward_postback():
    """
    AdvertsReward server-to-server conversion callback.

    AdvertsReward sends the reward in `amount` when the widget
    currency is Points. The configured rate is 1 USD = 1000
    Points, but the provider's `amount` field is the actual
    user reward for this callback.

    The provider transaction ID is used for duplicate protection.
    """

    try:
        # ----------------------------------------------------
        # Collect GET + POST parameters
        # ----------------------------------------------------
        data = {}

        if request.args:
            data.update(request.args.to_dict())

        if request.form:
            data.update(request.form.to_dict())

        logger.info(
            "AdvertsReward callback received: %s",
            data,
        )

        # ----------------------------------------------------
        # User ID
        # ----------------------------------------------------
        user_id = (
            data.get("user_id")
            or data.get("publisher_user_id")
            or data.get("uid")
            or data.get("subid")
            or data.get("sub_id")
            or data.get("telegram_id")
        )

        if not user_id:
            logger.error(
                "AdvertsReward callback missing user_id"
            )
            return "Missing user_id", 400

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            logger.error(
                "Invalid AdvertsReward user_id: %s",
                user_id,
            )
            return "Invalid user_id", 400

        # ----------------------------------------------------
        # Transaction ID
        # ----------------------------------------------------
        transaction_id = (
            data.get("transaction_id")
            or data.get("transaction")
            or data.get("txn_id")
            or data.get("txn")
            or data.get("conversion_id")
            or data.get("click_id")
        )

        if not transaction_id:
            logger.error(
                "AdvertsReward callback missing transaction_id"
            )
            return "Missing transaction_id", 400

        transaction_id = str(transaction_id).strip()

        if not transaction_id:
            return "Invalid transaction_id", 400

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------
        status = str(
            data.get("status")
            or data.get("conversion_status")
            or "approved"
        ).strip().lower()

        rejected_statuses = {
            "0",
            "rejected",
            "reject",
            "failed",
            "cancelled",
            "canceled",
            "reversed",
            "chargeback",
            "invalid",
        }

        if status in rejected_statuses:
            logger.info(
                "Ignoring rejected/reversed AdvertsReward callback | "
                "txn=%s status=%s",
                transaction_id,
                status,
            )
            return "OK", 200

        # ----------------------------------------------------
        # Reward
        #
        # IMPORTANT:
        # AdvertsReward sends the user's Points in `amount`.
        # Example test callback:
        #   amount=100
        #   amount_usd=0.01000000
        #
        # Do NOT calculate Points from amount_usd here because
        # the provider already supplies the reward amount.
        # ----------------------------------------------------
        raw_amount = data.get("amount")

        if raw_amount is None:
            raw_amount = (
                data.get("points")
                or data.get("reward")
                or data.get("coins")
            )

        if raw_amount is None:
            logger.error(
                "AdvertsReward callback missing reward amount: %s",
                data,
            )
            return "Missing amount", 400

        try:
            amount_float = float(
                str(raw_amount)
                .replace(",", "")
                .strip()
            )
        except (TypeError, ValueError):
            logger.error(
                "Invalid AdvertsReward amount: %s",
                raw_amount,
            )
            return "Invalid amount", 400

        points = int(round(amount_float))

        if points <= 0:
            logger.error(
                "AdvertsReward callback has no positive reward: %s",
                data,
            )
            return "Invalid reward", 400

        # ----------------------------------------------------
        # User lookup
        # ----------------------------------------------------
        from database import (
            get_user,
            add_balance,
            record_transaction,
            transactions,
        )

        user = get_user(
            user_id,
            create=False,
        )

        if not user:
            logger.warning(
                "AdvertsReward callback for unknown user=%s",
                user_id,
            )
            # A missing local user is not a provider failure.
            return "OK", 200

        # ----------------------------------------------------
        # Banned / blacklisted protection
        # ----------------------------------------------------
        if user.get("banned", False):
            logger.warning(
                "Blocked AdvertsReward callback for banned user=%s",
                user_id,
            )
            return "OK", 200

        if user.get("blacklisted", False):
            logger.warning(
                "Blocked AdvertsReward callback for blacklisted user=%s",
                user_id,
            )
            return "OK", 200

        # ----------------------------------------------------
        # DUPLICATE PROTECTION
        #
        # Search both the provider transaction id and the
        # external key stored in transaction metadata.
        # ----------------------------------------------------
        existing = transactions.find_one(
            {
                "$or": [
                    {
                        "metadata.external_transaction_id":
                            transaction_id,
                    },
                    {
                        "metadata.external_transaction_key":
                            "AR-" + transaction_id,
                    },
                ]
            }
        )

        if existing:
            logger.info(
                "Duplicate AdvertsReward conversion ignored | "
                "user=%s txn=%s",
                user_id,
                transaction_id,
            )
            return "OK", 200

        # ----------------------------------------------------
        # Credit balance
        #
        # add_balance() also records the normal balance reward
        # transaction and updates total distributed points.
        # ----------------------------------------------------
        credited = add_balance(
            user_id,
            points,
        )

        if not credited:
            logger.error(
                "Could not credit AdvertsReward balance | "
                "user=%s points=%s txn=%s",
                user_id,
                points,
                transaction_id,
            )
            return "Retry", 500

        # ----------------------------------------------------
        # Provider-specific transaction record
        # ----------------------------------------------------
        record_transaction(
            user_id=user_id,
            transaction_type="advertsreward",
            amount=points,
            source="advertsreward",
            status="completed",
            metadata={
                "external_transaction_id":
                    transaction_id,
                "external_transaction_key":
                    "AR-" + transaction_id,
                "amount":
                    data.get("amount"),
                "amount_usd":
                    data.get("amount_usd"),
                "gross_amount_usd":
                    data.get("gross_amount_usd"),
                "currency":
                    data.get("currency"),
                "type":
                    data.get("type"),
                "offer_id":
                    data.get("offer_id"),
                "offer_name":
                    data.get("offer_name"),
                "offer_category":
                    data.get("offer_category"),
                "status":
                    status,
                "widget_id":
                    data.get("widget_id"),
                "placement_id":
                    data.get("placement_id"),
                "section_id":
                    data.get("section_id"),
                "country_code":
                    data.get("country_code"),
            },
        )

        logger.info(
            "AdvertsReward conversion credited | "
            "user=%s points=%s txn=%s",
            user_id,
            points,
            transaction_id,
        )

        # Provider only needs a quick success response.
        return "OK", 200

    except Exception:
        logger.exception(
            "AdvertsReward postback processing failed"
        )
        return "Retry", 500

def run_web_server():

    port = int(
        os.getenv(
            "PORT",
            "10000",
        )
    )

    logger.info(
        "Starting Flask health server on port %s",
        port,
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )
   
    register_real_money_handlers(telegram_app)

# ============================================================
# TELEGRAM APPLICATION
# ============================================================

telegram_app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

register_real_money_handlers(telegram_app)
# ============================================================
# COMMAND HANDLERS
# ============================================================

telegram_app.add_handler(
    CommandHandler(
        "start",
        start,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "profile",
        profile,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "balance",
        balance,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "rank",
        rank,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "stats",
        stats,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "leaderboard",
        leaderboard_command,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "activity",
        activity,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "dailystatus",
        dailystatus,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "help",
        help_command,
    )
)

telegram_app.add_handler(
    CommandHandler(
        "myid",
        myid,
    )
)


# ============================================================
# ADMIN COMMAND
# ============================================================

telegram_app.add_handler(
    CommandHandler(
        "admin",
        admin_panel,
    )
)


# ============================================================
# TEXT MESSAGE ROUTER
# ============================================================

async def text_message_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    # --------------------------------------------------------
    # WITHDRAWAL FLOW FIRST
    # --------------------------------------------------------

    handled = await withdraw_text_handler(
        update,
        context,
    )

    if handled:
        return

    # --------------------------------------------------------
    # ADMIN TEXT FLOW
    # --------------------------------------------------------

    await admin_text_handler(
        update,
        context,
    )


# ============================================================
# TEXT HANDLER
# ============================================================

telegram_app.add_handler(
    CallbackQueryHandler(
        button_callback
    )
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_message_router,
    )
)

# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    error = context.error

    logger.error(
        "Telegram application error: %s",
        error,
        exc_info=error,
    )


telegram_app.add_error_handler(
    error_handler
)


# ============================================================
# START TELEGRAM BOT
# ============================================================

def run_bot():

    logger.info(
        "Starting Unlimited Energy Bot..."
    )

    telegram_app.run_polling(
        drop_pending_updates=True,
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    logger.info(
        "Launching Unlimited Energy Bot..."
    )

    # --------------------------------------------------------
    # Start Flask health server
    # --------------------------------------------------------

    web_thread = threading.Thread(
        target=run_web_server,
        name="flask-health-server",
        daemon=True,
    )

    web_thread.start()

    logger.info(
        "Flask health server started."
    )
    # --------------------------------------------------------
    # Start Telegram polling
    # --------------------------------------------------------

    run_bot()
    
