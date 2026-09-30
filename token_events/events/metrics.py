"""Step 4: pure metric functions (unit-tested in tests/test_metrics.py).

Price convention: panels are indexed by 5m bar OPEN time (UTC). "Price at time t" is the last traded
close of a bar that has fully ended by t, i.e. of the bar opened at or before t - 5 min."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .timeutil import BAR


def price_at(price: pd.Series, t) -> float:
    s = price.loc[: pd.Timestamp(t) - BAR].dropna()
    return float(s.iloc[-1]) if len(s) else np.nan


def captured(p, c0: float, o1: float):
    """Share of the official gap already priced in: (P - C0) / (O1 - C0)."""
    if o1 == c0 or not np.isfinite(o1 - c0):
        return np.nan if np.isscalar(p) else p * np.nan
    return (p - c0) / (o1 - c0)


def first_hold_time(cap: pd.Series, thr: float, hold: pd.Timedelta) -> pd.Timestamp | None:
    """First bar-end time at which captured >= thr and stays so for at least `hold`.

    cap is indexed by bar open; the value of bar b is known at b + 5m."""
    cap = cap.dropna()
    if cap.empty:
        return None
    ok = cap >= thr
    idx = cap.index
    n_hold = max(int(hold / BAR), 0)
    for i in np.flatnonzero(ok.to_numpy()):
        t0 = idx[i]
        seg = cap.loc[t0: t0 + hold]
        if len(seg) >= n_hold + 1 and (seg >= thr).all():
            return t0 + BAR
    return None


def overshoot_wrongway(price: pd.Series, c0: float, o1: float) -> tuple[float, float]:
    """max_overshoot: furthest move beyond O1 in the gap direction (as % of O1).
    max_wrong_way: furthest move against the gap direction from C0 (as % of C0). Both >= 0."""
    p = price.dropna()
    if p.empty or o1 == c0:
        return np.nan, np.nan
    sgn = np.sign(o1 - c0)
    over = max(float((sgn * (p / o1 - 1)).max()), 0.0)
    wrong = max(float((-sgn * (p / c0 - 1)).max()), 0.0)
    return over, wrong


def cross_section(prices: pd.DataFrame, traded: pd.DataFrame) -> pd.DataFrame:
    """Per bar: median price, dispersion, richest/cheapest source, number of live sources.

    Only sources that actually traded in the bar (volume > 0) enter the cross-section."""
    live = prices.where(traded.reindex_like(prices).fillna(False).astype(bool))
    n = live.notna().sum(axis=1)
    med = live.median(axis=1)
    mx, mn = live.max(axis=1), live.min(axis=1)
    disp = ((mx - mn) / med).where(n >= 2)
    cols = np.asarray(live.columns, dtype=object)
    v = live.to_numpy(dtype=float)
    ok = (n >= 2).to_numpy()
    rich = np.full(len(live), None, dtype=object)
    cheap = np.full(len(live), None, dtype=object)
    if ok.any():
        rich[ok] = cols[np.nanargmax(v[ok], axis=1)]
        cheap[ok] = cols[np.nanargmin(v[ok], axis=1)]
    rich, cheap = pd.Series(rich, index=live.index), pd.Series(cheap, index=live.index)
    return pd.DataFrame({"median_price": med.where(n >= 1), "dispersion": disp, "rich": rich, "cheap": cheap,
                         "n_live": n})


def premiums(prices: pd.DataFrame, traded: pd.DataFrame, median_price: pd.Series) -> pd.DataFrame:
    live = prices.where(traded.reindex_like(prices).fillna(False).astype(bool))
    return live.div(median_price, axis=0) - 1


def arb_windows(xs: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Contiguous runs of bars where dispersion (live sources only) exceeds threshold."""
    cols = ["start", "end", "duration_min", "bars", "max_dispersion", "peak_at", "rich_at_peak",
            "cheap_at_peak", "main_pair"]
    d = xs["dispersion"]
    above = (d > threshold).fillna(False).to_numpy()
    if not above.any():
        return pd.DataFrame(columns=cols)
    runs, i, n = [], 0, len(above)
    idx = xs.index
    while i < n:
        if not above[i]:
            i += 1
            continue
        j = i
        # contiguous in time: consecutive grid bars
        while j + 1 < n and above[j + 1] and idx[j + 1] - idx[j] == BAR:
            j += 1
        seg = xs.iloc[i: j + 1]
        pk = seg["dispersion"].idxmax()
        pairs = (seg["rich"].astype(str) + " > " + seg["cheap"].astype(str)).value_counts()
        runs.append({"start": idx[i], "end": idx[j] + BAR, "duration_min": (j - i + 1) * 5, "bars": j - i + 1,
                     "max_dispersion": float(seg["dispersion"].max()), "peak_at": pk,
                     "rich_at_peak": seg.at[pk, "rich"], "cheap_at_peak": seg.at[pk, "cheap"],
                     "main_pair": pairs.index[0]})
        i = j + 1
    return pd.DataFrame(runs, columns=cols)


def lead_lag(ra: pd.Series, rb: pd.Series, max_lag: int = 6) -> dict:
    """corr(ra[t], rb[t+lag]) for lag in [-max_lag, max_lag]. best_lag (highest correlation) > 0 means
    A's moves show up in B `best_lag` bars later, i.e. A leads B."""
    out = {}
    for lag in range(-max_lag, max_lag + 1):
        x = pd.concat([ra, rb.shift(-lag)], axis=1).dropna()
        out[lag] = float(x.iloc[:, 0].corr(x.iloc[:, 1])) if len(x) > 5 and x.std().min() > 0 else np.nan
    s = pd.Series(out)
    best = int(s.idxmax()) if s.notna().any() else 0
    return {"corr": out, "best_lag": best, "best_corr": out.get(best, np.nan), "corr0": out.get(0, np.nan)}
