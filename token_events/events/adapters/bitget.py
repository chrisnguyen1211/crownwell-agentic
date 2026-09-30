"""Bitget spot v2. Candles: [ts(ms), open, high, low, close, baseVol, usdtVol, quoteVol]."""
from .base import HTTP, Adapter, frame, ms, windows

BASE = "https://api.bitget.com"
GRAN = {"5m": "5min", "15m": "15min", "1h": "1h"}


class Bitget(Adapter):
    name = "bitget"
    kind = "cex_spot"
    intervals = ("5m", "15m", "1h")

    def list_markets(self):
        d = HTTP.get(f"{BASE}/api/v2/spot/public/symbols")["data"]
        return [{"symbol": s["symbol"], "base": s["baseCoin"], "quote": s["quoteCoin"], "name": "",
                 "status": s.get("status", "")} for s in d]

    def fetch(self, symbol, start, end, interval="5m"):
        rows = []
        for a, b in windows(start, end, interval, 200):
            params = {"symbol": symbol, "granularity": GRAN[interval], "startTime": ms(a), "endTime": ms(b),
                      "limit": 1000}
            d = HTTP.get(f"{BASE}/api/v2/spot/market/candles", params=params).get("data") or []
            if not d:  # older than the recent-candles retention -> history endpoint (paged by endTime)
                d = HTTP.get(f"{BASE}/api/v2/spot/market/history-candles", params={
                    "symbol": symbol, "granularity": GRAN[interval], "endTime": ms(b), "limit": 200}).get("data") or []
            rows += d
        return frame(rows, {"ts": 0, "open": 1, "high": 2, "low": 3, "close": 4, "volume": 5, "volume_quote": 7},
                     "ms", start, end)
