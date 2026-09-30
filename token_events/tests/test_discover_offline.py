"""Offline smoke test of `discover` with every network call mocked."""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from events import discover  # noqa: E402
from events.adapters import ADAPTERS  # noqa: E402
from events.adapters import yahoo  # noqa: E402
from events.config import DEFAULTS, Paths, load_yaml  # noqa: E402
from events.http import SourceUnavailable  # noqa: E402


def _candles(start, end, interval="5m"):
    ix = pd.date_range(pd.Timestamp(start).ceil("5min"), pd.Timestamp(end), freq="5min", inclusive="left")
    return pd.DataFrame({"ts": ix, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0,
                         "volume_quote": 100.0})


def test_discover_offline(tmp_path, monkeypatch):
    listings = {
        "gate": [{"symbol": "ORCLON_USDT", "base": "ORCLON", "quote": "USDT", "name": "Oracle Ondo", "status": ""},
                 {"symbol": "ORCLX_USDT", "base": "ORCLX", "quote": "USDT", "name": "", "status": ""},
                 {"symbol": "BTC_USDT", "base": "BTC", "quote": "USDT", "name": "", "status": ""}],
        "kraken": [{"symbol": "ORCLxUSD", "base": "ORCLx", "quote": "USD", "name": "ORCLx/USD", "status": ""},
                   {"symbol": "SMOLxUSD", "base": "SMOLx", "quote": "USD", "name": "", "status": ""}],
    }

    def lm(venue):
        def f(*a, **k):
            if venue in listings:
                return listings[venue]
            raise SourceUnavailable(f"{venue}: HTTP 403 (geo-block/forbidden)")
        return f

    for v in ("gate", "bitget", "mexc", "okx", "kraken", "bybit", "kucoin", "binance"):
        monkeypatch.setattr(ADAPTERS[v], "list_markets", lm(v))
    monkeypatch.setattr(ADAPTERS["hyperliquid"], "dexes", lambda: ["xyz"])
    monkeypatch.setattr(ADAPTERS["hyperliquid"], "list_markets",
                        lambda dex="xyz": [{"symbol": "xyz:ORCL", "base": "ORCL", "quote": "USD", "name": dex,
                                            "status": "trading"}])
    monkeypatch.setattr(ADAPTERS["binance_fut"], "list_markets", lambda: [])
    monkeypatch.setattr(ADAPTERS["geckoterminal"], "networks",
                        lambda: [{"id": "eth", "name": "Ethereum"}, {"id": "solana", "name": "Solana"}])
    pools = [{"network": "solana", "pool": "P1", "name": "ORCLx / USDC", "dex": "raydium", "base_symbol": "ORCLx",
              "base_name": "Oracle xStock", "base_address": "M1", "quote_symbol": "USDC", "reserve_usd": 5e5,
              "volume_24h_usd": 1e5, "created": None}]
    monkeypatch.setattr(ADAPTERS["geckoterminal"], "search_pools",
                        lambda q, net=None: [p for p in pools if p["base_symbol"].lower() == q.lower()])
    monkeypatch.setattr(ADAPTERS["pyth"], "exists", lambda s: s.endswith("/USD") or s.endswith(".ON"))

    days = pd.bdate_range("2026-08-03", "2026-09-29")
    daily = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1e6}, index=days)
    gapped = daily.copy()
    gapped.loc[pd.Timestamp("2026-09-11"), "open"] = 107.5      # AMC gap on the 09-10 night
    flat = daily.copy()
    flat.loc[pd.Timestamp("2026-09-11"), "open"] = 101.0        # ADBE-like: 1% < threshold
    monkeypatch.setattr(yahoo, "daily", lambda t, days=90: (gapped if t in ("ORCL", "SMOL") else flat).copy())
    monkeypatch.setattr(yahoo, "market_cap", lambda t: (7e11, "EQUITY") if t != "SMOL" else (5e8, "EQUITY"))
    monkeypatch.setattr(yahoo, "earnings_dates",
                        lambda t, limit=12: pd.DatetimeIndex([pd.Timestamp("2026-09-10 16:00", tz="America/New_York")]))
    for name, ad in ADAPTERS.items():
        monkeypatch.setattr(ad, "fetch", lambda s, a, b, i="5m": _candles(a, b, i))

    cfg = {**DEFAULTS, "universe": ["ORCL"], "probe_top": 5}
    paths = Paths(tmp_path).ensure()
    cand, chosen = discover.run(paths, cfg, today=date(2026, 9, 30))

    assert paths.candidates.exists() and paths.events.exists() and paths.sources.exists()
    orcl = cand[(cand.ticker == "ORCL") & (cand.prev_session == "2026-09-10")].iloc[0]
    assert orcl.event_type == "earnings_amc" and orcl.gap_pct == 7.5 and orcl.proposed
    assert orcl.n_issuers_with_data == 2          # ondo (gate) + xstocks (gate/kraken/solana)
    src = load_yaml(paths.sources)["tickers"]["ORCL"]
    venues = {s["venue"] for s in src}
    assert {"gate", "kraken", "solana_raydium", "hl_xyz", "yahoo", "pyth"} <= venues
    pyth = next(s for s in src if s["venue"] == "pyth")
    assert pyth["symbol"] == "Equity.US.ORCL/USD|Equity.US.ORCL/USD.ON"
    ev = load_yaml(paths.events)["events"]
    assert any(e["id"] == "ORCL_20260910_AMC" for e in ev)
    # MU seed on 09-30 cannot be evaluated because no MU listing exists in the mock -> just logged.
    # ADBE seed: gap 1% < 3%: listed as seed, not valid, not proposed.
    adbe = cand[cand.event_id == "ADBE_20260910_AMC"].iloc[0]
    assert adbe.seed and not adbe.valid and not adbe.proposed and "threshold" in adbe.note
    mu = cand[cand.event_id == "MU_20260929_AMC"]
    assert mu.empty   # 09-30 is "today": the MU seed night has no O1 yet -> pending row
    assert (cand.ticker == "MU").any() and cand[cand.ticker == "MU"].note.str.contains("pending").all()
    assert np.isfinite(cand["score"]).all()
