"""Gate.io spot. Candles: [t(sec), quote_vol, close, high, low, open, base_vol, closed]."""
from .base import HTTP, Adapter, frame, sec, windows

BASE = "https://api.gateio.ws/api/v4"


class Gate(Adapter):
    name = "gate"
    kind = "cex_spot"
    intervals = ("5m", "15m", "1h")
    max_bars_back = {"5m": 10000}  # Gate rejects points older than ~10k bars back

    def list_markets(self):
        out = []
        for p in HTTP.get(f"{BASE}/spot/currency_pairs"):
            out.append({"symbol": p["id"], "base": p.get("base", ""), "quote": p.get("quote", ""),
                        "name": p.get("base_name") or "", "status": p.get("trade_status", "")})
        return out

    def fetch(self, symbol, start, end, interval="5m"):
        rows = []
        for a, b in windows(start, end, interval, 900):
            rows += HTTP.get(f"{BASE}/spot/candlesticks", params={
                "currency_pair": symbol, "interval": interval, "from": sec(a), "to": sec(b)})
        return frame(rows, {"ts": 0, "volume_quote": 1, "close": 2, "high": 3, "low": 4, "open": 5, "volume": 6},
                     "s", start, end)
