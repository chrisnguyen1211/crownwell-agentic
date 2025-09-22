#!/usr/bin/env python3
"""
Enhanced Etherscan API client for large ETH transactions
"""
import requests
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EtherscanTransactionTracker:
    """
    Enhanced Etherscan API client for large ETH transactions
    Primary data source for Yasuo
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        self.base_url = "https://api.etherscan.io/api"
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 0.2  # 5 requests per second max
        
    def _rate_limit(self):
        """Simple rate limiting"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                import time
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = datetime.now()
    
    def get_large_transactions(self, min_eth: float = 1000, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get large ETH transactions using Etherscan API
        """
        if not self.api_key:
            self.logger.warning("No Etherscan API key available")
            return []
        
        try:
            # Get latest block number
            latest_block = self._get_latest_block()
            if not latest_block:
                return []
            
            # Calculate start block (approx 1 block per 12 seconds)
            blocks_per_hour = 300  # 3600/12
            start_block = latest_block - (hours_back * blocks_per_hour)
            
            self.logger.info(f"Scanning blocks {start_block} to {latest_block} for large transactions")
            
            large_transactions = []
            
            # Sample blocks to find large transactions
            # Increase sampling density to improve exchange flow detection
            block_step = max(1, (latest_block - start_block) // 200)  # Sample ~200 blocks
            
            for block_num in range(start_block, latest_block + 1, block_step):
                transactions = self._get_block_transactions(block_num)
                
                for tx in transactions:
                    if self._is_large_transaction(tx, min_eth):
                        large_transactions.append(self._format_transaction(tx))
                
                # Rate limiting
                self._rate_limit()
            
            self.logger.info(f"Found {len(large_transactions)} large transactions")
            return large_transactions
            
        except Exception as e:
            self.logger.error(f"Error getting large transactions: {e}")
            return []
    
    def _get_latest_block(self) -> Optional[int]:
        """Get latest block number with retries"""
        params = {
            "module": "proxy",
            "action": "eth_blockNumber",
            "apikey": self.api_key
        }
        for attempt in range(3):
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result"):
                        return int(data["result"], 16)
            except Exception as e:
                self.logger.warning(f"Attempt {attempt+1}/3 failed to get latest block: {e}")
                self._rate_limit()
                continue
        self.logger.error("Failed to get latest block after retries")
        return None
    
    def _get_block_transactions(self, block_num: int) -> List[Dict[str, Any]]:
        """Get transactions from a specific block with retries"""
        params = {
            "module": "proxy",
            "action": "eth_getBlockByNumber",
            "tag": hex(block_num),
            "boolean": "true",
            "apikey": self.api_key
        }
        for attempt in range(3):
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result") and data["result"].get("transactions"):
                        return data["result"]["transactions"]
            except Exception as e:
                self.logger.warning(f"Attempt {attempt+1}/3 block {block_num} failed: {e}")
                self._rate_limit()
                continue
        self.logger.error(f"Failed to get transactions for block {block_num} after retries")
        return []
    
    def _is_large_transaction(self, tx: Dict[str, Any], min_eth: float) -> bool:
        """Check if transaction is large enough"""
        try:
            value_wei = int(tx.get("value", "0x0"), 16)
            value_eth = value_wei / 1e18
            return value_eth >= min_eth
        except:
            return False
    
    def _format_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Format transaction data for Yasuo"""
        try:
            value_wei = int(tx.get("value", "0x0"), 16)
            value_eth = value_wei / 1e18
            
            return {
                "amount": value_eth,
                "sender": {
                    "address": tx.get("from", ""),
                    "annotation": None
                },
                "receiver": {
                    "address": tx.get("to", ""),
                    "annotation": None
                },
                "transaction": {
                    "hash": tx.get("hash", "")
                },
                "data_source": "etherscan"
            }
        except Exception as e:
            self.logger.error(f"Error formatting transaction: {e}")
            return {}

    def get_exchange_flows(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get exchange flows using Etherscan API
        """
        if not self.api_key:
            self.logger.warning("No Etherscan API key available")
            return {"error": "No API key", "net_flow": 0}
        
        try:
            # Known exchange addresses (simplified list)
            exchange_addresses = {
                "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE": "Binance",
                "0x28C6c06298d514Db089934071355E5743bf21d60": "Binance 2",
                "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549": "Binance 3",
                "0x56Eddb7aa87536c09CCc2793473599fD21A8b17F": "Binance 4",
                "0x564286362092D8e7936f0549571a803B203aAceD": "Binance 5"
            }
            # Normalize mapping to lowercase for robust matching
            exchange_addresses = {addr.lower(): name for addr, name in exchange_addresses.items()}
            
            # Get large transactions (lower threshold to capture more flows)
            large_txs = self.get_large_transactions(min_eth=50, hours_back=hours_back)
            
            # Calculate exchange flows
            exchange_flows = {}
            total_inflow = 0
            total_outflow = 0
            
            for tx in large_txs:
                from_addr = (tx.get("sender", {}) or {}).get("address", "").lower()
                to_addr = (tx.get("receiver", {}) or {}).get("address", "").lower()
                amount = float(tx.get("amount", 0))
                
                # Check if from exchange
                if from_addr in exchange_addresses:
                    if from_addr not in exchange_flows:
                        exchange_flows[from_addr] = {"inflow": 0, "outflow": 0, "name": exchange_addresses[from_addr]}
                    exchange_flows[from_addr]["outflow"] += amount
                    total_outflow += amount
                
                # Check if to exchange
                if to_addr in exchange_addresses:
                    if to_addr not in exchange_flows:
                        exchange_flows[to_addr] = {"inflow": 0, "outflow": 0, "name": exchange_addresses[to_addr]}
                    exchange_flows[to_addr]["inflow"] += amount
                    total_inflow += amount
            
            return {
                "exchange_addresses": exchange_flows,
                "total_exchanges": len(exchange_flows),
                "inflow": total_inflow,
                "outflow": total_outflow,
                "net_flow": total_outflow - total_inflow,
                "data_source": "etherscan_exchange_flows",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting exchange flows: {e}")
            return {"error": str(e), "net_flow": 0}

# Test the new tracker
if __name__ == "__main__":
    print("🔍 Testing Enhanced Etherscan Tracker")
    print("=" * 50)
    
    tracker = EtherscanTransactionTracker()
    transactions = tracker.get_large_transactions(min_eth=100, hours_back=6)
    
    print(f"Found {len(transactions)} transactions")
    
    for i, tx in enumerate(transactions[:5]):
        amount = tx.get("amount", 0)
        sender = tx.get("sender", {}).get("address", "Unknown")
        receiver = tx.get("receiver", {}).get("address", "Unknown")
        print(f"{i+1}. {amount:.2f} ETH: {sender[:10]}... -> {receiver[:10]}...")
