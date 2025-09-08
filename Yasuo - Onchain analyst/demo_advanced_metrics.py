#!/usr/bin/env python3
"""
Demo Advanced Metrics for Long-term ETH Strategy
Shows options, futures, exchange metrics, and long-term holder data
"""

import asyncio
import sys
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, '.')

async def demo_advanced_metrics():
    """Demo comprehensive advanced metrics"""
    print("🛡️ YASUO ADVANCED METRICS DEMO")
    print("=" * 80)
    print("🎯 Long-term ETH Strategy Metrics:")
    print("  📊 Options & Futures Data")
    print("  🏦 Exchange & Stablecoin Metrics")
    print("  💎 Long-term Holder Analysis")
    print("=" * 80)

    try:
        # Test standalone advanced metrics tracker
        print("\n📊 TESTING ADVANCED METRICS TRACKER:")
        print("-" * 50)
        
        from advanced_metrics_tracker import AdvancedMetricsTracker
        
        async with AdvancedMetricsTracker() as tracker:
            
            # Options Data
            print("\n📈 ETH OPTIONS MARKET:")
            options = await tracker.get_options_data()
            print(f"  💰 Open Interest: {options.open_interest:,.0f}")
            print(f"  📊 Put/Call Ratio: {options.put_call_ratio:.2f}")
            
            if options.put_call_ratio > 1.0:
                sentiment = "🐻 BEARISH (More puts than calls)"
            elif options.put_call_ratio < 0.5:
                sentiment = "🐂 BULLISH (More calls than puts)"
            else:
                sentiment = "😐 NEUTRAL"
            print(f"  🎯 Options Sentiment: {sentiment}")
            
            print(f"  📈 Implied Volatility: {options.implied_volatility:.1%}")
            print(f"  🎯 Max Pain: ${options.max_pain:,.0f}")
            print(f"  📡 Source: {options.data_source}")
            
            # Futures Data
            print("\n🚀 ETH FUTURES MARKET:")
            futures = await tracker.get_futures_data()
            print(f"  💰 Open Interest: {futures.open_interest:,.0f}")
            print(f"  💸 Funding Rate: {futures.funding_rate:.4f} ({futures.funding_rate*100:.2f}%)")
            
            if futures.funding_rate > 0.01:
                funding_sentiment = "🐂 BULLISH (Longs pay shorts)"
            elif futures.funding_rate < -0.01:
                funding_sentiment = "🐻 BEARISH (Shorts pay longs)"
            else:
                funding_sentiment = "😐 NEUTRAL"
            print(f"  🎯 Funding Sentiment: {funding_sentiment}")
            
            print(f"  📊 Market Structure: {futures.contango_backwardation.upper()}")
            print(f"  📡 Source: {futures.data_source}")
            
            # Exchange Metrics
            print("\n🏦 EXCHANGE & MARKET METRICS:")
            exchange = await tracker.get_exchange_metrics()
            print(f"  🏛️ Total ETH Reserves: {exchange.total_eth_reserves:,.0f} ETH")
            print(f"  📊 7d Reserve Change: {exchange.exchange_reserves_change_7d:+,.0f} ETH")
            
            if exchange.exchange_reserves_change_7d < -10000:
                reserve_sentiment = "🐂 BULLISH (Large outflows - accumulation)"
            elif exchange.exchange_reserves_change_7d > 10000:
                reserve_sentiment = "🐻 BEARISH (Large inflows - selling)"
            else:
                reserve_sentiment = "😐 NEUTRAL (Stable reserves)"
            print(f"  🎯 Reserve Sentiment: {reserve_sentiment}")
            
            print(f"  💰 Stablecoin Supply: ${exchange.stablecoin_supply:,.0f}")
            print(f"  🔄 DEX Volume 24h: ${exchange.dex_volume_24h:,.0f}")
            print(f"  🏢 CEX Volume 24h: ${exchange.cex_volume_24h:,.0f}")
            print(f"  📊 DEX/CEX Ratio: {exchange.dex_cex_ratio:.1%}")
            
            if exchange.dex_cex_ratio > 0.4:
                dex_sentiment = "🔥 HIGH DeFi Activity"
            elif exchange.dex_cex_ratio < 0.2:
                dex_sentiment = "🏢 CEX Dominated"
            else:
                dex_sentiment = "⚖️ Balanced"
            print(f"  🎯 DeFi Sentiment: {dex_sentiment}")
            
            print(f"  📡 Source: {exchange.data_source}")
            
            # Long-term Holder Data
            print("\n💎 LONG-TERM HOLDER ANALYSIS:")
            lth = await tracker.get_long_term_holder_data()
            print(f"  📊 LTH Supply (1y+): {lth.lth_supply_1y:,.0f} ETH ({lth.lth_supply_percentage:.1f}%)")
            print(f"  💰 Market Cap: ${lth.market_cap:,.0f}")
            print(f"  🔍 Realized Cap: ${lth.realized_cap:,.0f}")
            print(f"  📈 MVRV Ratio: {lth.mvrv_ratio:.2f}")
            
            if lth.mvrv_ratio > 3.0:
                mvrv_sentiment = "🚨 OVERVALUED (High risk)"
            elif lth.mvrv_ratio < 1.0:
                mvrv_sentiment = "💎 UNDERVALUED (Opportunity)"
            elif lth.mvrv_ratio < 1.5:
                mvrv_sentiment = "🟢 FAIR VALUE (Good entry)"
            else:
                mvrv_sentiment = "🟡 ELEVATED (Caution)"
            print(f"  🎯 MVRV Signal: {mvrv_sentiment}")
            
            print(f"  💰 Supply in Profit: {lth.supply_in_profit_ratio:.1%}")
            print(f"  📉 Supply in Loss: {lth.supply_in_loss_ratio:.1%}")
            print(f"  🔄 Coin Days Destroyed: {lth.coin_days_destroyed:,.0f}")
            print(f"  📊 Hodler Position Change: {lth.hodler_net_position_change:+,.0f} ETH")
            
            if lth.hodler_net_position_change < -50000:
                hodler_sentiment = "🐻 BEARISH (Heavy selling)"
            elif lth.hodler_net_position_change > 50000:
                hodler_sentiment = "🐂 BULLISH (Heavy accumulation)"
            else:
                hodler_sentiment = "😐 NEUTRAL (Balanced)"
            print(f"  🎯 Hodler Sentiment: {hodler_sentiment}")
            
            print(f"  📡 Source: {lth.data_source}")

        # Test integrated with Yasuo
        print("\n🛡️ TESTING YASUO INTEGRATION:")
        print("-" * 50)
        
        from yasuo_onchain_analyst import YasuoOnChainAnalyst
        
        yasuo = YasuoOnChainAnalyst()
        advanced_data = await yasuo.get_advanced_metrics()
        
        print(f"✅ Integration Status: {advanced_data['status']}")
        print(f"⏰ Data Timestamp: {advanced_data['timestamp']}")
        
        # Overall Long-term Strategy Assessment
        print("\n🎯 LONG-TERM ETH STRATEGY ASSESSMENT:")
        print("=" * 60)
        
        # Scoring system
        bullish_signals = 0
        bearish_signals = 0
        
        # Options sentiment
        put_call = advanced_data['options']['put_call_ratio']
        if put_call < 0.5:
            print("📈 Options: BULLISH (Call dominance)")
            bullish_signals += 1
        elif put_call > 1.0:
            print("📉 Options: BEARISH (Put dominance)")
            bearish_signals += 1
        else:
            print("📊 Options: NEUTRAL")
        
        # Futures sentiment
        funding = advanced_data['futures']['funding_rate']
        if funding > 0.005:
            print("📈 Futures: BULLISH (High funding)")
            bullish_signals += 1
        elif funding < -0.005:
            print("📉 Futures: BEARISH (Negative funding)")
            bearish_signals += 1
        else:
            print("📊 Futures: NEUTRAL")
        
        # Exchange reserves
        reserve_change = advanced_data['exchange_metrics']['reserves_change_7d']
        if reserve_change < -25000:
            print("📈 Reserves: BULLISH (Large outflows)")
            bullish_signals += 1
        elif reserve_change > 25000:
            print("📉 Reserves: BEARISH (Large inflows)")
            bearish_signals += 1
        else:
            print("📊 Reserves: NEUTRAL")
        
        # MVRV ratio
        mvrv = advanced_data['long_term_holders']['mvrv_ratio']
        if mvrv < 1.0:
            print("📈 MVRV: BULLISH (Undervalued)")
            bullish_signals += 2  # Double weight for MVRV
        elif mvrv > 3.0:
            print("📉 MVRV: BEARISH (Overvalued)")
            bearish_signals += 2
        elif mvrv < 1.5:
            print("📈 MVRV: BULLISH (Fair value)")
            bullish_signals += 1
        else:
            print("📊 MVRV: NEUTRAL")
        
        # Long-term holder behavior
        lth_change = advanced_data['long_term_holders']['hodler_net_position_change']
        if lth_change > 25000:
            print("📈 LTH Behavior: BULLISH (Accumulation)")
            bullish_signals += 1
        elif lth_change < -25000:
            print("📉 LTH Behavior: BEARISH (Distribution)")
            bearish_signals += 1
        else:
            print("📊 LTH Behavior: NEUTRAL")
        
        # Final assessment
        print(f"\n🎯 SIGNAL SUMMARY: {bullish_signals} Bullish | {bearish_signals} Bearish")
        
        if bullish_signals >= bearish_signals + 2:
            strategy = "🚀 STRONG BUY - Excellent long-term opportunity"
        elif bullish_signals > bearish_signals:
            strategy = "📈 BUY - Favorable long-term setup"
        elif bearish_signals > bullish_signals:
            strategy = "📉 HOLD/REDUCE - Risk management advised"
        elif bearish_signals >= bullish_signals + 2:
            strategy = "🚨 SELL - High risk environment"
        else:
            strategy = "😐 HOLD - Mixed signals, wait for clarity"
        
        print(f"💼 LONG-TERM STRATEGY: {strategy}")
        
        # Risk assessment
        total_signals = bullish_signals + bearish_signals
        if total_signals >= 6:
            confidence = "HIGH"
        elif total_signals >= 4:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        print(f"🎯 CONFIDENCE LEVEL: {confidence}")
        
        print("\n✅ Advanced metrics demo completed successfully!")
        print("🎯 These metrics provide comprehensive long-term ETH strategy insights!")

    except Exception as e:
        print(f"❌ Error in advanced metrics demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_advanced_metrics())








