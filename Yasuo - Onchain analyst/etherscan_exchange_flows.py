#!/usr/bin/env python3
"""
ETHERSCAN EXCHANGE FLOWS (Bitquery-free)

Compute exchange inflow/outflow/net_flow by querying Etherscan txlist for a curated
list of exchange addresses. Uses `exchange_addresses.json` if present.
"""
import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from pathlib import Path
import json


class EtherscanExchangeFlows:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        self.base_url = "https://api.etherscan.io/api"
        self.session = requests.Session()

        # Load known exchange addresses
        self.exchange_addresses = self._load_known_addresses()

    def _load_known_addresses(self) -> List[str]:
        seed = [
            # Binance
            "0x28c6c06298d514db089934071355e5743bf21d60",
            "0x9696f59e4d72e237be84ffd425dcad154bf96976",
            # Coinbase
            "0x503828976d22510aad0201ac7ec88293211d23da",
            "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",
            # Kraken
            "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13",
            # OKX / Huobi (sample)
            "0xdc76cd25977e0a5ae17155770273ad58648900d3",
            "0x8d12a197cb00d4747a1fe03395095ce2a5cc6819",
        ]
        cfg = Path(__file__).parent / "exchange_addresses.json"
        if cfg.exists():
            try:
                extra = json.loads(cfg.read_text())
                seed.extend([str(a) for a in extra])
            except Exception:
                pass
        # normalize lower
        uniq = []
        seen = set()
        for a in seed:
            al = a.lower()
            if al not in seen:
                uniq.append(al)
                seen.add(al)
        return uniq

    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {**params, "apikey": self.api_key}
        r = self.session.get(self.base_url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _fetch_address_txs(self, address: str, start_ts: int, end_ts: int, max_pages: int = 5, page_size: int = 10000) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            params = {
                "module": "account",
                "action": "txlist",
                "address": address,
                "starttimestamp": start_ts,
                "endtimestamp": end_ts,
                "page": page,
                "offset": page_size,
                "sort": "desc",
            }
            data = self._get(params)
            if data.get("status") == "1" and isinstance(data.get("result"), list):
                batch = data["result"]
                results.extend(batch)
                if len(batch) < page_size:
                    break
            else:
                break
        return results

    def get_exchange_flows(self, hours_back: int = 72, min_eth: float = 50.0) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "ETHERSCAN_API_KEY not set"}

        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=hours_back)
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())

        total_inflow = 0.0
        total_outflow = 0.0
        per_exchange: Dict[str, Dict[str, float]] = {}

        for addr in self.exchange_addresses:
            try:
                txs = self._fetch_address_txs(addr, start_ts, end_ts)
            except requests.RequestException:
                continue
            inflow = 0.0
            outflow = 0.0
            for tx in txs:
                try:
                    value_eth = float(tx.get("value", "0")) / 1e18
                except Exception:
                    value_eth = 0.0
                if value_eth < min_eth:
                    continue
                from_addr = (tx.get("from", "") or "").lower()
                to_addr = (tx.get("to", "") or "").lower()
                if to_addr == addr:
                    inflow += value_eth
                if from_addr == addr:
                    outflow += value_eth
            total_inflow += inflow
            total_outflow += outflow
            per_exchange[addr] = {"inflow": inflow, "outflow": outflow}

        return {
            "data_source": "etherscan_txlist",
            "hours_back": hours_back,
            "address_count": len(self.exchange_addresses),
            "inflow": total_inflow,
            "outflow": total_outflow,
            "net_flow": total_outflow - total_inflow,
            "exchanges": per_exchange,
            "timestamp": end.isoformat(),
        }


if __name__ == "__main__":
    api = EtherscanExchangeFlows()
    print(api.get_exchange_flows())


