# ============================================================
# provider_integrations.py
# Real provider integration layer for Unlimited Energy Bot.
#
# This module deliberately does NOT contain provider secrets.
# Credentials and exact provider endpoints are supplied through
# Render environment variables after the provider account is
# configured.
# ============================================================

import hashlib
import hmac
import json
import logging
import os
import time
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from database import db, add_balance, add_activity, record_transaction, get_user

logger = logging.getLogger(__name__)

provider_offers = db["provider_offers"]
provider_events = db["provider_events"]

try:
    provider_offers.create_index(
        [("provider", 1), ("offer_id", 1)],
        unique=True,
        name="provider_offer_unique",
    )
    provider_events.create_index(
        [("provider", 1), ("event_id", 1)],
        unique=True,
        name="provider_event_unique",
    )
except Exception:
    logger.exception("Provider integration indexes could not be created.")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _json_request(url: str, *, method: str = "GET",
                  params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None,
                  body: Optional[Dict[str, Any]] = None,
                  timeout: int = 15) -> Any:
    params = params or {}
    headers = {"User-Agent": "UnlimitedEnergyBot/2.1", **(headers or {})}

    if method.upper() == "GET" and params:
        parsed = urlparse(url)
        current = parse_qs(parsed.query, keep_blank_values=True)
        for key, value in params.items():
            current[key] = [str(value)]
        query = urlencode(current, doseq=True)
        url = urlunparse(parsed._replace(query=query))

    data = None
    if method.upper() != "GET":
        data = json.dumps(body or {}).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    req = Request(url, data=data, headers=headers, method=method.upper())
    with urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw


def _first(data: Dict[str, Any], keys: Iterable[str], default=None):
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return default


