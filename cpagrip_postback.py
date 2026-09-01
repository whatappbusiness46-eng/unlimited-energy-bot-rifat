# ============================================================
# cpagrip_postback.py
# CPAGrip Global Postback
# ============================================================

import hashlib
import logging
import os
from datetime import datetime, timezone

from flask import Blueprint, request

from cpagrip import (
    CPA_REWARD_POINTS,
    CPA_DAILY_LIMIT,
    get_user_id_from_tracking_id,
)

from database import (
    get_user,
    add_balance,
    add_activity,
    record_transaction,
    transactions,
    cpa_conversions,
)

logger = logging.getLogger(__name__)

cpagrip_bp = Blueprint(
    "cpagrip",
    __name__,
)

CPAGRIP_POSTBACK_PASSWORD = os.getenv(
    "CPAGRIP_POSTBACK_PASSWORD",
    "",
)


def _get_data():
    """
    CPAGrip can send POST data.
    GET is also accepted for easier testing.
    """
    data = {}

    if request.args:
        data.update(
            request.args.to_dict()
        )

    if request.form:
        data.update(
            request.form.to_dict()
        )

    return data


def _utc_day():
    return datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")


def _conversion_key(
    tracking_id,
    offer_id,
    payout,
):
    """
    CPAGrip's supplied fields do not include a guaranteed
    provider conversion ID in the documentation you provided.

    Therefore we create a stable same-day key from the fields
    CPAGrip gives us.
    """
    raw = (
        f"{tracking_id}|"
        f"{offer_id}|"
        f"{payout}|"
        f"{_utc_day()}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


@cpagrip_bp.route(
    "/cpagrip/postback",
    methods=["GET", "POST"],
)
def cpagrip_postback():

    try:

        data = _get_data()

        logger.info(
            "CPAGrip postback received: %s",
            data,
        )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        received_password = str(
            data.get("password", "")
        ).strip()

        if not CPAGRIP_POSTBACK_PASSWORD:
            logger.error(
                "CPAGRIP_POSTBACK_PASSWORD is not configured."
            )
            return "Server configuration error", 500

        if received_password != CPAGRIP_POSTBACK_PASSWORD:
            logger.warning(
                "Invalid CPAGrip postback password."
            )
            return "Invalid password", 403

        # ----------------------------------------------------
        # REQUIRED VARIABLES
        # ----------------------------------------------------

        tracking_id = str(
            data.get("tracking_id", "")
        ).strip()

        offer_id = str(
            data.get("offer_id", "")
        ).strip()

        payout_raw = str(
            data.get("payout", "0")
        ).strip()

        if not tracking_id:
            return "Missing tracking_id", 400

        if not offer_id:
            return "Missing offer_id", 400

        try:
            payout = float(
                payout_raw.replace(",", "")
            )
        except (
            TypeError,
            ValueError,
        ):
            return "Invalid payout", 400

        if payout < 0:
            return "Invalid payout", 400

        # ----------------------------------------------------
        # USER
        # ----------------------------------------------------

        user_id = get_user_id_from_tracking_id(
            tracking_id
        )

        if user_id is None:
            logger.warning(
                "Invalid tracking_id: %s",
                tracking_id,
            )
            return "Invalid tracking_id", 400

        user = get_user(
            user_id,
            create=False,
        )

        if not user:
            logger.warning(
                "CPAGrip conversion for unknown user=%s",
                user_id,
            )

            # Return 200 so provider does not endlessly retry
            # a conversion for a user that no longer exists.
            return "OK", 200

        # ----------------------------------------------------
        # BAN / BLACKLIST
        # ----------------------------------------------------

        if user.get("banned", False):
            logger.warning(
                "Blocked CPAGrip conversion for banned user=%s",
                user_id,
            )
            return "OK", 200

        if user.get("blacklisted", False):
            logger.warning(
                "Blocked CPAGrip conversion for blacklisted user=%s",
                user_id,
            )
            return "OK", 200

        # ----------------------------------------------------
        # CONVERSION KEY
        # ----------------------------------------------------

        conversion_key = _conversion_key(
            tracking_id,
            offer_id,
            payout,
        )

        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------

        existing = cpa_conversions.find_one(
            {
                "conversion_key": conversion_key
            }
        )

        if existing:
            logger.info(
                "Duplicate CPAGrip conversion ignored | "
                "user=%s offer=%s key=%s",
                user_id,
                offer_id,
                conversion_key,
            )

            return "OK", 200

        # ----------------------------------------------------
        # DAILY LIMIT
        # ----------------------------------------------------

        today = _utc_day()

        today_count = cpa_conversions.count_documents(
            {
                "user_id": int(user_id),
                "day": today,
                "status": "credited",
            }
        )

        if today_count >= CPA_DAILY_LIMIT:

            logger.info(
                "CPAGrip daily limit reached | "
                "user=%s count=%s limit=%s",
                user_id,
                today_count,
                CPA_DAILY_LIMIT,
            )

            # Store rejected conversion for audit.
            cpa_conversions.insert_one(
                {
                    "conversion_key": conversion_key,
                    "user_id": int(user_id),
                    "tracking_id": tracking_id,
                    "offer_id": offer_id,
                    "payout": payout,
                    "reward": 0,
                    "status": "daily_limit",
                    "day": today,
                    "created_at": datetime.now(
                        timezone.utc
                    ),
                }
            )

            return "OK", 200

        # ----------------------------------------------------
        # INSERT CONVERSION FIRST
        # ----------------------------------------------------

        try:

            cpa_conversions.insert_one(
                {
                    "conversion_key": conversion_key,
                    "user_id": int(user_id),
                    "tracking_id": tracking_id,
                    "offer_id": offer_id,
                    "payout": payout,
                    "reward": CPA_REWARD_POINTS,
                    "status": "processing",
                    "day": today,
                    "created_at": datetime.now(
                        timezone.utc
                    ),
                }
            )

        except Exception as error:

            # Unique index catches duplicate callbacks.
            logger.info(
                "CPAGrip conversion already recorded: %s",
                error,
            )

            return "OK", 200

        # ----------------------------------------------------
        # CREDIT POINTS
        # ----------------------------------------------------

        credited = add_balance(
            user_id,
            CPA_REWARD_POINTS,
        )

        if not credited:

            cpa_conversions.update_one(
                {
                    "conversion_key":
                        conversion_key
                },
                {
                    "$set": {
                        "status": "credit_failed"
                    }
                },
            )

            logger.error(
                "CPAGrip credit failed | user=%s",
                user_id,
            )

            return "Retry", 500

        # ----------------------------------------------------
        # MARK CREDITED
        # ----------------------------------------------------

        cpa_conversions.update_one(
            {
                "conversion_key":
                    conversion_key
            },
            {
                "$set": {
                    "status": "credited",
                    "credited_at":
                        datetime.now(
                            timezone.utc
                        ),
                }
            },
        )

        # ----------------------------------------------------
        # ACTIVITY
        # ----------------------------------------------------

        try:

            add_activity(
                user_id,
                "🎁 CPAGrip offer completed",
                CPA_REWARD_POINTS,
            )

        except Exception:

            logger.exception(
                "Could not create CPAGrip activity"
            )

        # ----------------------------------------------------
        # PROVIDER-SPECIFIC TRANSACTION
        # ----------------------------------------------------

        try:

            record_transaction(
                user_id=user_id,
                transaction_type="cpagrip",
                amount=CPA_REWARD_POINTS,
                source="cpagrip",
                status="completed",
                metadata={
                    "conversion_key":
                        conversion_key,
                    "tracking_id":
                        tracking_id,
                    "offer_id":
                        offer_id,
                    "payout":
                        payout,
                    "reward":
                        CPA_REWARD_POINTS,
                    "day":
                        today,
                },
            )

        except Exception:

            logger.exception(
                "CPAGrip transaction record failed"
            )

        logger.info(
            "CPAGrip conversion credited | "
            "user=%s offer=%s payout=%s reward=%s",
            user_id,
            offer_id,
            payout,
            CPA_REWARD_POINTS,
        )

        return "OK", 200

    except Exception:

        logger.exception(
            "CPAGrip postback processing failed"
        )

        return "Retry", 500
