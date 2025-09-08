#!/usr/bin/env python3
"""
Yasuo Trend Dashboard
Real-time trend monitoring and visualization
"""

import asyncio
import sys
from datetime import datetime
import json

# Add the current directory to path
sys.path.insert(0, '.')

def display_trend_dashboard():
    """Display comprehensive trend dashboard"""
    print("🛡️ YASUO TREND DASHBOARD")
    print("=" * 80)
    print(f"⏰ Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        from trend_tracker import YasuoTrendTracker
        
        # Initialize trend tracker
        trend_tracker = YasuoTrendTracker()
        
        # Get data summary
        data_summary = trend_tracker.get_data_summary()
        
        print("📊 DATA STATUS:")
        print("-" * 40)
        print(f"  📈 Total Samples: {data_summary.get('total_samples', 0)}")
        print(f"  ⏰ Time Range: {data_summary.get('time_range_hours', 0):.1f} hours")
        print(f"  🎯 Analysis Ready: {'✅ YES' if data_summary.get('data_ready_for_analysis', False) else '❌ NO'}")
        print(f"  📋 Status: {data_summary.get('next_sample_needed_in', 'Ready for analysis')}")
        
        # Show latest data point
        if data_summary.get('latest_data'):
            latest = data_summary['latest_data']
            print(f"\n📊 LATEST DATA POINT:")
            print("-" * 40)
            print(f"  💰 ETF Flow: ${latest.get('etf_daily_flow', 0):,.0f}")
            print(f"  📈 Exchange Flow: {latest.get('exchange_net_flow', 0):,.0f} ETH")
            print(f"  🎯 Liveliness: {latest.get('liveliness_score', 0.5):.2f}")
            print(f"  🔄 Large Transfers: {latest.get('large_transfers_count', 0)}")
            print(f"  📊 Total Exchanges: {latest.get('total_exchanges', 0)}")
            print(f"  💎 Total Volume: {latest.get('total_volume', 0):,.0f} ETH")
        
        # Get trend analysis
        trend_analysis = trend_tracker.get_trend_analysis()
        
        if trend_analysis:
            print(f"\n🎯 TREND ANALYSIS:")
            print("-" * 40)
            
            # Trend direction with emoji
            direction_emoji = {"bullish": "🚀", "bearish": "📉", "neutral": "➡️"}
            direction = trend_analysis.trend_direction
            print(f"  📊 Direction: {direction_emoji.get(direction, '❓')} {direction.upper()}")
            print(f"  💪 Strength: {trend_analysis.trend_strength:.1%}")
            print(f"  🎯 Confidence: {trend_analysis.confidence:.1%}")
            print(f"  📝 Samples: {trend_analysis.sample_count}")
            print(f"  ⏰ Timeframe: {trend_analysis.timeframe_hours}h lookback")
            
            # Recommendation with styling
            recommendation = trend_analysis.recommendation
            if "BUY" in recommendation:
                rec_emoji = "🟢"
            elif "SELL" in recommendation:
                rec_emoji = "🔴"
            else:
                rec_emoji = "🟡"
            
            print(f"\n💼 RECOMMENDATION:")
            print("-" * 40)
            print(f"  {rec_emoji} {recommendation}")
            
            print(f"\n🔍 KEY INDICATORS:")
            print("-" * 40)
            for i, indicator in enumerate(trend_analysis.key_indicators, 1):
                print(f"  {i}. {indicator}")
        
        else:
            print(f"\n⚠️ TREND ANALYSIS:")
            print("-" * 40)
            print("  📊 Insufficient data for trend analysis")
            print(f"  📋 Need: {trend_tracker.MIN_SAMPLES} minimum samples")
            print(f"  📈 Have: {data_summary.get('total_samples', 0)} samples")
            print("  🎯 Recommendation: Continue collecting data")
        
        # Historical data visualization (text-based)
        if len(trend_tracker.historical_data) > 1:
            print(f"\n📈 HISTORICAL TRENDS (Last {min(10, len(trend_tracker.historical_data))} samples):")
            print("-" * 40)
            
            recent_data = trend_tracker.historical_data[-10:]
            
            print("  Time      | ETF Flow (M$) | Exchange (ETH) | Liveliness")
            print("  " + "-" * 58)
            
            for point in recent_data:
                time_str = datetime.fromisoformat(point.timestamp).strftime('%H:%M:%S')
                etf_flow_m = point.etf_daily_flow / 1000000  # Convert to millions
                
                # Format with appropriate signs and colors
                etf_sign = "+" if etf_flow_m >= 0 else "-"
                exch_sign = "+" if point.exchange_net_flow >= 0 else "-"
                
                print(f"  {time_str} | {etf_sign}{abs(etf_flow_m):7.1f}      | {exch_sign}{abs(point.exchange_net_flow):10.0f}   | {point.liveliness_score:.2f}")
        
        print(f"\n📁 Data stored in: {trend_tracker.data_file}")
        print("🔄 Run this dashboard regularly to monitor trends")
        
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
        import traceback
        traceback.print_exc()

async def run_data_collection():
    """Run continuous data collection"""
    print("\n🔄 STARTING CONTINUOUS DATA COLLECTION")
    print("=" * 60)
    print("Press Ctrl+C to stop data collection")
    
    try:
        from yasuo_onchain_analyst import YasuoOnChainAnalyst
        
        yasuo = YasuoOnChainAnalyst()
        
        collection_count = 0
        while True:
            collection_count += 1
            print(f"\n📊 Data Collection #{collection_count}")
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run quick analysis (includes trend tracking)
            await yasuo.run_quick_analysis()
            
            print("✅ Data point collected and saved")
            print("⏰ Waiting 30 minutes for next collection...")
            print("🎯 Run trend_dashboard.py to see latest trends")
            
            # Wait 30 minutes (1800 seconds)
            await asyncio.sleep(1800)  # 30 minutes
            
    except KeyboardInterrupt:
        print("\n⚠️ Data collection stopped by user")
    except Exception as e:
        print(f"❌ Collection Error: {e}")

def main():
    """Main dashboard function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--collect":
        # Run continuous data collection
        asyncio.run(run_data_collection())
    else:
        # Show dashboard
        display_trend_dashboard()
        
        print("\n" + "=" * 60)
        print("🎯 USAGE OPTIONS:")
        print("  python trend_dashboard.py           # Show current trends")
        print("  python trend_dashboard.py --collect # Start data collection")
        print("  python test_trend_tracking.py       # Test trend system")

if __name__ == "__main__":
    main()








