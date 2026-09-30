"""Step 1: discover tokenized-stock sources, find valid overnight events, propose 5-6 of them.

Writes sources.yaml, events.yaml, events_candidates.csv and stops for human review."""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from datetime import date

import pandas as pd

from . import timeutil as tu
from .adapters import ADAPTERS, CEX_SPOT
from .adapters import pyth as pyth_mod
from .adapters import yahoo
from .config import dump_yaml
from .fetch import Cache, fetch_source
from .http import STATUS, SourceUnavailable
from .model import TOKEN_KINDS, Event, Source

log = logging.getLogger("events.discover")

ISSUER_WORDS = {"ondo": ("ondo",), "xstocks": ("xstock", "backed"), "bstocks": ("bstock",),
                "dinari": ("dinari", "dshare"), "robinhood": ("robinhood",)}


# ---------------------------------------------------------------- 1. CEX / perp listings
def _match_suffix(base: str, rules) -> tuple[str, str] | None:
    b = base.upper()
    for r in rules:
        suf = r["suffix"].upper()
        if b.endswith(suf) and 1 <= len(b) - len(suf) <= 5:
            t = b[: -len(suf)]
            if re.fullmatch(r"[A-Z]{1,5}", t):
                return t, r["issuer"]
    return None


def scan_cex(cfg, meta_dir) -> tuple[dict, dict]:
    """Returns ({ticker: [Source]}, {venue: [market dicts]}) from spot listings."""
    found: dict[str, list[Source]] = defaultdict(list)
    listings = {}
    for venue in CEX_SPOT:
        try:
            mk = ADAPTERS[venue].list_markets()
            listings[venue] = mk
            STATUS.add(f"listing:{venue}", "discover", True, f"{len(mk)} markets")
        except SourceUnavailable as e:
            STATUS.add(f"listing:{venue}", "discover", False, str(e)[:160])
            continue
        except Exception as e:
            STATUS.add(f"listing:{venue}", "discover", False, f"{e.__class__.__name__}: {e}"[:160])
            continue
        best: dict[tuple, dict] = {}
        for m in mk:
            if m["quote"].upper() not in cfg["quotes"]:
                continue
            hit = _match_suffix(m["base"], cfg["suffix_rules"])
            if venue == "kraken":   # the whole tokenized_asset class on Kraken is xStocks
                b = m["base"]
                hit = (b[:-1].upper(), "xstocks") if b.lower().endswith("x") else hit
            if not hit:
                continue
            t, issuer = hit
            key = (t, issuer)
            rank = cfg["quotes"].index(m["quote"].upper())
            if key not in best or rank < best[key]["_rank"]:
                best[key] = {**m, "_rank": rank}
        for (t, issuer), m in best.items():
            words = ISSUER_WORDS.get(issuer, ())
            by_name = any(w in (m.get("name") or "").lower() for w in words)
            why = f"{venue} listing base={m['base']} quote={m['quote']} suffix->{issuer}"
            if by_name:
                why += f" (name '{m['name']}')"
            if venue == "kraken":
                why += " (Kraken asset class tokenized_asset)"
            found[t].append(Source(ticker=t, issuer=issuer, venue=venue, kind="cex_spot", adapter=venue,
                                   symbol=m["symbol"], quote=m["quote"].upper(), identified_by=why,
                                   extra={"name_confirmed": by_name or venue == "kraken"}))
    (meta_dir / "listings.json").write_text(json.dumps(listings, default=str)[:50_000_000])
    return found, listings


