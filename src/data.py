"""Market data access: live quotes and 10-year daily history via yfinance.

* Every network call goes through `_retry` (simple retry with back-off).
* Daily history is cached as CSV under data/. If the cache file was written
  today it is reused instead of downloading again. If a download fails and an
  older cache exists, the stale cache is used so the app keeps working.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, date, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

ET = ZoneInfo("America/New_York")
SYMBOLS = ["SPY", "QQQ"]


class DataError(RuntimeError):
    """Raised when data could not be fetched after all retries."""


def _retry(func, *args, attempts: int = 3, delay: float = 2.0, **kwargs):
    """Call `func` up to `attempts` times, doubling the wait between tries."""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # yfinance raises many different types
            last_exc = exc
            log.warning("Attempt %d/%d failed for %s: %s", i + 1, attempts, func.__name__, exc)
            if i < attempts - 1:
                time.sleep(delay * (2 ** i))
    raise DataError(f"{func.__name__} failed after {attempts} attempts: {last_exc}")


# --------------------------------------------------------------------------- #
# Market hours
# --------------------------------------------------------------------------- #
def now_et() -> datetime:
    return datetime.now(ET)


def is_market_open(ts: datetime | None = None) -> bool:
    """US regular session: Mon-Fri 09:30-16:00 ET (exchange holidays ignored)."""
    ts = (ts or now_et()).astimezone(ET)
    if ts.weekday() >= 5:
        return False
    return dtime(9, 30) <= ts.time() < dtime(16, 0)


# --------------------------------------------------------------------------- #
# Live quote
# --------------------------------------------------------------------------- #
def _fetch_quote(symbol: str) -> dict:
    fi = yf.Ticker(symbol).fast_info
    last = float(fi["last_price"])
    # NOTE: fast_info["previous_close"] can be off (derived from a different
    # chart window); regular_market_previous_close matches the official close.
    try:
        prev = float(fi["regular_market_previous_close"])
    except Exception:
        prev = float(fi["previous_close"])
    if not last or last != last:  # 0 or NaN
        raise ValueError(f"empty last_price for {symbol}")
    return {
        "symbol": symbol,
        "price": last,
        "prev_close": prev,
        "open": float(fi["open"]),
        "high": float(fi["day_high"]),
        "low": float(fi["day_low"]),
        "change": last - prev,
        "change_pct": (last / prev - 1) * 100 if prev else float("nan"),
        "fetched_at": now_et(),
    }


def get_quote(symbol: str) -> dict:
    """Latest price snapshot. Raises DataError if all retries fail."""
    return _retry(_fetch_quote, symbol)


# --------------------------------------------------------------------------- #
# Historical data (with CSV cache)
# --------------------------------------------------------------------------- #
def _cache_path(symbol: str) -> Path:
    return DATA_DIR / f"{symbol}_history.csv"


def _read_cache(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col="Date", parse_dates=["Date"])
    return df.sort_index()


def _download_history(symbol: str, period: str) -> pd.DataFrame:
    df = yf.Ticker(symbol).history(period=period, auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"empty history for {symbol}")
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    # Store dates as tz-naive calendar days -> simpler CSV round-trip.
    df.index = pd.to_datetime(df.index.tz_localize(None).date)
    df.index.name = "Date"
    return df


def get_history(symbol: str, period: str = "10y", force: bool = False) -> pd.DataFrame:
    """Daily OHLCV (dividend-adjusted). Uses today's CSV cache when available."""
    path = _cache_path(symbol)
    if path.exists() and not force:
        if date.fromtimestamp(path.stat().st_mtime) == date.today():
            return _read_cache(path)
    try:
        df = _retry(_download_history, symbol, period)
        df.to_csv(path)
        return df
    except DataError:
        if path.exists():
            log.warning("Using stale cache for %s", symbol)
            return _read_cache(path)
        raise


def merge_live_price(hist: pd.DataFrame, quote: dict | None) -> pd.DataFrame:
    """Return a copy of `hist` whose last bar reflects the live quote.

    If today's bar already exists it is updated, otherwise a new bar is appended.
    This keeps MA / drawdown figures current during the trading day.
    """
    if not quote:
        return hist
    df = hist.copy()
    today = pd.Timestamp(quote["fetched_at"].astimezone(ET).date())
    bar = {"Open": quote["open"], "High": quote["high"], "Low": quote["low"],
           "Close": quote["price"]}
    if today in df.index:
        for k, v in bar.items():
            df.loc[today, k] = v
    elif today > df.index[-1]:
        df.loc[today] = {**bar, "Volume": float("nan")}
    return df
