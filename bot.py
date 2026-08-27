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

    IMPORTANT:
    The exact parameter names must match the macros configured
    in the AdvertsReward publisher dashboard.
    """

    try:
        # ----------------------------------------------------
        # Collect GET + POST parameters
        # ----------------------------------------------------
        data = {}

        if request.args:
            data.update(
                request.args.to_dict()
            )

        if request.form:
            data.update(
                request.form.to_dict()
            )

        logger.info(
            "AdvertsReward callback received: %s",
            data,
        )

        # ----------------------------------------------------
        # User ID / sub-ID
        # ----------------------------------------------------
        user_id = (
            data.get("user_id")
            or data.get("uid")
            or data.get("subid")
            or data.get("sub_id")
            or data.get("telegram_id")
        )

        # ----------------------------------------------------
        # Provider transaction ID
        # ----------------------------------------------------
        transaction_id = (
            data.get("transaction_id")
            or data.get("transaction")
            or data.get("txn_id")
            or data.get("txn")
            or data.get("conversion_id")
            or data.get("click_id")
        )

        # ----------------------------------------------------
        # Conversion status
        # ----------------------------------------------------
        status = str(
            data.get("status")
            or data.get("conversion_status")
            or "approved"
        ).strip().lower()

        rejected_statuses = {
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
            logger.warning(
                "AdvertsReward rejected/reversed callback: %s",
                data,
            )

            # Return 200 so provider does not keep retrying
            # a conversion that should not be credited.
            return "OK", 200

        # ----------------------------------------------------
        # Validate user
        # ----------------------------------------------------
        if not user_id:
            logger.error(
                "AdvertsReward callback missing user ID"
            )
            return "Missing user_id", 400

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            logger.error(
                "Invalid AdvertsReward user ID: %s",
                user_id,
            )
            return "Invalid user_id", 400

        # ----------------------------------------------------
        # Validate transaction ID
        # ----------------------------------------------------
        if not transaction_id:
            logger.error(
                "AdvertsReward callback missing transaction ID"
            )
            return "Missing transaction_id", 400

        transaction_id = str(
            transaction_id
        ).strip()

        if not transaction_id:
            return "Invalid transaction_id", 400

        # ----------------------------------------------------
        # Reward
        #
        # Your dashboard:
        # 1 USD = 1000 Points
        # ----------------------------------------------------
        payout = (
            data.get("payout")
            or data.get("payout_usd")
            or data.get("revenue")
            or data.get("usd")
        )

        direct_points = (
            data.get("points")
            or data.get("reward")
            or data.get("coins")
        )

        points = 0

        # Provider sends USD payout
        if payout is not None:

            try:
                payout_value = float(
                    str(payout)
                    .replace("$", "")
                    .strip()
                )

                points = int(
                    round(
                        payout_value * 1000
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                logger.error(
                    "Invalid AdvertsReward payout: %s",
                    payout,
                )
                return "Invalid payout", 400

        # Provider sends Points directly
        elif direct_points is not None:

            try:
                points = int(
                    float(
                        direct_points
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                logger.error(
                    "Invalid AdvertsReward reward: %s",
                    direct_points,
                )
                return "Invalid reward", 400

        if points <= 0:
            logger.error(
                "AdvertsReward callback has no positive reward: %s",
                data,
            )
            return "Invalid reward", 400

        # ----------------------------------------------------
        # Import database functions here
        # ----------------------------------------------------
        from database import (
            get_user,
            add_balance,
            record_transaction,
            transactions,
        )

        # ----------------------------------------------------
        # User must exist
        # ----------------------------------------------------
        user = get_user(
            user_id,
            create=False,
        )

        if not user:
            logger.warning(
                "AdvertsReward callback for unknown user=%s",
                user_id,
            )
            return "Unknown user", 200

        # ----------------------------------------------------
        # Do not reward banned / blacklisted users
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
        # Store provider transaction ID in our transaction
        # collection before crediting.
        # ----------------------------------------------------
        external_txn_id = (
            "AR-"
            + transaction_id
        )

        existing = transactions.find_one(
            {
                "external_transaction_id":
                    transaction_id,
                "source":
                    "advertsreward",
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
        # Add provider-specific transaction metadata
        # ----------------------------------------------------
        record_transaction(
            user_id=user_id,
            transaction_type="credit",
            amount=points,
            source="advertsreward",
            status="completed",
            metadata={
                "external_transaction_id":
                    transaction_id,
                "payout_usd":
                    payout,
                "status":
                    status,
                "provider":
                    "advertsreward",
                "external_transaction_key":
                    external_txn_id,
            },
        )

        logger.info(
            "AdvertsReward conversion credited | "
            "user=%s points=%s txn=%s",
            user_id,
            points,
            transaction_id,
        )

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


# ============================================================
# TELEGRAM APPLICATION
# ============================================================

telegram_app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)


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
    
