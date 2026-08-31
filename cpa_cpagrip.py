# ============================================================
# CPAGRIP CPA INTEGRATION - POLICY / POSTBACK SAFE
# ============================================================
# CPAGrip supports incentive offers / offer walls and virtual
# currency, but each individual offer must be checked for its
# allowed traffic/incentive rules before rewarding a user.
#
# This module:
#   - stores CPA offers in MongoDB
#   - creates per-user tracking IDs
#   - builds offer URLs with CPAGrip tracking_id
#   - receives CPAGrip postbacks
#   - deduplicates conversions
#   - records conversions and reward amounts
#   - NEVER auto-rewards an offer unless that offer is marked
#     incentive_allowed=True by the admin
#
# IMPORTANT:
#   Do not mark an offer incentive_allowed unless CPAGrip's
#   offer terms explicitly allow incentivized traffic.
# ============================================================

import hashlib
import hmac
import logging
import os
import time
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from database import db

logger = logging.getLogger(__name__)

CPA_OFFERS = db["cpa_offers"]
CPA_CONVERSIONS = db["cpa_conversions"]

CPA_POSTBACK_SECRET = os.getenv("CPAGRIP_POSTBACK_SECRET", "").strip()
CPA_ENABLED = os.getenv("CPAGRIP_ENABLED", "true").lower() in {
    "1", "true", "yes", "on"
}

DEFAULT_REWARD_PERCENT = Decimal(
    os.getenv("CPA_REWARD_PERCENT", "70")
)


def _now() -> int:
    return int(time.time())


def _money(value) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


def _tracking_id(user_id: int, offer_id: str) -> str:
    raw = f"{user_id}:{offer_id}:{uuid.uuid4().hex}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _sign(value: str) -> str:
    if not CPA_POSTBACK_SECRET:
        return ""
    return hmac.new(
        CPA_POSTBACK_SECRET.encode(),
        value.encode(),
        hashlib.sha256,
    ).hexdigest()


def _verify_signature(payload: str, signature: str) -> bool:
    if not CPA_POSTBACK_SECRET:
        return False
    expected = _sign(payload)
    return bool(
        signature
        and hmac.compare_digest(expected, signature)
    )


def register_cpa_offer(
    offer_id: str,
    title: str,
    offer_url: str,
    payout: float,
    geo: str = "WW",
    incentive_allowed: bool = False,
    enabled: bool = True,
    reward_percent: float = 70,
    category: str = "general",
) -> bool:
    """Create/update an admin-managed CPAGrip offer."""

    offer_id = str(offer_id or "").strip()
    title = str(title or "").strip()
    offer_url = str(offer_url or "").strip()

    if not offer_id or not title or not offer_url:
        return False

    item = {
        "offer_id": offer_id,
        "title": title,
        "offer_url": offer_url,
        "payout": float(_money(payout)),
        "geo": str(geo or "WW").strip().upper(),
        "incentive_allowed": bool(incentive_allowed),
        "enabled": bool(enabled),
        "reward_percent": float(
            _money(reward_percent or DEFAULT_REWARD_PERCENT)
        ),
        "category": str(category or "general").strip(),
        "updated_at": _now(),
    }

    try:
        CPA_OFFERS.create_index(
            "offer_id",
            unique=True,
            name="cpagrip_offer_id_unique",
        )
        CPA_OFFERS.update_one(
            {"offer_id": offer_id},
            {"$set": item},
            upsert=True,
        )
        return True
    except Exception:
        logger.exception(
            "Failed to save CPAGrip offer %s",
            offer_id,
        )
        return False


def get_cpa_offer(offer_id: str) -> Optional[Dict[str, Any]]:
    try:
        return CPA_OFFERS.find_one(
            {"offer_id": str(offer_id)},
            {"_id": 0},
        )
    except Exception:
        logger.exception("Failed to load CPA offer")
        return None


def get_cpa_offers(
    geo: Optional[str] = None,
    include_disabled: bool = False,
):
    query: Dict[str, Any] = {}

    if not include_disabled:
        query["enabled"] = True

    if geo:
        query["$or"] = [
            {"geo": str(geo).upper()},
            {"geo": "WW"},
        ]

    try:
        return list(
            CPA_OFFERS.find(
                query,
                {"_id": 0},
            ).sort("updated_at", -1)
        )
    except Exception:
        logger.exception("Failed to load CPA offers")
        return []


def set_cpa_offer_enabled(
    offer_id: str,
    enabled: bool,
) -> bool:
    try:
        result = CPA_OFFERS.update_one(
            {"offer_id": str(offer_id)},
            {
                "$set": {
                    "enabled": bool(enabled),
                    "updated_at": _now(),
                }
            },
        )
        return result.matched_count > 0
    except Exception:
        logger.exception("Failed to update CPA offer")
        return False


def delete_cpa_offer(offer_id: str) -> bool:
    try:
        result = CPA_OFFERS.delete_one(
            {"offer_id": str(offer_id)}
        )
        return result.deleted_count > 0
    except Exception:
        logger.exception("Failed to delete CPA offer")
        return False


