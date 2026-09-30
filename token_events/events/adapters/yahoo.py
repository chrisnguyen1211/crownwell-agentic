"""yfinance: stock 5m incl. extended hours (prepost=True), daily OHLC, earnings dates, market cap.
Yahoo keeps 5m/15m bars for ~60 days and 1h bars for ~730 days."""
import logging

import pandas as pd

from .base import Adapter, SourceUnavailable, clip, empty

log = logging.getLogger("events.yahoo")


def _yf():
    import yfinance as yf

    return yf


class Yahoo(Adapter):
    name = "yahoo"
    kind = "stock"
    intervals = ("5m", "15m", "1h")
    max_bars_back = {"5m": 59 * 288, "15m": 59 * 96}  # ~60 calendar days

    def fetch(self, symbol, start, end, interval="5m"):
        try:
            h = _yf().Ticker(symbol).history(start=pd.Timestamp(start).tz_convert("UTC").tz_localize(None),
                                             end=pd.Timestamp(end).tz_convert("UTC").tz_localize(None),
                                             interval=interval, prepost=True, auto_adjust=False)
        except Exception as e:  # yfinance raises a zoo of exceptions
            raise SourceUnavailable(f"yfinance {symbol}: {e}") from e
        if h is None or h.empty:
            return empty()
        df = pd.DataFrame({"ts": h.index.tz_convert("UTC"), "open": h["Open"].values, "high": h["High"].values,
                           "low": h["Low"].values, "close": h["Close"].values, "volume": h["Volume"].values})
        df["volume_quote"] = df["volume"] * df["close"]
        return clip(df, start, end)


def daily(ticker: str, days: int = 90) -> pd.DataFrame:
    """Official daily OHLC (unadjusted). Index = session date."""
    h = _yf().Ticker(ticker).history(period=f"{days}d", interval="1d", auto_adjust=False)
    if h is None or h.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    h.index = pd.to_datetime(h.index.date)
    return h.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]


def market_cap(ticker: str) -> tuple[float | None, str]:
    t = _yf().Ticker(ticker)
    try:
        mc = t.fast_info.get("marketCap")
        qt = t.fast_info.get("quoteType") or ""
        if mc:
            return float(mc), str(qt)
    except Exception:
        pass
    try:
        info = t.info
        return (float(info["marketCap"]) if info.get("marketCap") else None), str(info.get("quoteType", ""))
    except Exception as e:
        log.warning("market cap %s: %s", ticker, e)
        return None, ""


def earnings_dates(ticker: str, limit: int = 12) -> pd.DatetimeIndex:
    """Earnings timestamps (tz-aware ET). Yahoo sometimes shows 00:00 when the time is unknown."""
    try:
        df = _yf().Ticker(ticker).get_earnings_dates(limit=limit)
    except Exception as e:
        log.warning("earnings dates %s: %s", ticker, e)
        return pd.DatetimeIndex([], tz="America/New_York")
    if df is None or df.empty:
        return pd.DatetimeIndex([], tz="America/New_York")
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is None:
        idx = idx.tz_localize("America/New_York")
    return idx
