#!/usr/bin/env python3
"""
Yasuo Real Data Demo
Demonstrates the upgraded Yasuo with real data sources:
- Bitquery for Exchange Flows
- farside.co.uk for ETF Flows
- Bitquery GraphQL for Liveliness Metrics
"""

import asyncio
import sys
from datetime import datetime

# Add the current directory to path so we can import yasuo_onchain_analyst
sys.path.insert(0, '.')

async def demo_real_data():
    """Demonstrate the upgraded Yasuo with real data sources"""

    print("🛡️ YASUO REAL DATA DEMO - UPGRADED")
    print("=" * 60)
    print("🎯 New Features:")
    print("  ✅ Bitquery for Exchange Flows")
    print("  ✅ farside.co.uk for ETF Flows")
    print("  ✅ Bitquery GraphQL for Liveliness")
    print("=" * 60)

    try:
        from yasuo_onchain_analyst import YasuoOnChainAnalyst

        # Initialize Yasuo
        yasuo = YasuoOnChainAnalyst()

        print("📊 Fetching real market data...\n")

        # Get exchange flows (Bitquery - ALL EXCHANGES)
        print("📈 EXCHANGE FLOWS (Bitquery - All Exchanges Analysis):")
        try:
            exchange_flows = await yasuo.get_exchange_flows()
            print(f"  • Net Flow: {exchange_flows.get('net_flow', 0):,.0f} ETH")
            print(f"  • Total Inflows: {exchange_flows.get('total_inflows', 0):,.0f} ETH")
            print(f"  • Total Outflows: {exchange_flows.get('total_outflows', 0):,.0f} ETH")
            print(f"  • Predefined Exchanges: {exchange_flows.get('predefined_exchanges', 0)}")
            print(f"  • Detected Exchanges: {exchange_flows.get('detected_exchanges', 0)}")
            print(f"  • Total Exchanges: {exchange_flows.get('total_exchanges_analyzed', 0)}")
            print(f"  • Large Transfers (100+ ETH): {exchange_flows.get('large_transfers_count', 0)}")
            print(f"  • Transfers Analyzed: {exchange_flows.get('transfers_analyzed', 0)}")
            print(f"  • Data Source: {exchange_flows.get('data_source', 'unknown')}")
            print("  ✅ Bitquery all-exchanges integration working!")
        except Exception as e:
            print(f"  ❌ Bitquery exchange flows failed: {e}")
        print()

        # Get ETF flows (farside.co.uk - ETH ONLY, LATEST DAY)
        print("📊 ETH ETF FLOWS (farside.co.uk - Latest Day Only):")
        try:
            etf_flows = await yasuo.get_etf_flows()
            print(f"  • ETH Daily Flow: ${etf_flows.get('daily_flow', 0):,.0f}")
            print(f"  • Flow Direction: {etf_flows.get('flow_direction', 'neutral')}")
            print(f"  • Latest Day Only: {etf_flows.get('latest_day_only', False)}")
            print(f"  • ETF Count: {etf_flows.get('etf_count', 0)}")
            print(f"  • Data Source: {etf_flows.get('data_source', 'unknown')}")
            print("  ✅ farside.co.uk ETH-only scraping working!")
        except Exception as e:
            print(f"  ❌ farside.co.uk ETF scraping failed: {e}")
        print()

        # Get liveliness metrics (Bitquery GraphQL)
        print("🎯 ETH HOLDER LIVELINESS (Bitquery GraphQL):")
        try:
            liveliness = await yasuo.get_liveliness_metrics(days_back=30)
            print(f"  • Liveliness Score: {liveliness.get('liveliness_score', 0.5):.2f}")
            print(f"  • Category: {liveliness.get('liveliness_category', 'moderate')}")
            print(f"  • Active Addresses (24h): {liveliness.get('active_addresses_24h', 0):,}")
            print(f"  • Dormant Addresses Reactivated: {liveliness.get('dormant_addresses_reactivated', 0):,}")
            print(f"  • Total Addresses Analyzed: {liveliness.get('total_addresses_analyzed', 0):,}")
            print(f"  • Total Transfers Analyzed: {liveliness.get('total_transfers_analyzed', 0):,}")
            print(f"  • Total Volume ETH: {liveliness.get('total_volume_eth', 0):,.0f}")
            print(f"  • Avg Coin Age Moved: {liveliness.get('avg_coin_age_moved_days', 0):.0f} days")
            print(f"  • Data Source: {liveliness.get('data_source', 'unknown')}")
            print("  ✅ Bitquery GraphQL liveliness working!")
        except Exception as e:
            print(f"  ❌ Bitquery GraphQL liveliness failed: {e}")
        print()

        # Market analysis interpretation
        print("🔍 COMPREHENSIVE MARKET ANALYSIS:")
        print("=" * 50)

        # Overall market sentiment based on all data sources
        try:
            # Simple sentiment analysis based on combined data
            exchange_net = exchange_flows.get('net_flow', 0)
            etf_daily = etf_flows.get('daily_flow', 0)
            liveliness_score = liveliness.get('liveliness_score', 0.5)

            bullish_signals = 0
            bearish_signals = 0

            # Exchange flow analysis
            if exchange_net > 10000:
                print("📈 EXCHANGE FLOWS: Large outflows indicate strong accumulation")
                bullish_signals += 1
            elif exchange_net < -10000:
                print("📉 EXCHANGE FLOWS: Large inflows indicate profit-taking")
                bearish_signals += 1
            else:
                print("📊 EXCHANGE FLOWS: Balanced flows, market equilibrium")

            # ETF flow analysis
            if etf_daily > 50000000:
                print("🚀 ETF FLOWS: Strong institutional buying momentum")
                bullish_signals += 1
            elif etf_daily < -20000000:
                print("⚠️ ETF FLOWS: Institutional selling pressure")
                bearish_signals += 1
            else:
                print("📊 ETF FLOWS: Moderate institutional activity")

            # Liveliness analysis
            if liveliness_score < 0.3:
                print("🐌 LIVELINESS: Very low activity - long-term holders accumulating")
                bullish_signals += 1
            elif liveliness_score > 0.8:
                print("🚀 LIVELINESS: High activity - profit-taking/distribution")
                bearish_signals += 1
            else:
                print("📊 LIVELINESS: Moderate activity - balanced market")

            # Overall sentiment
            print("\n🎯 OVERALL MARKET SENTIMENT:")
            if bullish_signals > bearish_signals:
                print("🚀 BULLISH: Multiple signals point to accumulation and upside potential")
            elif bearish_signals > bullish_signals:
                print("⚠️ BEARISH: Profit-taking and selling pressure detected")
            else:
                print("📊 NEUTRAL: Mixed signals suggest market consolidation")

            print(f"📊 Signal Summary: {bullish_signals} bullish, {bearish_signals} bearish")

        except Exception as e:
            print(f"❌ Market analysis failed: {e}")

        print()
        print("✅ Real data demo completed successfully!")
        print("🎯 Yasuo now uses FOCUSED real data from:")
        print("   • Bitquery API for ALL exchange analysis (predefined + detected)")
        print("   • farside.co.uk for ETH ETF ONLY (latest day green row)")
        print("   • Bitquery GraphQL for liveliness metrics")
        print("   • NO combined BTC/ETH flows - ETH focused analysis!")

    except Exception as e:
        print(f"❌ Error in real data demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_real_data())
