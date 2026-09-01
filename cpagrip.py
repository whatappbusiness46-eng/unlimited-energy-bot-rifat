# ============================================================
# cpagrip.py
# CPAGrip Smart Link + tracking helpers
# ============================================================

import os
from urllib.parse import urlencode

CPAGRIP_SMARTLINK = os.getenv(
    "CPAGRIP_SMARTLINK",
    "https://playabledownload.com/1911566",
)

CPA_REWARD_POINTS = int(
    os.getenv("CPA_REWARD_POINTS", "10")
)

CPA_DAILY_LIMIT = int(
    os.getenv("CPA_DAILY_LIMIT", "5")
)


def build_tracking_id(user_id: int) -> str:
    """
    Stable CPAGrip tracking/subid for a Telegram user.
    """
    return f"tg_{int(user_id)}"


def get_user_id_from_tracking_id(tracking_id: str):
    """
    Convert tg_123456789 -> 123456789.
    """
    if not tracking_id:
        return None

    tracking_id = str(tracking_id).strip()

    if not tracking_id.startswith("tg_"):
        return None

    raw_id = tracking_id[3:]

    try:
        return int(raw_id)
    except (TypeError, ValueError):
        return None


def build_cpa_link(user_id: int) -> str:
    """
    Build a user-specific Smart Link.

    CPAGrip documentation supports tracking_id/subid
    being appended to offer/monetization URLs.
    """
    tracking_id = build_tracking_id(user_id)

    separator = (
        "&"
        if "?" in CPAGRIP_SMARTLINK
        else "?"
    )

    return (
        f"{CPAGRIP_SMARTLINK}"
        f"{separator}"
        f"{urlencode({'tracking_id': tracking_id})}"
  )