def _normalise_offer(provider: str, raw: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
    offer_id = _first(raw, ("offer_id", "id", "offerId", "campaign_id", "campaignId"))
    title = _first(raw, ("title", "name", "offer_name", "offerName"), f"{provider.title()} Offer")
    url = _first(raw, ("url", "link", "click_url", "tracking_url", "offer_url"))
    if not offer_id or not url:
        return None

    reward = _first(raw, ("reward", "payout", "amount", "points"), 0)
    try:
        reward = float(reward)
    except (TypeError, ValueError):
        reward = 0.0

    description = str(_first(raw, ("description", "desc", "details"), "") or "")
    category = str(_first(raw, ("category", "vertical", "type"), "") or "")
    platform = str(_first(raw, ("platform", "device", "os"), "") or "")

    # Provider links sometimes expose a {user_id} placeholder.
    # Never invent tracking parameters if the provider has not documented them.
    url = str(url).replace("{user_id}", str(user_id)).replace("{uid}", str(user_id))

    return {
        "provider": provider,
        "offer_id": str(offer_id),
        "title": str(title),
        "description": description,
        "url": url,
        "provider_reward": reward,
        "category": category,
        "platform": platform,
        "raw": raw,
        "updated_at": int(time.time()),
    }


def _extract_offer_list(payload: Any) -> list:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    for key in ("offers", "data", "results", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for subkey in ("offers", "items", "results"):
                if isinstance(value.get(subkey), list):
                    return value[subkey]
    return []


def _provider_request_config(provider: str, user_id: int) -> Optional[Dict[str, Any]]:
    provider = provider.lower()

    if provider == "advertsreward":
        url = _env("ADVERTSREWARD_OFFERS_API_URL")
        if not url:
            return None
        return {
            "url": url,
            "headers": {
                "Authorization": f"Bearer {_env('ADVERTSREWARD_API_KEY')}"
            } if _env("ADVERTSREWARD_API_KEY") else {},
            "params": {
                "site_key": _env("ADVERTSREWARD_SITE_KEY"),
                "user_id": user_id,
                "format": _env("ADVERTSREWARD_FORMAT", "offerwall"),
            },
        }

    if provider == "cpagrip":
        template = _env("CPAGRIP_OFFERS_API_URL")
        if not template:
            return None
        url = template.replace("{user_id}", str(user_id))
        if "{api_key}" in url:
            url = url.replace("{api_key}", _env("CPAGRIP_API_KEY"))
        return {
            "url": url,
            "headers": {},
            "params": {} if "?" in url else {"user_id": user_id},
        }

    return None


def sync_provider_offers(provider: str, user_id: int) -> int:
    provider = provider.lower()
    config = _provider_request_config(provider, int(user_id))
    if not config:
        return 0

    try:
        payload = _json_request(
            config["url"],
            params=config.get("params"),
            headers=config.get("headers"),
        )
        count = 0
        for raw in _extract_offer_list(payload):
            if not isinstance(raw, dict):
                continue
            offer = _normalise_offer(provider, raw, int(user_id))
            if not offer:
                continue
            provider_offers.update_one(
                {"provider": provider, "offer_id": offer["offer_id"]},
                {"$set": offer},
                upsert=True,
            )
            count += 1
        return count
    except Exception:
        logger.exception("Provider offer sync failed | provider=%s user=%s", provider, user_id)
        return 0


def get_provider_offers(user_id: int, providers: Optional[Iterable[str]] = None) -> list:
    providers = list(providers or (
        "advertsreward",
        "cpagrip",
    ))
    for provider in providers:
        sync_provider_offers(provider, user_id)

    query = {"provider": {"$in": providers}}
    return list(provider_offers.find(query, {"_id": 0}).sort("updated_at", -1).limit(100))


def _reward_points(provider: str, reward: Any) -> int:
    try:
        amount = Decimal(str(reward))
    except (InvalidOperation, ValueError):
        return 0

    # Provider payout is assumed to be USD unless configured otherwise.
    # Example: 1000 points per $1.00.
    rate = Decimal(_env("REWARD_POINTS_PER_USD", "1000"))
    if rate <= 0:
        return 0
    return max(0, int((amount * rate).quantize(Decimal("1"))))


def _verify_shared_secret(provider: str, params: Dict[str, Any]) -> bool:
    secret = _env(f"{provider.upper()}_POSTBACK_SECRET")
    if not secret:
        return False

    supplied = str(
        params.get("secret")
        or params.get("token")
        or params.get("api_key")
        or params.get("password")
        or ""
    )
    return hmac.compare_digest(supplied, secret)


def _verify_hmac(provider: str, params: Dict[str, Any]) -> bool:
    secret = _env(f"{provider.upper()}_POSTBACK_SECRET")
    signature = str(params.get("signature") or params.get("sig") or "")
    if not secret or not signature:
        return False

    template = _env(
        f"{provider.upper()}_POSTBACK_SIGNATURE_TEMPLATE",
        "{event}|{user_id}|{event_id}|{reward}",
    )
    try:
        message = template.format(
            event=params.get("event", ""),
            user_id=params.get("user_id", ""),
            event_id=params.get("event_id", ""),
            reward=params.get("reward", ""),
            click_id=params.get("click_id", ""),
            offer_id=params.get("offer_id", ""),
        )
    except Exception:
        return False

    digest = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(digest, signature)


def process_postback(provider: str, params: Dict[str, Any]) -> Dict[str, Any]:
    provider = str(provider).lower().strip()

    event_id = str(
        params.get("event_id")
        or params.get("transaction_id")
        or params.get("txn")
        or params.get("conversion_id")
        or params.get("click_id")
        or ""
    ).strip()

    user_id_raw = (
        params.get("user_id")
        or params.get("uid")
        or params.get("subid")
        or params.get("sub_id")
    )
    reward_raw = (
        params.get("reward")
        if params.get("reward") not in (None, "")
        else params.get("payout", params.get("amount", 0))
    )
    status = str(params.get("status") or params.get("event") or "approved").lower()

    if not event_id or user_id_raw in (None, ""):
        return {"ok": False, "error": "missing_event_or_user"}

    try:
        user_id = int(str(user_id_raw))
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_user_id"}

    user = get_user(user_id, create=False)
    if not user:
        return {"ok": False, "error": "user_not_found"}

    # Provider-specific verification must be configured. Never credit an
    # unverified callback.
    verified = _verify_shared_secret(provider, params)
    if not verified:
        verified = _verify_hmac(provider, params)
    if not verified:
        return {"ok": False, "error": "invalid_signature"}

    # Reversal/chargeback events should remove a previously credited amount.
    try:
        reward_amount = Decimal(str(reward_raw or "0"))
    except (InvalidOperation, ValueError):
        reward_amount = Decimal("0")

    points = _reward_points(provider, reward_amount)
    if points <= 0:
        return {"ok": False, "error": "invalid_reward"}

    # Idempotency: provider event is unique.
    event_doc = {
        "provider": provider,
        "event_id": event_id,
        "user_id": user_id,
        "reward_raw": str(reward_raw),
        "points": points,
        "status": status,
        "received_at": int(time.time()),
        "params": {str(k): str(v) for k, v in params.items()},
    }

    if status in {"reversed", "chargeback", "reject", "rejected"}:
        existing = provider_events.find_one({
            "provider": provider,
            "event_id": event_id,
        })
        if not existing:
            # We cannot safely reverse a conversion we never credited.
            return {"ok": True, "message": "reversal_ignored_unknown_event"}

        provider_events.update_one(
            {"_id": existing["_id"]},
            {"$set": {"status": status, "reversed_at": int(time.time())}},
        )
        return {"ok": True, "message": "reversal_recorded"}

    try:
        provider_events.insert_one(event_doc)
    except Exception as exc:
        # Duplicate event => already processed.
        if "duplicate" in str(exc).lower() or "e11000" in str(exc).lower():
            return {"ok": True, "message": "duplicate_ignored"}
        logger.exception("Provider event insert failed")
        return {"ok": False, "error": "event_store_failed"}

    if not add_balance(user_id, points):
        provider_events.delete_one({"provider": provider, "event_id": event_id})
        return {"ok": False, "error": "credit_failed"}

    try:
        add_activity(
            user_id,
            f"💸 {provider.title()} conversion",
            points,
        )
    except Exception:
        logger.exception("Provider activity log failed")

    return {
        "ok": True,
        "message": "credited",
        "provider": provider,
        "event_id": event_id,
        "user_id": user_id,
        "points": points,
    }


def provider_status() -> Dict[str, Any]:
    return {
        "advertsreward": bool(_env("ADVERTSREWARD_OFFERS_API_URL")),
        "cpagrip": bool(_env("CPAGRIP_OFFERS_API_URL")),
        "advertsreward_postback": bool(_env("ADVERTSREWARD_POSTBACK_SECRET")),
        "cpagrip_postback": bool(_env("CPAGRIP_POSTBACK_SECRET")),
        "reward_points_per_usd": _env("REWARD_POINTS_PER_USD", "1000"),
    }