def scan_perps(cfg, tickers: set[str]) -> dict[str, list[Source]]:
    out: dict[str, list[Source]] = defaultdict(list)
    hl = ADAPTERS["hyperliquid"]
    try:
        dexes = hl.dexes()
        STATUS.add("listing:hyperliquid", "discover", True, f"dexes={dexes}")
    except SourceUnavailable as e:
        STATUS.add("listing:hyperliquid", "discover", False, str(e)[:160])
        dexes = []
    for dex in dexes:
        try:
            for m in hl.list_markets(dex):
                t = m["base"].upper()
                if m["status"] != "trading":
                    continue
                enabled = dex in cfg["hyperliquid_dexes"]
                out[t].append(Source(ticker=t, issuer="perp", venue=f"hl_{dex}", kind="perp", adapter="hyperliquid",
                                     symbol=m["symbol"], quote="USD", enabled=enabled,
                                     identified_by=f"Hyperliquid meta dex={dex} coin={m['symbol']}"
                                                   + ("" if enabled else " (dex not in hyperliquid_dexes)")))
        except SourceUnavailable as e:
            STATUS.add(f"listing:hyperliquid:{dex}", "discover", False, str(e)[:160])
    try:
        fut = ADAPTERS["binance_fut"].list_markets()
        STATUS.add("listing:binance_fut", "discover", True, f"{len(fut)} contracts")
    except SourceUnavailable as e:
        STATUS.add("listing:binance_fut", "discover", False, str(e)[:160])
        fut = []
    for m in fut:
        if m["quote"] != "USDT" or "PERPETUAL" not in (m.get("contractType") or "") or m["status"] != "TRADING":
            continue
        t = m["base"].upper()
        if t not in tickers:
            continue
        stockish = any(w in (m.get("name") or "").upper() for w in ("TRADFI", "STOCK", "EQUITY"))
        why = f"Binance USD-M {m['symbol']} underlying='{m.get('name')}'"
        common = dict(ticker=t, issuer="perp", quote="USDT", enabled=stockish,
                      identified_by=why + ("" if stockish else " -- underlying not flagged as stock: VERIFY"))
        out[t] += [
            Source(venue="binance_fut", kind="perp", adapter="binance_fut", symbol=m["symbol"], **common),
            Source(venue="binance_fut_index", kind="perp_index", adapter="binance_fut_index", symbol=m["symbol"],
                   **common),
            Source(venue="binance_fut_mark", kind="perp_mark", adapter="binance_fut_mark", symbol=m["symbol"],
                   **common),
        ]
    return out


# ---------------------------------------------------------------- 2. yfinance: validation, caps, events
def _cached_json(path, fn):
    if path.exists():
        return json.loads(path.read_text())
    v = fn()
    path.write_text(json.dumps(v, default=str))
    return v


def validate_tickers(cands: dict[str, list[Source]], cfg, meta_dir) -> dict[str, dict]:
    """Keep tickers that are real US equities/ETFs; attach market cap and cap group."""
    caps_path = meta_dir / "marketcap.json"
    caps = json.loads(caps_path.read_text()) if caps_path.exists() else {}
    universe = set(cfg["universe"]) | {x["ticker"] for x in cfg["seeds"]}
    info = {}
    for t, srcs in sorted(cands.items()):
        issuers = {s.issuer for s in srcs if s.kind in TOKEN_KINDS}
        venues = {s.venue for s in srcs}
        strong = (t in universe or any(s.extra.get("name_confirmed") for s in srcs)
                  or (len(venues) >= 2 and issuers))
        if not strong:
            log.info("skip %s: only one unconfirmed listing (%s)", t, [s.symbol for s in srcs])
            continue
        if t not in caps:
            mc, qt = yahoo.market_cap(t)
            caps[t] = {"market_cap": mc, "quote_type": qt}
            caps_path.write_text(json.dumps(caps))
        mc = caps[t]["market_cap"]
        if not mc and caps[t]["quote_type"] not in ("ETF",):
            log.info("skip %s: yfinance has no market cap (not a US stock?)", t)
            continue
        grp = ("etf" if caps[t]["quote_type"] == "ETF" else
               "large" if mc >= cfg["cap_large"] else "mid" if mc >= cfg["cap_mid"] else "small")
        info[t] = {"market_cap": mc, "cap_group": grp}
    return info


