"""Event and Source records (what lives in events.yaml / sources.yaml)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

from . import timeutil as tu

TOKEN_KINDS = ("cex_spot", "dex")              # compared across issuers (median, dispersion, arb)
OVERLAY_ONLY = ("perp_index", "perp_mark")     # plotted, no metrics


@dataclass
class Event:
    ticker: str
    event_type: str            # earnings_amc | earnings_bmo | earnings_unknown_time | weekend | gap_no_earnings
    t_event_utc: str
    prev_session: str          # date of C0 (also used for k calibration)
    next_session: str          # date of O1
    c0: float | None = None
    o1: float | None = None
    cap_group: str = ""
    market_cap: float | None = None
    seed: bool = False
    note: str = ""
    before_hours: float = 12
    after_open_hours: float = 2

    @property
    def id(self) -> str:
        tag = {"earnings_amc": "AMC", "earnings_bmo": "BMO"}.get(self.event_type, self.event_type.upper())
        return f"{self.ticker}_{self.prev_session.replace('-', '')}_{tag}"

    @property
    def t_evt(self) -> pd.Timestamp:
        return tu.utc(self.t_event_utc)

    @property
    def gap(self) -> float | None:
        return (self.o1 / self.c0 - 1) if self.c0 and self.o1 else None

    @property
    def open1(self) -> pd.Timestamp:
        return tu.session_open(self.next_session)

    @property
    def win_start(self) -> pd.Timestamp:
        return tu.floor5(self.t_evt - pd.Timedelta(hours=self.before_hours))

    @property
    def win_end(self) -> pd.Timestamp:
        return self.open1 + pd.Timedelta(hours=self.after_open_hours)

    @property
    def calib_start(self) -> pd.Timestamp:
        return tu.session_open(self.prev_session)

    @property
    def calib_end(self) -> pd.Timestamp:
        return tu.session_close(self.prev_session)

    @property
    def fetch_start(self) -> pd.Timestamp:
        # 1h of margin so "price at t_evt - 12h" has a print before it
        return min(self.win_start, self.calib_start) - pd.Timedelta(hours=1)

    @property
    def fetch_end(self) -> pd.Timestamp:
        return self.win_end

    @property
    def date_tag(self) -> str:
        return self.prev_session.replace("-", "")

    def to_dict(self) -> dict:
        d = asdict(self)
        d = {"id": self.id, **d}
        d["t_event_et"] = tu.fmt_et(self.t_evt)
        d["t_event_vn"] = tu.fmt_vn(self.t_evt)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in d.items() if k in keys})


@dataclass
class Source:
    ticker: str
    issuer: str        # ondo | xstocks | bstocks | robinhood | dinari | native_<venue> | perp | pyth | stock
    venue: str         # gate, kraken, solana_raydium, hl_xyz, binance_fut, pyth, yahoo, ...
    kind: str          # cex_spot | dex | perp | perp_index | perp_mark | ref | stock
    adapter: str       # key in adapters.ADAPTERS
    symbol: str        # adapter-specific symbol
    quote: str = "USD"
    enabled: bool = True
    identified_by: str = ""
    extra: dict = field(default_factory=dict)   # pool address, reserve, dex, ...

    @property
    def id(self) -> str:
        return f"{self.ticker}.{self.issuer}.{self.venue}"

    @property
    def label(self) -> str:
        return f"{self.issuer}@{self.venue}"

    def to_dict(self) -> dict:
        d = asdict(self)
        if not d["extra"]:
            d.pop("extra")
        return {"id": self.id, **d}

    @classmethod
    def from_dict(cls, d: dict) -> "Source":
        keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in d.items() if k in keys})


def load_events(path) -> list[Event]:
    from .config import load_yaml

    doc = load_yaml(path, {}) or {}
    return [Event.from_dict(e) for e in doc.get("events", []) if e.get("enabled", True)]


def load_sources(path) -> tuple[dict[str, list[Source]], dict]:
    from .config import load_yaml

    doc = load_yaml(path, {}) or {}
    out = {}
    for t, lst in (doc.get("tickers") or {}).items():
        out[t] = [Source.from_dict({"ticker": t, **s}) for s in lst or []]
    return out, doc.get("fx") or {}
