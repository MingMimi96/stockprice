"""Alert rules: definition, persistence (rules.json), evaluation and the alert log.

rules.json layout:
    {
      "settings": {"ntfy_topic": "", "check_interval_min": 5, "desktop_notify": true},
      "rules": [{"id": "...", "symbol": "SPY", "type": "price_below",
                 "value": 500, "enabled": true, "note": ""}, ...]
    }

Both the dashboard and monitor.py use `check_and_notify`, so behaviour
(including "once per rule per day" de-duplication) is identical in both.
"""
from __future__ import annotations

import csv
import json
import logging
import uuid
from pathlib import Path

import pandas as pd

from . import notify
from .data import DATA_DIR, ROOT, now_et

log = logging.getLogger(__name__)

RULES_PATH = ROOT / "rules.json"
LOG_PATH = DATA_DIR / "alerts_log.csv"
LOG_COLUMNS = ["timestamp_et", "symbol", "rule_id", "rule", "price", "change_pct",
               "dev_ma200_pct", "drawdown_pct", "vol_20d"]

# type -> (UI label, needs a numeric value?)
RULE_TYPES: dict[str, tuple[str, bool]] = {
    "price_below":   ("Price below X", True),
    "price_above":   ("Price above X", True),
    "daily_drop":    ("Daily drop exceeds X%", True),
    "drawdown":      ("Drawdown from high exceeds X%", True),
    "cross_below_ma200": ("Breaks below MA200", False),
    "cross_above_ma200": ("Breaks above MA200", False),
    "cross_below_ma50":  ("Breaks below MA50", False),
    "cross_above_ma50":  ("Breaks above MA50", False),
    "golden_cross":  ("Golden cross (MA50 crosses above MA200)", False),
    "death_cross":   ("Death cross (MA50 crosses below MA200)", False),
}
LABEL_TO_TYPE = {label: t for t, (label, _) in RULE_TYPES.items()}

DEFAULT_SETTINGS = {"ntfy_topic": "", "check_interval_min": 5, "desktop_notify": True}


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def new_id() -> str:
    return uuid.uuid4().hex[:8]


def load_config(path: Path = RULES_PATH) -> dict:
    """Read rules.json; returns defaults if the file is missing or corrupt."""
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        cfg = {}
    except json.JSONDecodeError as exc:
        log.error("rules.json is not valid JSON (%s); using empty rule set", exc)
        cfg = {}
    cfg["settings"] = {**DEFAULT_SETTINGS, **cfg.get("settings", {})}
    cfg.setdefault("rules", [])
    for r in cfg["rules"]:
        r.setdefault("id", new_id())
        r.setdefault("enabled", True)
        r.setdefault("note", "")
    return cfg


def save_config(cfg: dict, path: Path = RULES_PATH) -> None:
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def describe(rule: dict) -> str:
    """Human-readable rule text, e.g. 'SPY: Price below 500'."""
    label, needs_value = RULE_TYPES.get(rule["type"], (rule["type"], False))
    if needs_value:
        unit = "%" if rule["type"] in ("daily_drop", "drawdown") else ""
        label = label.replace("X%", f"{rule['value']:g}{unit}").replace("X", f"{rule['value']:g}")
    return f"{rule['symbol']}: {label}"


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def evaluate(rule: dict, s: dict) -> bool:
    """True if `rule` is satisfied by snapshot `s` (from indicators.snapshot).

    Threshold rules (price / drop / drawdown) are *state* checks.
    MA and cross rules are *events*: they fire only on the day the line is
    crossed (previous close on one side, current price on the other).
    """
    t, v = rule["type"], rule.get("value")
    prev = s["prev_close"]
    match t:
        case "price_below":  return s["price"] < v
        case "price_above":  return s["price"] > v
        case "daily_drop":   return s["change_pct"] <= -abs(v)
        case "drawdown":     return s["drawdown_pct"] <= -abs(v)
        case "cross_below_ma200": return prev >= s["prev_ma200"] and s["price"] < s["ma200"]
        case "cross_above_ma200": return prev <= s["prev_ma200"] and s["price"] > s["ma200"]
        case "cross_below_ma50":  return prev >= s["prev_ma50"] and s["price"] < s["ma50"]
        case "cross_above_ma50":  return prev <= s["prev_ma50"] and s["price"] > s["ma50"]
        case "golden_cross": return s["cross_today"] == "Golden"
        case "death_cross":  return s["cross_today"] == "Death"
    log.warning("Unknown rule type %s", t)
    return False


# --------------------------------------------------------------------------- #
# Alert log (CSV) + de-duplication
# --------------------------------------------------------------------------- #
def read_log() -> pd.DataFrame:
    if not LOG_PATH.exists():
        return pd.DataFrame(columns=LOG_COLUMNS)
    try:
        return pd.read_csv(LOG_PATH)
    except Exception as exc:  # corrupt/locked file shouldn't break the UI
        log.error("Could not read alert log: %s", exc)
        return pd.DataFrame(columns=LOG_COLUMNS)


def already_fired_today(rule_id: str) -> bool:
    """De-dup: has this rule already been logged on today's (ET) date?"""
    df = read_log()
    if df.empty:
        return False
    today = now_et().strftime("%Y-%m-%d")
    return bool(((df["rule_id"] == rule_id) & df["timestamp_et"].str.startswith(today)).any())


def append_log(rule: dict, s: dict) -> dict:
    row = {
        "timestamp_et": now_et().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": rule["symbol"], "rule_id": rule["id"], "rule": describe(rule),
        "price": round(s["price"], 2), "change_pct": round(s["change_pct"], 2),
        "dev_ma200_pct": round(s["dev_ma200_pct"], 2),
        "drawdown_pct": round(s["drawdown_pct"], 2), "vol_20d": round(s["vol_20d"], 1),
    }
    new_file = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        if new_file:
            w.writeheader()
        w.writerow(row)
    return row


def format_message(rule: dict, s: dict) -> tuple[str, str]:
    """Notification title and body with the key market data."""
    title = f"{rule['symbol']} alert: {describe(rule).split(': ', 1)[1]}"
    body = (f"Price ${s['price']:.2f} ({s['change_pct']:+.2f}% today)\n"
            f"vs MA200: {s['dev_ma200_pct']:+.2f}% | Drawdown: {s['drawdown_pct']:.2f}%\n"
            f"20D vol: {s['vol_20d']:.1f}%")
    return title, body


def check_and_notify(snapshots: dict[str, dict], cfg: dict | None = None) -> list[dict]:
    """Evaluate all enabled rules; notify + log those that fire (max once/day each).

    `snapshots` maps symbol -> indicators.snapshot(...). Returns the logged rows.
    """
    cfg = cfg or load_config()
    settings = cfg["settings"]
    fired = []
    for rule in cfg["rules"]:
        if not rule.get("enabled"):
            continue
        s = snapshots.get(rule["symbol"])
        if s is None:
            continue
        try:
            if not evaluate(rule, s) or already_fired_today(rule["id"]):
                continue
        except Exception as exc:  # bad rule data shouldn't stop the others
            log.error("Rule %s could not be evaluated: %s", rule, exc)
            continue
        title, body = format_message(rule, s)
        log.info("TRIGGERED %s -> %s", describe(rule), body.replace("\n", " | "))
        if settings.get("desktop_notify", True):
            notify.desktop(title, body)
        if settings.get("ntfy_topic"):
            notify.ntfy(settings["ntfy_topic"], title, body)
        fired.append(append_log(rule, s))
    return fired
