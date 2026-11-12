"""Technical / risk indicators computed from a daily OHLC DataFrame.

All functions take a DataFrame (index = dates, column "Close") or a Close
Series and are pure (no I/O), so they are easy to test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with MA50 and MA200 columns added."""
    out = df.copy()
    out["MA50"] = out["Close"].rolling(50).mean()
    out["MA200"] = out["Close"].rolling(200).mean()
    return out


def drawdown_series(close: pd.Series) -> pd.Series:
    """Percent below the running all-time high (0 at a new high, negative otherwise)."""
    return (close / close.cummax() - 1) * 100


def max_drawdown(close: pd.Series) -> tuple[float, pd.Timestamp]:
    """Deepest drawdown % in the series and the date it occurred."""
    dd = drawdown_series(close)
    return float(dd.min()), dd.idxmin()


def annualized_vol(close: pd.Series, window: int) -> float:
    """Std-dev of the last `window` daily returns, annualised, in %."""
    rets = close.pct_change().dropna().iloc[-window:]
    return float(rets.std() * np.sqrt(TRADING_DAYS) * 100)


def rolling_vol(close: pd.Series, window: int = 20) -> pd.Series:
    """Rolling annualised volatility series in %."""
    return close.pct_change().rolling(window).std() * np.sqrt(TRADING_DAYS) * 100


PERIODS = {"1M": pd.DateOffset(months=1), "3M": pd.DateOffset(months=3),
           "1Y": pd.DateOffset(years=1), "5Y": pd.DateOffset(years=5),
           "10Y": pd.DateOffset(years=10)}


def period_returns(close: pd.Series) -> dict[str, float]:
    """Total return % over calendar look-backs (1M/3M/1Y/5Y/10Y).

    Uses the last close on/before the start date; if history is slightly
    shorter than the look-back (e.g. exactly 10y), the first close is used.
    """
    last_date, last = close.index[-1], close.iloc[-1]
    out = {}
    for label, offset in PERIODS.items():
        start = last_date - offset
        past = close.loc[:start]
        base = past.iloc[-1] if len(past) else close.iloc[0]
        out[label] = float((last / base - 1) * 100)
    return out


def cross_events(df: pd.DataFrame) -> pd.DataFrame:
    """All MA50/MA200 crossovers: rows with columns Date, Type ('Golden'/'Death')."""
    if "MA50" not in df:
        df = add_moving_averages(df)
    diff = (df["MA50"] - df["MA200"]).dropna()
    sign = np.sign(diff)
    changed = sign.ne(sign.shift()) & sign.shift().notna() & (sign != 0)
    ev = sign[changed]
    return pd.DataFrame({"Date": ev.index,
                         "Type": np.where(ev.values > 0, "Golden", "Death")})


def drawdown_events(close: pd.Series, threshold: float) -> pd.DataFrame:
    """Every episode where price fell more than `threshold`% below a prior high.

    An episode runs from the peak to the first close back at/above that peak.
    Columns: Peak Date, Trough Date, Max Drawdown %, Recovery Date,
    Days Peak→Trough, Days to Recover (trough→recovery, trading days).
    """
    rows = []
    values, dates = close.values, close.index
    peak_i, trough_i, in_dd = 0, 0, False
    for i in range(1, len(values)):
        if values[i] >= values[peak_i]:
            # Back at (or above) the high: close any open episode.
            if in_dd:
                _add_episode(rows, close, peak_i, trough_i, i, threshold)
            peak_i, trough_i, in_dd = i, i, False
        else:
            in_dd = True
            if values[i] < values[trough_i]:
                trough_i = i
    if in_dd:  # still under water at the end of the data
        _add_episode(rows, close, peak_i, trough_i, None, threshold)
    cols = ["Peak Date", "Trough Date", "Max Drawdown %", "Recovery Date",
            "Days Peak→Trough", "Days to Recover"]
    return pd.DataFrame(rows, columns=cols)


def _add_episode(rows, close, peak_i, trough_i, rec_i, threshold):
    dd = (close.iloc[trough_i] / close.iloc[peak_i] - 1) * 100
    if dd > -threshold:
        return
    rows.append({
        "Peak Date": close.index[peak_i].date(),
        "Trough Date": close.index[trough_i].date(),
        "Max Drawdown %": round(float(dd), 2),
        "Recovery Date": close.index[rec_i].date() if rec_i is not None else "Not recovered",
        "Days Peak→Trough": trough_i - peak_i,
        "Days to Recover": (rec_i - trough_i) if rec_i is not None else "Not recovered",
    })


def snapshot(df: pd.DataFrame) -> dict:
    """All headline metrics for the most recent bar, as a flat dict.

    `df` should already contain the live price as its last row
    (see data.merge_live_price).
    """
    df = add_moving_averages(df)
    close = df["Close"]
    last = df.iloc[-1]
    prev_close = close.iloc[-2]
    price = float(last["Close"])
    ma50, ma200 = float(last["MA50"]), float(last["MA200"])
    dd_now = float(drawdown_series(close).iloc[-1])
    mdd, mdd_date = max_drawdown(close)
    crosses = cross_events(df)
    last_cross = crosses.iloc[-1] if len(crosses) else None

    return {
        "price": price,
        "prev_close": float(prev_close),
        "change": price - prev_close,
        "change_pct": (price / prev_close - 1) * 100,
        "ma50": ma50,
        "ma200": ma200,
        # Previous bar's values, used to detect "crossed today" events.
        "prev_ma50": float(df["MA50"].iloc[-2]),
        "prev_ma200": float(df["MA200"].iloc[-2]),
        "dev_ma50_pct": (price / ma50 - 1) * 100,
        "dev_ma200_pct": (price / ma200 - 1) * 100,
        "ath": float(close.max()),
        "drawdown_pct": dd_now,
        "max_drawdown_pct": mdd,
        "max_drawdown_date": mdd_date.date(),
        "vol_20d": annualized_vol(close, 20),
        "vol_1y": annualized_vol(close, TRADING_DAYS),
        "returns": period_returns(close),
        "ma50_above_ma200": ma50 > ma200,
        "last_cross_type": last_cross["Type"] if last_cross is not None else None,
        "last_cross_date": last_cross["Date"].date() if last_cross is not None else None,
        # Did a cross happen on the most recent bar?
        "cross_today": (last_cross["Type"] if last_cross is not None
                        and last_cross["Date"] == df.index[-1] else None),
        "as_of": df.index[-1].date(),
    }
