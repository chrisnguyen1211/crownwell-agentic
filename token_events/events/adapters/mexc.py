"""MEXC spot v3 (Binance-compatible klines: [openTime, o, h, l, c, vol, closeTime, quoteVol])."""
from .base import HTTP, Adapter, frame, ms, windows

BASE = "https://api.mexc.com"
IV = {"5m": "5m", "15m": "15m", "1h": "60m"}


class Mexc(Adapter):
    name = "mexc"
    kind = "cex_spot"
    intervals = ("5m", "15m", "1h")

    def list_markets(self):
        d = HTTP.get(f"{BASE}/api/v3/exchangeInfo")["symbols"]
        return [{"symbol": s["symbol"], "base": s["baseAsset"], "quote": s["quoteAsset"],
                 "name": s.get("fullName") or "", "status": str(s.get("status", ""))} for s in d]

    def fetch(self, symbol, start, end, interval="5m"):
        rows = []
        for a, b in windows(start, end, interval, 500):
            rows += HTTP.get(f"{BASE}/api/v3/klines", params={
                "symbol": symbol, "interval": IV[interval], "startTime": ms(a), "endTime": ms(b), "limit": 1000})
        return frame(rows, {"ts": 0, "open": 1, "high": 2, "low": 3, "close": 4, "volume": 5, "volume_quote": 7},
                     "ms", start, end)
