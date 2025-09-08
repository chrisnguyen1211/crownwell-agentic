#!/usr/bin/env python3
"""
🛡️ YASUO DUNE INTEGRATION
Enhanced Yasuo with Dune Analytics whale intelligence

Features:
- Real-time whale tracking from Dune dashboard
- Integration with existing Yasuo analysis
- Advanced whale behavior analysis
- Market impact assessment
"""

import os
import json
import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

# Import existing Yasuo modules
try:
    from yasuo_onchain_analyst import YasuoOnChainAnalyst
    from dune_whale_tracker import DuneWhaleTracker
    from dune_dashboard_analyzer import DuneDashboardAnalyzer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all required modules are in the same directory")

class YasuoDuneIntegration:
    """
    Enhanced Yasuo with Dune Analytics integration
    """
    
    def __init__(self, dune_api_key: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.yasuo = YasuoOnChainAnalyst()
        self.dune_tracker = DuneWhaleTracker(dune_api_key)
        self.dashboard_analyzer = DuneDashboardAnalyzer()
        
        # Configuration
        self.dashboard_url = "https://dune.com/marvy_kings8/ethereum-whale-intelligence-dashboard"
        self.analysis_interval = 300  # 5 minutes
        self.whale_threshold_eth = 1000  # ETH
        self.whale_threshold_usd = 4000000  # $4M
        
        # Cache for performance
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def validate_setup(self) -> Dict[str, bool]:
        """
        Validate all components are properly configured
        
        Returns:
            Dictionary with validation status
        """
        validation = {
            "yasuo": False,
            "dune_api": False,
            "dune_tracker": False,
            "dashboard_access": False
        }
        
        try:
            # Validate Yasuo
            if hasattr(self.yasuo, 'validate_config'):
                yasuo_config = self.yasuo.validate_config()
                validation["yasuo"] = yasuo_config.get("valid", False)
            else:
                validation["yasuo"] = True  # Assume valid if no validation method
            
            # Validate Dune API
            validation["dune_api"] = self.dune_tracker.validate_api_key()
            
            # Validate Dune tracker
            validation["dune_tracker"] = validation["dune_api"]
            
            # Test dashboard access
            try:
                response = self.dashboard_analyzer.session.get(self.dashboard_url, timeout=10)
                validation["dashboard_access"] = response.status_code == 200
            except:
                validation["dashboard_access"] = False
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Error validating setup: {e}")
            return validation
    
    def get_whale_intelligence_data(self) -> Dict[str, Any]:
        """
        Get comprehensive whale intelligence data
        
        Returns:
            Dictionary with whale intelligence data
        """
        try:
            # Check cache first
            cache_key = "whale_intelligence_data"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    self.logger.info("Using cached whale intelligence data")
                    return cached_data
            
            # Get data from Dune
            whale_analysis = self.dune_tracker.analyze_whale_activity()
            
            # Get additional data from Yasuo's existing sources
            yasuo_data = {}
            try:
                # Get ETF flows
                etf_tracker = self.yasuo.etf_tracker
                if etf_tracker:
                    etf_data = etf_tracker.get_etf_flows()
                    yasuo_data["etf_flows"] = etf_data
                
                # Get exchange flows
                exchange_tracker = self.yasuo.exchange_tracker
                if exchange_tracker:
                    exchange_data = exchange_tracker.get_exchange_flows()
                    yasuo_data["exchange_flows"] = exchange_data
                    
            except Exception as e:
                self.logger.warning(f"Could not get additional Yasuo data: {e}")
            
            # Combine data
            combined_data = {
                "timestamp": datetime.now().isoformat(),
                "dune_whale_data": whale_analysis,
                "yasuo_additional_data": yasuo_data,
                "data_sources": {
                    "dune_dashboard": self.dashboard_url,
                    "yasuo_modules": list(yasuo_data.keys())
                }
            }
            
            # Cache the results
            self.cache[cache_key] = (combined_data, time.time())
            
            return combined_data
            
        except Exception as e:
            self.logger.error(f"Error getting whale intelligence data: {e}")
            return {"error": str(e)}
    
    def analyze_whale_market_impact(self) -> Dict[str, Any]:
        """
        Analyze the market impact of whale activity
        
        Returns:
            Dictionary with market impact analysis
        """
        try:
            whale_data = self.get_whale_intelligence_data()
            
            if "error" in whale_data:
                return {"error": whale_data["error"]}
            
            dune_data = whale_data.get("dune_whale_data", {})
            yasuo_data = whale_data.get("yasuo_additional_data", {})
            
            # Market impact analysis
            impact_analysis = {
                "timestamp": datetime.now().isoformat(),
                "whale_activity_level": "low",
                "market_impact_score": 0.0,
                "risk_factors": [],
                "opportunities": [],
                "recommendations": []
            }
            
            # Analyze whale activity level
            recent_transactions = dune_data.get("recent_transactions", 0)
            total_whale_balance = dune_data.get("total_whale_balance_usd", 0)
            
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
                    else:
                        impact_analysis["risk_factors"].append("Large ETF outflows detected")
            
            # Analyze exchange flows
            exchange_flows = yasuo_data.get("exchange_flows", {})
            if exchange_flows:
                exchange_flow_value = exchange_flows.get("net_flow", 0)
                if abs(exchange_flow_value) > 100000:  # 100K ETH
                    impact_analysis["market_impact_score"] += 0.1
                    if exchange_flow_value > 0:
                        impact_analysis["risk_factors"].append("Large exchange inflows (selling pressure)")
                    else:
                        impact_analysis["opportunities"].append("Large exchange outflows (accumulation)")
            
            # Generate recommendations
            if impact_analysis["market_impact_score"] > 0.7:
                impact_analysis["recommendations"].append("High whale activity - monitor closely for market moves")
            elif impact_analysis["market_impact_score"] > 0.4:
                impact_analysis["recommendations"].append("Moderate whale activity - watch for trend changes")
            else:
                impact_analysis["recommendations"].append("Low whale activity - normal market conditions")
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing whale market impact: {e}")
            return {"error": str(e)}
    
    def generate_enhanced_report(self) -> str:
        """
        Generate enhanced Yasuo report with Dune whale intelligence
        
        Returns:
            Formatted report string
        """
        try:
            # Get whale intelligence data
            whale_data = self.get_whale_intelligence_data()
            impact_analysis = self.analyze_whale_market_impact()
            
            if "error" in whale_data:
                return f"❌ Error generating enhanced report: {whale_data['error']}"
            
            # Generate report
            report = f"""
🛡️ YASUO ENHANCED WHALE INTELLIGENCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================================

🎯 WHALE INTELLIGENCE OVERVIEW:
"""
            
            dune_data = whale_data.get("dune_whale_data", {})
            if dune_data:
                report += f"""• Total Whales Tracked: {dune_data.get('total_whales_tracked', 0)}
• Total Whale Balance: {dune_data.get('total_whale_balance_eth', 0):,.2f} ETH (${dune_data.get('total_whale_balance_usd', 0):,.2f})
• Recent Transactions (24h): {dune_data.get('recent_transactions', 0)}
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
• Dune Dashboard: {self.dashboard_url}
• Yasuo Modules: {', '.join(whale_data.get('data_sources', {}).get('yasuo_modules', []))}

✅ Enhanced whale intelligence analysis complete!
"""
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced report: {e}")
            return f"❌ Error generating enhanced report: {e}"
    
    def run_continuous_monitoring(self, duration_hours: int = 24):
        """
        Run continuous whale monitoring
        
        Args:
            duration_hours: Duration to run monitoring in hours
        """
        try:
            self.logger.info(f"Starting continuous whale monitoring for {duration_hours} hours")
            
            end_time = datetime.now() + timedelta(hours=duration_hours)
            
            while datetime.now() < end_time:
                # Generate report
                report = self.generate_enhanced_report()
                
                # Save report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = f"yasuo_whale_report_{timestamp}.txt"
                
                with open(report_file, 'w') as f:
                    f.write(report)
                
                self.logger.info(f"Report saved: {report_file}")
                
                # Wait for next interval
                time.sleep(self.analysis_interval)
            
            self.logger.info("Continuous monitoring completed")
            
        except Exception as e:
            self.logger.error(f"Error in continuous monitoring: {e}")

def main():
    """Main function for Yasuo Dune integration"""
    print("🛡️ YASUO DUNE INTEGRATION")
    print("=" * 50)
    
    # Initialize integration
    integration = YasuoDuneIntegration()
    
    # Validate setup
    print("🔧 Validating setup...")
    validation = integration.validate_setup()
    
    print("📊 Setup Status:")
    for component, status in validation.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {component.title()}: {'Ready' if status else 'Not configured'}")
    
    if not all(validation.values()):
        print("\n⚠️ Some components are not properly configured")
        print("💡 Please check your API keys and network connection")
        return
    
    print("\n🎯 Generating enhanced whale intelligence report...")
    
    # Generate report
    report = integration.generate_enhanced_report()
    print(report)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"yasuo_enhanced_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n💾 Enhanced report saved to: {report_file}")
    print("\n✅ Yasuo Dune integration complete!")

if __name__ == "__main__":
    main()
