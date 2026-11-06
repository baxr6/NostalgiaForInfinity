# Offline markets for backtests: when FT_MARKETS_FILE is set, ccxt binance loads its markets from that file instead of the API.
import json, os
if os.environ.get("FT_MARKETS_FILE"):
  import ccxt, ccxt.async_support as ccxt_async
  _M = json.load(open(os.environ["FT_MARKETS_FILE"]))
  def _load(self, reload=False, params={}):
    return self.set_markets(_M["markets"], _M["currencies"])
  async def _aload(self, reload=False, params={}):
    return self.set_markets(_M["markets"], _M["currencies"])
  ccxt.binance.load_markets = _load
  ccxt_async.binance.load_markets = _aload
  # leverage tiers for the pairs rebuilt in the market list (gone from Binance and from freqtrade's tier file): copy a similar pair
  import freqtrade.exchange.binance as _fb
  _TPL = {"EOS/USDT:USDT": "XLM/USDT:USDT", "SXP/USDT:USDT": "ZIL/USDT:USDT", "AERGO/USDT:USDT": "ZIL/USDT:USDT"}
  _orig_tiers = _fb.Binance.load_leverage_tiers
  def _tiers(self):
    t = _orig_tiers(self)
    for p, src in _TPL.items():
      if p not in t and src in t:
        t[p] = [dict(x, symbol=p) if "symbol" in x else dict(x) for x in t[src]]
    return t
  _fb.Binance.load_leverage_tiers = _tiers