def classify_night(d0: date, d1: date, earnings: pd.DatetimeIndex) -> tuple[str, pd.Timestamp, str]:
    """Event type and t_evt for the closed-market window between session d0 close and d1 open."""
    close0, open1 = tu.session_close(d0), tu.session_open(d1)
    for e in earnings:
        eu = e.tz_convert("UTC")
        e_et = e.tz_convert(tu.ET)
        unknown_time = e_et.hour == 0 and e_et.minute == 0
        if unknown_time and e_et.date() in (d0, d1):
            if e_et.date() == d0:
                return "earnings_unknown_time", close0, "earnings on d0, time unknown -> assumed AMC 16:00 ET"
            return "earnings_unknown_time", tu.et_clock_on(d1, 7), "earnings on d1, time unknown -> BMO 07:00"
        if close0 <= eu < open1:
            if e_et.date() == d0:
                return "earnings_amc", eu, ""
            if e_et.date() == d1:
                return "earnings_bmo", eu, "BMO: short closed window"
            return "earnings_weekend", eu, "released on a non-trading day"
        if tu.session_open(d0) <= eu < close0 and e_et.date() == d0:
            return "earnings_intraday", eu, "released during regular session -> not an overnight event"
    if (d1 - d0).days > 1:
        return "weekend", close0, "no earnings found; weekend/holiday gap, t_evt set to prior close"
    return "gap_no_earnings", close0, "no earnings found; news time unknown, t_evt set to prior close"


def find_events(tickers: dict[str, dict], cfg, meta_dir, today: date) -> list[dict]:
    rows = []
    seeds = {(s["ticker"], s["date"]): s for s in cfg["seeds"]}
    for t, inf in tickers.items():
        try:
            d = yahoo.daily(t, days=cfg["lookback_days"] + 30)
        except Exception as e:
            STATUS.add(f"yahoo_daily:{t}", "discover", False, str(e)[:120])
            continue
        if d.empty:
            STATUS.add(f"yahoo_daily:{t}", "discover", False, "no daily data")
            continue
        d = d[d.index >= pd.Timestamp(today) - pd.Timedelta(days=cfg["lookback_days"])]
        earn = yahoo.earnings_dates(t, limit=12)
        sessions = list(d.index.date)
        for i in range(len(sessions)):
            d0 = sessions[i]
            d1 = sessions[i + 1] if i + 1 < len(sessions) else None
            seed = seeds.get((t, str(d0)))
            if d1 is None or (d0 == today and d1 is None):
                if seed:   # event tonight / not opened yet
                    rows.append({"ticker": t, **inf, "event_type": f"earnings_{seed['type'].lower()}",
                                 "t_evt": tu.session_close(d0), "d0": d0, "d1": tu.next_weekday(d0),
                                 "c0": float(d.loc[pd.Timestamp(d0), "close"]), "o1": None, "gap": None,
                                 "valid": False, "seed": True, "note": "pending: next session has not opened yet"})
                continue
            c0, o1 = float(d.loc[pd.Timestamp(d0), "close"]), float(d.loc[pd.Timestamp(d1), "open"])
            gap = o1 / c0 - 1
            if abs(gap) < cfg["gap_threshold"] and not seed:
                continue
            et, t_evt, note = classify_night(d0, d1, earn)
            if seed and not et.startswith("earnings_"):
                et, t_evt = f"earnings_{seed['type'].lower()}", tu.session_close(d0)
                note = "seed from brief; Yahoo has no earnings time -> assumed 16:00 ET"
            valid = abs(gap) >= cfg["gap_threshold"] and et != "earnings_intraday"
            if seed and abs(gap) < cfg["gap_threshold"]:
                note = (note + "; " if note else "") + f"|gap| {abs(gap):.2%} < threshold {cfg['gap_threshold']:.0%}"
            rows.append({"ticker": t, **inf, "event_type": et, "t_evt": t_evt, "d0": d0, "d1": d1, "c0": c0,
                         "o1": o1, "gap": gap, "valid": valid, "seed": bool(seed), "note": note})
        covered = {str(x) for x in sessions[:-1]}
        for (st, ds), sd in seeds.items():
            if st != t or ds in covered or any(r["ticker"] == t and str(r["d0"]) == ds for r in rows):
                continue
            last_c = float(d["close"].iloc[-1]) if len(d) else None
            rows.append({"ticker": t, **inf, "event_type": f"earnings_{sd['type'].lower()}",
                         "t_evt": tu.session_close(ds), "d0": pd.Timestamp(ds).date(),
                         "d1": tu.next_weekday(pd.Timestamp(ds).date()), "c0": last_c, "o1": None, "gap": None,
                         "valid": False, "seed": True,
                         "note": "pending: event night has not finished (no O1 yet)"
                                 if pd.Timestamp(ds).date() >= sessions[-1] else "seed date not in daily data"})
    # seeds whose ticker was not listed anywhere
    for (t, ds), s in seeds.items():
        if t not in tickers:
            log.warning("seed %s %s: ticker has no token listing found (not validated)", t, ds)
    return rows


