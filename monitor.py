"""Background monitor: checks alert rules during US market hours and sends notifications.

Usage:
    python monitor.py              # loop forever, interval from rules.json (default 5 min)
    python monitor.py --interval 2 # override interval (minutes)
    python monitor.py --once       # run a single check and exit
    python monitor.py --force      # ignore market hours (useful for testing)

rules.json is re-read every cycle, so edits made in the dashboard take effect
without restarting. Errors are logged and the loop keeps running.
"""
from __future__ import annotations

import argparse
import logging
import time

from src import data, indicators as ind, rules
from src.data import DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler(DATA_DIR / "monitor.log", encoding="utf-8")],
)
log = logging.getLogger("monitor")


def build_snapshots(symbols: set[str]) -> dict[str, dict]:
    """Live snapshot per symbol; a failing symbol is skipped, not fatal."""
    snaps = {}
    for sym in sorted(symbols):
        try:
            hist = data.get_history(sym)            # cached once per day
            quote = data.get_quote(sym)
            snaps[sym] = ind.snapshot(data.merge_live_price(hist, quote))
            s = snaps[sym]
            log.info("%s %.2f (%+.2f%%) | MA200 %+.2f%% | DD %.2f%%",
                     sym, s["price"], s["change_pct"], s["dev_ma200_pct"], s["drawdown_pct"])
        except Exception as exc:
            log.error("Could not load %s: %s", sym, exc)
    return snaps


def run_check() -> None:
    cfg = rules.load_config()
    active = [r for r in cfg["rules"] if r.get("enabled")]
    if not active:
        log.info("No enabled rules.")
        return
    snaps = build_snapshots({r["symbol"] for r in active})
    fired = rules.check_and_notify(snaps, cfg)
    log.info("Checked %d rule(s), %d new alert(s).", len(active), len(fired))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--interval", type=float, help="minutes between checks (overrides rules.json)")
    p.add_argument("--once", action="store_true", help="run one check and exit")
    p.add_argument("--force", action="store_true", help="check even when the market is closed")
    args = p.parse_args()

    log.info("Monitor started. Press Ctrl+C to stop.")
    while True:
        interval = args.interval or rules.load_config()["settings"]["check_interval_min"]
        interval = max(float(interval), 1.0)  # never poll faster than once a minute
        try:
            if args.force or data.is_market_open():
                run_check()
            else:
                log.info("Market closed (%s ET) - skipping check.", f"{data.now_et():%a %H:%M}")
        except Exception:
            log.exception("Unexpected error during check; will retry next cycle.")
        if args.once:
            break
        try:
            time.sleep(interval * 60)
        except KeyboardInterrupt:
            break
    log.info("Monitor stopped.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Monitor stopped.")
