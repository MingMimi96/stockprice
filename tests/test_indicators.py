"""Stage 2 check: print SPY headline indicators and drawdown episodes."""
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from src import data, indicators as ind

t = time.time(); hist = data.get_history("SPY"); print(f"history load {time.time()-t:.2f}s rows={len(hist)}")
t = time.time(); hist = data.get_history("SPY"); print(f"cached load  {time.time()-t:.2f}s")
q = data.get_quote("SPY")
snap = ind.snapshot(data.merge_live_price(hist, q))
for k, v in snap.items():
    print(f"{k:20s} {v:.2f}" if isinstance(v, float) else f"{k:20s} {v}")
print("\nCrosses (last 5):\n", ind.cross_events(ind.add_moving_averages(hist)).tail())
print("\n>10% drawdowns:\n", ind.drawdown_events(hist["Close"], 10).to_string())
print("market open now:", data.is_market_open())
