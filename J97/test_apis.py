#!/usr/bin/env python3
"""
J97 API Test Script - Test all 4 news APIs
"""

import asyncio
import logging
from news_crawler import NewsCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_all_apis():
    """Test all 4 news APIs"""
    print("🕵️ J97 API Test Suite")
    print("="*50)
    
    async with NewsCrawler() as crawler:
        # Test all APIs
        await crawler.test_all_apis()
        
        print("\n📊 API Status Summary:")
        print("-" * 30)
        
        working_count = 0
        for source, status in crawler.api_status.items():
            status_emoji = "✅" if status == 'working' else "❌" if status == 'no_key' else "⚠️"
            print(f"{status_emoji} {source.upper()}: {status}")
            if status == 'working':
                working_count += 1
        
        print(f"\n🎯 Working APIs: {working_count}/4")
        
        if working_count > 0:
            print("\n🔄 Testing actual news crawling...")
            articles = await crawler.crawl_all_sources()
            
            if articles:
                print(f"\n📰 Successfully crawled {len(articles)} articles!")
                
                # Show sample articles
                print("\n📄 Sample Articles:")
                for i, article in enumerate(articles[:3], 1):
                    print(f"\n{i}. {article.get('title', 'No title')}")
                    print(f"   Source: {article.get('source', 'Unknown')}")
                    print(f"   API: {article.get('api_source', 'Unknown')}")
                    print(f"   URL: {article.get('url', 'No URL')[:80]}...")
            else:
                print("⚠️ No articles found from any API")
        else:
            print("❌ No working APIs found")
    
    return working_count

async def test_individual_apis():
    """Test each API individually with detailed output"""
    print("\n🔍 Individual API Testing")
    print("="*50)
    
    async with NewsCrawler() as crawler:
        for source in ['gnews', 'newsapi', 'mediastack', 'newsdata']:
            print(f"\n🧪 Testing {source.upper()}...")
            print("-" * 20)
            
            # Test API
            is_working = await crawler.test_api(source)
            
            if is_working:
                print(f"✅ {source.upper()} is working!")
                
                # Try to get actual articles
                try:
                    if source == 'gnews':
                        articles = await crawler.crawl_gnews()
                    elif source == 'newsapi':
                        articles = await crawler.crawl_newsapi()
                    elif source == 'mediastack':
                        articles = await crawler.crawl_mediastack()
                    elif source == 'newsdata':
                        articles = await crawler.crawl_newsdata()
                    
                    if articles:
                        print(f"   📰 Found {len(articles)} articles")
                        if articles:
                            print(f"   📄 Sample: {articles[0].get('title', 'No title')[:60]}...")
                    else:
                        print("   ⚠️ No articles returned")
                        
                except Exception as e:
                    print(f"   ❌ Error getting articles: {e}")
            else:
                print(f"❌ {source.upper()} is not working")
            
            await asyncio.sleep(1)  # Rate limiting

if __name__ == "__main__":
    print("🚀 Starting J97 API Tests...")
    
    # Run comprehensive test
    working_count = asyncio.run(test_all_apis())
    
    # Run individual tests
    asyncio.run(test_individual_apis())
    
    print(f"\n🎉 Test Complete! {working_count}/4 APIs are working.")
    
    if working_count > 0:
        print("✅ J97 is ready for production use!")
    else:
        print("❌ Please check your API keys and try again.")



