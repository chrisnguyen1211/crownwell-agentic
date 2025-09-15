#!/usr/bin/env python3
"""
J97 Test Script - Test with sample data
"""

import asyncio
import json
from datetime import datetime
from news_analyzer import NewsAnalyzer

# Sample articles for testing
sample_articles = [
    {
        'title': 'Ethereum 2.0 Merge Successfully Completed - Major Milestone Achieved',
        'description': 'The long-awaited Ethereum merge has been completed successfully, transitioning from Proof of Work to Proof of Stake consensus mechanism.',
        'url': 'https://example.com/eth-merge-success',
        'publishedAt': datetime.now().isoformat(),
        'source': 'CryptoNews',
        'api_source': 'test'
    },
    {
        'title': 'Ethereum Gas Fees Drop 90% After Latest Upgrade',
        'description': 'Ethereum gas fees have significantly decreased following the implementation of EIP-1559, making transactions more affordable for users.',
        'url': 'https://example.com/eth-gas-fees-drop',
        'publishedAt': datetime.now().isoformat(),
        'source': 'DeFiPulse',
        'api_source': 'test'
    },
    {
        'title': 'Major DeFi Protocol Launches on Ethereum Layer 2',
        'description': 'A leading DeFi protocol has successfully launched on Ethereum Layer 2, offering faster and cheaper transactions.',
        'url': 'https://example.com/defi-layer2-launch',
        'publishedAt': datetime.now().isoformat(),
        'source': 'DeFiNews',
        'api_source': 'test'
    },
    {
        'title': 'Ethereum Price Surges 15% on Institutional Adoption News',
        'description': 'Ethereum price has surged following news of major institutional adoption and increased staking rewards.',
        'url': 'https://example.com/eth-price-surge',
        'publishedAt': datetime.now().isoformat(),
        'source': 'CryptoMarket',
        'api_source': 'test'
    },
    {
        'title': 'Ethereum Smart Contract Security Audit Reveals Critical Vulnerabilities',
        'description': 'A recent security audit of popular Ethereum smart contracts has revealed several critical vulnerabilities that need immediate attention.',
        'url': 'https://example.com/eth-security-audit',
        'publishedAt': datetime.now().isoformat(),
        'source': 'SecurityNews',
        'api_source': 'test'
    }
]

async def test_j97_analysis():
    """Test J97 analysis with sample data"""
    print("🕵️ J97 News Analyst - Test Mode")
    print("="*50)
    
    # Initialize analyzer
    analyzer = NewsAnalyzer()
    
    # Generate report
    print("📊 Analyzing sample articles...")
    report = analyzer.generate_daily_report(sample_articles)
    
    # Print results
    print(f"\n📅 Date: {report['date']}")
    print(f"📰 Total Articles: {report['total_articles']}")
    
    trading_signal = report.get('trading_signal', {})
    print(f"💹 Trading Signal: {trading_signal.get('signal', 'HOLD')}")
    print(f"😊 Sentiment: {trading_signal.get('sentiment', 'neutral')}")
    print(f"🎯 Confidence: {trading_signal.get('confidence', 0.0):.2f}")
    
    print(f"\n📈 Categories:")
    for category, count in report.get('categories', {}).items():
        print(f"   {category}: {count}")
    
    print(f"\n😊 Sentiment Breakdown:")
    for sentiment, count in report.get('sentiment_breakdown', {}).items():
        print(f"   {sentiment}: {count}")
    
    print(f"\n🔑 Top Key Phrases:")
    for phrase, count in report.get('top_key_phrases', [])[:5]:
        print(f"   {phrase}: {count}")
    
    print(f"\n🔥 High Impact Articles: {report.get('high_impact_articles', 0)}")
    
    print(f"\n📰 High Impact Titles:")
    for title in report.get('high_impact_titles', [])[:3]:
        print(f"   • {title}")
    
    # Save test results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"j97_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Test results saved to {filename}")
    
    return report

if __name__ == "__main__":
    asyncio.run(test_j97_analysis())



