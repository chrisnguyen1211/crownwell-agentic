"""Binance spot (bStocks / any stock token found in exchangeInfo) and USD-M futures
(stock perps: last-price, index-price and mark-price klines + funding history)."""
import pandas as pd

from .base import HTTP, Adapter, frame, ms, windows

SPOT = "https://api.binance.com"
FUT = "https://fapi.binance.com"
KLINE_MAP = {"ts": 0, "open": 1, "high": 2, "low": 3, "close": 4, "volume": 5, "volume_quote": 7}


class BinanceSpot(Adapter):
    name = "binance"
    kind = "cex_spot"
    intervals = ("5m", "15m", "1h")

    def list_markets(self):
        d = HTTP.get(f"{SPOT}/api/v3/exchangeInfo")["symbols"]
        return [{"symbol": s["symbol"], "base": s["baseAsset"], "quote": s["quoteAsset"], "name": "",
                 "status": s.get("status", "")} for s in d]

    def fetch(self, symbol, start, end, interval="5m"):
        rows = []
        for a, b in windows(start, end, interval, 1000):
            rows += HTTP.get(f"{SPOT}/api/v3/klines", params={
                "symbol": symbol, "interval": interval, "startTime": ms(a), "endTime": ms(b) - 1, "limit": 1000})
        return frame(rows, KLINE_MAP, "ms", start, end)


class BinancePerp(Adapter):
    name = "binance_fut"
    kind = "perp"
    intervals = ("5m", "15m", "1h")
    endpoint, key = "/fapi/v1/klines", "symbol"

    def list_markets(self):
        d = HTTP.get(f"{FUT}/fapi/v1/exchangeInfo")["symbols"]
        return [{"symbol": s["symbol"], "base": s["baseAsset"], "quote": s["quoteAsset"],
                 "name": f"{s.get('underlyingType', '')} {' '.join(s.get('underlyingSubType') or [])}".strip(),
                 "status": s.get("status", ""), "contractType": s.get("contractType", "")} for s in d]

    def fetch(self, symbol, start, end, interval="5m"):
        rows = []
        for a, b in windows(start, end, interval, 1000):
            rows += HTTP.get(f"{FUT}{self.endpoint}", params={
                self.key: symbol, "interval": interval, "startTime": ms(a), "endTime": ms(b) - 1, "limit": 1500})
        df = frame(rows, KLINE_MAP, "ms", start, end)
        if self.kind != "perp":  # index/mark klines carry no volume; not tradeable prints
            df["volume"] = float("nan")
            df["volume_quote"] = float("nan")
        return df

    def funding(self, symbol, start, end) -> pd.DataFrame:
        d = HTTP.get(f"{FUT}/fapi/v1/fundingRate", params={"symbol": symbol, "startTime": ms(start),
                                                          "endTime": ms(end), "limit": 1000})
        df = pd.DataFrame(d)
        if df.empty:
            return pd.DataFrame(columns=["ts", "funding_rate", "mark_price"])
        df["ts"] = pd.to_datetime(df["fundingTime"], unit="ms", utc=True)
        df["funding_rate"] = pd.to_numeric(df["fundingRate"])
        df["mark_price"] = pd.to_numeric(df.get("markPrice"), errors="coerce")
        return df[["ts", "funding_rate", "mark_price"]]


class BinancePerpIndex(BinancePerp):
    name = "binance_fut_index"
    kind = "perp_index"
    endpoint, key = "/fapi/v1/indexPriceKlines", "pair"


class BinancePerpMark(BinancePerp):
    name = "binance_fut_mark"
    kind = "perp_mark"
    endpoint, key = "/fapi/v1/markPriceKlines", "symbol"
