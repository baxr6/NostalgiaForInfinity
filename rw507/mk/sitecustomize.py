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
