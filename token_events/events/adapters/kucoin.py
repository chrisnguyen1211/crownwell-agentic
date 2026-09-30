"""KuCoin spot. candles rows: [time(sec), open, close, high, low, volume, turnover], newest first."""
from .base import HTTP, Adapter, frame, sec, windows

BASE = "https://api.kucoin.com"
IV = {"5m": "5min", "15m": "15min", "1h": "1hour"}


class Kucoin(Adapter):
    name = "kucoin"
    kind = "cex_spot"
    intervals = ("5m", "15m", "1h")

    def list_markets(self):
        d = HTTP.get(f"{BASE}/api/v2/symbols")["data"]
        return [{"symbol": s["symbol"], "base": s["baseCurrency"], "quote": s["quoteCurrency"],
                 "name": s.get("name", ""), "status": "trading" if s.get("enableTrading") else "halt"} for s in d]

    def fetch(self, symbol, start, end, interval="5m"):
        rows = []
        for a, b in windows(start, end, interval, 1400):
            rows += HTTP.get(f"{BASE}/api/v1/market/candles", params={
                "type": IV[interval], "symbol": symbol, "startAt": sec(a), "endAt": sec(b)}).get("data") or []
        return frame(rows, {"ts": 0, "open": 1, "close": 2, "high": 3, "low": 4, "volume": 5, "volume_quote": 6},
                     "s", start, end)
