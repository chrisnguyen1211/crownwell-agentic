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
            block_step = max(1, (latest_block - start_block) // 50)  # Sample 50 blocks
            
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
        """Get latest block number"""
        try:
            params = {
                "module": "proxy",
                "action": "eth_blockNumber",
                "apikey": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("result"):
                    return int(data["result"], 16)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting latest block: {e}")
            return None
    
    def _get_block_transactions(self, block_num: int) -> List[Dict[str, Any]]:
        """Get transactions from a specific block"""
        try:
            params = {
                "module": "proxy",
                "action": "eth_getBlockByNumber",
                "tag": hex(block_num),
                "boolean": "true",
                "apikey": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("result") and data["result"].get("transactions"):
                    return data["result"]["transactions"]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting block {block_num} transactions: {e}")
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
