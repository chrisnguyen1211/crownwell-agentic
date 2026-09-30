"""Shared HTTP client: per-host throttling, retry with exponential backoff, and a
source status registry that is printed at the end of every run."""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from urllib.parse import urlparse

import requests

log = logging.getLogger("events.http")

# Minimum seconds between two requests to the same host (conservative, public limits).
HOST_MIN_INTERVAL = {
    "api.geckoterminal.com": 2.2,        # ~30 req/min
    "api.kraken.com": 1.1,
    "benchmarks.pyth.network": 0.5,
    "api.hyperliquid.xyz": 0.3,
    "api.gateio.ws": 0.25,
    "api.bitget.com": 0.15,
    "api.mexc.com": 0.15,
    "www.okx.com": 0.25,
    "api.bybit.com": 0.15,
    "api.kucoin.com": 0.25,
    "api.binance.com": 0.15,
    "fapi.binance.com": 0.15,
}
DEFAULT_INTERVAL = 0.3


class SourceUnavailable(Exception):
    """Endpoint is blocked (geo/403/451), missing (404) or keeps failing. Pipeline skips the source."""


class HttpClient:
    def __init__(self, timeout: float = 25, max_retries: int = 5):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "token-events-study/0.1 (+research; no-auth public endpoints)"
        self.timeout = timeout
        self.max_retries = max_retries
        self._last: dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
        self.blocked_hosts: dict[str, str] = {}

    def _throttle(self, host: str):
        gap = HOST_MIN_INTERVAL.get(host, DEFAULT_INTERVAL)
        with self._lock:
            wait = self._last[host] + gap - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last[host] = time.monotonic()

    def request(self, method: str, url: str, **kw):
        host = urlparse(url).netloc
        if host in self.blocked_hosts:
            raise SourceUnavailable(f"{host} previously blocked: {self.blocked_hosts[host]}")
        kw.setdefault("timeout", self.timeout)
        delay = 2.0
        last_err = None
        for attempt in range(self.max_retries):
            self._throttle(host)
            try:
                r = self.s.request(method, url, **kw)
            except requests.exceptions.ProxyError as e:
                # A CONNECT refused by a proxy/firewall is a block, not a transient error.
                self.blocked_hosts[host] = f"proxy refused ({e.__class__.__name__})"
                raise SourceUnavailable(f"{host}: proxy refused connection") from e
            except requests.RequestException as e:
                last_err = f"{e.__class__.__name__}: {e}"
                log.warning("%s %s failed (%s), retry in %.0fs", method, host, last_err, delay)
                time.sleep(delay)
                delay *= 2
                continue
            if r.status_code in (401, 403, 451):
                self.blocked_hosts[host] = f"HTTP {r.status_code}"
                raise SourceUnavailable(f"{host}: HTTP {r.status_code} (geo-block/forbidden)")
            if r.status_code == 404:
                raise SourceUnavailable(f"{url}: HTTP 404")
            if r.status_code == 429 or r.status_code >= 500:
                ra = r.headers.get("Retry-After")
                wait = float(ra) if ra and ra.replace(".", "").isdigit() else delay
                log.warning("%s -> HTTP %s, retry in %.0fs", host, r.status_code, wait)
                time.sleep(wait)
                delay *= 2
                last_err = f"HTTP {r.status_code}"
                continue
            if r.status_code >= 400:
                raise SourceUnavailable(f"{url}: HTTP {r.status_code} {r.text[:200]}")
            try:
                return r.json()
            except ValueError as e:
                raise SourceUnavailable(f"{host}: non-JSON response") from e
        raise SourceUnavailable(f"{host}: gave up after {self.max_retries} tries ({last_err})")

    def get(self, url: str, params=None, **kw):
        return self.request("GET", url, params=params, **kw)

    def post(self, url: str, json=None, **kw):
        return self.request("POST", url, json=json, **kw)


HTTP = HttpClient()


class StatusBoard:
    """Collects ok/fail per source; printed as a table at the end of the log."""

    def __init__(self):
        self.rows: list[dict] = []

    def add(self, source: str, stage: str, ok: bool, detail: str = ""):
        self.rows.append({"source": source, "stage": stage, "status": "OK" if ok else "FAIL", "detail": detail})
        (log.info if ok else log.warning)("[%s] %s %s %s", stage, source, "OK" if ok else "FAIL", detail)

    def table(self) -> str:
        if not self.rows:
            return "(no sources touched)"
        import pandas as pd

        df = pd.DataFrame(self.rows).drop_duplicates(subset=["source", "stage", "status", "detail"])
        with pd.option_context("display.max_rows", 500, "display.max_colwidth", 90, "display.width", 200):
            return df.to_string(index=False)

    def dump(self, path):
        import pandas as pd

        pd.DataFrame(self.rows).to_csv(path, index=False)


STATUS = StatusBoard()
