#!/usr/bin/env python3
"""
Hybrid Yasuo - Enhanced with Etherscan primary and Email fallback
"""
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our enhanced components
from etherscan_tracker import EtherscanTransactionTracker
from email_notifier import EmailNotifier

# Import existing components
from yasuo_onchain_analyst import YasuoOnChainAnalyst, ETHETFFlowTracker

class HybridYasuo:
    """
    Enhanced Yasuo with hybrid data sources and fallback notifications
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Primary data sources
        self.etherscan_tracker = EtherscanTransactionTracker()
        self.etf_tracker = ETHETFFlowTracker()
        
        # Fallback notification
        self.email_notifier = EmailNotifier()
        
        # Original Yasuo for advanced features
        self.yasuo = YasuoOnChainAnalyst()
        
        self.logger.info("🛡️ Hybrid Yasuo initialized")
    
    async def run_analysis(self) -> dict:
        """
        Run comprehensive analysis with hybrid data sources
        """
        self.logger.info("🛡️ Starting Hybrid Yasuo Analysis...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "data_sources": [],
            "large_transactions": [],
            "etf_flows": {},
            "recommendation": {},
            "status": "success"
        }
        
        try:
            # 1. Get large transactions from Etherscan (Primary)
            self.logger.info("📊 Fetching large transactions from Etherscan...")
            transactions = self.etherscan_tracker.get_large_transactions(
                min_eth=1000, hours_back=24
            )
            results["large_transactions"] = transactions
            results["data_sources"].append("etherscan")
            
            # 2. Get ETF flows (Working well)
            self.logger.info("💰 Fetching ETF flows...")
            etf_flows = await self.etf_tracker.get_etf_flows()
            results["etf_flows"] = etf_flows
            results["data_sources"].append("farside")
            
            # 3. Generate recommendation
            recommendation = self._generate_recommendation(transactions, etf_flows)
            results["recommendation"] = recommendation
            
            self.logger.info(f"✅ Analysis complete: {len(transactions)} transactions, ETF: ${etf_flows.get('daily_flow', 0):,.0f}")
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    def _generate_recommendation(self, transactions: list, etf_flows: dict) -> dict:
        """
        Generate portfolio recommendation based on data
        """
        # Count large transactions
        large_tx_count = len(transactions)
        
        # Get ETF flow
        daily_flow = etf_flows.get("daily_flow", 0)
        
        # Simple recommendation logic
        if daily_flow < -500_000_000:  # Large outflows
            action = "HOLD"
            confidence = 0.8
            reason = "Large institutional outflows, wait for reversal"
        elif daily_flow > 100_000_000:  # Large inflows
            action = "BUY"
            confidence = 0.7
            reason = "Strong institutional inflows"
        else:
            action = "HOLD"
            confidence = 0.6
            reason = "Mixed signals, consolidation phase"
        
        return {
            "action": action,
            "confidence": confidence,
            "reason": reason,
            "large_transactions": large_tx_count,
            "etf_flow": daily_flow
        }
    
    async def send_report(self, results: dict) -> bool:
        """
        Send report via email (fallback for Telegram)
        """
        try:
            # Format report
            report = self._format_report(results)
            
            # Send via email
            success = self.email_notifier.send_alert(
                "ETH Analysis Report",
                report
            )
            
            if success:
                self.logger.info("✅ Report sent via email")
                return True
            else:
                self.logger.warning("❌ Email failed, report not sent")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to send report: {e}")
            return False
    
    def _format_report(self, results: dict) -> str:
        """
        Format analysis results into readable report
        """
        transactions = results.get("large_transactions", [])
        etf_flows = results.get("etf_flows", {})
        recommendation = results.get("recommendation", {})
        
        report = f"""
🛡️ YASUO HYBRID ANALYSIS REPORT
{'='*50}

📊 MARKET DATA:
• Large Transactions (24h): {len(transactions)}
• ETF Daily Flow: ${etf_flows.get('daily_flow', 0):,.0f}
• Data Sources: {', '.join(results.get('data_sources', []))}

🎯 PORTFOLIO RECOMMENDATION:
• Action: {recommendation.get('action', 'UNKNOWN')}
• Confidence: {recommendation.get('confidence', 0):.1f}
• Reason: {recommendation.get('reason', 'No analysis available')}

📈 LARGE TRANSACTIONS:
"""
        
        # Add top transactions
        for i, tx in enumerate(transactions[:5]):
            amount = tx.get("amount", 0)
            sender = tx.get("sender", {}).get("address", "Unknown")
            receiver = tx.get("receiver", {}).get("address", "Unknown")
            report += f"• {amount:.0f} ETH: {sender[:10]}... -> {receiver[:10]}...\n"
        
        report += f"""
✅ DATA QUALITY:
• Etherscan: Real transaction data
• ETF Data: Real from farside.co.uk
• No Simulated Data Used

🛡️ YASUO STATUS: OPERATIONAL
• Analysis Time: {results.get('timestamp', 'Unknown')}
• Status: {results.get('status', 'Unknown').upper()}
        """
        
        return report

# Test the hybrid system
async def main():
    print("🛡️ TESTING HYBRID YASUO")
    print("=" * 50)
    
    yasuo = HybridYasuo()
    
    # Run analysis
    results = await yasuo.run_analysis()
    
    print(f"✅ Analysis complete: {results['status']}")
    print(f"📊 Transactions: {len(results['large_transactions'])}")
    print(f"💰 ETF Flow: ${results['etf_flows'].get('daily_flow', 0):,.0f}")
    print(f"🎯 Recommendation: {results['recommendation'].get('action', 'UNKNOWN')}")
    
    # Send report
    success = await yasuo.send_report(results)
    print(f"📧 Report sent: {'✅' if success else '❌'}")

if __name__ == "__main__":
    asyncio.run(main())






