"""Hyperliquid perps incl. HIP-3 builder dexes (e.g. dex "xyz" -> coin "xyz:TSLA").
candleSnapshot only serves the most recent 5000 candles per interval (5m ~ 17 days)."""
from .base import HTTP, Adapter, frame, ms

URL = "https://api.hyperliquid.xyz/info"


class Hyperliquid(Adapter):
    name = "hyperliquid"
    kind = "perp"
    intervals = ("5m", "15m", "1h")
    max_bars_back = {"5m": 5000, "15m": 5000, "1h": 5000}

    def dexes(self) -> list[str]:
        d = HTTP.post(URL, json={"type": "perpDexs"}) or []
        return [x["name"] for x in d if isinstance(x, dict) and x.get("name")]

    def list_markets(self, dex: str = "xyz"):
        d = HTTP.post(URL, json={"type": "meta", "dex": dex})
        return [{"symbol": u["name"], "base": u["name"].split(":")[-1], "quote": "USD", "name": dex,
                 "status": "delisted" if u.get("isDelisted") else "trading"} for u in d.get("universe", [])]

    def fetch(self, symbol, start, end, interval="5m"):
        d = HTTP.post(URL, json={"type": "candleSnapshot", "req": {
            "coin": symbol, "interval": interval, "startTime": ms(start), "endTime": ms(end)}}) or []
        rows = [[c["t"], c["o"], c["h"], c["l"], c["c"], c["v"]] for c in d]
        df = frame(rows, {"ts": 0, "open": 1, "high": 2, "low": 3, "close": 4, "volume": 5}, "ms", start, end)
        df["volume_quote"] = df["volume"] * df["close"]
        return df
