"""Steps 3-4 orchestration: normalize every source of an event and compute all metrics.

Writes data/analysis/<event_id>/{adj,close_adj,traded,volq,xs,prem,prem_pyth}.parquet and
{metrics,arb,k,leadlag}.csv + event.json, consumed by report.py / excel.py."""
from __future__ import annotations

import json
import logging
from itertools import combinations

import numpy as np
import pandas as pd

from . import metrics as M
from . import timeutil as tu
from .fetch import Cache, fx_source, load_event_raw
from .http import STATUS
from .model import OVERLAY_ONLY, TOKEN_KINDS, Event, Source
from .normalize import calibrate_k, convert_usd, fx_rate_on_grid, to_grid

log = logging.getLogger("events.analyze")

CAPTURE_POINTS = [("t+5m", None, 5), ("t+15m", None, 15), ("t+1h", None, 60), ("t+3h", None, 180),
                  ("03:00ET", (3, 0), None), ("07:00ET", (7, 0), None), ("09:25ET", (9, 25), None)]


def _capture_times(ev: Event):
    out = []
    for name, hm, mins in CAPTURE_POINTS:
        if mins is not None:
            out.append((name, ev.t_evt + pd.Timedelta(minutes=mins)))
        else:
            t = tu.et_clock_on(ev.next_session, *hm)
            out.append((name, t if t > ev.t_evt else None))   # e.g. 03:00 ET is before a 07:00 BMO release
    return out


