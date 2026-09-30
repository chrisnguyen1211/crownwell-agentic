"""Kraken xStocks (asset class tokenized_asset). OHLC rows: [time, o, h, l, c, vwap, volume, count].
Kraken only serves the 720 most recent candles per interval, whatever `since` says."""
from .base import HTTP, Adapter, SourceUnavailable, frame, sec

BASE = "https://api.kraken.com/0/public"
IV = {"5m": 5, "15m": 15, "1h": 60, "4h": 240}


class Kraken(Adapter):
    name = "kraken"
    kind = "cex_spot"
    intervals = ("5m", "15m", "1h", "4h")
    max_bars_back = {"5m": 720, "15m": 720, "1h": 720, "4h": 720}

    def list_markets(self):
        d = HTTP.get(f"{BASE}/AssetPairs", params={"aclass_base": "tokenized_asset"})
        if d.get("error"):
            raise SourceUnavailable(f"kraken AssetPairs: {d['error']}")
        out = []
        for key, p in d["result"].items():
            quote = p.get("quote", "")
            quote = {"ZUSD": "USD", "USD": "USD"}.get(quote, quote)
            out.append({"symbol": p.get("altname", key), "base": p.get("base", ""), "quote": quote,
                        "name": p.get("wsname", ""), "status": p.get("status", ""),
                        "aclass": "tokenized_asset"})
        return out

    def fetch(self, symbol, start, end, interval="5m"):
        d = HTTP.get(f"{BASE}/OHLC", params={"pair": symbol, "interval": IV[interval], "since": sec(start),
                                            "asset_class": "tokenized_asset"})
        if d.get("error"):
            raise SourceUnavailable(f"kraken OHLC {symbol}: {d['error']}")
        rows = next((v for k, v in d["result"].items() if k != "last"), [])
        df = frame(rows, {"ts": 0, "open": 1, "high": 2, "low": 3, "close": 4, "volume": 6}, "s", start, end)
        # vwap * volume is the traded quote amount
        vw = frame(rows, {"ts": 0, "open": 5, "high": 5, "low": 5, "close": 5, "volume": 6}, "s", start, end)
        df["volume_quote"] = vw["close"] * vw["volume"]
        return df
