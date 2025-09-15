#!/usr/bin/env python3
"""
J97 Article Viewer - Show detailed articles that J97 selected to read
"""

import asyncio
import json
from datetime import datetime
from news_crawler import NewsCrawler
from news_analyzer import NewsAnalyzer

async def view_j97_articles():
    """View detailed articles that J97 selected"""
    print("🕵️ J97 Article Selection Analysis")
    print("=" * 60)
    
    async with NewsCrawler() as crawler:
        # Test all APIs first
        await crawler.test_all_apis()
        
        # Get working APIs
        working_apis = crawler.get_working_apis()
        print(f"📡 Working APIs: {', '.join(working_apis)}")
        print()
        
        all_articles = []
        
        # Crawl from each API individually to see what J97 selects
        for source in working_apis:
            print(f"🔍 Crawling {source.upper()}...")
            print("-" * 40)
            
            try:
                if source == 'gnews':
                    articles = await crawler.crawl_gnews()
                elif source == 'newsapi':
                    articles = await crawler.crawl_newsapi()
                elif source == 'mediastack':
                    articles = await crawler.crawl_mediastack()
                elif source == 'newsdata':
                    articles = await crawler.crawl_newsdata()
                else:
                    continue
                
                if articles:
                    print(f"✅ Found {len(articles)} articles from {source.upper()}")
                    
                    # Show first 3 articles from each source
                    for i, article in enumerate(articles[:3], 1):
                        print(f"\n{i}. {article.get('title', 'No title')}")
                        print(f"   Source: {article.get('source', 'Unknown')}")
                        print(f"   URL: {article.get('url', 'No URL')[:80]}...")
                        print(f"   Published: {article.get('publishedAt', 'Unknown')}")
                        if article.get('description'):
                            desc = article['description'][:100] + "..." if len(article['description']) > 100 else article['description']
                            print(f"   Description: {desc}")
                    
                    if len(articles) > 3:
                        print(f"   ... and {len(articles) - 3} more articles")
                    
                    all_articles.extend(articles)
                else:
                    print(f"⚠️ No articles found from {source.upper()}")
                
                print()
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error crawling {source.upper()}: {e}")
                continue
        
        print(f"📊 Total Articles Selected: {len(all_articles)}")
        
        # Analyze articles with J97's analyzer
        if all_articles:
            print("\n🧠 J97 Analysis of Selected Articles:")
            print("=" * 50)
            
            analyzer = NewsAnalyzer()
            analyzed_articles = analyzer.analyze_articles(all_articles)
            
            # Show analysis results
            print(f"📈 Categories Found:")
            categories = {}
            for article in analyzed_articles:
                category = article.get('category', 'general')
                categories[category] = categories.get(category, 0) + 1
            
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"   {category}: {count} articles")
            
            print(f"\n🎯 High Impact Articles (score > 5):")
            high_impact = [a for a in analyzed_articles if a.get('impact_score', 0) > 5]
            print(f"   Found: {len(high_impact)} high impact articles")
            
            for i, article in enumerate(high_impact[:5], 1):
                print(f"\n{i}. {article.get('title', 'No title')}")
                print(f"   Impact Score: {article.get('impact_score', 0):.1f}")
                print(f"   Category: {article.get('category', 'general')}")
                print(f"   Sentiment: {article.get('sentiment', {}).get('compound', 0):.2f}")
                print(f"   Key Phrases: {', '.join(article.get('key_phrases', [])[:3])}")
            
            print(f"\n🔑 Top Key Phrases Across All Articles:")
            all_phrases = []
            for article in analyzed_articles:
                all_phrases.extend(article.get('key_phrases', []))
            
            phrase_counts = {}
            for phrase in all_phrases:
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
            
            top_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for phrase, count in top_phrases:
                print(f"   {phrase}: {count}")
            
            # Save detailed results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"j97_articles_detail_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analyzed_articles, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Detailed analysis saved to {filename}")
        
        return all_articles

if __name__ == "__main__":
    asyncio.run(view_j97_articles())



