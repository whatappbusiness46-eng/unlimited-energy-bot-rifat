# ============================================================
# bot.py
# Unlimited Energy Bot V2
# FINAL APPLICATION ENTRY POINT
# Render Worker + Flask Health Server
# ============================================================

import logging
import os
import threading

from flask import Flask

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
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

from withdraw import withdraw_text_handler


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
# ============================================================
# TEXT MESSAGE ROUTER
# ============================================================

async def text_message_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    # Withdrawal gets priority
    handled = await withdraw_text_handler(
        update,
        context,
    )

    if handled:
        return

    # Otherwise process admin text
    await admin_text_handler(
        update,
        context,
    )

    # -----------------------------------------
    # WITHDRAWAL FLOW
    # -----------------------------------------

    handled = await withdraw_text_handler(
        update,
        context,
    )

    if handled:
        return

    # -----------------------------------------
    # ADMIN TEXT FLOW
    # -----------------------------------------

    await admin_text_handler(
        update,
        context,
    )


# ============================================================
# ADMIN TEXT HANDLER
# ============================================================
#
# Handles non-command text messages used by the
# admin panel workflow.
#

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_message_router,
    )
)


# ============================================================
# CALLBACK QUERY HANDLER
# ============================================================

telegram_app.add_handler(
    CallbackQueryHandler(
        button_callback,
    )
)


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context,
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
    