def analyze_event(paths, cfg, ev: Event, sources: list[Source], fx_cfg: dict) -> dict | None:
    cache = Cache(paths)
    raw = load_event_raw(cache, ev, sources, fx_cfg)
    grid = tu.grid(ev.fetch_start, ev.fetch_end)
    rates = {q: fx_rate_on_grid((raw.get(fx_source(q, fx_cfg).id) or (None, None))[0], grid)
             for q in ("USDT", "USDC") if fx_source(q, fx_cfg)}
    warnings, g_by, meta_by = [], {}, {}
    for src in sources:
        if not src.enabled or src.id not in raw:
            continue
        df, meta = raw[src.id]
        if df is None or df.empty:
            continue
        g = to_grid(df, grid, meta.get("interval", "5m"))
        fx_note = ""
        if src.quote in ("USDT", "USDC"):
            g, fx_note = convert_usd(g, rates.get(src.quote), cfg["fx_threshold_bps"])
        g_by[src.id] = g
        meta_by[src.id] = {"interval": meta.get("interval", "5m"), "fx": fx_note, "src": src}
    if not g_by:
        log.warning("%s: no cached data, run fetch first", ev.id)
        return None

    # ---- P_stock for calibration: yfinance regular session, fallback Pyth
    by_kind = {s.id: s for s in sources}
    stock_id = next((i for i in g_by if by_kind[i].kind == "stock"), None)
    pyth_id = next((i for i in g_by if by_kind[i].kind == "ref"), None)
    calib_ref, calib_name = None, ""
    for cand in (stock_id, pyth_id):
        if cand is None:
            continue
        g = g_by[cand]
        m = (g.index >= ev.calib_start) & (g.index < ev.calib_end)
        if g.loc[m, "close"].notna().sum() >= 10:
            calib_ref, calib_name = g["close"], by_kind[cand].label
            break
    if calib_ref is None:
        warnings.append("no 5m stock prices in the calibration session: k set to 1 for all sources")

    k_rows, adj, close_adj, traded, volq = [], {}, {}, {}, {}
    for sid, g in g_by.items():
        src = by_kind[sid]
        if src.kind == "stock":
            kk = {"k": 1.0, "k_std": 0.0, "k_n": 0}
            how = "reference (k=1 by definition)"
        elif calib_ref is None:
            kk, how = {"k": 1.0, "k_std": np.nan, "k_n": 0}, "no calibration data"
        else:
            kk = calibrate_k(g["close"], g["traded"], calib_ref, ev.calib_start, ev.calib_end)
            how = f"median(P/P_stock) vs {calib_name}, session {ev.prev_session}"
            if not np.isfinite(kk["k"]):
                kk = {"k": 1.0, "k_std": np.nan, "k_n": 0}
                how = "no traded bars in calibration session -> k=1"
                warnings.append(f"{src.label}: no traded bars in the {ev.prev_session} session, k defaulted to 1")
        dev = kk["k"] - 1
        flag = abs(dev) > cfg["k_warn"]
        if flag:
            warnings.append(f"{src.label}: k={kk['k']:.4f} deviates {dev:+.2%} from 1 -- check the issuer's "
                            f"multiplier (dividend reinvestment / share ratio) and quote currency")
        k_rows.append({"event_id": ev.id, "source": sid, "issuer": src.issuer, "venue": src.venue,
                       "kind": src.kind, "quote": src.quote, "interval": meta_by[sid]["interval"],
                       **kk, "k_minus_1": dev, "warn": flag, "method": how, "fx": meta_by[sid]["fx"]})
        adj[sid] = g["price"] / kk["k"]
        close_adj[sid] = g["close"] / kk["k"]
        traded[sid] = g["traded"]
        volq[sid] = g["volume_quote"]
    adj, close_adj = pd.DataFrame(adj), pd.DataFrame(close_adj)
    traded, volq = pd.DataFrame(traded), pd.DataFrame(volq)

    win = (adj.index >= ev.win_start) & (adj.index < ev.win_end)
    night = (adj.index >= ev.t_evt) & (adj.index < ev.open1)
    c0, o1 = ev.c0, ev.o1
    caps = _capture_times(ev)
    hold = pd.Timedelta(minutes=cfg["hold_minutes"])

    # ---- cross-issuer (token sources only)
    tok = [s for s in adj.columns if by_kind[s].kind in TOKEN_KINDS]
    xs = M.cross_section(adj.loc[win, tok], traded.loc[win, tok]) if tok else pd.DataFrame(index=adj.index[win])
    prem = M.premiums(adj.loc[win, tok], traded.loc[win, tok], xs["median_price"]) if tok else pd.DataFrame()
    arb = M.arb_windows(xs, cfg["arb_threshold"]) if tok else pd.DataFrame()
    if not arb.empty:
        for c in ("rich_at_peak", "cheap_at_peak"):
            arb[c] = arb[c].map(lambda s: by_kind[s].label if s in by_kind else s)
        arb["main_pair"] = arb["main_pair"].map(
            lambda p: " > ".join(by_kind[x].label if x in by_kind else x for x in p.split(" > ")))
        arb.insert(0, "event_id", ev.id)
    prem_pyth = pd.DataFrame()
    if pyth_id:
        live = adj.loc[win].where(traded.loc[win])
        prem_pyth = live.div(adj.loc[win, pyth_id], axis=0) - 1

    # ---- per-source metrics
    rows = []
    for sid in adj.columns:
        src = by_kind[sid]
        if src.kind in OVERLAY_ONLY:
            continue
        p = adj[sid]
        r = {"event_id": ev.id, "ticker": ev.ticker, "cap_group": ev.cap_group, "source": sid,
             "issuer": src.issuer, "venue": src.venue, "kind": src.kind, "label": src.label,
             "interval": meta_by[sid]["interval"], "gap_stock": ev.gap}
        p_start, p925, p930 = M.price_at(p, ev.win_start), M.price_at(p, tu.et_clock_on(ev.next_session, 9, 25)), \
            M.price_at(p, ev.open1)
        r["move_token"] = p925 / p_start - 1 if p_start else np.nan
        r["residual_preopen"] = p925 / o1 - 1
        r["residual_at_open"] = p930 / o1 - 1
        for name, t in caps:
            r[f"captured_{name}"] = M.captured(M.price_at(p, t), c0, o1) if t is not None else np.nan
        cap_series = M.captured(p[night], c0, o1)
        for thr, key in ((0.5, "t50"), (0.9, "t90")):
            t = M.first_hold_time(cap_series, thr, hold)
            r[key] = tu.fmt_et(t) if t is not None else None
            r[f"{key}_min_after_event"] = (t - ev.t_evt).total_seconds() / 60 if t is not None else np.nan
        r["max_overshoot"], r["max_wrong_way"] = M.overshoot_wrongway(p[night], c0, o1)
        tw = traded.loc[win, sid]
        r["pct_zero_volume_bars"] = float(1 - tw.mean()) if src.kind not in ("ref",) else np.nan
        r["volume_usd"] = float(volq.loc[win, sid].sum(min_count=1)) if volq[sid].notna().any() else np.nan
        t925 = tu.et_clock_on(ev.next_session, 9, 25)
        before = tw[tw & (tw.index <= t925 - tu.BAR)]
        r["stale_min_at_0925"] = ((t925 - (before.index.max() + tu.BAR)).total_seconds() / 60
                                  if len(before) else np.nan)   # minutes since the last print at 09:25 ET
        if tok and sid in prem:
            r["premium_mean_night"] = float(prem.loc[prem.index < ev.open1, sid].mean())
        if not prem_pyth.empty and sid != pyth_id:
            r["premium_vs_pyth_mean_night"] = float(prem_pyth.loc[prem_pyth.index < ev.open1, sid].mean())
        rows.append(r)
    met = pd.DataFrame(rows)
    if not met.empty:
        met["rank_t50"] = met.loc[met["kind"].isin(TOKEN_KINDS), "t50_min_after_event"].rank(method="min")
        met["rank_t90"] = met.loc[met["kind"].isin(TOKEN_KINDS), "t90_min_after_event"].rank(method="min")

    # ---- lead-lag on 5m log returns of traded prices, from t_evt to the end of the window
    ll_rows = []
    llcols = [s for s in adj.columns if by_kind[s].kind in TOKEN_KINDS + ("perp", "ref")]
    seg = (adj.index >= ev.t_evt) & (adj.index < ev.win_end)
    rets = np.log(adj.loc[seg, llcols]).diff()
    for a, b in combinations(llcols, 2):
        res = M.lead_lag(rets[a], rets[b], cfg["leadlag_max_lag"])
        ll_rows.append({"event_id": ev.id, "a": by_kind[a].label, "b": by_kind[b].label,
                        "best_lag_bars": res["best_lag"], "best_corr": res["best_corr"], "corr_lag0": res["corr0"],
                        **{f"lag{k:+d}": v for k, v in res["corr"].items()}})
    ll = pd.DataFrame(ll_rows)

    out = paths.analysis / ev.id
    out.mkdir(parents=True, exist_ok=True)
    for name, df in (("adj", adj), ("close_adj", close_adj), ("traded", traded), ("volq", volq), ("xs", xs),
                     ("prem", prem), ("prem_pyth", prem_pyth)):
        df.to_parquet(out / f"{name}.parquet")
    met.to_csv(out / "metrics.csv", index=False)
    arb.to_csv(out / "arb.csv", index=False)
    pd.DataFrame(k_rows).to_csv(out / "k.csv", index=False)
    ll.to_csv(out / "leadlag.csv", index=False)
    funding = []
    for src in sources:
        p = cache.path(ev, src, "funding")
        if src.enabled and p.exists():
            f = pd.read_parquet(p)
            f["source"] = src.label
            funding.append(f)
    if funding:
        pd.concat(funding).to_parquet(out / "funding.parquet")
    info = {**ev.to_dict(), "gap": ev.gap, "warnings": warnings, "calibration_ref": calib_name,
            "labels": {s: by_kind[s].label for s in adj.columns},
            "kinds": {s: by_kind[s].kind for s in adj.columns},
            "t_evt": str(ev.t_evt), "win_start": str(ev.win_start), "win_end": str(ev.win_end),
            "open1": str(ev.open1)}
    (out / "event.json").write_text(json.dumps(info, indent=1, default=str))
    for w in warnings:
        log.warning("%s: %s", ev.id, w)
    STATUS.add(ev.id, "analyze", True, f"{len(met)} sources, {len(arb)} arb windows, {len(warnings)} warnings")
    return info


def run(paths, cfg, events, sources_by_ticker, fx_cfg, only=None):
    done = []
    for ev in events:
        if only and ev.id not in only and ev.ticker not in only:
            continue
        info = analyze_event(paths, cfg, ev, sources_by_ticker.get(ev.ticker, []), fx_cfg)
        if info:
            done.append(ev.id)
    return done
