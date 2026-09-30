"""Paths, parameters and YAML I/O."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULTS = {
    "gap_threshold": 0.03,          # |Open(T+1)/Close(T) - 1| to qualify
    "lookback_days": 60,            # daily history scanned for events
    "cap_large": 10e9,              # market cap >= -> large
    "cap_mid": 2e9,                 # market cap >= -> mid, else small
    "window_before_hours": 12,      # crawl from t_evt - 12h
    "window_after_open_hours": 2,   # ... to 09:30 ET next session + 2h
    "arb_threshold": 0.005,         # dispersion above this = potential arb window
    "fx_threshold_bps": 5,          # convert USDT/USDC -> USD only if the peg deviates more than this
    "k_warn": 0.02,                 # warn when |k - 1| exceeds this
    "hold_minutes": 30,             # t50/t90 must hold this long
    "leadlag_max_lag": 6,           # bars
    "n_events": 6,
    "per_cap_group": 2,
    "probe_top": 20,                # candidates whose windows are actually probed during discover
    "min_pool_reserve_usd": 1000,   # ignore dust DEX pools
    "quotes": ["USDT", "USDC", "USD"],
    # Ticker suffix rules on CEX listings / on-chain token symbols -> issuer
    "suffix_rules": [
        {"suffix": "ON", "issuer": "ondo"},
        {"suffix": "X", "issuer": "xstocks"},
    ],
    # On-chain symbol patterns searched on GeckoTerminal. {T} = ticker.
    "onchain": [
        {"issuer": "ondo", "symbol": "{T}on", "networks": ["eth", "bsc", "solana"]},
        {"issuer": "xstocks", "symbol": "{T}x", "networks": ["solana", "eth", "bsc"]},
        {"issuer": "bstocks", "symbol": "{T}b", "networks": ["bsc"]},
        {"issuer": "dinari", "symbol": "{T}.d", "networks": ["arbitrum", "base"]},
        {"issuer": "robinhood", "symbol": "{T}", "networks": ["@robinhood"]},  # resolved from /networks
    ],
    "hyperliquid_dexes": ["xyz"],   # other HIP-3 dexes are listed but disabled
    # Tickers always considered (discovery also adds everything it finds on venues)
    "universe": [
        "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "AVGO", "ORCL", "ADBE", "MU", "AMD", "NFLX",
        "COIN", "PLTR", "HOOD", "MSTR", "CRWD", "INTC", "CRM", "LULU", "COST", "SNOW", "CRWV", "CRCL", "SPY",
        "QQQ", "GME", "AMC", "RDDT", "HIMS", "SOFI", "RIVN", "IONQ", "RGTI", "MARA", "RIOT", "CLSK", "UPST",
        "AFRM", "OPEN", "SBET", "BMNR", "CRVO", "OKLO", "SMCI", "DKNG", "FUBO", "PLUG", "QBTS", "ASTS",
        "GLXY", "BTBT", "NKE", "FDX", "KMX", "CCL", "GIS", "PAYX", "CTAS", "MKC", "JEF", "CAG", "LEVI",
    ],
    # Seeds from the brief, always evaluated (marked seed=true) even if they fail the gap filter.
    "seeds": [
        {"ticker": "ORCL", "date": "2026-09-10", "type": "AMC"},
        {"ticker": "AVGO", "date": "2026-09-02", "type": "AMC"},
        {"ticker": "ADBE", "date": "2026-09-10", "type": "AMC"},
        {"ticker": "MU", "date": "2026-09-30", "type": "AMC"},
    ],
}


@dataclass
class Paths:
    root: Path

    @property
    def data(self):
        return self.root / "data"

    @property
    def raw(self):
        return self.data / "raw"

    @property
    def meta(self):
        return self.data / "meta"

    @property
    def analysis(self):
        return self.data / "analysis"

    @property
    def config(self):
        return self.root / "config.yaml"

    @property
    def events(self):
        return self.root / "events.yaml"

    @property
    def sources(self):
        return self.root / "sources.yaml"

    @property
    def candidates(self):
        return self.root / "events_candidates.csv"

    @property
    def report(self):
        return self.root / "report.html"

    @property
    def xlsx(self):
        return self.root / "summary.xlsx"

    def ensure(self):
        for p in (self.raw, self.meta, self.analysis):
            p.mkdir(parents=True, exist_ok=True)
        return self


def load_yaml(path: Path, default=None):
    if not path.exists():
        return copy.deepcopy(default)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or copy.deepcopy(default)


def dump_yaml(obj, path: Path, header: str = ""):
    with open(path, "w", encoding="utf-8") as f:
        if header:
            f.write("".join(f"# {line}\n" for line in header.strip().splitlines()))
        yaml.safe_dump(obj, f, sort_keys=False, allow_unicode=True, width=120)


def load_config(paths: Paths) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    user = load_yaml(paths.config, {}) or {}
    cfg.update(user.get("params", user))
    return cfg
