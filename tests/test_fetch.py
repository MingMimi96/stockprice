"""Stage 1 smoke test: confirm yfinance returns live prices and 10y history."""
import yfinance as yf

for sym in ["SPY", "QQQ"]:
    t = yf.Ticker(sym)
    fi = t.fast_info
    print(f"{sym}: last={fi['last_price']:.2f} prev_close={fi['previous_close']:.2f} "
          f"open={fi['open']:.2f} high={fi['day_high']:.2f} low={fi['day_low']:.2f}")
    hist = t.history(period="10y")
    print(f"  history rows: {len(hist)}  range: {hist.index[0].date()} -> {hist.index[-1].date()}")
