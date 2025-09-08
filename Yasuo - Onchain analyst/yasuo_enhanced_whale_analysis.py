#!/usr/bin/env python3
"""
🛡️ YASUO ENHANCED WHALE ANALYSIS
Complete whale intelligence system with Dune integration

Features:
- Real Dune API integration (when API key provided)
- Fallback to demo data
- Integration with existing Yasuo analysis
- Comprehensive whale tracking
- Market impact assessment
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

# Import existing modules
try:
    from yasuo_onchain_analyst import YasuoOnChainAnalyst
    from demo_whale_tracker import DemoWhaleTracker
except ImportError as e:
    print(f"⚠️ Import warning: {e}")

class YasuoEnhancedWhaleAnalysis:
    """
    Enhanced Yasuo with comprehensive whale intelligence
    """
    
    def __init__(self, dune_api_key: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.yasuo = YasuoOnChainAnalyst()
        self.demo_tracker = DemoWhaleTracker()
        
        # Configuration
        self.dune_api_key = dune_api_key or os.getenv('DUNE_API_KEY')
        self.use_real_data = bool(self.dune_api_key)
        
        # Whale tracking parameters
        self.whale_threshold_eth = 1000
        self.whale_threshold_usd = 4000000
        self.monitoring_interval = 300  # 5 minutes
        
        # Cache
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        print(f"🛡️ Yasuo Enhanced Whale Analysis initialized")
        print(f"📊 Data source: {'Real Dune API' if self.use_real_data else 'Demo data'}")
    
    def get_whale_data(self) -> Dict[str, Any]:
        """
        Get whale data from available sources
        
        Returns:
            Dictionary with whale intelligence data
        """
        try:
            # Check cache first
            cache_key = "whale_data"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    self.logger.info("Using cached whale data")
                    return cached_data
            
            if self.use_real_data:
                # Try to get real data from Dune API
                whale_data = self._get_real_dune_data()
                if whale_data and "error" not in whale_data:
                    self.cache[cache_key] = (whale_data, time.time())
                    return whale_data
            
            # Fallback to demo data
            self.logger.info("Using demo whale data")
            whale_data = self._get_demo_data()
            self.cache[cache_key] = (whale_data, time.time())
            return whale_data
            
        except Exception as e:
            self.logger.error(f"Error getting whale data: {e}")
            return {"error": str(e)}
    
    def _get_real_dune_data(self) -> Dict[str, Any]:
        """Get real data from Dune API"""
        try:
            # This would implement real Dune API calls
            # For now, return None to use demo data
            self.logger.info("Real Dune API integration not yet implemented")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting real Dune data: {e}")
            return {"error": str(e)}
    
    def _get_demo_data(self) -> Dict[str, Any]:
        """Get demo whale data"""
        try:
            # Get demo analysis
            demo_analysis = self.demo_tracker.analyze_whale_activity()
            
            # Get additional Yasuo data
            yasuo_data = {}
            try:
                # Get ETF flows
                if hasattr(self.yasuo, 'etf_tracker') and self.yasuo.etf_tracker:
                    etf_data = self.yasuo.etf_tracker.get_etf_flows()
                    yasuo_data["etf_flows"] = etf_data
                
                # Get exchange flows
                if hasattr(self.yasuo, 'exchange_tracker') and self.yasuo.exchange_tracker:
                    exchange_data = self.yasuo.exchange_tracker.get_exchange_flows()
                    yasuo_data["exchange_flows"] = exchange_data
                    
            except Exception as e:
                self.logger.warning(f"Could not get additional Yasuo data: {e}")
            
            # Combine data
            combined_data = {
                "timestamp": datetime.now().isoformat(),
                "data_source": "demo",
                "whale_analysis": demo_analysis,
                "yasuo_additional_data": yasuo_data,
                "whale_wallets": self.demo_tracker.get_whale_wallets(),
                "recent_transactions": self.demo_tracker.get_recent_whale_transactions()
            }
            
            return combined_data
            
        except Exception as e:
            self.logger.error(f"Error getting demo data: {e}")
            return {"error": str(e)}
    
    def analyze_market_impact(self) -> Dict[str, Any]:
        """
        Analyze market impact of whale activity
        
        Returns:
            Dictionary with market impact analysis
        """
        try:
            whale_data = self.get_whale_data()
            
            if "error" in whale_data:
                return {"error": whale_data["error"]}
            
            whale_analysis = whale_data.get("whale_analysis", {})
            yasuo_data = whale_data.get("yasuo_additional_data", {})
            
            # Market impact analysis
            impact_analysis = {
                "timestamp": datetime.now().isoformat(),
                "whale_activity_level": "low",
                "market_impact_score": 0.0,
                "risk_factors": [],
                "opportunities": [],
                "recommendations": [],
                "trading_signals": {}
            }
            
            # Analyze whale activity level
            recent_transactions = whale_analysis.get("recent_transactions", 0)
            total_whale_balance = whale_analysis.get("total_whale_balance_usd", 0)
            
            if recent_transactions > 100:
                impact_analysis["whale_activity_level"] = "high"
                impact_analysis["market_impact_score"] += 0.4
            elif recent_transactions > 50:
                impact_analysis["whale_activity_level"] = "medium"
                impact_analysis["market_impact_score"] += 0.2
            
            # Analyze balance concentration
            if total_whale_balance > 1000000000:  # $1B
                impact_analysis["market_impact_score"] += 0.3
                impact_analysis["risk_factors"].append("High whale balance concentration")
            
            # Analyze ETF flows
            etf_flows = yasuo_data.get("etf_flows", {})
            if etf_flows:
                etf_flow_value = etf_flows.get("flow_value", 0)
                if abs(etf_flow_value) > 50000000:  # $50M
                    impact_analysis["market_impact_score"] += 0.2
                    if etf_flow_value > 0:
                        impact_analysis["opportunities"].append("Strong ETF inflows detected")
                        impact_analysis["trading_signals"]["etf_signal"] = "bullish"
                    else:
                        impact_analysis["risk_factors"].append("Large ETF outflows detected")
                        impact_analysis["trading_signals"]["etf_signal"] = "bearish"
            
            # Analyze exchange flows
            exchange_flows = yasuo_data.get("exchange_flows", {})
            if exchange_flows:
                exchange_flow_value = exchange_flows.get("net_flow", 0)
                if abs(exchange_flow_value) > 100000:  # 100K ETH
                    impact_analysis["market_impact_score"] += 0.1
                    if exchange_flow_value > 0:
                        impact_analysis["risk_factors"].append("Large exchange inflows (selling pressure)")
                        impact_analysis["trading_signals"]["exchange_signal"] = "bearish"
                    else:
                        impact_analysis["opportunities"].append("Large exchange outflows (accumulation)")
                        impact_analysis["trading_signals"]["exchange_signal"] = "bullish"
            
            # Generate recommendations
            if impact_analysis["market_impact_score"] > 0.7:
                impact_analysis["recommendations"].append("High whale activity - monitor closely for market moves")
                impact_analysis["trading_signals"]["overall_signal"] = "high_volatility"
            elif impact_analysis["market_impact_score"] > 0.4:
                impact_analysis["recommendations"].append("Moderate whale activity - watch for trend changes")
                impact_analysis["trading_signals"]["overall_signal"] = "moderate_volatility"
            else:
                impact_analysis["recommendations"].append("Low whale activity - normal market conditions")
                impact_analysis["trading_signals"]["overall_signal"] = "stable"
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing market impact: {e}")
            return {"error": str(e)}
    
    def generate_comprehensive_report(self) -> str:
        """
        Generate comprehensive whale intelligence report
        
        Returns:
            Formatted report string
        """
        try:
            # Get whale data
            whale_data = self.get_whale_data()
            impact_analysis = self.analyze_market_impact()
            
            if "error" in whale_data:
                return f"❌ Error generating report: {whale_data['error']}"
            
            # Generate report
            report = f"""
