"""Common adapter interface.

Every adapter implements
    fetch(symbol, start, end, interval) -> DataFrame[ts, open, high, low, close, volume, volume_quote]
with `ts` = bar OPEN time (tz-aware UTC), `volume` in base units and `volume_quote` in the
quote currency (NaN when the venue does not report it). Discovery-capable adapters also
implement list_markets() -> list[dict(symbol, base, quote, name, status)].
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from ..http import HTTP, SourceUnavailable  # noqa: F401  (re-exported for adapters)

COLS = ["ts", "open", "high", "low", "close", "volume", "volume_quote"]
INTERVAL_MIN = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}


def empty() -> pd.DataFrame:
    df = pd.DataFrame({c: pd.Series(dtype="float64") for c in COLS})
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def frame(rows: Iterable, mapping: dict[str, int], ts_unit: str, start, end) -> pd.DataFrame:
    """Build a normalized frame from row arrays. mapping: column -> index in the row."""
    rows = list(rows)
    if not rows:
        return empty()
    data = {}
    for col, i in mapping.items():
        data[col] = [r[i] for r in rows]
    df = pd.DataFrame(data)
    df["ts"] = pd.to_datetime(pd.to_numeric(df["ts"]), unit=ts_unit, utc=True)
    for c in COLS[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce") if c in df else float("nan")
    return clip(df, start, end)


def clip(df: pd.DataFrame, start, end) -> pd.DataFrame:
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    df = df[(df["ts"] >= start) & (df["ts"] < end)]
    df = df.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)
    return df[COLS]


def windows(start, end, interval: str, limit: int):
    """Split [start, end) into chunks of at most `limit` bars."""
    step = pd.Timedelta(minutes=INTERVAL_MIN[interval] * limit)
    t = pd.Timestamp(start)
    end = pd.Timestamp(end)
    while t < end:
        yield t, min(t + step, end)
        t += step


def ms(ts) -> int:
    return int(pd.Timestamp(ts).timestamp() * 1000)


def sec(ts) -> int:
    return int(pd.Timestamp(ts).timestamp())


class Adapter:
    name = "base"
    kind = "cex_spot"          # cex_spot | dex | perp | perp_index | perp_mark | ref | stock
    intervals = ("5m",)        # supported, finest first
    max_bars_back: dict[str, int] = {}   # history depth limits counted back from "now"

    def fetch(self, symbol: str, start, end, interval: str = "5m") -> pd.DataFrame:
        raise NotImplementedError

    def list_markets(self) -> list[dict]:
        return []

    def best_interval(self, start, now=None) -> str | None:
        """Finest supported interval whose history limit still reaches `start`."""
        now = pd.Timestamp.now(tz="UTC") if now is None else now
        for iv in self.intervals:
            lim = self.max_bars_back.get(iv)
            if lim is None or now - pd.Timedelta(minutes=INTERVAL_MIN[iv] * lim) <= pd.Timestamp(start):
                return iv
        return None