# ---------------------------------------------------------------- 3. on-chain + Pyth + Yahoo per ticker
def resolve_networks(gt, cfg, meta_dir) -> dict[str, str]:
    """Map '@robinhood' style placeholders to real GeckoTerminal network ids."""
    try:
        nets = _cached_json(meta_dir / "gt_networks.json", gt.networks)
        STATUS.add("geckoterminal:networks", "discover", True, f"{len(nets)} networks")
    except SourceUnavailable as e:
        STATUS.add("geckoterminal:networks", "discover", False, str(e)[:160])
        return {}
    out = {}
    rh = [n for n in nets if "robinhood" in (n["id"] + n["name"]).lower()]
    if rh:
        out["@robinhood"] = rh[0]["id"]
        STATUS.add("geckoterminal:robinhood_chain", "discover", True, f"network id={rh[0]['id']}")
    else:
        STATUS.add("geckoterminal:robinhood_chain", "discover", False,
                   "không có nguồn: GeckoTerminal has no Robinhood Chain network -> Robinhood Stock Tokens skipped")
    return out


def scan_onchain(t: str, cfg, net_alias: dict, meta_dir) -> list[Source]:
    gt = ADAPTERS["geckoterminal"]
    cache_path = meta_dir / "gt_search.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    out = []
    for rule in cfg["onchain"]:
        sym = rule["symbol"].replace("{T}", t)
        nets = [net_alias.get(n, None) if n.startswith("@") else n for n in rule["networks"]]
        nets = [n for n in nets if n]
        if not nets:
            continue
        pools = []
        for q_net in [None] + nets:
            key = f"{sym}|{q_net}"
            if key not in cache:
                try:
                    cache[key] = gt.search_pools(sym, q_net)
                except SourceUnavailable as e:
                    STATUS.add(f"geckoterminal:search:{sym}", "discover", False, str(e)[:160])
                    cache_path.write_text(json.dumps(cache))
                    return out
                cache_path.write_text(json.dumps(cache))
            pools += cache[key]
            found_nets = {p["network"] for p in pools if p["base_symbol"].lower() == sym.lower()}
            if q_net is None and set(nets) <= found_nets:
                break   # the global search already covered every expected network
        by_net: dict[str, dict] = {}
        for p in pools:
            if p["base_symbol"].lower() != sym.lower() or p["network"] not in nets:
                continue
            if p["reserve_usd"] < cfg["min_pool_reserve_usd"]:
                continue
            if p["network"] not in by_net or p["reserve_usd"] > by_net[p["network"]]["reserve_usd"]:
                by_net[p["network"]] = p
        for net, p in by_net.items():
            dex = (p["dex"] or "dex").replace(f"{net}_", "").replace("-", "")
            out.append(Source(
                ticker=t, issuer=rule["issuer"], venue=f"{net}_{dex}", kind="dex", adapter="geckoterminal",
                symbol=f"{net}:{p['pool']}", quote="USD",
                identified_by=(f"GeckoTerminal search '{sym}' on {net}: base token {p['base_symbol']} "
                               f"'{p['base_name']}' ({p['base_address']}), largest pool by reserve"),
                extra={"pool": p["pool"], "pool_name": p["name"], "dex": p["dex"],
                       "reserve_usd": round(p["reserve_usd"]), "volume_24h_usd": round(p["volume_24h_usd"]),
                       "base_token": p["base_address"]}))
    return out


