"""Synthetic end-to-end fixture: one fake AMC event with several issuers/venues, written as if fetched.
Lets you check analyze/report/excel without network. Ticker is 'DEMO' so it can't be mistaken for data."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import timeutil as tu
from .config import dump_yaml
from .fetch import Cache, fx_source
from .model import Event, Source


def _path(ev: Event, true_px: pd.Series, lag_bars: int, noise: float, k: float, p_trade: float, rng,
          basis: float = 0.0, hours=None, vol_scale=5_000.0) -> pd.DataFrame:
    """Token follows the fair value with a lag, noise, a multiplier k and sparse trading."""
    px = true_px.shift(lag_bars).bfill() * (1 + basis) * k
    px = px * np.exp(rng.normal(0, noise, len(px)))
    trade = rng.random(len(px)) < p_trade
    if hours is not None:
        trade &= hours(px.index)
    vol = np.where(trade, rng.gamma(2.0, vol_scale / 2, len(px)) / px.values, 0.0)
    close = px.values
    return pd.DataFrame({"ts": px.index, "open": close, "high": close * 1.001, "low": close * 0.999,
                         "close": close, "volume": vol, "volume_quote": vol * close})


def build(paths):
    paths.ensure()
    rng = np.random.default_rng(7)
    d0, d1 = "2026-09-10", "2026-09-11"
    ev = Event(ticker="DEMO", event_type="earnings_amc", t_event_utc=str(tu.et_clock_on(d0, 16, 5)),
               prev_session=d0, next_session=d1, c0=100.0, o1=107.5, cap_group="large", market_cap=5e11,
               note="SYNTHETIC DEMO DATA - not a real event")
    idx = tu.grid(ev.fetch_start, ev.fetch_end)
    # fair value: random walk ending at C0=100 at the event, then a jump that drifts to O1=107.5 by the open
    fv = pd.Series(np.nan, index=idx)
    pre, night, day = idx < ev.t_evt, (idx >= ev.t_evt) & (idx < ev.open1), idx >= ev.open1
    walk = np.cumsum(rng.normal(0, 0.0008, pre.sum()))
    fv[pre] = 100 * np.exp(walk - walk[-1])
    m = night.sum()
    path = np.interp(np.arange(m), [0, 6, m - 1], [100, 104, 107.5])
    bridge = np.cumsum(rng.normal(0, 0.0012, m))
    bridge -= np.linspace(0, 1, m) * bridge[-1]          # Brownian bridge: pinned to 0 at both ends
    fv[night] = path * np.exp(bridge)
    fv[day] = 107.5 * np.exp(np.cumsum(rng.normal(0, 0.001, day.sum())))

    ext = lambda ix: np.array([tu.us_session_label(t) in ("regular", "pre", "post") for t in ix])  # noqa: E731
    specs = [
        (Source("DEMO", "stock", "yahoo", "stock", "yahoo", "DEMO"), dict(lag_bars=0, noise=0.0004, k=1, p_trade=1,
                                                                          hours=ext, vol_scale=2e6)),
        (Source("DEMO", "pyth", "pyth", "ref", "pyth", "Equity.US.DEMO/USD"), dict(lag_bars=0, noise=0.0003, k=1,
                                                                                    p_trade=1)),
        (Source("DEMO", "ondo", "gate", "cex_spot", "gate", "DEMOON_USDT", "USDT"),
         dict(lag_bars=2, noise=0.0015, k=1.0, p_trade=0.8, vol_scale=20_000)),
        (Source("DEMO", "ondo", "eth_uniswapv3", "dex", "geckoterminal", "eth:0xdemo"),
         dict(lag_bars=9, noise=0.002, k=1.0, p_trade=0.15, vol_scale=3_000)),
        (Source("DEMO", "xstocks", "kraken", "cex_spot", "kraken", "DEMOxUSD"),
         dict(lag_bars=1, noise=0.001, k=1.0031, p_trade=0.9, vol_scale=40_000)),
        (Source("DEMO", "xstocks", "bybit", "cex_spot", "bybit", "DEMOXUSDT", "USDT"),
         dict(lag_bars=3, noise=0.0015, k=1.0031, p_trade=0.7, vol_scale=15_000, basis=0.002)),
        (Source("DEMO", "xstocks", "solana_raydium", "dex", "geckoterminal", "solana:Demo111"),
         dict(lag_bars=14, noise=0.002, k=1.0031, p_trade=0.3, vol_scale=4_000, basis=-0.004)),
        (Source("DEMO", "perp", "hl_xyz", "perp", "hyperliquid", "xyz:DEMO"),
         dict(lag_bars=0, noise=0.0008, k=1.0, p_trade=0.95, vol_scale=80_000)),
    ]
    cache = Cache(paths)
    for src, kw in specs:
        df = _path(ev, fv, rng=rng, **kw)
        if src.kind == "ref":
            df["volume"] = np.nan
            df["volume_quote"] = np.nan
        cache.put(cache.path(ev, src), df, {"source": src.id, "interval": "5m", "rows": len(df), "synthetic": True})
    fx = fx_source("USDT", {"USDT": "Crypto.USDT/USD"})
    fx_df = pd.DataFrame({"ts": idx, "open": 1.0003, "high": 1.0003, "low": 1.0003, "close": 1.0003,
                          "volume": np.nan, "volume_quote": np.nan})
    cache.put(cache.path(ev, fx), fx_df, {"source": fx.id, "interval": "5m", "synthetic": True})

    dump_yaml({"events": [ev.to_dict()]}, paths.events, header="SYNTHETIC demo event")
    dump_yaml({"fx": {"USDT": "Crypto.USDT/USD", "USDC": "Crypto.USDC/USD"},
               "tickers": {"DEMO": [{k: v for k, v in s.to_dict().items() if k != "ticker"} for s, _ in specs]}},
              paths.sources, header="SYNTHETIC demo sources")
