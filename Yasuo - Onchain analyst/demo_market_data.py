#!/usr/bin/env python3
"""
Yasuo Market Data Demo
Demonstrates the new ETH ETF flows, exchange flows, and liveliness features
"""

import asyncio
import sys
from datetime import datetime

# Add the current directory to path so we can import yasuo_onchain_analyst
sys.path.insert(0, '.')

async def demo_market_data():
    """Demonstrate the new market data features"""

    print("🛡️ YASUO MARKET DATA DEMO")
    print("=" * 50)

    try:
        from yasuo_onchain_analyst import YasuoOnChainAnalyst

        # Initialize Yasuo
        yasuo = YasuoOnChainAnalyst()

        print("📊 Fetching market context data...\n")

        # Get exchange flows
        print("📈 EXCHANGE FLOWS:")
        exchange_flows = await yasuo.get_exchange_flows()
        print(f"  • Net Flow: {exchange_flows.get('net_flow', 0):,.0f} ETH")
        print(f"  • Total Inflows: {exchange_flows.get('total_inflows', 0):,.0f} ETH")
        print(f"  • Total Outflows: {exchange_flows.get('total_outflows', 0):,.0f} ETH")
        print(f"  • Data Source: {exchange_flows.get('data_source', 'unknown')}")
        print(f"  • Exchanges Tracked: {exchange_flows.get('exchange_count', 0)}")
        print()

        # Get ETF flows
        print("📊 ETH ETF FLOWS:")
        etf_flows = await yasuo.get_etf_flows()
        print(f"  • Daily Flow: ${etf_flows.get('daily_flow', 0):,.0f}")
        print(f"  • Weekly Flow: ${etf_flows.get('weekly_flow', 0):,.0f}")
        print(f"  • Monthly Flow: ${etf_flows.get('monthly_flow', 0):,.0f}")
        print(f"  • Assets Under Management: ${etf_flows.get('aum', 0):,.0f}")
        print(f"  • Flow Direction: {etf_flows.get('flow_direction', 'neutral')}")
        print(f"  • ETFs Tracked: {etf_flows.get('etf_count', 0)}")
        print(f"  • Providers: {etf_flows.get('providers_count', 0)}")
        print()

        # Get liveliness metrics
        print("🎯 ETH HOLDER LIVELINESS:")
        liveliness = await yasuo.get_liveliness_metrics(days_back=30)
        print(f"  • Liveliness Score: {liveliness.get('liveliness_score', 0.5):.2f}")
        print(f"  • Category: {liveliness.get('liveliness_category', 'moderate')}")
        print(f"  • Active Addresses (24h): {liveliness.get('active_addresses_24h', 0):,}")
        print(f"  • Dormant Addresses Reactivated: {liveliness.get('dormant_addresses_reactivated', 0):,}")
        print(f"  • Avg Coin Age Moved: {liveliness.get('avg_coin_age_moved_days', 0):.0f} days")
        print(f"  • Analysis Period: {liveliness.get('analysis_period_days', 30)} days")
        print()

        # Market analysis interpretation
        print("🔍 MARKET ANALYSIS INTERPRETATION:")
        print("=" * 40)

        # Exchange flow analysis
        net_flow = exchange_flows.get('net_flow', 0)
        if net_flow > 10000:
            print("📈 EXCHANGE FLOWS: Large outflows indicate accumulation")
        elif net_flow < -10000:
            print("📉 EXCHANGE FLOWS: Large inflows indicate profit-taking")
        else:
            print("📊 EXCHANGE FLOWS: Balanced flows, consolidation")

        # ETF flow analysis
        etf_daily = etf_flows.get('daily_flow', 0)
        if etf_daily > 50000000:
            print("🚀 ETF FLOWS: Strong institutional buying")
        elif etf_daily < -20000000:
            print("⚠️ ETF FLOWS: Institutional selling pressure")
        else:
            print("📊 ETF FLOWS: Moderate institutional activity")

        # Liveliness analysis
        liveliness_score = liveliness.get('liveliness_score', 0.5)
        if liveliness_score < 0.3:
            print("🐌 LIVELINESS: Low activity - long-term holders accumulating")
        elif liveliness_score > 0.8:
            print("🚀 LIVELINESS: High activity - profit-taking/distribution")
        else:
            print("📊 LIVELINESS: Moderate activity - balanced market")

        print()
        print("✅ Market data demo completed successfully!")

    except Exception as e:
        print(f"❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_market_data())