def build_cpa_link(
    user_id: int,
    offer_id: str,
) -> Optional[str]:
    """
    Adds CPAGrip's tracking_id parameter.

    CPAGrip tracking examples commonly use:
        {your_offer_url}&tracking_id={subid}
    """

    if not CPA_ENABLED:
        return None

    offer = get_cpa_offer(offer_id)

    if not offer or not offer.get("enabled", True):
        return None

    tracking_id = _tracking_id(
        user_id,
        str(offer_id),
    )

    # Store the click before redirecting.
    try:
        CPA_CONVERSIONS.insert_one(
            {
                "tracking_id": tracking_id,
                "user_id": int(user_id),
                "offer_id": str(offer_id),
                "status": "click",
                "created_at": _now(),
            }
        )
    except Exception:
        logger.exception("Failed to store CPA click")
        return None

    parts = urlsplit(
        str(offer["offer_url"])
    )

    params = dict(parse_qsl(parts.query))
    params["tracking_id"] = tracking_id

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(params),
            parts.fragment,
        )
    )


def calculate_user_reward(
    offer: Dict[str, Any],
) -> Decimal:
    payout = _money(offer.get("payout", 0))

    if not offer.get("incentive_allowed", False):
        return Decimal("0.00")

    percent = _money(
        offer.get(
            "reward_percent",
            DEFAULT_REWARD_PERCENT,
        )
    )

    if percent <= 0:
        return Decimal("0.00")

    return (
        payout * percent / Decimal("100")
    ).quantize(Decimal("0.01"))


def process_cpagrip_postback(
    tracking_id: str,
    payout: float,
    status: str = "approved",
    txid: str = "",
    signature: str = "",
) -> Dict[str, Any]:
    """
    CPAGrip conversion endpoint logic.

    Suggested CPAGrip postback pattern:
      https://YOUR-DOMAIN/postback/cpagrip
          ?tracking_id={tracking_id}
          &payout={payout}
          &txid={transaction_id}
          &status={status}

    If CPAGrip account settings support a signature/secret,
    configure CPAGRIP_POSTBACK_SECRET and verify it here.
    """

    tracking_id = str(tracking_id or "").strip()
    status = str(status or "approved").strip().lower()
    txid = str(txid or "").strip()

    if not tracking_id:
        return {
            "ok": False,
            "error": "missing_tracking_id",
        }

    click = CPA_CONVERSIONS.find_one(
        {"tracking_id": tracking_id}
    )

    if not click:
        return {
            "ok": False,
            "error": "unknown_tracking_id",
        }

    offer = get_cpa_offer(
        click.get("offer_id")
    )

    if not offer:
        return {
            "ok": False,
            "error": "offer_not_found",
        }

    # Deduplicate by transaction ID when supplied.
    if txid:
        duplicate = CPA_CONVERSIONS.find_one(
            {
                "txid": txid,
                "status": "approved",
            }
        )
        if duplicate:
            return {
                "ok": True,
                "duplicate": True,
                "reward": 0,
            }

    # Handle rejected / reversed conversions.
    if status not in {
        "approved",
        "complete",
        "completed",
        "converted",
        "1",
    }:
        CPA_CONVERSIONS.update_one(
            {"tracking_id": tracking_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": _now(),
                }
            },
        )
        return {
            "ok": True,
            "reward": 0,
            "status": status,
        }

    reward = calculate_user_reward(offer)

    conversion = {
        "tracking_id": tracking_id,
        "user_id": click.get("user_id"),
        "offer_id": click.get("offer_id"),
        "payout": float(_money(payout)),
        "reward": float(reward),
        "txid": txid,
        "status": "approved",
        "incentive_allowed": bool(
            offer.get("incentive_allowed", False)
        ),
        "created_at": _now(),
    }

    # One conversion per tracking ID.
    updated = CPA_CONVERSIONS.update_one(
        {
            "tracking_id": tracking_id,
            "status": "click",
        },
        {"$set": conversion},
    )

    if updated.matched_count == 0:
        return {
            "ok": True,
            "duplicate": True,
            "reward": 0,
        }

    return {
        "ok": True,
        "duplicate": False,
        "user_id": click.get("user_id"),
        "offer_id": click.get("offer_id"),
        "reward": float(reward),
        "incentive_allowed": bool(
            offer.get("incentive_allowed", False)
        ),
    }


def get_user_cpa_stats(user_id: int) -> Dict[str, Any]:
    try:
        rows = list(
            CPA_CONVERSIONS.find(
                {
                    "user_id": int(user_id),
                    "status": "approved",
                },
                {"_id": 0},
            )
        )
    except Exception:
        rows = []

    total_payout = sum(
        _money(x.get("payout", 0))
        for x in rows
    )
    total_reward = sum(
        _money(x.get("reward", 0))
        for x in rows
    )

    return {
        "conversions": len(rows),
        "payout": float(total_payout),
        "reward": float(total_reward),
    }


def cpa_offer_keyboard(
    user_id: int,
    geo: Optional[str] = None,
):
    buttons = []

    for offer in get_cpa_offers(geo=geo):
        buttons.append(
            [
                InlineKeyboardButton(
                    f"🎯 {str(offer.get('title', offer['offer_id']))[:40]}",
                    callback_data=(
                        f"cpa_offer_{offer['offer_id']}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


__all__ = [
    "register_cpa_offer",
    "get_cpa_offer",
    "get_cpa_offers",
    "set_cpa_offer_enabled",
    "delete_cpa_offer",
    "build_cpa_link",
    "calculate_user_reward",
    "process_cpagrip_postback",
    "get_user_cpa_stats",
    "cpa_offer_keyboard",
]
