# one row per run: arm year slice | 507 all pairs | all tags all pairs | 507 blacklist applied | all tags blacklist applied
# each block: trades real_losers force net market_days liq. Blacklist = pinned v18.0.214 blacklist-binance, removed after the
# run (exact here: <= 27 pairs per slice vs 60 slots and a 100k wallet, so slots never fill and pairs trade independently).
import os, sys, glob, json, re, zipfile, pandas as pd
O, arm, y, s = sys.argv[1:5]
R = os.environ.get("RW", "/freqtrade/scratch_test/rw507")
bl = [re.compile(x) for x in json.loads(re.sub(r"(?m)^\s*//.*$", "", open(f"{R}/cfg/blacklist-binance.json").read()))["exchange"]["pair_blacklist"]]
z = zipfile.ZipFile(sorted(glob.glob(f"{O}/ud/backtest_results/*.zip"))[-1])
n = [x for x in z.namelist() if x.endswith(".json") and "config" not in x and "meta" not in x][0]
t = pd.DataFrame([x for v in json.load(z.open(n))["strategy"].values() for x in v["trades"]])
if t.empty: t = pd.DataFrame(columns=["pair", "enter_tag", "profit_abs", "exit_reason", "trade_duration"])
t.to_pickle(f"{O}/trades.pkl")
def row(d):
  real = ((d.profit_abs <= 0) & (d.exit_reason != "force_exit")).sum()
  return [len(d), int(real), int((d.exit_reason == "force_exit").sum()), round(float(d.profit_abs.sum()), 2),
          round(float(d.trade_duration.sum()) / 1440, 2), int((d.exit_reason == "liquidation").sum())]
is507 = t.enter_tag.astype(str).str.split().apply(lambda x: "507" in x)
keep = ~t.pair.apply(lambda p: any(b.fullmatch(p) for b in bl))
print("\t".join(map(str, [arm, y, s] + row(t[is507]) + row(t) + row(t[is507 & keep]) + row(t[keep]))))
