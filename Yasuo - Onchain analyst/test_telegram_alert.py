#!/usr/bin/env python3
"""
Test Telegram Alert for Yasuo On-Chain Analyst
Sends a comprehensive portfolio report to verify Telegram integration
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from yasuo_onchain_analyst import YasuoOnChainAnalyst, LargeTransaction, WalletInfo, TransactionType

# Load environment variables
load_dotenv()

async def test_telegram_alert():
    """Test Telegram alert with a mock large transaction and real market data"""
    
    print("🧪 TESTING YASUO TELEGRAM ALERT")
    print("=" * 50)
    
    # Initialize Yasuo
    print("🛡️ Initializing Yasuo...")
    yasuo = YasuoOnChainAnalyst()

    # Setup Telegram bot
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token:
        yasuo.setup_telegram_bot(telegram_token)
        print("✅ Telegram bot configured")
    else:
        print("⚠️ Telegram bot token not found")
    
    # Create a mock large transaction
    print("📊 Creating mock large ETH transaction...")
    mock_transaction = LargeTransaction(
        hash="0x1234567890abcdef",
        timestamp=datetime.now(),
        block_number=21234567,
        sender_address="0xkraken456...def",
        receiver_address="0xwhale123...abc",
        eth_amount=2500.0,
        usd_value=10000000.0,  # $10M
        gas_price=30000000000,  # 30 gwei
        gas_used=21000,
        transaction_type=TransactionType.WHALE_ACCUMULATION,
        buyer_info=WalletInfo(
            address="0xwhale123...abc",
            entity_type="whale",
            entity_name="Unknown Whale",
            confidence=0.8,
            tags=["large_holder", "accumulator"]
        ),
        seller_info=WalletInfo(
            address="0xkraken456...def",
            entity_type="exchange",
            entity_name="Kraken Exchange",
            confidence=0.95,
            tags=["centralized_exchange", "high_volume"]
        )
    )
    
    # Get real market context
    print("📈 Fetching real market context...")
    try:
        # Get current market data
        exchange_flows = await yasuo.get_exchange_flows()
        etf_flows = await yasuo.get_etf_flows()
        liveliness = await yasuo.get_liveliness_metrics()
        advanced_metrics = await yasuo.get_advanced_metrics()
        
        print(f"✅ Exchange Flows: {exchange_flows.get('net_flow', 0):,.0f} ETH")
        print(f"✅ ETF Flows: ${etf_flows.get('daily_flow', 0):,.0f}")
        print(f"✅ Liveliness: {liveliness.get('liveliness_score', 0.5):.2f}")
        print(f"✅ Advanced Metrics: {advanced_metrics.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"⚠️ Error fetching market data: {e}")
        print("📊 Using fallback data for demo...")
        exchange_flows = {"net_flow": 5000, "data_source": "demo"}
        etf_flows = {"daily_flow": -50000000, "data_source": "demo"}
        liveliness = {"liveliness_score": 0.45, "data_source": "demo"}
        advanced_metrics = {"status": "demo", "data_source": "demo"}
    
    # Analyze market implications
    print("🔍 Analyzing market implications...")
    market_analysis = await yasuo.analyze_market_implications(
        mock_transaction, exchange_flows, etf_flows, liveliness
    )
    
    # Generate portfolio recommendation
    print("🎯 Generating portfolio recommendation...")
    portfolio_rec = yasuo.generate_portfolio_recommendation(
        mock_transaction, market_analysis, exchange_flows, etf_flows, liveliness
    )
    
    # Create comprehensive alert message
    print("📱 Creating alert message...")
    alert_message = yasuo.create_alert_message(
        mock_transaction, market_analysis, portfolio_rec
    )
    
    # Send Telegram alert
    print("🚀 Sending Telegram alert...")
    try:
        success = await yasuo.send_telegram_alert(alert_message)
        
        if success:
            print("✅ TELEGRAM ALERT SENT SUCCESSFULLY!")
            print("\n📱 Alert Details:")
            print(f"📊 Transaction: {mock_transaction.eth_amount:,.0f} ETH (${mock_transaction.usd_value:,.0f})")
            print(f"🔄 Direction: {mock_transaction.seller_info.entity_type} → {mock_transaction.buyer_info.entity_type}")
            print(f"📈 Market Sentiment: {market_analysis.sentiment}")
            print(f"🎯 Portfolio Action: {portfolio_rec.action}")
            print(f"🎯 Confidence: {portfolio_rec.confidence}")
            
            print("\n📲 Message sent to:")
            bot_token_preview = (os.getenv("TELEGRAM_BOT_TOKEN") or "")[:10]
            chat_id_value = os.getenv("TELEGRAM_CHAT_ID") or "unknown"
            print(f"🤖 Bot Token: {bot_token_preview}...")
            print(f"💬 Chat ID: {chat_id_value}")
            
        else:
            print("❌ TELEGRAM ALERT FAILED!")
            print("🔍 Check your Telegram bot token and chat ID")
            
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        print("🔍 Please verify:")
        print("   1. TELEGRAM_BOT_TOKEN in .env")
        print("   2. TELEGRAM_CHAT_ID in .env")
        print("   3. Bot has permission to send messages")
    
    print("\n🎯 TELEGRAM TEST COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_telegram_alert())
