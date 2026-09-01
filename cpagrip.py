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
    """Return a stable CPAGrip tracking ID for a Telegram user."""
    return f"tg_{int(user_id)}"


def get_user_id_from_tracking_id(tracking_id: str):
    """Convert tg_123456 -> 123456."""
    if not tracking_id:
        return None

    value = str(tracking_id).strip()

    if not value.startswith("tg_"):
        return None

    try:
        return int(value[3:])
    except (TypeError, ValueError):
        return None


def build_cpa_link(user_id: int) -> str:
    """
    Build a user-specific Smart Link.

    CPAGrip receives the tracking_id back in its postback.
    """
    tracking_id = build_tracking_id(user_id)

    separator = "&" if "?" in CPAGRIP_SMARTLINK else "?"

    return (
        f"{CPAGRIP_SMARTLINK}"
        f"{separator}"
        f"{urlencode({'tracking_id': tracking_id})}"
    )
