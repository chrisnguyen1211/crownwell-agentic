#!/usr/bin/env python3
"""
Yasuo Real Data Fetcher
Fetches real data from all sources:
- Dune query (whale transactions)
- ETF flow (farside.co.uk)
- Liveliness (Bitquery)
- Exchange flow (Bitquery)
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, '.')

async def fetch_real_data():
    """Fetch real data from all sources"""
    
    print("🛡️ YASUO REAL DATA FETCHER")
    print("=" * 60)
    print("🎯 Fetching real data from all sources:")
    print("  • Dune Analytics (whale transactions)")
    print("  • farside.co.uk (ETF flows)")
    print("  • Bitquery (exchange flows)")
    print("  • Bitquery (liveliness metrics)")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "data_sources": {},
        "status": "success"
    }
    
    try:
        # Enforce source mapping
        import json as _json
        mapping_path = os.path.join(os.path.dirname(__file__), 'source_mapping.json')
        with open(mapping_path, 'r') as mf:
            source_map = _json.load(mf)
        # 1. Dune Whale Transactions
        print("\n🐋 FETCHING DUNE WHALE TRANSACTIONS...")
        try:
            if source_map.get("whale_holding") != "dune":
                raise RuntimeError("Whale holding source must be Dune per mapping")
            from dune_whale_tracker import DuneWhaleTracker
            dune_tracker = DuneWhaleTracker()
            whale_transactions = dune_tracker.get_recent_whale_transactions(hours_back=24)
            # Convert to dict format for consistency
            whale_data = {
                "transactions": [
                    {
                        "hash": tx.hash,
                        "from_address": tx.from_address,
                        "to_address": tx.to_address,
                        "value_eth": tx.value_eth,
                        "value_usd": tx.value_usd,
                        "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                        "whale_type": tx.whale_type
                    } for tx in whale_transactions
                ],
                "count": len(whale_transactions),
                "data_source": "dune_whale_tracker"
            }
            results["data_sources"]["dune_whales"] = whale_data
            print(f"  ✅ Dune: Found {len(whale_transactions)} whale transactions")
        except Exception as e:
            print(f"  ❌ Dune failed: {e}")
            results["data_sources"]["dune_whales"] = {"error": str(e)}
        
        # 2. ETF Flows
        print("\n💰 FETCHING ETF FLOWS...")
        try:
            if source_map.get("etf_flow") != "farside":
                raise RuntimeError("ETF flow source must be Farside per mapping")
            from etf_tracker_fixed import ETHETFFlowTracker
            etf_tracker = ETHETFFlowTracker()
            etf_data = await etf_tracker.get_etf_flows()
            results["data_sources"]["etf_flows"] = etf_data
            print(f"  ✅ ETF: Daily flow ${etf_data.get('daily_flow', 0):,.0f}")
        except Exception as e:
            print(f"  ❌ ETF failed: {e}")
            results["data_sources"]["etf_flows"] = {"error": str(e)}
        
        # 3. Exchange Flows (Etherscan)
        print("\n📈 FETCHING EXCHANGE FLOWS...")
        try:
            if source_map.get("exchange_flow") != "etherscan":
                raise RuntimeError("Exchange flow source must be Etherscan per mapping")
            from etherscan_tracker import EtherscanTransactionTracker
            etherscan = EtherscanTransactionTracker()
            exchange_data = etherscan.get_exchange_flows(hours_back=24)
            results["data_sources"]["exchange_flows"] = exchange_data
            print(f"  ✅ Exchange: Net flow {exchange_data.get('net_flow', 0):,.0f} ETH")
        except Exception as e:
            print(f"  ❌ Exchange failed: {e}")
            results["data_sources"]["exchange_flows"] = {"error": str(e)}
        
        # 4. Liveliness Metrics
        print("\n🎯 FETCHING LIVELINESS METRICS...")
        try:
            if source_map.get("liveliness") != "bitquery":
                raise RuntimeError("Liveliness source must be Bitquery per mapping")
            from fixed_bitquery_api import FixedBitqueryAPI
            bitquery = FixedBitqueryAPI()
            liveliness_data = bitquery.get_liveliness_metrics(days_back=7)
            results["data_sources"]["liveliness"] = liveliness_data
            print(f"  ✅ Liveliness: Score {liveliness_data.get('liveliness_score', 0):.2f}")
        except Exception as e:
            print(f"  ❌ Liveliness failed: {e}")
            results["data_sources"]["liveliness"] = {"error": str(e)}
        
        # 5. Generate comprehensive analysis
        print("\n🔍 GENERATING COMPREHENSIVE ANALYSIS...")
        analysis = generate_comprehensive_analysis(results["data_sources"])
        results["analysis"] = analysis
        
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"  • Market Sentiment: {analysis.get('market_sentiment', 'Unknown')}")
        print(f"  • Trading Signal: {analysis.get('trading_signal', 'Unknown')}")
        print(f"  • Confidence: {analysis.get('confidence', 0):.2f}")
        print(f"  • Key Insights: {len(analysis.get('key_insights', []))}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"yasuo_real_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            import json
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Real data saved to: {filename}")
        
    except Exception as e:
        print(f"\n❌ Error in main process: {e}")
        results["status"] = "error"
        results["error"] = str(e)
    
    return results

def generate_comprehensive_analysis(data_sources: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive analysis from all data sources"""
    
    analysis = {
        "market_sentiment": "neutral",
        "trading_signal": "HOLD",
        "confidence": 0.5,
        "key_insights": [],
        "risk_factors": [],
        "bullish_signals": [],
        "bearish_signals": []
    }
    
    # Analyze whale transactions
    whale_data = data_sources.get("dune_whales", {})
    if "error" not in whale_data:
        transactions = whale_data.get("transactions", [])
        if transactions:
            large_txs = [tx for tx in transactions if tx.get("value_eth", 0) > 1000]
            if len(large_txs) > 5:
                analysis["bullish_signals"].append("High whale activity - accumulation phase")
                analysis["key_insights"].append(f"Found {len(large_txs)} large whale transactions")
            else:
                analysis["bearish_signals"].append("Low whale activity - distribution phase")
    
    # Analyze ETF flows
    etf_data = data_sources.get("etf_flows", {})
    if "error" not in etf_data:
        daily_flow = etf_data.get("daily_flow", 0)
        if daily_flow > 100_000_000:  # $100M+
            analysis["bullish_signals"].append("Strong ETF inflows - institutional buying")
            analysis["key_insights"].append(f"ETF daily flow: ${daily_flow:,.0f}")
        elif daily_flow < -100_000_000:  # -$100M+
            analysis["bearish_signals"].append("Strong ETF outflows - institutional selling")
            analysis["key_insights"].append(f"ETF daily flow: ${daily_flow:,.0f}")
        else:
            analysis["key_insights"].append(f"ETF daily flow: ${daily_flow:,.0f} (neutral)")
    
    # Analyze exchange flows
    exchange_data = data_sources.get("exchange_flows", {})
    if "error" not in exchange_data:
        net_flow = exchange_data.get("net_flow", 0)
        if net_flow > 10000:  # 10k+ ETH outflows
            analysis["bullish_signals"].append("Large exchange outflows - accumulation")
            analysis["key_insights"].append(f"Exchange net flow: {net_flow:,.0f} ETH")
        elif net_flow < -10000:  # 10k+ ETH inflows
            analysis["bearish_signals"].append("Large exchange inflows - distribution")
            analysis["key_insights"].append(f"Exchange net flow: {net_flow:,.0f} ETH")
        else:
            analysis["key_insights"].append(f"Exchange net flow: {net_flow:,.0f} ETH (neutral)")
    
    # Analyze liveliness
    liveliness_data = data_sources.get("liveliness", {})
    if "error" not in liveliness_data:
        score = liveliness_data.get("liveliness_score", 0.5)
        if score > 0.7:
            analysis["bullish_signals"].append("High network activity - bullish momentum")
            analysis["key_insights"].append(f"Liveliness score: {score:.2f} (high)")
        elif score < 0.3:
            analysis["bearish_signals"].append("Low network activity - bearish momentum")
            analysis["key_insights"].append(f"Liveliness score: {score:.2f} (low)")
        else:
            analysis["key_insights"].append(f"Liveliness score: {score:.2f} (moderate)")
    
    # Determine overall sentiment
    bullish_count = len(analysis["bullish_signals"])
    bearish_count = len(analysis["bearish_signals"])
    
    if bullish_count > bearish_count:
        analysis["market_sentiment"] = "bullish"
        analysis["trading_signal"] = "BUY"
        analysis["confidence"] = min(0.8, 0.5 + (bullish_count - bearish_count) * 0.1)
    elif bearish_count > bullish_count:
        analysis["market_sentiment"] = "bearish"
        analysis["trading_signal"] = "SELL"
        analysis["confidence"] = min(0.8, 0.5 + (bearish_count - bullish_count) * 0.1)
    else:
        analysis["market_sentiment"] = "neutral"
        analysis["trading_signal"] = "HOLD"
        analysis["confidence"] = 0.5
    
    return analysis

async def main():
    """Main function"""
    print("🚀 Starting Yasuo Real Data Fetcher...")
    results = await fetch_real_data()
    
    if results["status"] == "success":
        print("\n🎉 Yasuo real data fetching completed successfully!")
    else:
        print(f"\n❌ Yasuo real data fetching failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
