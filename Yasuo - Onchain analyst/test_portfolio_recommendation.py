#!/usr/bin/env python3
"""
Test Portfolio Recommendation Logic
"""

import asyncio
import sys

# Add the current directory to path
sys.path.insert(0, '.')

async def test_portfolio_recommendation():
    """Test portfolio recommendation with current market data"""
    print("🛡️ YASUO PORTFOLIO RECOMMENDATION TEST")
    print("=" * 60)

    try:
        from yasuo_onchain_analyst import YasuoOnChainAnalyst

        # Initialize Yasuo
        yasuo = YasuoOnChainAnalyst()
        print("✅ Yasuo initialized")

        # Get current market data
        print("\n📊 Fetching current market data...")
        
        exchange_flows = await yasuo.get_exchange_flows()
        etf_flows = await yasuo.get_etf_flows()
        liveliness_metrics = await yasuo.get_liveliness_metrics()

        print("\n🔍 CURRENT MARKET STATE:")
        print("=" * 40)
        print(f"📈 Exchange Net Flow: {exchange_flows.get('net_flow', 0):,.0f} ETH")
        print(f"📊 ETF Daily Flow: ${etf_flows.get('daily_flow', 0):,.0f}")
        print(f"🎯 Liveliness Score: {liveliness_metrics.get('liveliness_score', 0.5):.2f}")

        # Create a mock transaction for testing
        from yasuo_onchain_analyst import LargeTransaction, WalletInfo, TransactionType, EntityType
        
        from datetime import datetime
        
        # Create mock wallet infos
        sender_wallet = WalletInfo(
            address="0xwhale123...",
            entity_type=EntityType.WHALE,
            entity_name="Large Whale",
            confidence=0.9,
            tags=["whale", "holder"]
        )
        
        receiver_wallet = WalletInfo(
            address="0xexchange456...",
            entity_type=EntityType.EXCHANGE,
            entity_name="Major Exchange",
            confidence=0.95,
            tags=["exchange", "centralized"]
        )
        
        mock_transaction = LargeTransaction(
            hash="0x123...test",
            timestamp=datetime.now(),
            block_number=12345678,
            sender_address="0xwhale123...",
            receiver_address="0xexchange456...",
            eth_amount=1500.0,  # 1500 ETH
            usd_value=6000000.0,  # $6M at $4000/ETH
            gas_price=20,
            gas_used=21000,
            transaction_type=TransactionType.EXCHANGE_DEPOSIT,
            buyer_info=receiver_wallet,  # Exchange is receiving (buying)
            seller_info=sender_wallet   # Whale is sending (selling)
        )

        # Analyze market implications
        print("\n🧠 MARKET IMPLICATIONS ANALYSIS:")
        print("=" * 40)
        
        market_analysis = await yasuo.analyze_market_implications(
            transaction=mock_transaction,
            exchange_flows=exchange_flows,
            etf_flows=etf_flows,
            liveliness_metrics=liveliness_metrics
        )
        
        print(f"💭 Sentiment: {market_analysis.sentiment}")
        print(f"🎯 Confidence: {market_analysis.confidence:.1%}")
        print(f"⚠️ Risk Level: {market_analysis.risk_level}")
        print(f"📝 Key Signals: {', '.join(market_analysis.key_signals)}")
        print(f"⏰ Timeframe Impact: {market_analysis.timeframe_impact}")

        # Generate portfolio recommendation
        print("\n📋 PORTFOLIO RECOMMENDATION:")
        print("=" * 40)
        
        recommendation = yasuo.generate_portfolio_recommendation(
            transaction=mock_transaction,
            implication=market_analysis,
            exchange_flows=exchange_flows,
            etf_flows=etf_flows,
            liveliness_metrics=liveliness_metrics
        )
        
        print(f"📈 Action: {recommendation.action}")
        print(f"🎯 Confidence: {recommendation.confidence:.1%}")
        print(f"⚠️ Risk Assessment: {recommendation.risk_assessment}")
        print(f"⏰ Timeframe: {recommendation.timeframe}")
        print(f"💭 Reasoning: {recommendation.reasoning}")

        # Test alert message creation
        print("\n📱 ALERT MESSAGE PREVIEW:")
        print("=" * 40)
        
        alert_message = yasuo.create_alert_message(mock_transaction, market_analysis, recommendation)
        print(alert_message)

        print("\n✅ Portfolio recommendation test completed!")

    except Exception as e:
        print(f"❌ Error in portfolio recommendation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_portfolio_recommendation())