def scan_reference(t: str, meta_dir) -> list[Source]:
    out = [Source(ticker=t, issuer="stock", venue="yahoo", kind="stock", adapter="yahoo", symbol=t, quote="USD",
                  identified_by="yfinance 5m prepost=True (regular + extended hours)")]
    cache_path = meta_dir / "pyth_symbols.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    ok = []
    for v in pyth_mod.variants(t):
        if v not in cache:
            try:
                cache[v] = ADAPTERS["pyth"].exists(v)
            except SourceUnavailable as e:
                STATUS.add(f"pyth:{v}", "discover", False, str(e)[:160])
                break
            cache_path.write_text(json.dumps(cache))
        if cache[v]:
            ok.append(v)
    if ok:
        out.append(Source(ticker=t, issuer="pyth", venue="pyth", kind="ref", adapter="pyth", symbol="|".join(ok),
                          quote="USD", identified_by=f"Pyth Benchmarks symbols found: {ok}"))
    return out


# ---------------------------------------------------------------- 4. probe, score, propose
def _to_event(r: dict, cfg) -> Event:
    return Event(ticker=r["ticker"], event_type=r["event_type"], t_event_utc=tu.utc(r["t_evt"]).isoformat(),
                 prev_session=str(r["d0"]), next_session=str(r["d1"]), c0=r["c0"], o1=r["o1"],
                 cap_group=r["cap_group"], market_cap=r["market_cap"], seed=r["seed"], note=r["note"],
                 before_hours=cfg["window_before_hours"], after_open_hours=cfg["window_after_open_hours"])


TYPE_SCORE = {"earnings_amc": 4, "earnings_bmo": 2, "earnings_unknown_time": 1.5, "earnings_weekend": 1,
              "weekend": 0.5, "gap_no_earnings": 0}


def score(r: dict) -> float:
    n = r.get("n_issuers", 0)
    return (10 * (n >= 2) + 2 * n + TYPE_SCORE.get(r["event_type"], 0)
            + min(abs(r["gap"] or 0) * 100, 20) / 2 + (2 if r["seed"] else 0))


def probe(paths, rows, sources, cfg):
    """Fetch the event windows of the top candidates (results are cached for `fetch`)."""
    cache = Cache(paths)
    for r in rows:
        r["listed_issuers"] = sorted({s.issuer for s in sources.get(r["ticker"], [])
                                      if s.kind in TOKEN_KINDS and s.enabled})
        r["n_issuers"] = len(r["listed_issuers"])
        r["probed"] = False
    ranked = sorted([r for r in rows if r["valid"] or r["seed"]], key=score, reverse=True)
    for r in ranked[: cfg["probe_top"]]:
        if r["o1"] is None:
            continue
        ev = _to_event(r, cfg)
        with_data, res = set(), {}
        for s in sources.get(r["ticker"], []):
            if not s.enabled or s.kind in ("perp_index", "perp_mark"):
                continue
            df, meta = fetch_source(cache, ev, s)
            if df is None:
                res[s.label] = "fail"
                continue
            win = df[(df["ts"] >= ev.win_start) & (df["ts"] < ev.win_end)]
            traded = int((win["volume"].fillna(0) > 0).sum()) if s.kind != "ref" else len(win)
            res[s.label] = f"{meta.get('interval', '?')}:{traded}bars" if len(win) else "no bars"
            if s.kind in TOKEN_KINDS and traded > 0:
                with_data.add(s.issuer)
        r["n_issuers"] = len(with_data)
        r["issuers_with_data"] = sorted(with_data)
        r["resolution"] = "; ".join(f"{k}={v}" for k, v in res.items())
        r["probed"] = True
    return rows


def propose(rows, cfg) -> list[dict]:
    pool = [r for r in rows if r["valid"] and r["o1"] is not None]
    pool.sort(key=score, reverse=True)
    chosen, used = [], set()
    for grp in ("large", "mid", "small"):
        for r in (r for r in pool if r["cap_group"] == grp):
            if sum(c["cap_group"] == grp for c in chosen) >= cfg["per_cap_group"]:
                break
            if r["ticker"] in used:
                continue
            chosen.append(r)
            used.add(r["ticker"])
    for r in pool:
        if len(chosen) >= cfg["n_events"]:
            break
        if r not in chosen and r["ticker"] not in used:
            chosen.append(r)
            used.add(r["ticker"])
    return chosen[: cfg["n_events"]]