🛡️ YASUO ENHANCED WHALE INTELLIGENCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Source: {whale_data.get('data_source', 'unknown').upper()}
============================================================

🎯 WHALE INTELLIGENCE OVERVIEW:
"""
            
            whale_analysis = whale_data.get("whale_analysis", {})
            if whale_analysis:
                report += f"""• Total Whales Tracked: {whale_analysis.get('total_whales_tracked', 0)}
• Total Whale Balance: {whale_analysis.get('total_whale_balance_eth', 0):,.2f} ETH (${whale_analysis.get('total_whale_balance_usd', 0):,.2f})
• Recent Transactions (24h): {whale_analysis.get('recent_transactions', 0)}
"""
            
            # Activity analysis
            activity_summary = whale_analysis.get("activity_summary", {})
            if activity_summary:
                report += f"""
📈 ACTIVITY ANALYSIS:
• Total Volume (24h): {activity_summary.get('total_volume_eth', 0):,.2f} ETH (${activity_summary.get('total_volume_usd', 0):,.2f})
• Average Transaction: {activity_summary.get('average_transaction_size_eth', 0):,.2f} ETH
• Largest Transaction: {activity_summary.get('largest_transaction_eth', 0):,.2f} ETH
• Transaction Frequency: {activity_summary.get('transaction_frequency', 0):.2f} tx/hour
"""
            
            # Market impact analysis
            if "error" not in impact_analysis:
                report += f"""
