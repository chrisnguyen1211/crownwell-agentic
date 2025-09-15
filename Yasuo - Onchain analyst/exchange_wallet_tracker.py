#!/usr/bin/env python3
"""
Enhanced Exchange Wallet Tracking for ETH In/Out Flows
Focus on exchange wallets for better flow analysis
"""
import requests
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

load_dotenv()

class ExchangeWalletTracker:
    """
    Enhanced tracker focusing on exchange wallets for ETH flows
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        self.base_url = "https://api.etherscan.io/api"
        self.logger = logging.getLogger(__name__)
        
        # Major exchange wallets (known addresses)
        self.exchange_wallets = {
            # Binance
            "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance Hot Wallet",
            "0xd551234ae421e3bcba99a0da6d736074f22192ff": "Binance Cold Wallet",
            "0x564286362092d8e7936f0549571a803b203aaced": "Binance Wallet",
            
            # Coinbase
            "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase Wallet",
            "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase Wallet",
            "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Coinbase Wallet",
            
            # Kraken
            "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "Kraken Wallet",
            "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13": "Kraken Wallet",
            
            # Huobi
            "0xab83d182f3485cf1d6ccdd34c7cfef95b4c08da4": "Huobi Wallet",
            "0x6748f50f686bfbca6fe8ad62b22228b87f31ff2b": "Huobi Wallet",
            
            # OKX
            "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKX Wallet",
            "0x236f9f97e0e62388479bf9e5ba4889e46b0273c3": "OKX Wallet",
            
            # Bitfinex
            "0x7727e5113d1d161373623e5f49fd568b4f543a9e": "Bitfinex Wallet",
            "0x4fdd92bd67acf3083d34fbd83a336f0b1b6c1e22": "Bitfinex Wallet",
        }
        
        # Exchange-like patterns (heuristics)
        self.exchange_patterns = {
            "high_frequency": 100,  # >100 transactions per day
            "large_volume": 1000,   # >1000 ETH daily volume
            "multiple_addresses": 50,  # Interacts with >50 addresses
        }
    
    def get_exchange_flows(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get ETH flows for known exchange wallets
        """
        if not self.api_key:
            self.logger.warning("No Etherscan API key available")
            return {}
        
        try:
            self.logger.info(f"Tracking exchange flows for {len(self.exchange_wallets)} wallets")
            
            flows = {
                "exchanges": {},
                "total_inflow": 0,
                "total_outflow": 0,
                "net_flow": 0,
                "timestamp": datetime.now().isoformat()
            }
            
            for wallet_address, exchange_name in self.exchange_wallets.items():
                exchange_data = self._analyze_exchange_wallet(wallet_address, exchange_name, hours_back)
                if exchange_data:
                    flows["exchanges"][exchange_name] = exchange_data
                    flows["total_inflow"] += exchange_data.get("inflow", 0)
                    flows["total_outflow"] += exchange_data.get("outflow", 0)
            
            flows["net_flow"] = flows["total_inflow"] - flows["total_outflow"]
            
            self.logger.info(f"Exchange flows: In={flows['total_inflow']:.2f} ETH, Out={flows['total_outflow']:.2f} ETH, Net={flows['net_flow']:.2f} ETH")
            return flows
            
        except Exception as e:
            self.logger.error(f"Error getting exchange flows: {e}")
            return {}
    
    def _analyze_exchange_wallet(self, wallet_address: str, exchange_name: str, hours_back: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a specific exchange wallet
        """
        try:
            # Get recent transactions
            transactions = self._get_wallet_transactions(wallet_address, hours_back)
            
            if not transactions:
                return None
            
            inflow = 0
            outflow = 0
            large_transactions = []
            
            for tx in transactions:
                amount_eth = tx.get("amount_eth", 0)
                
                if tx.get("direction") == "in":
                    inflow += amount_eth
                else:
                    outflow += amount_eth
                
                # Track large transactions (>100 ETH)
                if amount_eth > 100:
                    large_transactions.append({
                        "amount": amount_eth,
                        "direction": tx.get("direction"),
                        "from": tx.get("from"),
                        "to": tx.get("to"),
                        "timestamp": tx.get("timestamp")
                    })
            
            return {
                "address": wallet_address,
                "inflow": inflow,
                "outflow": outflow,
                "net_flow": inflow - outflow,
                "transaction_count": len(transactions),
                "large_transactions": large_transactions,
                "exchange_name": exchange_name
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {exchange_name}: {e}")
            return None
    
    def _get_wallet_transactions(self, wallet_address: str, hours_back: int) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific wallet
        """
        try:
            # Get latest block
            latest_block = self._get_latest_block()
            if not latest_block:
                return []
            
            # Calculate start block
            blocks_per_hour = 300
            start_block = latest_block - (hours_back * blocks_per_hour)
            
            transactions = []
            
            # Get transactions where wallet is sender or receiver
            params = {
                "module": "account",
                "action": "txlist",
                "address": wallet_address,
                "startblock": start_block,
                "endblock": latest_block,
                "sort": "desc",
                "apikey": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    tx_list = data.get("result", [])
                    
                    for tx in tx_list:
                        # Only ETH transfers (value > 0)
                        value_wei = int(tx.get("value", "0"))
                        if value_wei > 0:
                            amount_eth = value_wei / 1e18
                            
                            # Determine direction
                            if tx.get("from", "").lower() == wallet_address.lower():
                                direction = "out"
                                from_addr = wallet_address
                                to_addr = tx.get("to", "")
                            else:
                                direction = "in"
                                from_addr = tx.get("from", "")
                                to_addr = wallet_address
                            
                            transactions.append({
                                "amount_eth": amount_eth,
                                "direction": direction,
                                "from": from_addr,
                                "to": to_addr,
                                "timestamp": tx.get("timeStamp"),
                                "hash": tx.get("hash")
                            })
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting transactions for {wallet_address}: {e}")
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

# Test the exchange tracker
if __name__ == "__main__":
    print("🔍 TESTING EXCHANGE WALLET TRACKER")
    print("=" * 60)
    
    tracker = ExchangeWalletTracker()
    flows = tracker.get_exchange_flows(hours_back=6)  # Last 6 hours
    
    print(f"📊 EXCHANGE FLOWS SUMMARY:")
    print(f"• Total Inflow: {flows.get('total_inflow', 0):.2f} ETH")
    print(f"• Total Outflow: {flows.get('total_outflow', 0):.2f} ETH")
    print(f"• Net Flow: {flows.get('net_flow', 0):.2f} ETH")
    print(f"• Exchanges Tracked: {len(flows.get('exchanges', {}))}")
    
    print(f"\n📈 EXCHANGE BREAKDOWN:")
    for exchange_name, data in flows.get("exchanges", {}).items():
        print(f"• {exchange_name}:")
        print(f"  - Inflow: {data.get('inflow', 0):.2f} ETH")
        print(f"  - Outflow: {data.get('outflow', 0):.2f} ETH")
        print(f"  - Net: {data.get('net_flow', 0):.2f} ETH")
        print(f"  - Large TX: {len(data.get('large_transactions', []))}")
    
    print(f"\n🎯 INTERPRETATION:")
    net_flow = flows.get('net_flow', 0)
    if net_flow > 1000:
        print("🟢 Strong accumulation (exchanges losing ETH)")
    elif net_flow < -1000:
        print("🔴 Strong selling pressure (exchanges gaining ETH)")
    else:
        print("⚪ Balanced flows (consolidation)")






