import logging
import os

from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
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
    verify_join,
)

from callbacks import (
    button_callback,
)


# ==========================
# LOGGING
# ==========================

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


# ==========================
# FLASK SERVER
# ==========================

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


# ==========================
# TELEGRAM APPLICATION
# ==========================

telegram_app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)


# ==========================
# COMMAND HANDLERS
# ==========================

telegram_app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

telegram_app.add_handler(
    CommandHandler(
        "profile",
        profile
    )
)

telegram_app.add_handler(
    CommandHandler(
        "balance",
        balance
    )
)

telegram_app.add_handler(
    CommandHandler(
        "rank",
        rank
    )
)

telegram_app.add_handler(
    CommandHandler(
        "stats",
        stats
    )
)

telegram_app.add_handler(
    CommandHandler(
        "leaderboard",
        leaderboard_command
    )
)

telegram_app.add_handler(
    CommandHandler(
        "activity",
        activity
    )
)

telegram_app.add_handler(
    CommandHandler(
        "dailystatus",
        dailystatus
    )
)

telegram_app.add_handler(
    CommandHandler(
        "help",
        help_command
    )
)

telegram_app.add_handler(
    CommandHandler(
        "myid",
        myid
    )
)


# ==========================
# CALLBACK HANDLER
# ==========================

telegram_app.add_handler(
    CallbackQueryHandler(
        button_callback
    )
)


# ==========================
# ERROR HANDLER
# ==========================

async def error_handler(
    update: object,
    context
):

    logger.error(
        "Telegram error: %s",
        context.error,
        exc_info=context.error,
    )


telegram_app.add_error_handler(
    error_handler
)


# ==========================
# START BOT
# ==========================

def run_bot():

    logger.info(
        "Starting Unlimited Energy Bot..."
    )

    telegram_app.run_polling(
        drop_pending_updates=True
    )


# ==========================
# MAIN
# ==========================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    # Flask runs separately only if needed.
    # Render worker normally starts the Telegram bot.
    run_bot()
    
