"""OKX spot. history-candles rows: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm], newest first.
`after` returns records strictly older than the given ts, so we page backwards from `end`."""
import pandas as pd

from .base import HTTP, Adapter, frame, ms

BASE = "https://www.okx.com"
BAR = {"5m": "5m", "15m": "15m", "1h": "1H"}


class Okx(Adapter):
    name = "okx"
    kind = "cex_spot"
    intervals = ("5m", "15m", "1h")

    def list_markets(self):
        d = HTTP.get(f"{BASE}/api/v5/public/instruments", params={"instType": "SPOT"})["data"]
        return [{"symbol": s["instId"], "base": s["baseCcy"], "quote": s["quoteCcy"], "name": "",
                 "status": s.get("state", "")} for s in d]

    def fetch(self, symbol, start, end, interval="5m"):
        rows, cursor, stop = [], ms(end), ms(start)
        for _ in range(200):
            d = HTTP.get(f"{BASE}/api/v5/market/history-candles", params={
                "instId": symbol, "bar": BAR[interval], "after": cursor, "limit": 100}).get("data") or []
            if not d:
                break
            rows += d
            cursor = int(d[-1][0])
            if cursor <= stop:
                break
        return frame(rows, {"ts": 0, "open": 1, "high": 2, "low": 3, "close": 4, "volume": 5, "volume_quote": 7},
                     "ms", pd.Timestamp(start), pd.Timestamp(end))
