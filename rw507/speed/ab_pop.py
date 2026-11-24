# Paired CPU timing of NFIX8 populate_indicators: all variants in ONE process, shuffled order per (rep, pair), so load hits all alike.
# python ab_pop.py OUTDIR DATADIR REPS CFG[,CFG..] up=DIR name=DIR ...   (first variant = reference)
# Live-sized frames (5m 1500 rows, informatives 1000), signals as in each file (defaults = off).
from pathlib import Path
import sys, time, json, logging, random, glob, os, numpy as np, pandas as pd
logging.disable(logging.WARNING)
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode, CandleType
from freqtrade.resolvers import StrategyResolver
from freqtrade.data.dataprovider import DataProvider
from freqtrade.data.history import load_pair_history
out, datadir, reps, cfgs = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4].split(",")
V = [a.split("=", 1) for a in sys.argv[5:]]
TFS = {"5m": 1500, "15m": 1000, "1h": 1000, "4h": 1000, "1d": 1000}
want = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK", "LTC", "AVAX", "DOT"]
full = lambda c: all(os.path.exists(f"{datadir}/futures/{c}_USDT_USDT-{tf}-futures.feather") for tf in TFS)
have = sorted(os.path.basename(f).split("_USDT")[0] for f in glob.glob(f"{datadir}/futures/*_USDT_USDT-5m-futures.feather"))
pairs = [f"{c}/USDT:USDT" for c in want + have if full(c)]
pairs = list(dict.fromkeys(pairs))[:6]  # majors first, then any other coin with all timeframes
cache = {}
for p in pairs:
  for tf, n in TFS.items():
    cache[(p, tf)] = load_pair_history(pair=p, timeframe=tf, datadir=datadir, candle_type=CandleType.FUTURES).tail(n).reset_index(drop=True)
class DP(DataProvider):
  def get_pair_dataframe(self, pair, timeframe=None, candle_type=""): return cache[(pair, timeframe or "5m")].copy()
  def current_whitelist(self): return pairs
S = {}
for name, d in V:
  os.makedirs(Path(out) / "ud" / name, exist_ok=True)
  cfg = Configuration.from_files(cfgs)
  cfg.update(strategy="NostalgiaForInfinityX8", strategy_path=d, runmode=RunMode.BACKTEST, datadir=datadir, timeframe="5m",
             user_data_dir=Path(out) / "ud" / name)
  st = StrategyResolver.load_strategy(cfg); dp = DP(cfg, None); dp._set_dataframe_max_index = lambda *a, **k: None
  st.dp = dp; st.ft_bot_start(); S[name] = st
  print(name, d, "btc_info_timeframes", st.btc_info_timeframes, flush=True)
print("pairs", pairs, "rows", {tf: len(cache[(pairs[0], tf)]) for tf in TFS}, flush=True)
rng = random.Random(7); rows = []
for rep in range(reps + 1):
  for p in pairs:
    order = list(S); rng.shuffle(order)
    for name in order:
      df = cache[(p, "5m")].copy(); c0, w0 = time.process_time(), time.perf_counter()
      S[name].populate_indicators(df, {"pair": p})
      if rep: rows.append((rep, p, name, (time.process_time() - c0) * 1000, (time.perf_counter() - w0) * 1000))
d = pd.DataFrame(rows, columns=["rep", "pair", "v", "cpu", "wall"]); d.to_csv(f"{out}/ab_raw.csv", index=False)
ref = V[0][0]; w = d.pivot_table(index=["rep", "pair"], columns="v", values="cpu")
def ci(x):  # median and 95 % bootstrap interval
  b = np.random.default_rng(1).choice(x, (2000, len(x))); m = np.median(b, 1); return np.median(x), np.percentile(m, 2.5), np.percentile(m, 97.5)
lines = [f"paired CPU ms/pair, {len(w)} calls per variant ({reps} reps x {len(pairs)} pairs), reference {ref}"]
lines.append(f"{'variant':<12}{'median ms':>10}{'diff ms':>9}{'95% CI':>18}{'diff %':>8}")
for name, _ in V:
  x = (w[name] - w[ref]).to_numpy(); m, lo, hi = ci(x)
  lines.append(f"{name:<12}{w[name].median():>10.2f}{m:>+9.2f}   [{lo:+6.2f}, {hi:+6.2f}]{m / w[ref].median():>+8.1%}")
for name, _ in V:  # BTC 1h pass = variant minus its no1h twin, same call
  if name + "no1h" in w:
    m, lo, hi = ci((w[name] - w[name + "no1h"]).to_numpy()); lines.append(f"BTC 1h pass in {name}: {m:+.2f} ms [{lo:+.2f}, {hi:+.2f}]")
open(f"{out}/ab_result.txt", "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
