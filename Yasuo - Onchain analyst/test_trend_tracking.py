#!/usr/bin/env python3
"""
Test Yasuo Trend Tracking System
"""

import asyncio
import sys
import time
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, '.')

async def test_trend_tracking():
    """Test trend tracking functionality"""
    print("🛡️ YASUO TREND TRACKING TEST")
    print("=" * 60)

    try:
        from yasuo_onchain_analyst import YasuoOnChainAnalyst
        from trend_tracker import YasuoTrendTracker

        # Initialize components
        yasuo = YasuoOnChainAnalyst()
        trend_tracker = YasuoTrendTracker()
        
        print("✅ Yasuo and Trend Tracker initialized")
        
        # Get current data summary
        print("\n📊 CURRENT TREND DATA STATUS:")
        print("=" * 40)
        
        data_summary = trend_tracker.get_data_summary()
        print(f"📈 Total Samples: {data_summary.get('total_samples', 0)}")
        print(f"📊 Data Ready: {data_summary.get('data_ready_for_analysis', False)}")
        print(f"🎯 Next Sample: {data_summary.get('next_sample_needed_in', 'N/A')}")
        
        if data_summary.get('total_samples', 0) > 0:
            print(f"⏰ Time Range: {data_summary.get('time_range_hours', 0):.1f} hours")
            latest = data_summary.get('latest_data', {})
            print(f"💰 Latest ETF Flow: ${latest.get('etf_daily_flow', 0):,.0f}")
            print(f"📈 Latest Exchange Flow: {latest.get('exchange_net_flow', 0):,.0f} ETH")

        # Collect multiple data points for trend demo
        print("\n🔄 COLLECTING DATA SAMPLES FOR TREND ANALYSIS:")
        print("=" * 50)
        
        sample_count = 6  # Collect 6 samples for demo
        for i in range(sample_count):
            print(f"\n📊 Sample {i+1}/{sample_count}:")
            
            # Get fresh market data
            exchange_flows = await yasuo.get_exchange_flows()
            etf_flows = await yasuo.get_etf_flows()
            liveliness_metrics = await yasuo.get_liveliness_metrics()
            
            # Add to trend tracker
            trend_tracker.add_data_point(exchange_flows, etf_flows, liveliness_metrics)
            
            print(f"  • Exchange Net Flow: {exchange_flows.get('net_flow', 0):,.0f} ETH")
            print(f"  • ETF Daily Flow: ${etf_flows.get('daily_flow', 0):,.0f}")
            print(f"  • Liveliness Score: {liveliness_metrics.get('liveliness_score', 0.5):.2f}")
            print(f"  • Large Transfers: {exchange_flows.get('large_transfers_count', 0)}")
            
            # Check if we can do trend analysis yet
            current_summary = trend_tracker.get_data_summary()
            total_samples = current_summary.get('total_samples', 0)
            print(f"  • Total Samples: {total_samples}")
            
            # Try trend analysis if we have enough data
            if total_samples >= trend_tracker.MIN_SAMPLES:
                trend_analysis = trend_tracker.get_trend_analysis()
                if trend_analysis:
                    print(f"  ✅ Trend: {trend_analysis.trend_direction} ({trend_analysis.trend_strength:.1%})")
                    print(f"  📋 Recommendation: {trend_analysis.recommendation}")
            else:
                print(f"  ⏳ Need {trend_tracker.MIN_SAMPLES - total_samples} more samples")
            
            # Wait a bit between samples (simulate time passing)
            if i < sample_count - 1:
                print("    ⏰ Waiting 2 seconds for next sample...")
                time.sleep(2)

        # Final trend analysis
        print("\n🎯 FINAL TREND ANALYSIS:")
        print("=" * 40)
        
        final_trend = trend_tracker.get_trend_analysis()
        if final_trend:
            print(f"📊 Trend Direction: {final_trend.trend_direction.upper()}")
            print(f"💪 Trend Strength: {final_trend.trend_strength:.1%}")
            print(f"🎯 Confidence: {final_trend.confidence:.1%}")
            print(f"📈 Recommendation: {final_trend.recommendation}")
            print(f"📝 Sample Count: {final_trend.sample_count}")
            print(f"⏰ Timeframe: {final_trend.timeframe_hours} hours")
            
            print("\n🔍 Key Indicators:")
            for indicator in final_trend.key_indicators:
                print(f"  • {indicator}")
        else:
            print("❌ Insufficient data for trend analysis")

        # Test with Yasuo integration
        print("\n🔗 YASUO INTEGRATED TREND ANALYSIS:")
        print("=" * 40)
        
        print("Running Yasuo quick analysis with trend tracking...")
        result = await yasuo.run_quick_analysis()
        
        if result:
            print("✅ Yasuo analysis completed with trend tracking")
        else:
            print("⚠️ Yasuo analysis completed but no large transactions found")

        # Show final data summary
        print("\n📊 FINAL DATA SUMMARY:")
        print("=" * 30)
        
        final_summary = trend_tracker.get_data_summary()
        print(f"📈 Total Samples: {final_summary.get('total_samples', 0)}")
        print(f"📊 Ready for Analysis: {final_summary.get('data_ready_for_analysis', False)}")
        print(f"⏰ Time Range: {final_summary.get('time_range_hours', 0):.1f} hours")

        print("\n✅ Trend tracking test completed!")
        print("💾 Historical data saved to yasuo_trend_data.json")

    except Exception as e:
        print(f"❌ Error in trend tracking test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_trend_tracking())