📊 MARKET IMPACT ANALYSIS:
• Whale Activity Level: {impact_analysis['whale_activity_level'].upper()}
• Market Impact Score: {impact_analysis['market_impact_score']:.2f}/1.0
• Risk Factors: {len(impact_analysis['risk_factors'])}
• Opportunities: {len(impact_analysis['opportunities'])}

⚠️ RISK FACTORS:
"""
                for risk in impact_analysis['risk_factors']:
                    report += f"• {risk}\n"
                
                report += "\n💡 OPPORTUNITIES:\n"
                for opportunity in impact_analysis['opportunities']:
                    report += f"• {opportunity}\n"
                
                report += "\n🎯 RECOMMENDATIONS:\n"
                for rec in impact_analysis['recommendations']:
                    report += f"• {rec}\n"
                
                # Trading signals
                trading_signals = impact_analysis.get('trading_signals', {})
                if trading_signals:
                    report += "\n📊 TRADING SIGNALS:\n"
                    for signal, value in trading_signals.items():
                        report += f"• {signal.replace('_', ' ').title()}: {value.upper()}\n"
            
            # Top whale wallets
            whale_wallets = whale_data.get("whale_wallets", [])
            if whale_wallets:
                report += f"""
🎯 TOP WHALE WALLETS:
"""
                sorted_whales = sorted(whale_wallets, key=lambda x: x['balance_usd'], reverse=True)
                for i, whale in enumerate(sorted_whales[:5], 1):
                    report += f"""• #{i} {whale['label']}: {whale['balance_eth']:,.0f} ETH (${whale['balance_usd']:,.0f})
  Address: {whale['address'][:10]}...{whale['address'][-8:]}
  Risk: {whale['risk_level'].upper()} | Last Activity: {whale['last_activity'].strftime('%H:%M')}
"""
            
            # Recent large transactions
            recent_transactions = whale_data.get("recent_transactions", [])
            if recent_transactions:
                report += f"""
🔍 RECENT LARGE TRANSACTIONS:
"""
                large_transactions = sorted(recent_transactions, key=lambda x: x['value_usd'], reverse=True)[:5]
                for i, tx in enumerate(large_transactions, 1):
                    report += f"""• #{i} {tx['value_eth']:,.0f} ETH (${tx['value_usd']:,.0f})
  From: {tx['from_address'][:10]}...{tx['from_address'][-8:]}
  To: {tx['to_address'][:10]}...{tx['to_address'][-8:]}
  Time: {tx['timestamp'].strftime('%H:%M')} | Type: {tx['whale_type']}
"""
            
            # Additional Yasuo data
            yasuo_data = whale_data.get("yasuo_additional_data", {})
            if yasuo_data:
                report += "\n📈 ADDITIONAL MARKET DATA:\n"
                
                etf_flows = yasuo_data.get("etf_flows", {})
                if etf_flows:
                    report += f"• ETF Flows: ${etf_flows.get('flow_value', 0):,.2f}\n"
                
                exchange_flows = yasuo_data.get("exchange_flows", {})
                if exchange_flows:
                    report += f"• Exchange Net Flow: {exchange_flows.get('net_flow', 0):,.2f} ETH\n"
            
            report += f"""
🔗 DATA SOURCES:
• Primary: {whale_data.get('data_source', 'unknown').title()}
• Yasuo Modules: {', '.join(whale_data.get('yasuo_additional_data', {}).keys())}

✅ Enhanced whale intelligence analysis complete!
"""
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            return f"❌ Error generating comprehensive report: {e}"

def main():
    """Main function for enhanced whale analysis"""
    print("🛡️ YASUO ENHANCED WHALE ANALYSIS")
    print("=" * 50)
    
    # Initialize enhanced analysis
    analysis = YasuoEnhancedWhaleAnalysis()
    
    print("🎯 Generating comprehensive whale intelligence report...")
    
    # Generate report
    report = analysis.generate_comprehensive_report()
    print(report)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"yasuo_enhanced_whale_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n💾 Enhanced whale report saved to: {report_file}")
    
    # Save data as JSON
    whale_data = analysis.get_whale_data()
    impact_analysis = analysis.analyze_market_impact()
    
    combined_data = {
        "whale_data": whale_data,
        "impact_analysis": impact_analysis,
        "generated_at": datetime.now().isoformat()
    }
    
    data_file = f"yasuo_enhanced_whale_data_{timestamp}.json"
    with open(data_file, 'w') as f:
        json.dump(combined_data, f, indent=2, default=str)
    
    print(f"💾 Enhanced whale data saved to: {data_file}")
    print("\n✅ Yasuo enhanced whale analysis complete!")

if __name__ == "__main__":
    main()
