#!/usr/bin/env python3
"""
🛡️ DUNE WHALE INTELLIGENCE TRACKER
Advanced whale tracking using Dune Analytics API

Features:
- Real-time whale wallet monitoring
- Large transaction analysis
- Portfolio tracking
- Market impact assessment
- Integration with Yasuo's analysis engine
"""

import os
import json
import logging
import asyncio
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from dataclasses import dataclass

@dataclass
class WhaleWallet:
    """Whale wallet data structure"""
    address: str
    label: str
    balance_eth: float
    balance_usd: float
    last_activity: datetime
    transaction_count: int
    portfolio_value: float
    risk_level: str

@dataclass
class WhaleTransaction:
    """Whale transaction data structure"""
    hash: str
    from_address: str
    to_address: str
    value_eth: float
    value_usd: float
    timestamp: datetime
    gas_used: int
    gas_price: float
    whale_type: str

class DuneWhaleTracker:
    """
    Tracks Ethereum whale activity using Dune Analytics API
    """
    
    def __init__(self, api_key: str = None):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key or os.getenv('DUNE_API_KEY')
        self.base_url = "https://api.dune.com/api/v1"
        self.headers = {
            "x-dune-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Dashboard configuration
        self.dashboard_id = "marvy_kings8/ethereum-whale-intelligence-dashboard"
        self.whale_queries = {
            "top_whales": "5199702",  # Real query ID from dashboard
            "recent_transactions": "5199685",
            "portfolio_analysis": "5199583",
            "exchange_flows": "5199720"
        }
        
        # Whale tracking parameters
        self.whale_threshold_eth = 1000  # ETH
        self.whale_threshold_usd = 4000000  # $4M
        self.monitoring_interval = 300  # 5 minutes
        
        # Cache for performance
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def validate_api_key(self) -> bool:
        """Validate Dune API key"""
        if not self.api_key:
            self.logger.error("DUNE_API_KEY not found in environment variables")
            return False
            
        try:
            # Test API key with a simple request
            response = requests.get(
                f"{self.base_url}/user/profile",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"API key validation failed: {e}")
            return False
    
    def get_query_results(self, query_id: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        """
        Get results from a Dune query
        
        Args:
            query_id: Dune query ID
            limit: Maximum number of results
            
        Returns:
            DataFrame with query results or None if failed
        """
        try:
            # Check cache first
            cache_key = f"query_{query_id}_{limit}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    self.logger.info(f"Using cached data for query {query_id}")
                    return cached_data
            
            # Get results directly (faster than execute + wait)
            results_url = f"{self.base_url}/query/{query_id}/results?limit={limit}"
            results_response = requests.get(results_url, headers=self.headers, timeout=30)
            
            if results_response.status_code == 200:
                data = results_response.json()
                if 'result' in data and 'rows' in data['result']:
                    df = pd.DataFrame(data['result']['rows'])
                    
                    # Cache the results
                    self.cache[cache_key] = (df, time.time())
                    
                    self.logger.info(f"Successfully retrieved {len(df)} rows from query {query_id}")
                    return df
                else:
                    self.logger.error("No results found in response")
                    return None
            else:
                self.logger.error(f"Failed to get results: {results_response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting query results: {e}")
            return None
    
    def get_whale_wallets(self) -> List[WhaleWallet]:
        """
        Get list of tracked whale wallets from portfolio analysis query
        
        Returns:
            List of WhaleWallet objects
        """
        try:
            # Use portfolio analysis query for whale wallets
            query_id = self.whale_queries.get("portfolio_analysis")
            if not query_id:
                self.logger.error("Portfolio analysis query ID not configured")
                return []
            
            df = self.get_query_results(query_id)
            if df is None or df.empty:
                self.logger.warning("No whale wallet data available")
                return []
            
            whale_wallets = []
            for _, row in df.iterrows():
                try:
                    # Map Dune data to WhaleWallet structure
                    eth_balance = float(row.get('eth_balance', 0))
                    usd_value = float(row.get('usd_value', 0))
                    institution_size = row.get('institution_size', 'Unknown')
                    
                    # Determine risk level based on institution size
                    if 'Mega' in institution_size:
                        risk_level = 'high'
                    elif 'Large' in institution_size:
                        risk_level = 'medium'
                    else:
                        risk_level = 'low'
                    
                    wallet = WhaleWallet(
                        address=row.get('address', ''),
                        label=institution_size,
                        balance_eth=eth_balance,
                        balance_usd=usd_value,
                        last_activity=datetime.now(),  # Dune doesn't provide last activity
                        transaction_count=0,  # Not available in this query
                        portfolio_value=usd_value,
                        risk_level=risk_level
                    )
                    whale_wallets.append(wallet)
                except Exception as e:
                    self.logger.error(f"Error parsing whale wallet data: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(whale_wallets)} whale wallets")
            return whale_wallets
            
        except Exception as e:
            self.logger.error(f"Error getting whale wallets: {e}")
            return []
    
    def get_recent_whale_transactions(self, hours_back: int = 24) -> List[WhaleTransaction]:
        """
        Get recent whale transactions from exchange flows query
        
        Args:
            hours_back: Number of hours to look back
            
        Returns:
            List of WhaleTransaction objects
        """
        try:
            query_id = self.whale_queries.get("exchange_flows")
            if not query_id:
                self.logger.error("Exchange flows query ID not configured")
                return []
            
            df = self.get_query_results(query_id)
            if df is None or df.empty:
                self.logger.warning("No recent whale transaction data available")
                return []
            
            whale_transactions = []
            for _, row in df.iterrows():
                try:
                    # Map Dune exchange flows data to WhaleTransaction structure
                    total_volume = float(row.get('total_eth_volume', 0))
                    transaction_count = int(row.get('transaction_count', 0))
                    avg_amount = float(row.get('avg_eth_amount', 0))
                    
                    # Create synthetic transaction data based on aggregated data
                    for i in range(min(transaction_count, 10)):  # Limit to 10 transactions per hour
                        transaction = WhaleTransaction(
                            hash=f"dune_aggregated_{i}_{row.get('hour_of_day', 0)}",
                            from_address="exchange_aggregated",
                            to_address="whale_aggregated",
                            value_eth=avg_amount,
                            value_usd=avg_amount * 4000,  # Approximate ETH price
                            timestamp=datetime.now() - timedelta(hours=row.get('hour_of_day', 0)),
                            gas_used=21000,  # Standard gas
                            gas_price=50.0,  # Approximate gas price
                            whale_type=f"Exchange Flow - {row.get('activity_level', 'Unknown')}"
                        )
                        whale_transactions.append(transaction)
                        
                except Exception as e:
                    self.logger.error(f"Error parsing transaction data: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(whale_transactions)} recent whale transactions")
            return whale_transactions
            
        except Exception as e:
            self.logger.error(f"Error getting recent whale transactions: {e}")
            return []
    
    def analyze_whale_activity(self) -> Dict[str, Any]:
        """
        Analyze whale activity patterns using real Dune data
        
        Returns:
            Dictionary with analysis results
        """
        try:
            # Get real data from Dune queries
            top_whales_df = self.get_query_results(self.whale_queries.get("top_whales"))
            recent_tx_df = self.get_query_results(self.whale_queries.get("recent_transactions"))
            portfolio_df = self.get_query_results(self.whale_queries.get("portfolio_analysis"))
            exchange_flows_df = self.get_query_results(self.whale_queries.get("exchange_flows"))
            
            if portfolio_df is None or portfolio_df.empty:
                return {"error": "No whale data available from Dune"}
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "data_source": "dune_real",
                "total_whales_tracked": len(portfolio_df),
                "recent_transactions": len(exchange_flows_df) if exchange_flows_df is not None else 0,
                "total_whale_balance_eth": portfolio_df['eth_balance'].sum(),
                "total_whale_balance_usd": portfolio_df['usd_value'].sum(),
                "activity_summary": {},
                "risk_assessment": {},
                "market_impact": {},
                "market_sentiment": {},
                "institutional_behavior": {}
            }
            
            # Activity analysis from exchange flows
            if exchange_flows_df is not None and not exchange_flows_df.empty:
                total_volume = exchange_flows_df['total_eth_volume'].sum()
                total_transactions = exchange_flows_df['transaction_count'].sum()
                
                analysis["activity_summary"] = {
                    "total_volume_eth": total_volume,
                    "total_volume_usd": total_volume * 4000,  # Approximate ETH price
                    "average_transaction_size_eth": exchange_flows_df['avg_eth_amount'].mean(),
                    "largest_transaction_eth": exchange_flows_df['avg_eth_amount'].max(),
                    "transaction_frequency": total_transactions / 24,  # per hour
                    "unique_senders": exchange_flows_df['unique_senders'].sum(),
                    "unique_receivers": exchange_flows_df['unique_receivers'].sum()
                }
            
            # Market sentiment from recent transactions
            if recent_tx_df is not None and not recent_tx_df.empty:
                latest_sentiment = recent_tx_df.iloc[0] if len(recent_tx_df) > 0 else None
                if latest_sentiment is not None:
                    analysis["market_sentiment"] = {
                        "current_sentiment": latest_sentiment.get('market_sentiment', 'Unknown'),
                        "institutional_behavior": latest_sentiment.get('institutional_behavior', 'Unknown'),
                        "net_whale_selling": latest_sentiment.get('net_whale_selling', 0),
                        "exchange_to_whale": latest_sentiment.get('exchange_to_whale', 0),
                        "whale_to_exchange": latest_sentiment.get('whale_to_exchange', 0)
                    }
            
            # Risk assessment based on portfolio analysis
            mega_institutions = portfolio_df[portfolio_df['institution_size'].str.contains('Mega', na=False)]
            large_institutions = portfolio_df[portfolio_df['institution_size'].str.contains('Large', na=False)]
            
            analysis["risk_assessment"] = {
                "mega_institutions": len(mega_institutions),
                "large_institutions": len(large_institutions),
                "total_mega_balance_usd": mega_institutions['usd_value'].sum(),
                "total_large_balance_usd": large_institutions['usd_value'].sum(),
                "risk_distribution": {
                    "mega": len(mega_institutions),
                    "large": len(large_institutions),
                    "other": len(portfolio_df) - len(mega_institutions) - len(large_institutions)
                }
            }
            
            # Market impact assessment
            total_portfolio_value = portfolio_df['usd_value'].sum()
            max_whale_value = portfolio_df['usd_value'].max()
            
            analysis["market_impact"] = {
                "total_tracked_portfolio_usd": total_portfolio_value,
                "average_whale_size_usd": total_portfolio_value / len(portfolio_df),
                "concentration_risk": max_whale_value / total_portfolio_value if total_portfolio_value > 0 else 0,
                "largest_whale_usd": max_whale_value,
                "top_5_concentration": portfolio_df.nlargest(5, 'usd_value')['usd_value'].sum() / total_portfolio_value if total_portfolio_value > 0 else 0
            }
            
            # Institutional behavior from top whales data
            if top_whales_df is not None and not top_whales_df.empty:
                latest_behavior = top_whales_df.iloc[0] if len(top_whales_df) > 0 else None
                if latest_behavior is not None:
                    analysis["institutional_behavior"] = {
                        "current_behavior": latest_behavior.get('institutional_behavior', 'Unknown'),
                        "market_condition": latest_behavior.get('market_condition', 'Unknown'),
                        "price_change_pct": latest_behavior.get('price_change_pct', 0),
                        "whale_eth_volume": latest_behavior.get('whale_eth_volume', 0),
                        "whale_transactions": latest_behavior.get('whale_transactions', 0),
                        "unique_whale_senders": latest_behavior.get('unique_whale_senders', 0),
                        "unique_whale_receivers": latest_behavior.get('unique_whale_receivers', 0)
                    }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing whale activity: {e}")
            return {"error": str(e)}
    
    def generate_whale_report(self) -> str:
        """
        Generate a comprehensive whale intelligence report
        
        Returns:
            Formatted report string
        """
        try:
            analysis = self.analyze_whale_activity()
            
            if "error" in analysis:
                return f"❌ Error generating whale report: {analysis['error']}"
            
            report = f"""
🛡️ WHALE INTELLIGENCE REPORT
Generated: {analysis['timestamp']}
============================================================

📊 WHALE OVERVIEW:
• Total Whales Tracked: {analysis['total_whales_tracked']}
• Total Balance: {analysis['total_whale_balance_eth']:,.2f} ETH (${analysis['total_whale_balance_usd']:,.2f})
• Recent Transactions (24h): {analysis['recent_transactions']}

📈 ACTIVITY ANALYSIS:
"""
            
            if analysis['activity_summary']:
                activity = analysis['activity_summary']
                report += f"""• Total Volume (24h): {activity['total_volume_eth']:,.2f} ETH (${activity['total_volume_usd']:,.2f})
• Average Transaction: {activity['average_transaction_size_eth']:,.2f} ETH
• Largest Transaction: {activity['largest_transaction_eth']:,.2f} ETH
• Transaction Frequency: {activity['transaction_frequency']:.2f} tx/hour
"""
            
            report += f"""
⚠️ RISK ASSESSMENT:
• High Risk Whales: {analysis['risk_assessment']['high_risk_whales']}
• High Risk Balance: ${analysis['risk_assessment']['total_high_risk_balance_usd']:,.2f}
• Risk Distribution: High({analysis['risk_assessment']['risk_distribution']['high']}) | Medium({analysis['risk_assessment']['risk_distribution']['medium']}) | Low({analysis['risk_assessment']['risk_distribution']['low']})

💼 MARKET IMPACT:
• Total Tracked Portfolio: ${analysis['market_impact']['total_tracked_portfolio_usd']:,.2f}
• Average Whale Size: ${analysis['market_impact']['average_whale_size_usd']:,.2f}
• Concentration Risk: {analysis['market_impact']['concentration_risk']:.2%}

🎯 RECOMMENDATIONS:
"""
            
            # Generate recommendations based on analysis
            if analysis['recent_transactions'] > 50:
                report += "• High whale activity detected - monitor for market impact\n"
            if analysis['risk_assessment']['high_risk_whales'] > 5:
                report += "• Multiple high-risk whales active - increased volatility expected\n"
            if analysis['market_impact']['concentration_risk'] > 0.3:
                report += "• High concentration risk - single whale has significant market influence\n"
            
            report += "\n✅ Whale intelligence analysis complete!"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating whale report: {e}")
            return f"❌ Error generating whale report: {e}"

def main():
    """Main function for testing the Dune whale tracker"""
    print("🛡️ DUNE WHALE INTELLIGENCE TRACKER")
    print("=" * 50)
    
    # Initialize tracker
    tracker = DuneWhaleTracker()
    
    # Validate API key
    if not tracker.validate_api_key():
        print("❌ Dune API key validation failed")
        print("💡 Please set DUNE_API_KEY environment variable")
        return
    
    print("✅ Dune API key validated")
    
    # Generate whale report
    print("\n🔍 Generating whale intelligence report...")
    report = tracker.generate_whale_report()
    print(report)
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"whale_intelligence_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")

if __name__ == "__main__":
    main()
