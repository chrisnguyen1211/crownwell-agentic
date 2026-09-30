"""Step 2: crawl 5m candles for every (event, source) into data/raw with caching."""
from __future__ import annotations

import json
import logging
import time

import pandas as pd

from .adapters import ADAPTERS
from .adapters.base import empty
from .http import STATUS, SourceUnavailable
from .model import Event, Source

log = logging.getLogger("events.fetch")


class Cache:
    def __init__(self, paths):
        self.dir = paths.raw
        self.dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.dir / "_manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text()) if self.manifest_path.exists() else {}

    def path(self, ev: Event, src: Source, suffix: str = ""):
        venue = src.venue + (f"-{suffix}" if suffix else "")
        return self.dir / f"{src.ticker}_{src.issuer}_{venue}_{ev.date_tag}.parquet"

    def get(self, p):
        if p.exists():
            return pd.read_parquet(p), self.manifest.get(p.name, {})
        return None, None

    def put(self, p, df: pd.DataFrame, meta: dict):
        df.to_parquet(p, index=False)
        self.manifest[p.name] = meta
        self.manifest_path.write_text(json.dumps(self.manifest, indent=1, default=str))


def fetch_source(cache: Cache, ev: Event, src: Source, refresh: bool = False, start=None, end=None):
    """Returns (df, meta). df is None when the source failed; empty df when the venue had no bars."""
    p = cache.path(ev, src)
    if not refresh:
        df, meta = cache.get(p)
        if df is not None:
            return df, meta
    adapter = ADAPTERS.get(src.adapter)
    if adapter is None:
        STATUS.add(src.id, "fetch", False, f"unknown adapter {src.adapter}")
        return None, {}
    start = start or ev.fetch_start
    end = end or ev.fetch_end
    interval = src.extra.get("interval") or adapter.best_interval(start)
    if interval is None:
        STATUS.add(src.id, "fetch", False,
                   f"{adapter.name}: history limit {adapter.max_bars_back} does not reach {start:%Y-%m-%d}")
        return None, {}
    try:
        df = adapter.fetch(src.symbol, start, end, interval)
    except SourceUnavailable as e:
        STATUS.add(src.id, "fetch", False, str(e)[:160])
        return None, {}
    except Exception as e:  # never stop the pipeline on one bad source
        log.exception("unexpected error on %s", src.id)
        STATUS.add(src.id, "fetch", False, f"{e.__class__.__name__}: {e}"[:160])
        return None, {}
    note = "" if interval == "5m" else f"downgraded to {interval} (history limit)"
    meta = {"source": src.id, "interval": interval, "rows": len(df), "fetched_at": time.time(), "note": note,
            "start": str(start), "end": str(end)}
    cache.put(p, df if len(df) else empty(), meta)
    STATUS.add(src.id, "fetch", len(df) > 0, f"{len(df)} bars @{interval} {note}".strip())
    return df, meta


def fetch_funding(cache: Cache, ev: Event, src: Source, refresh=False):
    if src.adapter != "binance_fut":
        return None
    p = cache.path(ev, src, "funding")
    if p.exists() and not refresh:
        return pd.read_parquet(p)
    try:
        df = ADAPTERS["binance_fut"].funding(src.symbol, ev.fetch_start - pd.Timedelta(hours=8), ev.fetch_end)
    except SourceUnavailable as e:
        STATUS.add(src.id + ":funding", "fetch", False, str(e)[:160])
        return None
    cache.put(p, df, {"source": src.id + ":funding", "rows": len(df)})
    return df


def fx_source(quote: str, fx_cfg: dict) -> Source | None:
    sym = fx_cfg.get(quote)
    if not sym:
        return None
    return Source(ticker="FX", issuer=quote, venue="pyth", kind="ref", adapter="pyth", symbol=sym, quote="USD")


def fetch_event(cache: Cache, ev: Event, sources: list[Source], fx_cfg: dict, refresh=False) -> dict:
    """Fetch every enabled source for one event plus FX series. Returns {source_id: (df, meta)}."""
    out = {}
    quotes = set()
    for src in sources:
        if not src.enabled:
            continue
        df, meta = fetch_source(cache, ev, src, refresh)
        out[src.id] = (df, meta)
        if df is not None and len(df) and src.quote in ("USDT", "USDC"):
            quotes.add(src.quote)
        fetch_funding(cache, ev, src, refresh)
    for q in sorted(quotes):
        fsrc = fx_source(q, fx_cfg)
        if fsrc:
            out[fsrc.id] = fetch_source(cache, ev, fsrc, refresh)
    return out


def load_event_raw(cache: Cache, ev: Event, sources: list[Source], fx_cfg: dict) -> dict:
    """Read whatever is cached (no network)."""
    out = {}
    for src in sources + [s for s in (fx_source(q, fx_cfg) for q in ("USDT", "USDC")) if s]:
        if not src.enabled:
            continue
        df, meta = cache.get(cache.path(ev, src))
        if df is not None:
            out[src.id] = (df, meta or {})
    return out


def run(paths, cfg, events, sources_by_ticker, fx_cfg, refresh=False, only=None):
    cache = Cache(paths)
    for ev in events:
        if only and ev.id not in only and ev.ticker not in only:
            continue
        srcs = sources_by_ticker.get(ev.ticker, [])
        log.info("== %s: %d sources, window %s -> %s", ev.id, len(srcs), ev.fetch_start, ev.fetch_end)
        fetch_event(cache, ev, srcs, fx_cfg, refresh)