# ---------------------------------------------------------------- main
def run(paths, cfg, today: date | None = None):
    paths.ensure()
    today = today or date.today()
    meta = paths.meta
    log.info("1/5 scanning CEX spot listings ...")
    cex, _ = scan_cex(cfg, meta)
    for t in list(cfg["universe"]) + [x["ticker"] for x in cfg["seeds"]]:
        cex.setdefault(t, [])
    log.info("2/5 validating %d candidate tickers with yfinance ...", len(cex))
    info = validate_tickers(cex, cfg, meta)
    perps = scan_perps(cfg, set(info))
    log.info("3/5 scanning daily gaps / earnings for %d tickers ...", len(info))
    rows = find_events(info, cfg, meta, today)
    tickers_with_events = sorted({r["ticker"] for r in rows if r["valid"] or r["seed"]})
    log.info("4/5 on-chain pools + Pyth for %d tickers with candidate nights ...", len(tickers_with_events))
    net_alias = resolve_networks(ADAPTERS["geckoterminal"], cfg, meta)
    sources: dict[str, list[Source]] = {}
    for i, t in enumerate(tickers_with_events, 1):
        log.info("   [%d/%d] %s", i, len(tickers_with_events), t)
        s = cex.get(t, []) + scan_onchain(t, cfg, net_alias, meta) + perps.get(t, []) + scan_reference(t, meta)
        sources[t] = s
    log.info("5/5 probing top %d candidate windows ...", cfg["probe_top"])
    rows = probe(paths, rows, sources, cfg)
    chosen = propose(rows, cfg)
    chosen_ids = {_to_event(r, cfg).id for r in chosen}

    # ---- events_candidates.csv
    recs = []
    for r in rows:
        ev = _to_event(r, cfg)
        srcs = sources.get(r["ticker"], [])
        recs.append({
            "event_id": ev.id, "proposed": ev.id in chosen_ids, "ticker": r["ticker"], "cap_group": r["cap_group"],
            "market_cap_usd_bn": round((r["market_cap"] or 0) / 1e9, 2), "event_type": r["event_type"],
            "t_event_et": tu.fmt_et(r["t_evt"]), "t_event_utc": tu.fmt_utc(r["t_evt"]),
            "t_event_vn": tu.fmt_vn(r["t_evt"]), "prev_session": str(r["d0"]), "next_session": str(r["d1"]),
            "close_before": r["c0"], "open_after": r["o1"],
            "gap_pct": round(r["gap"] * 100, 2) if r["gap"] is not None else None,
            "n_issuers_with_data": r["n_issuers"], "probed": r["probed"],
            "issuers": ",".join(r.get("issuers_with_data") or r.get("listed_issuers") or []),
            "sources": ", ".join(s.label for s in srcs if s.enabled),
            "resolution": r.get("resolution", "not probed"), "valid": r["valid"], "seed": r["seed"],
            "score": round(score(r), 2), "note": r["note"],
        })
    cand = pd.DataFrame(recs).sort_values(["proposed", "score"], ascending=False)
    cand.to_csv(paths.candidates, index=False)

    # ---- sources.yaml (only tickers that have candidate events)
    doc = {"fx": {"USDT": "Crypto.USDT/USD", "USDC": "Crypto.USDC/USD"},
           "tickers": {t: [{k: v for k, v in s.to_dict().items() if k != "ticker"} for s in lst]
                       for t, lst in sorted(sources.items())}}
    dump_yaml(doc, paths.sources, header=f"""
Generated by `run.py discover` on {today}. REVIEW before `fetch`:
  - set enabled: false for anything misidentified; add missing sources by hand (same fields).
  - identified_by explains how each source was recognised; pools keep their address + reserve.
  - adapter/symbol are passed as-is to events/adapters/<adapter>.py fetch().""")

    # ---- events.yaml (proposal)
    evs = [_to_event(r, cfg).to_dict() for r in chosen]
    dump_yaml({"events": evs}, paths.events, header=f"""
Proposed by `run.py discover` on {today} ({len(evs)} events). Edit freely, then run `run.py fetch`.
All candidates are in events_candidates.csv (copy rows here to add them). t_event_utc is authoritative;
prev_session = day of C0 (and of the k calibration), next_session = day of O1.""")
    return cand, chosen
