"""Notification channels: Windows desktop toast (plyer) and ntfy.sh phone push.

Both functions return True/False and never raise, so a failed notification
can't crash the monitor.
"""
from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)

APP_NAME = "SPY/QQQ Monitor"


def desktop(title: str, message: str, timeout: int = 10) -> bool:
    """Show a Windows desktop notification."""
    try:
        from plyer import notification
        # Windows balloon tips cap title at 64 and message at 256 chars.
        notification.notify(title=title[:63], message=message[:255],
                            app_name=APP_NAME, timeout=timeout)
        return True
    except Exception as exc:
        log.error("Desktop notification failed: %s", exc)
        return False


def ntfy(topic: str, title: str, message: str, priority: str = "high") -> bool:
    """Push to https://ntfy.sh/<topic>. Subscribe to the same topic in the ntfy app."""
    topic = (topic or "").strip()
    if not topic:
        return False
    try:
        r = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            # HTTP headers must be latin-1; drop anything else from the title.
            headers={"Title": title.encode("latin-1", "ignore").decode("latin-1"),
                     "Priority": priority, "Tags": "chart_with_upwards_trend"},
            timeout=10,
        )
        r.raise_for_status()
        return True
    except Exception as exc:
        log.error("ntfy push failed: %s", exc)
        return False
