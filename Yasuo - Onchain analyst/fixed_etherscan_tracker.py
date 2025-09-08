#!/usr/bin/env python3
"""
Fixed Etherscan Transaction Tracker
Resolves exchange flow and large transaction issues
"""
import requests
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

load_dotenv()

class FixedEtherscanTracker:
    """
    Fixed Etherscan tracker with proper API key handling
    """
    
    def __init__(self, api_key: Optional[str] = None, min_eth_amount: float = 1000):
        self.etherscan_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        self.base_url = "https://api.etherscan.io/api"
        self.logger = logging.getLogger(__name__)
        self.min_eth_amount = min_eth_amount
        
        if not self.etherscan_key:
            self.logger.error("❌ No Etherscan API key provided")
        else:
            self.logger.info(f"✅ Etherscan API key loaded: {self.etherscan_key[:8]}...")
    
    def get_latest_block(self) -> Optional[int]:
        """
        Get latest block number
        """
        try:
            params = {
                'module': 'proxy',
                'action': 'eth_blockNumber',
                'apikey': self.etherscan_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'result' in data:
                block_number = int(data['result'], 16)
                self.logger.info(f"✅ Latest block: {block_number}")
                return block_number
            else:
                self.logger.error(f"❌ Error getting latest block: {data}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting latest block: {e}")
            return None
    
    def get_large_transactions(self, min_eth: float = 1000, hours_back: int = 24) -> List[Dict]:
        """
        Get large ETH transactions using Etherscan API
        """
        if not self.etherscan_key:
            self.logger.error("❌ No Etherscan API key available")
            return []
        
        try:
            # Get latest block
            latest_block = self.get_latest_block()
            if not latest_block:
                return []
            
            # Calculate blocks to scan (assuming 12s per block)
            blocks_per_hour = 300  # 3600s / 12s
            blocks_to_scan = hours_back * blocks_per_hour
            start_block = max(0, latest_block - blocks_to_scan)
            
            self.logger.info(f"📊 Scanning blocks {start_block} to {latest_block}")
            
            # Get transactions in batches
            all_transactions = []
            batch_size = 1000  # Etherscan limit
            
            for start in range(start_block, latest_block, batch_size):
                end = min(start + batch_size - 1, latest_block)
                
                # Get block range
                params = {
                    'module': 'proxy',
                    'action': 'eth_getLogs',
                    'fromBlock': hex(start),
                    'toBlock': hex(end),
                    'address': '0x0000000000000000000000000000000000000000',  # ETH contract
                    'apikey': self.etherscan_key
                }
                
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                if 'result' in data:
                    logs = data['result']
                    self.logger.info(f"📊 Found {len(logs)} logs in blocks {start}-{end}")
                    
                    # Process logs for large transfers
                    for log in logs:
                        if len(log.get('data', '')) >= 66:  # Minimum data length
                            try:
                                # Parse transfer data
                                amount_hex = log['data'][2:66]  # Remove '0x' and get first 32 bytes
                                amount_wei = int(amount_hex, 16)
                                amount_eth = amount_wei / 1e18
                                
                                if amount_eth >= min_eth:
                                    transaction = {
                                        'amount': amount_eth,
                                        'sender': log.get('topics', [''])[1] if len(log.get('topics', [])) > 1 else 'unknown',
                                        'receiver': log.get('topics', [''])[2] if len(log.get('topics', [])) > 2 else 'unknown',
                                        'block_number': int(log.get('blockNumber', '0x0'), 16),
                                        'transaction_hash': log.get('transactionHash', 'unknown'),
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    all_transactions.append(transaction)
                                    
                            except Exception as e:
                                self.logger.debug(f"⚠️ Error parsing log: {e}")
                                continue
                
                # Rate limiting
                import time
                time.sleep(0.2)
            
            # Sort by amount descending
            all_transactions.sort(key=lambda x: x['amount'], reverse=True)
            
            self.logger.info(f"✅ Found {len(all_transactions)} large transactions")
            return all_transactions[:50]  # Return top 50
            
        except Exception as e:
            self.logger.error(f"❌ Error getting large transactions: {e}")
            return []
    
    def get_exchange_flows(self, exchange_addresses: List[str], hours_back: int = 24) -> Dict:
        """
        Get exchange flows for specific addresses
        """
        if not self.etherscan_key:
            self.logger.error("❌ No Etherscan API key available")
            return {"net_flow": 0, "exchanges": {}}
        
        try:
            # Get latest block
            latest_block = self.get_latest_block()
            if not latest_block:
                return {"net_flow": 0, "exchanges": {}}
            
            # Calculate blocks to scan
            blocks_per_hour = 300
            blocks_to_scan = hours_back * blocks_per_hour
            start_block = max(0, latest_block - blocks_to_scan)
            
            exchange_flows = {}
            total_inflow = 0
            total_outflow = 0
            
            for exchange_address in exchange_addresses:
                self.logger.info(f"📊 Analyzing exchange: {exchange_address}")
                
                # Get transactions to/from this address
                inflow = self._get_address_flows(exchange_address, start_block, latest_block, 'in')
                outflow = self._get_address_flows(exchange_address, start_block, latest_block, 'out')
                
                net_flow = outflow - inflow
                
                exchange_flows[exchange_address] = {
                    'inflow': inflow,
                    'outflow': outflow,
                    'net_flow': net_flow,
                    'wallet_count': 1
                }
                
                total_inflow += inflow
                total_outflow += outflow
            
            return {
                'net_flow': total_outflow - total_inflow,
                'total_inflow': total_inflow,
                'total_outflow': total_outflow,
                'exchanges': exchange_flows,
                'analysis_period': f"{hours_back} hours"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting exchange flows: {e}")
            return {"net_flow": 0, "exchanges": {}}
    
    def _get_address_flows(self, address: str, start_block: int, end_block: int, direction: str) -> float:
        """
        Get flows for a specific address
        """
        try:
            # Get transactions for this address
            params = {
                'module': 'account',
                'action': 'txlist' if direction == 'out' else 'txlistinternal',
                'address': address,
                'startblock': start_block,
                'endblock': end_block,
                'sort': 'desc',
                'apikey': self.etherscan_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'result' in data and data['result']:
                total_eth = 0
                for tx in data['result']:
                    try:
                        value_wei = int(tx.get('value', '0'))
                        value_eth = value_wei / 1e18
                        total_eth += value_eth
                    except:
                        continue
                
                return total_eth
            else:
                return 0
                
        except Exception as e:
            self.logger.debug(f"⚠️ Error getting flows for {address}: {e}")
            return 0

# Test function
def main():
    print("🔧 FIXED ETHERSCAN TRACKER TEST")
    print("=" * 50)
    
    tracker = FixedEtherscanTracker()
    
    # Test large transactions
    print("📈 Testing large transactions...")
    large_tx = tracker.get_large_transactions(min_eth=1000, hours_back=24)
    print(f"✅ Found {len(large_tx)} large transactions")
    
    if large_tx:
        print("Top 3 transactions:")
        for i, tx in enumerate(large_tx[:3]):
            print(f"  {i+1}. {tx['amount']:.2f} ETH: {tx['sender'][:10]}... -> {tx['receiver'][:10]}...")
    
    # Test exchange flows
    print("\n📊 Testing exchange flows...")
    exchange_addresses = [
        "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE",  # Binance
        "0x28C6c06298d514Db089934071355E5743bf21d60",  # Binance 2
        "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549",  # Binance 3
    ]
    
    flows = tracker.get_exchange_flows(exchange_addresses, hours_back=24)
    print(f"✅ Exchange flows: {flows['net_flow']:.2f} ETH net flow")

if __name__ == "__main__":
    main()



