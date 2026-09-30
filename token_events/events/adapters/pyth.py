"""Pyth Benchmarks (TradingView shim). Equity feeds are split by session:
  Equity.US.NVDA/USD        regular hours
  Equity.US.NVDA/USD.PRE    pre-market
  Equity.US.NVDA/USD.POST   post-market
  Equity.US.NVDA/USD.ON     overnight (Blue Ocean ATS)
fetch() takes a "|"-joined list of variants and stitches them by US session. Also used for
Crypto.USDT/USD and Crypto.USDC/USD (FX conversion)."""
import pandas as pd

from ..timeutil import us_session_label
from .base import HTTP, Adapter, SourceUnavailable, clip, empty, sec, windows

BASE = "https://benchmarks.pyth.network/v1/shims/tradingview"
RES = {"5m": "5", "15m": "15", "1h": "60"}
SESSION_OF = {"": "regular", ".PRE": "pre", ".POST": "post", ".ON": "closed"}


def variants(ticker: str) -> list[str]:
    root = f"Equity.US.{ticker}/USD"
    return [root + suf for suf in SESSION_OF]


class Pyth(Adapter):
    name = "pyth"
    kind = "ref"
    intervals = ("5m", "15m", "1h")

    def exists(self, symbol: str) -> bool:
        try:
            d = HTTP.get(f"{BASE}/symbols", params={"symbol": symbol})
            return bool(d) and not d.get("s") == "error"
        except SourceUnavailable as e:
            if "404" in str(e):
                return False
            raise

    def _one(self, symbol, start, end, interval):
        parts = []
        for a, b in windows(start, end, interval, 288):
            d = HTTP.get(f"{BASE}/history", params={"symbol": symbol, "resolution": RES[interval],
                                                     "from": sec(a), "to": sec(b)})
            if d.get("s") != "ok" or not d.get("t"):
                continue
            parts.append(pd.DataFrame({"ts": pd.to_datetime(d["t"], unit="s", utc=True), "open": d["o"],
                                       "high": d["h"], "low": d["l"], "close": d["c"]}))
        if not parts:
            return empty()
        df = pd.concat(parts)
        df["volume"] = float("nan")          # quotes, not trades
        df["volume_quote"] = float("nan")
        return clip(df, start, end)

    def fetch(self, symbol, start, end, interval="5m"):
        syms = symbol.split("|")
        frames = {}
        for s in syms:
            df = self._one(s, start, end, interval)
            if not df.empty:
                suf = next((x for x in (".PRE", ".POST", ".ON") if s.endswith(x)), "")
                frames[SESSION_OF[suf]] = df.set_index("ts")
        if not frames:
            return empty()
        if len(frames) == 1:
            return next(iter(frames.values())).reset_index()
        idx = sorted(set().union(*[f.index for f in frames.values()]))
        out = []
        for ts in idx:
            pref = frames.get(us_session_label(ts))
            if pref is not None and ts in pref.index:
                out.append(pref.loc[ts])
            else:  # any variant that printed in this bar
                out.append(next(f.loc[ts] for f in frames.values() if ts in f.index))
        df = pd.DataFrame(out)
        df.index.name = "ts"
        return df.reset_index()
