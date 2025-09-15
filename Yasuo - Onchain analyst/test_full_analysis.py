#!/usr/bin/env python3
"""
Test Full Yasuo Analysis Pipeline
"""

import asyncio
import sys

# Add the current directory to path
sys.path.insert(0, '.')

async def test_full_analysis():
    """Test complete Yasuo analysis pipeline"""
    print("🛡️ YASUO FULL ANALYSIS TEST")
    print("=" * 60)

    try:
        from yasuo_onchain_analyst import YasuoOnChainAnalyst

        # Initialize Yasuo
        yasuo = YasuoOnChainAnalyst()
        print("✅ Yasuo initialized")

        # Run quick analysis (full pipeline)
        print("\n🔍 Running complete market analysis...")
        analysis_result = await yasuo.run_quick_analysis()
        
        print("\n📊 ANALYSIS RESULTS:")
        print("=" * 40)
        
        if analysis_result:
            print(f"✅ Analysis completed successfully!")
            print(f"📈 Recommendation: {analysis_result.get('recommendation', 'N/A')}")
            print(f"🎯 Confidence: {analysis_result.get('confidence', 0):.1%}")
            print(f"⚠️ Risk Level: {analysis_result.get('risk_level', 'N/A')}")
            print(f"⏰ Timeframe: {analysis_result.get('timeframe', 'N/A')}")
            print(f"💭 Reasoning: {analysis_result.get('reasoning', 'N/A')}")
        else:
            print("❌ Analysis returned no results")

        # Test individual components
        print("\n🔧 COMPONENT TEST:")
        print("=" * 30)

        # Test exchange flows
        print("📈 Exchange Flows:")
        exchange_data = await yasuo.get_exchange_flows()
        print(f"  Net Flow: {exchange_data.get('net_flow', 0):,.0f} ETH")
        print(f"  Exchanges: {exchange_data.get('total_exchanges_analyzed', 0)}")

        # Test ETF flows  
        print("\n📊 ETF Flows:")
        etf_data = await yasuo.get_etf_flows()
        print(f"  Daily Flow: ${etf_data.get('daily_flow', 0):,.0f}")
        print(f"  Direction: {etf_data.get('flow_direction', 'neutral')}")

        # Test liveliness
        print("\n🎯 Liveliness:")
        liveliness_data = await yasuo.get_liveliness_metrics()
        print(f"  Score: {liveliness_data.get('liveliness_score', 0.5):.2f}")
        print(f"  Category: {liveliness_data.get('liveliness_category', 'moderate')}")

        print("\n✅ Full analysis test completed!")

    except Exception as e:
        print(f"❌ Error in full analysis test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_analysis())











