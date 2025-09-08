#!/usr/bin/env python3
"""
Fixed Bitquery API with proper GraphQL syntax and limits
"""
import requests
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from pathlib import Path
import json

load_dotenv()

class FixedBitqueryAPI:
    """
    Fixed Bitquery API client with proper GraphQL syntax
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BITQUERY_API_KEY")
        self.base_url = "https://graphql.bitquery.io"
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 1.0  # 1 request per second max
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            if self.api_key.startswith("ory_at_"):
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                headers["X-API-KEY"] = self.api_key
        return headers
    
    def _rate_limit(self):
        """Simple rate limiting"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                import time
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = datetime.now()
    
    def _load_known_addresses(self) -> List[str]:
        """Load additional known exchange addresses from exchange_addresses.json if present"""
        try:
            cfg_path = Path(__file__).parent / "exchange_addresses.json"
            if cfg_path.exists():
                with open(cfg_path, "r") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return [str(a).lower() for a in data]
        except Exception as e:
            self.logger.warning(f"Couldn't load exchange_addresses.json: {e}")
        return []

    def get_large_eth_transactions(self, min_eth: float = 10, hours_back: int = 72) -> List[Dict[str, Any]]:
        """
        Get large ETH transactions with proper GraphQL syntax
        """
        if not self.api_key:
            self.logger.warning("No Bitquery API key available")
            return []
        
        self._rate_limit()
        
        # Fixed GraphQL query with proper datetime format
        from datetime import datetime, timedelta
        since_time = (datetime.now() - timedelta(hours=hours_back)).isoformat() + "Z"
        
        query = """
        query GetLargeETHTransfers($minAmount: Float!, $sinceTime: ISO8601DateTime!) {
          ethereum(network: ethereum) {
            transfers(
              currency: {is: "0x0000000000000000000000000000000000000000"}
              amount: {gt: $minAmount}
              time: {since: $sinceTime}
              options: {desc: "amount", limit: 50}
            ) {
              amount
              sender {
                address
                annotation
              }
              receiver {
                address
                annotation
              }
              transaction {
                hash
              }
              currency {
                symbol
              }
              date {
                date
              }
            }
          }
        }
        """
        
        variables = {
            "minAmount": min_eth,
            "sinceTime": since_time
        }
        
        try:
            response = requests.post(
                self.base_url,
                json={"query": query, "variables": variables},
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    self.logger.error(f"Bitquery GraphQL errors: {data['errors']}")
                    return []
                
                transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
                self.logger.info(f"Found {len(transfers)} large ETH transactions")
                return transfers
            else:
                self.logger.error(f"Bitquery API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error querying Bitquery API: {e}")
            return []
    
    def get_exchange_flows(self, hours_back: int = 72) -> Dict[str, Any]:
        """
        Get exchange flows using Bitquery with proper syntax
        """
        if not self.api_key:
            self.logger.warning("No Bitquery API key available")
            return {}
        
        self._rate_limit()
        
        # Query for exchange-like addresses with proper datetime
        from datetime import datetime, timedelta
        since_time = (datetime.now() - timedelta(hours=hours_back)).isoformat() + "Z"
        
        query = """
        query GetExchangeFlows($sinceTime: ISO8601DateTime!) {
          ethereum(network: ethereum) {
            transfers(
              currency: {is: "0x0000000000000000000000000000000000000000"}
              amount: {gt: 10.0}
              time: {since: $sinceTime}
              options: {desc: "date.date", limit: 100, offset: 0}
            ) {
              amount
              sender {
                address
                annotation
              }
              receiver {
                address
                annotation
              }
              transaction {
                hash
              }
              date { date }
            }
          }
        }
        """
        
        variables = {
            "sinceTime": since_time
        }
        
        try:
            aggregated: List[Dict[str, Any]] = []
            # paginate up to 1000 rows in chunks of 100
            for offset in range(0, 1000, 100):
                self._rate_limit()
                q = query.replace("offset: 0", f"offset: {offset}")
                response = requests.post(
                    self.base_url,
                    json={"query": q, "variables": variables},
                    headers=self._get_headers(),
                    timeout=30
                )
                if response.status_code != 200:
                    self.logger.error(f"Bitquery API error (page {offset}): {response.status_code} - {response.text}")
                    break
                data = response.json()
                if "errors" in data:
                    self.logger.error(f"Bitquery GraphQL errors (page {offset}): {data['errors']}")
                    break
                page_rows = data.get("data", {}).get("ethereum", {}).get("transfers", [])
                aggregated.extend(page_rows)
                if len(page_rows) < 100:
                    break
            self.logger.info(f"Bitquery aggregated {len(aggregated)} transfers for exchange analysis")
            exchange_flows = self._analyze_exchange_patterns(aggregated)
            return exchange_flows
        except Exception as e:
            self.logger.error(f"Error querying Bitquery API: {e}")
            return {}
    
    def _analyze_exchange_patterns(self, transfers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze transfers for exchange patterns
        """
        exchange_addresses = {}
        # Curated list of known exchange wallet addresses (sample subset)
        seed_addresses = [
            # Binance
            "0x28c6c06298d514db089934071355e5743bf21d60",
            "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
            # Coinbase
            "0x503828976d22510aad0201ac7ec88293211d23da",
            "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",
            # Kraken
            "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13",
            # Bitfinex
            "0x742d35cc6634c0532925a3b844bc454e4438f44e",
            # OKX
            "0x8d12a197cb00d4747a1fe03395095ce2a5cc6819",
            # Huobi
            "0xdc76cd25977e0a5ae17155770273ad58648900d3",
            # Bybit (example)
            "0x67b7f3f69ef2d3b5a793bcee66475d27c7f7346a",
        ]
        file_addresses = self._load_known_addresses()
        known_exchange_addresses = set([a.lower() for a in seed_addresses + file_addresses])
        total_inflow = 0.0
        total_outflow = 0.0
        
        keywords = [
            "exchange", "binance", "coinbase", "kraken", "okx", "bybit",
            "huobi", "bitfinex", "bitstamp", "kucoin", "gate.io", "mexc"
        ]
        def is_exchange_annot(s: str) -> bool:
            s = (s or "").lower()
            return any(k in s for k in keywords)

        for transfer in transfers:
            sender = transfer.get("sender", {})
            receiver = transfer.get("receiver", {})
            amount = float(transfer.get("amount", 0))
            
            # Check sender annotation for exchange
            sender_annotation = sender.get("annotation", "")
            sender_addr = (sender.get("address", "") or "").lower()
            if is_exchange_annot(sender_annotation) or sender_addr in known_exchange_addresses:
                addr = sender.get("address", "")
                if addr not in exchange_addresses:
                    exchange_addresses[addr] = {"inflow": 0, "outflow": 0, "name": sender_annotation or "known_exchange"}
                exchange_addresses[addr]["outflow"] += amount
                total_outflow += amount
            
            # Check receiver annotation for exchange
            receiver_annotation = receiver.get("annotation", "")
            receiver_addr = (receiver.get("address", "") or "").lower()
            if is_exchange_annot(receiver_annotation) or receiver_addr in known_exchange_addresses:
                addr = receiver.get("address", "")
                if addr not in exchange_addresses:
                    exchange_addresses[addr] = {"inflow": 0, "outflow": 0, "name": receiver_annotation or "known_exchange"}
                exchange_addresses[addr]["inflow"] += amount
                total_inflow += amount
        
        return {
            "exchange_addresses": exchange_addresses,
            "total_exchanges": len(exchange_addresses),
            "inflow": total_inflow,
            "outflow": total_outflow,
            "net_flow": total_outflow - total_inflow,
            "timestamp": datetime.now().isoformat()
        }

# Test the fixed Bitquery API
if __name__ == "__main__":
    print("🔍 TESTING FIXED BITQUERY API")
    print("=" * 50)
    
    api = FixedBitqueryAPI()
    
    # Test 1: Large transactions
    print("Test 1: Large transactions")
    transactions = api.get_large_eth_transactions(min_eth=100, hours_back=6)
    print(f"✅ Found {len(transactions)} transactions")
    
    for i, tx in enumerate(transactions[:3]):
        amount = float(tx.get("amount", 0))
        sender = tx.get("sender", {}).get("address", "Unknown")
        receiver = tx.get("receiver", {}).get("address", "Unknown")
        print(f"  {i+1}. {amount:.2f} ETH: {sender[:10]}... -> {receiver[:10]}...")
    
    print("\n" + "=" * 50)
    
    # Test 2: Exchange flows
    print("Test 2: Exchange flows")
    flows = api.get_exchange_flows(hours_back=6)
    print(f"✅ Found {flows.get('total_exchanges', 0)} exchange addresses")
    
    for addr, data in flows.get("exchange_addresses", {}).items():
        print(f"  • {data.get('name', 'Unknown')}: In={data['inflow']:.2f}, Out={data['outflow']:.2f}")
