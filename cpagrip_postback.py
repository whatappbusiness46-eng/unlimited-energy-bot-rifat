# ============================================================
# cpagrip_postback.py
# CPAGrip Global Postback endpoint
# ============================================================

import hashlib
import logging
import os
from datetime import datetime, timezone

from flask import Blueprint, request
from pymongo.errors import DuplicateKeyError

from database import (
    cpa_conversions,
    get_user,
    add_balance,
    add_activity,
    record_transaction,
)

from cpagrip import (
    CPA_REWARD_POINTS,
    CPA_DAILY_LIMIT,
    get_user_id_from_tracking_id,
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


def _collect_request_data():
    data = {}

    if request.args:
        data.update(request.args.to_dict())

    if request.form:
        data.update(request.form.to_dict())

    return data


def _today_utc():
    return datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")


def _conversion_key(
    tracking_id,
    offer_id,
    payout,
):
    """
    CPAGrip's documented postback fields do not include a
    guaranteed conversion ID. We therefore use the stable
    provider fields plus UTC day as the duplicate key.
    """
    raw = (
        f"{tracking_id}|"
        f"{offer_id}|"
        f"{payout}|"
        f"{_today_utc()}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def _ensure_cpa_indexes():
    """
    Make duplicate protection available even though the existing
    database.py already creates the cpa_conversions collection
    but does not currently create its indexes.
    """
    try:
        cpa_conversions.create_index(
            [("conversion_key", 1)],
            unique=True,
            name="cpagrip_conversion_unique",
        )

        cpa_conversions.create_index(
            [
                ("user_id", 1),
                ("day", 1),
                ("status", 1),
            ],
            name="cpagrip_user_day_status",
        )

    except Exception:
        logger.exception(
            "Could not create CPAGrip MongoDB indexes."
        )


_ensure_cpa_indexes()


@cpagrip_bp.route(
    "/cpagrip/postback",
    methods=["GET", "POST"],
)
def cpagrip_postback():
    try:
        data = _collect_request_data()

        logger.info(
            "CPAGrip postback received: %s",
            data,
        )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        configured_password = (
            CPAGRIP_POSTBACK_PASSWORD
        )

        if not configured_password:
            logger.error(
                "CPAGRIP_POSTBACK_PASSWORD is not configured."
            )
            return "Server configuration error", 500

        received_password = str(
            data.get("password", "")
        ).strip()

        if received_password != configured_password:
            logger.warning(
                "Invalid CPAGrip postback password."
            )
            return "Invalid password", 403

        # ----------------------------------------------------
        # REQUIRED PROVIDER FIELDS
        # ----------------------------------------------------

        tracking_id = str(
            data.get("tracking_id", "")
        ).strip()

        offer_id = str(
            data.get("offer_id", "")
        ).strip()

        payout_raw = str(
            data.get("payout", "")
        ).strip()

        if not tracking_id:
            return "Missing tracking_id", 400

        if not offer_id:
            return "Missing offer_id", 400

        try:
            payout = float(
                payout_raw.replace(",", "")
            )
        except (TypeError, ValueError):
            return "Invalid payout", 400

        if payout <= 0:
            return "Invalid payout", 400

        # ----------------------------------------------------
        # TELEGRAM USER
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
                "CPAGrip callback for unknown user=%s",
                user_id,
            )
            # Do not make the provider retry forever.
            return "OK", 200

        if user.get("banned", False):
            logger.warning(
                "Blocked CPAGrip callback for banned user=%s",
                user_id,
            )
            return "OK", 200

        if user.get("blacklisted", False):
            logger.warning(
                "Blocked CPAGrip callback for blacklisted user=%s",
                user_id,
            )
            return "OK", 200

        # ----------------------------------------------------
        # DUPLICATE KEY
        # ----------------------------------------------------

        day = _today_utc()

        conversion_key = _conversion_key(
            tracking_id,
            offer_id,
            payout,
        )

        existing = cpa_conversions.find_one(
            {
                "conversion_key": conversion_key
            }
        )

        if existing:
            logger.info(
                "Duplicate CPAGrip conversion ignored | "
                "user=%s offer=%s",
                user_id,
                offer_id,
            )
            return "OK", 200

        # ----------------------------------------------------
        # DAILY LIMIT
        # ----------------------------------------------------

        today_count = cpa_conversions.count_documents(
            {
                "user_id": int(user_id),
                "day": day,
                "status": "credited",
            }
        )

        if today_count >= CPA_DAILY_LIMIT:
            cpa_conversions.update_one(
                {
                    "conversion_key": conversion_key
                },
                {
                    "$set": {
                        "user_id": int(user_id),
                        "tracking_id": tracking_id,
                        "offer_id": offer_id,
                        "payout": payout,
                        "reward": 0,
                        "status": "daily_limit",
                        "day": day,
                        "created_at": datetime.now(
                            timezone.utc
                        ),
                    }
                },
                upsert=True,
            )

            logger.info(
                "CPAGrip daily limit reached | "
                "user=%s count=%s limit=%s",
                user_id,
                today_count,
                CPA_DAILY_LIMIT,
            )

            return "OK", 200

        # ----------------------------------------------------
        # RESERVE CONVERSION
        # ----------------------------------------------------

        conversion = {
            "conversion_key": conversion_key,
            "user_id": int(user_id),
            "tracking_id": tracking_id,
            "offer_id": offer_id,
            "payout": payout,
            "reward": CPA_REWARD_POINTS,
            "status": "processing",
            "day": day,
            "created_at": datetime.now(
                timezone.utc
            ),
        }

        try:
            cpa_conversions.insert_one(
                conversion
            )

        except DuplicateKeyError:
            logger.info(
                "Duplicate CPAGrip conversion ignored "
                "during insert | user=%s",
                user_id,
            )
            return "OK", 200

        # ----------------------------------------------------
        # CREDIT USER
        # ----------------------------------------------------

        credited = add_balance(
            user_id,
            CPA_REWARD_POINTS,
        )

        if not credited:
            cpa_conversions.delete_one(
                {
                    "conversion_key":
                        conversion_key
                }
            )

            logger.error(
                "CPAGrip balance credit failed | "
                "user=%s reward=%s",
                user_id,
                CPA_REWARD_POINTS,
            )

            return "Retry", 500

        # ----------------------------------------------------
        # MARK CONVERSION CREDITED
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
                "🎁 CPAGrip Offer",
                CPA_REWARD_POINTS,
            )
        except Exception:
            logger.exception(
                "Could not add CPAGrip activity."
            )

        # ----------------------------------------------------
        # PROVIDER-SPECIFIC TRANSACTION
        #
        # add_balance() already creates the normal credit
        # transaction. This second record identifies the
        # provider conversion.
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
                        day,
                },
            )
        except Exception:
            logger.exception(
                "Could not create CPAGrip transaction record."
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
            "CPAGrip postback processing failed."
        )
        return "Retry", 500
