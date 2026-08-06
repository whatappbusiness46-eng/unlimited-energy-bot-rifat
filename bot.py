import os
import threading
import logging

from flask import Flask

from telegram.ext import (
    Application,
)

# ==========================
# IMPORT PROJECT FILES
# ==========================

from config import BOT_TOKEN

# Handlers (Later)
# from handlers import *
# from callbacks import *

# ==========================
# LOGGING
# ==========================

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ==========================
# FLASK APP
# ==========================

web = Flask(__name__)

@web.route("/")
def home():
    return "✅ Unlimited Energy Bot V2 is Running."

def run_web():
    web.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

# ==========================
# CREATE TELEGRAM APPLICATION
# ==========================

app = Application.builder().token(BOT_TOKEN).build()
# ==========================
# BOT STARTUP
# ==========================

async def on_startup(app: Application):

    logger.info("==============================")
    logger.info("Unlimited Energy Bot V2 Started")
    logger.info("==============================")


# ==========================
# ERROR HANDLER
# ==========================

async def error_handler(update, context):

    logger.error(
        "Exception while handling update:",
        exc_info=context.error
    )


# ==========================
# REGISTER HANDLERS
# ==========================

def register_handlers():

    # User Commands
    # app.add_handler(CommandHandler(...))

    # Admin Commands
    # app.add_handler(CommandHandler(...))

    # Callback Buttons
    # app.add_handler(CallbackQueryHandler(...))

    pass


# ==========================
# BUILD BOT
# ==========================

def build_bot():

    register_handlers()

    app.add_error_handler(error_handler)

    app.post_init = on_startup
  # ==========================
# MAIN FUNCTION
# ==========================

def main():

    build_bot()

    threading.Thread(

        target=run_web,

        daemon=True

    ).start()

    logger.info("Flask Server Started")

    logger.info("Starting Telegram Bot...")

    app.run_polling(

        allowed_updates=None,

        drop_pending_updates=True

    )


# ==========================
# RUN BOT
# ==========================

if __name__ == "__main__":

    main()
  
