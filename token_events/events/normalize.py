"""Step 3: put every source on the common 5m grid, convert to USD, calibrate k."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .adapters.base import INTERVAL_MIN
from .timeutil import BAR


def to_grid(df: pd.DataFrame, grid: pd.DatetimeIndex, interval: str = "5m") -> pd.DataFrame:
    """Align candles to the 5m grid (index = bar open, UTC).

    Returns columns: close (last print in the bar, NaN if none), volume, volume_quote, traded (bool),
    price (last traded close carried forward = the price you would have seen at the bar's end).
    A coarser candle (15m/1h) is placed on its LAST 5m slot, since its close is only known then."""
    out = pd.DataFrame(index=grid)
    if df is None or df.empty:
        for c in ("close", "volume", "volume_quote"):
            out[c] = np.nan
        out["traded"] = False
        out["price"] = np.nan
        return out
    d = df.copy()
    shift = pd.Timedelta(minutes=INTERVAL_MIN.get(interval, 5)) - BAR
    d["slot"] = (pd.to_datetime(d["ts"], utc=True) + shift).dt.floor("5min")
    d = d.groupby("slot").agg(close=("close", "last"), volume=("volume", "sum"),
                              volume_quote=("volume_quote", "sum"),
                              has_vol=("volume", lambda v: v.notna().any()))
    d = d.reindex(grid)
    has_vol = d["has_vol"].astype("boolean").fillna(False).astype(bool)
    d.loc[~has_vol, "volume"] = np.nan          # venue does not report volume (quotes/index feeds)
    vol_q = d["volume_quote"].where(has_vol)
    out["close"] = d["close"].astype(float)
    out["volume"] = d["volume"].astype(float)
    out["volume_quote"] = vol_q.astype(float)
    # quotes without volume (Pyth, index/mark) count as observations; trades need volume > 0
    out["traded"] = np.where(has_vol, out["volume"].fillna(0) > 0, out["close"].notna())
    out["price"] = out["close"].where(out["traded"]).ffill()
    return out


def fx_rate_on_grid(fx_df: pd.DataFrame | None, grid, interval="5m") -> pd.Series | None:
    if fx_df is None or fx_df.empty:
        return None
    g = to_grid(fx_df, grid, interval)
    r = g["price"].ffill().bfill()
    return r if r.notna().any() else None


def convert_usd(g: pd.DataFrame, rate: pd.Series | None, threshold_bps: float) -> tuple[pd.DataFrame, str]:
    """Quote(USDT/USDC) -> USD when the peg deviates by more than threshold within the window."""
    if rate is None:
        return g, "no FX series: quote assumed = 1 USD"
    dev_bps = float((rate - 1).abs().max() * 1e4)
    if dev_bps <= threshold_bps:
        return g, f"peg max deviation {dev_bps:.1f} bps <= {threshold_bps} bps: not converted"
    g = g.copy()
    for c in ("close", "price"):
        g[c] = g[c] * rate
    g["volume_quote"] = g["volume_quote"] * rate
    return g, f"converted with 5m FX (max deviation {dev_bps:.1f} bps)"


def calibrate_k(p_token: pd.Series, traded: pd.Series, p_stock: pd.Series, start, end) -> dict:
    """k = median(P_token / P_stock) over the regular session [start, end), token bars with volume > 0 only."""
    m = (p_token.index >= start) & (p_token.index < end)
    t = p_token[m & traded.reindex(p_token.index).fillna(False).to_numpy()]
    s = p_stock.reindex(t.index)
    ratio = (t / s).replace([np.inf, -np.inf], np.nan).dropna()
    if ratio.empty:
        return {"k": np.nan, "k_std": np.nan, "k_n": 0}
    return {"k": float(ratio.median()), "k_std": float(ratio.std(ddof=0)), "k_n": int(len(ratio))}
