#!/usr/bin/env python3
"""
🛡️ YASUO COMPLETE ANALYSIS
Complete Yasuo analysis with whale intelligence integration

Features:
- On-chain analysis (existing)
- ETF flow tracking
- Exchange flow monitoring
- Whale intelligence from Dune
- Comprehensive reporting
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
    from dune_whale_tracker import DuneWhaleTracker
    from etf_tracker_fixed import ETHETFFlowTracker
    from etherscan_exchange_flows import EtherscanExchangeFlows
except ImportError as e:
    print(f"⚠️ Import warning: {e}")

class YasuoCompleteAnalysis:
    """
    Complete Yasuo analysis with all modules integrated
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize all components
        self.yasuo = YasuoOnChainAnalyst()
        self.whale_tracker = DuneWhaleTracker()
        self.etf_tracker = ETHETFFlowTracker()
        
        # Analysis results
        self.results = {}
        
        print("🛡️ Yasuo Complete Analysis initialized")
        print("📊 Modules: On-chain + Whale Intelligence + ETF + Exchange")
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """
        Run complete analysis with all modules
        
        Returns:
            Dictionary with complete analysis results
        """
        try:
            print("\n🚀 STARTING COMPLETE YASUO ANALYSIS")
            print("=" * 60)
            
            # 1. Whale Intelligence Analysis
            print("\n🐋 1. WHALE INTELLIGENCE ANALYSIS")
            print("-" * 40)
            whale_analysis = self.whale_tracker.analyze_whale_activity()
            
            if "error" in whale_analysis:
                print(f"❌ Whale analysis failed: {whale_analysis['error']}")
                whale_analysis = {"error": "Whale analysis failed"}
            else:
                print("✅ Whale intelligence analysis complete")
                print(f"   Data source: {whale_analysis.get('data_source', 'unknown')}")
                print(f"   Whales tracked: {whale_analysis.get('total_whales_tracked', 0)}")
                print(f"   Total balance: {whale_analysis.get('total_whale_balance_eth', 0):,.0f} ETH")
            
            # 2. ETF Flow Analysis
            print("\n📈 2. ETF FLOW ANALYSIS")
            print("-" * 40)
            try:
                # Use synchronous wrapper to avoid awaiting in sync flow
                etf_data = self.etf_tracker.get_etf_flows_sync()
                print("✅ ETF flow analysis complete")
                print(f"   Flow value: ${etf_data.get('flow_value', 0):,.0f}")
                print(f"   Data source: {etf_data.get('data_source', 'unknown')}")
            except Exception as e:
                print(f"❌ ETF analysis failed: {e}")
                etf_data = {"error": str(e)}
            
            # 3. On-chain Analysis (existing Yasuo)
            print("\n🔗 3. ON-CHAIN ANALYSIS")
            print("-" * 40)
            try:
                # Use Etherscan-based exchange flows (no Bitquery)
                exchange_data = {}
                try:
                    etherscan_key = os.getenv("ETHERSCAN_API_KEY")
                    es = EtherscanExchangeFlows(api_key=etherscan_key)
                    exchange_data = es.get_exchange_flows(hours_back=72, min_eth=1.0)
                    print("✅ Exchange flow analysis complete (Etherscan)")
                except Exception as inner_e:
                    print(f"⚠️ Etherscan exchange flow failed: {inner_e}")
                    exchange_data = {"error": str(inner_e)}
                
                # Get large transactions
                large_tx_data = {}
                if hasattr(self.yasuo, 'large_tx_tracker') and self.yasuo.large_tx_tracker:
                    large_tx_data = self.yasuo.large_tx_tracker.get_large_transactions()
                    print("✅ Large transaction analysis complete")
                else:
                    print("⚠️ Large transaction tracker not available")
                
            except Exception as e:
                print(f"❌ On-chain analysis failed: {e}")
                exchange_data = {"error": str(e)}
                large_tx_data = {"error": str(e)}
            
            # 4. Combine all results
            complete_results = {
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "complete_yasuo_analysis",
                "whale_intelligence": whale_analysis,
                "etf_flows": etf_data,
                "exchange_flows": exchange_data,
                "large_transactions": large_tx_data,
                "summary": self._generate_summary(whale_analysis, etf_data, exchange_data, large_tx_data)
            }
            
            self.results = complete_results
            return complete_results
            
        except Exception as e:
            self.logger.error(f"Error in complete analysis: {e}")
            return {"error": str(e)}
    
    def _generate_summary(self, whale_data, etf_data, exchange_data, large_tx_data) -> Dict[str, Any]:
        """Generate analysis summary"""
        summary = {
            "overall_sentiment": "neutral",
            "market_condition": "stable",
            "risk_level": "medium",
            "trading_signals": {},
            "key_insights": [],
            "recommendations": []
        }
        
        # Analyze whale data
        if "error" not in whale_data:
            market_sentiment = whale_data.get('market_sentiment', {})
            institutional_behavior = whale_data.get('institutional_behavior', {})
            
            if market_sentiment:
                current_sentiment = market_sentiment.get('current_sentiment', 'Unknown')
                if 'Heavy Institutional Buying' in current_sentiment:
                    summary["overall_sentiment"] = "bullish"
                    summary["key_insights"].append("Heavy institutional buying detected")
                elif 'Selling' in current_sentiment:
                    summary["overall_sentiment"] = "bearish"
                    summary["key_insights"].append("Institutional selling pressure")
            
            if institutional_behavior:
                behavior = institutional_behavior.get('current_behavior', 'Unknown')
                market_condition = institutional_behavior.get('market_condition', 'Unknown')
                
                if 'Taking Profits' in behavior:
                    summary["key_insights"].append("Institutions taking profits")
                if 'Strong Pump' in market_condition:
                    summary["market_condition"] = "strong_uptrend"
                    summary["key_insights"].append("Strong market pump detected")
        
        # Analyze ETF data
        if "error" not in etf_data:
            flow_value = etf_data.get('flow_value', 0)
            if flow_value > 50000000:  # $50M+
                summary["key_insights"].append(f"Strong ETF inflows: ${flow_value:,.0f}")
                if summary["overall_sentiment"] == "neutral":
                    summary["overall_sentiment"] = "bullish"
            elif flow_value < -50000000:  # -$50M+
                summary["key_insights"].append(f"Large ETF outflows: ${flow_value:,.0f}")
                if summary["overall_sentiment"] == "neutral":
                    summary["overall_sentiment"] = "bearish"
        
        # Generate trading signals
        if summary["overall_sentiment"] == "bullish":
            summary["trading_signals"]["primary"] = "BUY"
            summary["trading_signals"]["confidence"] = "high"
        elif summary["overall_sentiment"] == "bearish":
            summary["trading_signals"]["primary"] = "SELL"
            summary["trading_signals"]["confidence"] = "high"
        else:
            summary["trading_signals"]["primary"] = "HOLD"
            summary["trading_signals"]["confidence"] = "medium"
        
        # Generate recommendations
        if summary["overall_sentiment"] == "bullish":
            summary["recommendations"].append("Consider long positions with proper risk management")
        elif summary["overall_sentiment"] == "bearish":
            summary["recommendations"].append("Consider short positions or reduce exposure")
        else:
            summary["recommendations"].append("Maintain current positions, monitor for signals")
        
        return summary
    
    def generate_complete_report(self) -> str:
        """
        Generate complete analysis report
        
        Returns:
            Formatted report string
        """
        if not self.results:
            return "❌ No analysis results available. Run analysis first."
        
        whale_data = self.results.get('whale_intelligence', {})
        etf_data = self.results.get('etf_flows', {})
        exchange_data = self.results.get('exchange_flows', {})
        summary = self.results.get('summary', {})
        
        report = f"""
🛡️ YASUO COMPLETE ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================================

📊 EXECUTIVE SUMMARY:
• Overall Sentiment: {summary.get('overall_sentiment', 'Unknown').upper()}
• Market Condition: {summary.get('market_condition', 'Unknown').upper()}
• Risk Level: {summary.get('risk_level', 'Unknown').upper()}
• Primary Signal: {summary.get('trading_signals', {}).get('primary', 'Unknown')}
• Confidence: {summary.get('trading_signals', {}).get('confidence', 'Unknown')}

🐋 WHALE INTELLIGENCE:
"""
        
        if "error" not in whale_data:
            report += f"""• Data Source: {whale_data.get('data_source', 'Unknown').upper()}
• Whales Tracked: {whale_data.get('total_whales_tracked', 0)}
• Total Balance: {whale_data.get('total_whale_balance_eth', 0):,.0f} ETH (${whale_data.get('total_whale_balance_usd', 0):,.0f})
• Recent Transactions: {whale_data.get('recent_transactions', 0)}
"""
            
            # Market sentiment
            market_sentiment = whale_data.get('market_sentiment', {})
            if market_sentiment:
                report += f"""
📈 MARKET SENTIMENT:
• Current Sentiment: {market_sentiment.get('current_sentiment', 'Unknown')}
• Institutional Behavior: {market_sentiment.get('institutional_behavior', 'Unknown')}
• Net Whale Selling: {market_sentiment.get('net_whale_selling', 0):,.2f} ETH
• Exchange to Whale: {market_sentiment.get('exchange_to_whale', 0):,.2f} ETH
• Whale to Exchange: {market_sentiment.get('whale_to_exchange', 0):,.2f} ETH
"""
            
            # Institutional behavior
            institutional_behavior = whale_data.get('institutional_behavior', {})
            if institutional_behavior:
                report += f"""
🏛️ INSTITUTIONAL BEHAVIOR:
• Current Behavior: {institutional_behavior.get('current_behavior', 'Unknown')}
• Market Condition: {institutional_behavior.get('market_condition', 'Unknown')}
• Price Change: {institutional_behavior.get('price_change_pct', 0):.2f}%
• Whale Volume: {institutional_behavior.get('whale_eth_volume', 0):,.2f} ETH
• Whale Transactions: {institutional_behavior.get('whale_transactions', 0)}
"""
            
            # Risk assessment
            risk_assessment = whale_data.get('risk_assessment', {})
            if risk_assessment:
                report += f"""
⚠️ RISK ASSESSMENT:
• Mega Institutions: {risk_assessment.get('mega_institutions', 0)}
• Large Institutions: {risk_assessment.get('large_institutions', 0)}
• Mega Balance: ${risk_assessment.get('total_mega_balance_usd', 0):,.0f}
• Large Balance: ${risk_assessment.get('total_large_balance_usd', 0):,.0f}
"""
            
            # Market impact
            market_impact = whale_data.get('market_impact', {})
            if market_impact:
                report += f"""
💼 MARKET IMPACT:
• Total Portfolio: ${market_impact.get('total_tracked_portfolio_usd', 0):,.0f}
• Average Whale Size: ${market_impact.get('average_whale_size_usd', 0):,.0f}
• Concentration Risk: {market_impact.get('concentration_risk', 0):.2%}
• Largest Whale: ${market_impact.get('largest_whale_usd', 0):,.0f}
"""
        else:
            report += f"❌ Whale analysis failed: {whale_data.get('error', 'Unknown error')}\n"
        
        # ETF Analysis
        report += f"""
📈 ETF FLOW ANALYSIS:
"""
        if "error" not in etf_data:
            report += f"""• Flow Value: ${etf_data.get('flow_value', 0):,.0f}
• Data Source: {etf_data.get('data_source', 'Unknown')}
• Status: {etf_data.get('status', 'Unknown')}
"""
        else:
            report += f"❌ ETF analysis failed: {etf_data.get('error', 'Unknown error')}\n"
        
        # Exchange Flows
        report += f"""
💱 EXCHANGE FLOW ANALYSIS:
"""
        if "error" not in exchange_data:
            report += f"""• Net Flow: {exchange_data.get('net_flow', 0):,.2f} ETH
• Inflow: {exchange_data.get('inflow', 0):,.2f} ETH
• Outflow: {exchange_data.get('outflow', 0):,.2f} ETH
"""
        else:
            report += f"❌ Exchange flow analysis failed: {exchange_data.get('error', 'Unknown error')}\n"
        
        # Key Insights
        key_insights = summary.get('key_insights', [])
        if key_insights:
            report += f"""
🔍 KEY INSIGHTS:
"""
            for insight in key_insights:
                report += f"• {insight}\n"
        
        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            report += f"""
🎯 RECOMMENDATIONS:
"""
            for rec in recommendations:
                report += f"• {rec}\n"
        
        report += f"""
📊 DATA SOURCES:
• Whale Intelligence: Dune Analytics (Real-time)
• ETF Flows: farside.co.uk
• Exchange Flows: Yasuo On-chain Analysis
• Large Transactions: Yasuo On-chain Analysis

✅ Complete Yasuo analysis finished!
"""
        
        return report

def main():
    """Main function"""
    print("🛡️ YASUO COMPLETE ANALYSIS")
    print("=" * 50)
    
    # Initialize complete analysis
    analysis = YasuoCompleteAnalysis()
    
    # Run complete analysis
    results = analysis.run_complete_analysis()
    
    if "error" in results:
        print(f"❌ Analysis failed: {results['error']}")
        return
    
    # Generate report
    print("\n📝 Generating complete report...")
    report = analysis.generate_complete_report()
    print(report)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"yasuo_complete_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save data
    data_file = f"yasuo_complete_data_{timestamp}.json"
    with open(data_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Complete report saved to: {report_file}")
    print(f"💾 Complete data saved to: {data_file}")
    print("\n✅ Yasuo complete analysis finished!")

if __name__ == "__main__":
    main()
