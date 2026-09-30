"""GeckoTerminal (on-chain DEX pools). Free public API, ~30 req/min (throttled in http.py).
symbol format for fetch(): "<network>:<pool_address>". Prices requested in USD, volume in USD."""
import pandas as pd

from .base import HTTP, Adapter, frame, sec

BASE = "https://api.geckoterminal.com/api/v2"
HDR = {"Accept": "application/json;version=20230302"}
AGG = {"5m": ("minute", 5), "15m": ("minute", 15), "1h": ("hour", 1)}


class GeckoTerminal(Adapter):
    name = "geckoterminal"
    kind = "dex"
    intervals = ("5m", "15m", "1h")

    def networks(self) -> list[dict]:
        out, page = [], 1
        while page < 30:
            d = HTTP.get(f"{BASE}/networks", params={"page": page}, headers=HDR)
            out += [{"id": n["id"], "name": n["attributes"].get("name", "")} for n in d.get("data", [])]
            if not (d.get("links") or {}).get("next"):
                break
            page += 1
        return out

    def search_pools(self, query: str, network: str | None = None) -> list[dict]:
        params = {"query": query, "include": "base_token,quote_token,dex"}
        if network:
            params["network"] = network
        d = HTTP.get(f"{BASE}/search/pools", params=params, headers=HDR)
        inc = {i["id"]: i.get("attributes", {}) for i in d.get("included", [])}
        pools = []
        for p in d.get("data", []):
            a, rel = p["attributes"], p.get("relationships", {})
            bt = inc.get(((rel.get("base_token") or {}).get("data") or {}).get("id"), {})
            qt = inc.get(((rel.get("quote_token") or {}).get("data") or {}).get("id"), {})
            net = p["id"].split("_", 1)[0]
            pools.append({
                "network": net, "pool": a["address"], "name": a.get("name", ""),
                "dex": ((rel.get("dex") or {}).get("data") or {}).get("id", ""),
                "base_symbol": bt.get("symbol", ""), "base_name": bt.get("name", ""),
                "base_address": bt.get("address", ""), "quote_symbol": qt.get("symbol", ""),
                "reserve_usd": float(a.get("reserve_in_usd") or 0),
                "volume_24h_usd": float(((a.get("volume_usd") or {}).get("h24")) or 0),
                "created": a.get("pool_created_at"),
            })
        return pools

    def fetch(self, symbol, start, end, interval="5m"):
        network, pool = symbol.split(":", 1)
        tf, agg = AGG[interval]
        rows, before, stop = [], sec(end), sec(start)
        for _ in range(50):
            d = HTTP.get(f"{BASE}/networks/{network}/pools/{pool}/ohlcv/{tf}", headers=HDR, params={
                "aggregate": agg, "before_timestamp": before, "limit": 1000, "currency": "usd", "token": "base"})
            lst = (((d.get("data") or {}).get("attributes") or {}).get("ohlcv_list")) or []
            if not lst:
                break
            rows += lst
            oldest = min(int(r[0]) for r in lst)
            if oldest <= stop or oldest >= before:
                break
            before = oldest
        df = frame(rows, {"ts": 0, "open": 1, "high": 2, "low": 3, "close": 4, "volume_quote": 5}, "s",
                   pd.Timestamp(start), pd.Timestamp(end))
        df["volume"] = df["volume_quote"] / df["close"]
        return df
