"""Bybit v5 spot. kline rows: [startTime, o, h, l, c, volume, turnover], newest first."""
from .base import HTTP, Adapter, frame, ms, windows

BASE = "https://api.bybit.com"
IV = {"5m": "5", "15m": "15", "1h": "60"}


class Bybit(Adapter):
    name = "bybit"
    kind = "cex_spot"
    intervals = ("5m", "15m", "1h")

    def list_markets(self):
        out, cursor = [], ""
        while True:
            r = HTTP.get(f"{BASE}/v5/market/instruments-info", params={"category": "spot", "limit": 1000,
                                                                       "cursor": cursor})["result"]
            out += [{"symbol": s["symbol"], "base": s["baseCoin"], "quote": s["quoteCoin"], "name": "",
                     "status": s.get("status", "")} for s in r["list"]]
            cursor = r.get("nextPageCursor") or ""
            if not cursor:
                return out

    def fetch(self, symbol, start, end, interval="5m"):
        rows = []
        for a, b in windows(start, end, interval, 900):
            r = HTTP.get(f"{BASE}/v5/market/kline", params={
                "category": "spot", "symbol": symbol, "interval": IV[interval], "start": ms(a), "end": ms(b),
                "limit": 1000})
            rows += (r.get("result") or {}).get("list") or []
        return frame(rows, {"ts": 0, "open": 1, "high": 2, "low": 3, "close": 4, "volume": 5, "volume_quote": 6},
                     "ms", start, end)
