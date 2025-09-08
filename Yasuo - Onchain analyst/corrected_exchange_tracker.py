#!/usr/bin/env python3
"""
Fixed Exchange Flow Interpretation
Outflow = Positive (Accumulation) - People buying and withdrawing from exchanges
Inflow = Negative (Selling) - People depositing to exchanges to sell
"""
import requests
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import time

load_dotenv()

class CorrectExchangeTracker:
    """
    Exchange tracker with CORRECT interpretation:
    - Outflow = POSITIVE (Accumulation) - People withdrawing from exchanges
    - Inflow = NEGATIVE (Selling) - People depositing to exchanges
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        self.base_url = "https://api.etherscan.io/api"
        self.logger = logging.getLogger(__name__)
        
        # Enhanced exchange wallet database
        self.exchange_wallets = {
            # Binance (Multiple wallets)
            "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": {"name": "Binance Hot Wallet", "exchange": "Binance"},
            "0xd551234ae421e3bcba99a0da6d736074f22192ff": {"name": "Binance Cold Wallet", "exchange": "Binance"},
            "0x564286362092d8e7936f0549571a803b203aaced": {"name": "Binance Wallet", "exchange": "Binance"},
            "0x28c6c06298d514db089934071355e5743bf21d60": {"name": "Binance Wallet 2", "exchange": "Binance"},
            
            # Coinbase (Multiple wallets)
            "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": {"name": "Coinbase Wallet", "exchange": "Coinbase"},
            "0x503828976d22510aad0201ac7ec88293211d23da": {"name": "Coinbase Wallet 2", "exchange": "Coinbase"},
            "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": {"name": "Coinbase Wallet 3", "exchange": "Coinbase"},
            "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": {"name": "Coinbase Wallet 4", "exchange": "Coinbase"},
            
            # Kraken
            "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": {"name": "Kraken Wallet", "exchange": "Kraken"},
            "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13": {"name": "Kraken Wallet 2", "exchange": "Kraken"},
            
            # Huobi
            "0xab83d182f3485cf1d6ccdd34c7cfef95b4c08da4": {"name": "Huobi Wallet", "exchange": "Huobi"},
            "0x6748f50f686bfbca6fe8ad62b22228b87f31ff2b": {"name": "Huobi Wallet 2", "exchange": "Huobi"},
            
            # OKX
            "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": {"name": "OKX Wallet", "exchange": "OKX"},
            "0x236f9f97e0e62388479bf9e5ba4889e46b0273c3": {"name": "OKX Wallet 2", "exchange": "OKX"},
            
            # Bitfinex
            "0x7727e5113d1d161373623e5f49fd568b4f543a9e": {"name": "Bitfinex Wallet", "exchange": "Bitfinex"},
            "0x4fdd92bd67acf3083d34fbd83a336f0b1b6c1e22": {"name": "Bitfinex Wallet 2", "exchange": "Bitfinex"},
            
            # Additional major exchanges
            "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa": {"name": "FTX Wallet", "exchange": "FTX"},
            "0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2": {"name": "FTX Wallet 2", "exchange": "FTX"},
            "0xc098b2a3aa256d2140208c3de6543aaef5cd3a94": {"name": "Gate.io Wallet", "exchange": "Gate.io"},
            "0x0d0707963952f2fba59dd06f2b425ace40b492fe": {"name": "Gate.io Wallet 2", "exchange": "Gate.io"},
        }
        
        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 0.2
    
    def _rate_limit(self):
        """Rate limiting"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def get_daily_exchange_flows(self) -> Dict[str, Any]:
        """
        Get daily exchange flows with CORRECT interpretation
        """
        if not self.api_key:
            self.logger.warning("No Etherscan API key available")
            return {}
        
        try:
            self.logger.info(f"Analyzing {len(self.exchange_wallets)} exchange wallets for daily flows")
            
            # Get latest block
            latest_block = self._get_latest_block()
            if not latest_block:
                return {}
            
            # Calculate 24-hour period (1 day)
            blocks_per_hour = 300
            hours_back = 24
            start_block = latest_block - (hours_back * blocks_per_hour)
            
            flows = {
                "exchanges": {},
                "total_outflow": 0,  # POSITIVE = Accumulation
                "total_inflow": 0,   # NEGATIVE = Selling
                "net_flow": 0,       # Positive = Net Accumulation, Negative = Net Selling
                "timestamp": datetime.now().isoformat(),
                "analysis_period": "24 hours (1 day)",
                "block_range": f"{start_block} to {latest_block}"
            }
            
            # Process exchanges in batches
            batch_size = 5
            wallet_list = list(self.exchange_wallets.items())
            
            for i in range(0, len(wallet_list), batch_size):
                batch = wallet_list[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(wallet_list) + batch_size - 1)//batch_size}")
                
                for wallet_address, wallet_info in batch:
                    exchange_data = self._analyze_exchange_wallet_daily(
                        wallet_address, wallet_info, start_block, latest_block
                    )
                    
                    if exchange_data:
                        exchange_name = wallet_info["exchange"]
                        if exchange_name not in flows["exchanges"]:
                            flows["exchanges"][exchange_name] = {
                                "outflow": 0,      # POSITIVE = Accumulation
                                "inflow": 0,       # NEGATIVE = Selling
                                "net_flow": 0,     # Positive = Net Accumulation
                                "wallet_count": 0,
                                "large_transactions": []
                            }
                        
                        flows["exchanges"][exchange_name]["outflow"] += exchange_data.get("outflow", 0)
                        flows["exchanges"][exchange_name]["inflow"] += exchange_data.get("inflow", 0)
                        flows["exchanges"][exchange_name]["wallet_count"] += 1
                        flows["exchanges"][exchange_name]["large_transactions"].extend(
                            exchange_data.get("large_transactions", [])
                        )
                        
                        flows["total_outflow"] += exchange_data.get("outflow", 0)
                        flows["total_inflow"] += exchange_data.get("inflow", 0)
                
                self._rate_limit()
            
            # Calculate net flows with CORRECT interpretation
            flows["net_flow"] = flows["total_outflow"] - flows["total_inflow"]
            
            for exchange_name in flows["exchanges"]:
                exchange_data = flows["exchanges"][exchange_name]
                exchange_data["net_flow"] = exchange_data["outflow"] - exchange_data["inflow"]
            
            self.logger.info(f"Daily exchange analysis complete: Net flow = {flows['net_flow']:.2f} ETH")
            return flows
            
        except Exception as e:
            self.logger.error(f"Error in daily exchange analysis: {e}")
            return {}
    
    def _analyze_exchange_wallet_daily(self, wallet_address: str, wallet_info: Dict[str, str], 
                                     start_block: int, end_block: int) -> Optional[Dict[str, Any]]:
        """
        Analyze exchange wallet for daily flows with CORRECT interpretation
        """
        try:
            transactions = self._get_wallet_transactions_daily(wallet_address, start_block, end_block)
            
            if not transactions:
                return None
            
            outflow = 0  # POSITIVE = People withdrawing (accumulation)
            inflow = 0   # NEGATIVE = People depositing (selling)
            large_transactions = []
            
            for tx in transactions:
                amount_eth = tx.get("amount_eth", 0)
                
                if tx.get("direction") == "out":
                    # Exchange sending ETH out = People withdrawing = ACCUMULATION (POSITIVE)
                    outflow += amount_eth
                else:
                    # Exchange receiving ETH = People depositing = SELLING (NEGATIVE)
                    inflow += amount_eth
                
                # Track large transactions (>500 ETH)
                if amount_eth > 500:
                    large_transactions.append({
                        "amount": amount_eth,
                        "direction": tx.get("direction"),
                        "from": tx.get("from"),
                        "to": tx.get("to"),
                        "timestamp": tx.get("timestamp"),
                        "wallet_name": wallet_info["name"],
                        "interpretation": "Accumulation" if tx.get("direction") == "out" else "Selling"
                    })
            
            return {
                "address": wallet_address,
                "name": wallet_info["name"],
                "exchange": wallet_info["exchange"],
                "outflow": outflow,      # POSITIVE = Accumulation
                "inflow": inflow,        # NEGATIVE = Selling
                "net_flow": outflow - inflow,  # Positive = Net Accumulation
                "transaction_count": len(transactions),
                "large_transactions": large_transactions
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {wallet_info['name']}: {e}")
            return None
    
    def _get_wallet_transactions_daily(self, wallet_address: str, start_block: int, end_block: int) -> List[Dict[str, Any]]:
        """
        Get daily transactions for wallet
        """
        try:
            params = {
                "module": "account",
                "action": "txlist",
                "address": wallet_address,
                "startblock": start_block,
                "endblock": end_block,
                "sort": "desc",
                "apikey": self.api_key
            }
            
            self._rate_limit()
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    tx_list = data.get("result", [])
                    
                    transactions = []
                    for tx in tx_list:
                        value_wei = int(tx.get("value", "0"))
                        if value_wei > 0:  # Only ETH transfers
                            amount_eth = value_wei / 1e18
                            
                            # Determine direction
                            if tx.get("from", "").lower() == wallet_address.lower():
                                direction = "out"  # Exchange sending = People withdrawing
                                from_addr = wallet_address
                                to_addr = tx.get("to", "")
                            else:
                                direction = "in"   # Exchange receiving = People depositing
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
            
            return []
            
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

# Test the corrected exchange tracker
if __name__ == "__main__":
    print("🔍 TESTING CORRECTED EXCHANGE TRACKER")
    print("=" * 60)
    
    tracker = CorrectExchangeTracker()
    flows = tracker.get_daily_exchange_flows()
    
    print(f"📊 DAILY EXCHANGE FLOWS (CORRECTED INTERPRETATION):")
    print(f"• Analysis Period: {flows.get('analysis_period', 'Unknown')}")
    print(f"• Block Range: {flows.get('block_range', 'Unknown')}")
    print(f"• Total Outflow: {flows.get('total_outflow', 0):.2f} ETH (Accumulation)")
    print(f"• Total Inflow: {flows.get('total_inflow', 0):.2f} ETH (Selling)")
    print(f"• Net Flow: {flows.get('net_flow', 0):.2f} ETH")
    print(f"• Exchanges Analyzed: {len(flows.get('exchanges', {}))}")
    
    print(f"\n📈 EXCHANGE BREAKDOWN:")
    for exchange_name, data in flows.get("exchanges", {}).items():
        print(f"• {exchange_name}:")
        print(f"  - Wallets: {data.get('wallet_count', 0)}")
        print(f"  - Outflow: {data.get('outflow', 0):.2f} ETH (Accumulation)")
        print(f"  - Inflow: {data.get('inflow', 0):.2f} ETH (Selling)")
        print(f"  - Net: {data.get('net_flow', 0):.2f} ETH")
        print(f"  - Large TX: {len(data.get('large_transactions', []))}")
    
    print(f"\n🎯 CORRECTED MARKET INTERPRETATION:")
    net_flow = flows.get('net_flow', 0)
    if net_flow > 5000:
        print("🟢 STRONG ACCUMULATION: More people withdrawing than depositing (BULLISH)")
    elif net_flow < -5000:
        print("🔴 STRONG SELLING: More people depositing than withdrawing (BEARISH)")
    elif net_flow > 1000:
        print("🟡 MODERATE ACCUMULATION: Slight bullish pressure")
    elif net_flow < -1000:
        print("🟡 MODERATE SELLING: Slight bearish pressure")
    else:
        print("⚪ BALANCED FLOWS: Consolidation phase")



