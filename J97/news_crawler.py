#!/usr/bin/env python3
"""
J97 News Crawler - 24/7 Ethereum News Analyst
Crawls multiple news sources for ETH-related content with rate limiting
"""

import asyncio
import aiohttp
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import schedule
import threading

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('j97_news_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsCrawler:
    """J97 News Crawler - 24/7 Ethereum News Analyst"""
    
    def __init__(self):
        self.session = None
        
        # API Priority Order (1 = highest priority)
        self.api_priority = {
            'gnews': 1,      # 100 requests/day, 1 req/sec - BEST
            'newsapi': 2,    # 1000 requests/month - GOOD
            'newsdata': 3,   # 200 requests/day - GOOD
            'mediastack': 4  # 100 requests/month - BACKUP
        }
        
        self.rate_limits = {
            'gnews': {'requests': 0, 'reset_time': time.time(), 'max_per_day': 100, 'max_per_second': 1},
            'newsapi': {'requests': 0, 'reset_time': time.time(), 'max_per_month': 1000},
            'mediastack': {'requests': 0, 'reset_time': time.time(), 'max_per_month': 100},
            'newsdata': {'requests': 0, 'reset_time': time.time(), 'max_per_day': 200}
        }
        
        # Load API keys from api_keys.env
        load_dotenv('api_keys.env')
        self.api_keys = {
            'gnews': os.getenv('GNEWS_API_KEY'),
            'newsapi': os.getenv('NEWSAPI_KEY'),
            'mediastack': os.getenv('MEDIASTACK_API_KEY'),
            'newsdata': os.getenv('NEWSDATA_API_KEY')
        }
        
        # Track API status
        self.api_status = {
            'gnews': 'unknown',
            'newsapi': 'unknown', 
            'mediastack': 'unknown',
            'newsdata': 'unknown'
        }
        
        self.keywords = os.getenv('J97_KEYWORDS', 'ethereum,eth,ethereum 2.0,eth2,defi,smart contracts,gas fees').split(',')
        self.max_articles = int(os.getenv('J97_MAX_ARTICLES_PER_SOURCE', '50'))
        self.sleep_interval = int(os.getenv('J97_SLEEP_INTERVAL', '3600'))
        
        self.crawled_articles = set()  # Track to avoid duplicates
        self.articles_buffer = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'J97-News-Analyst/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def check_rate_limit(self, source: str) -> bool:
        """Check if we can make a request to the source"""
        now = time.time()
        limit_info = self.rate_limits[source]
        
        # Reset daily/monthly counters
        if source in ['gnews', 'newsdata'] and now - limit_info['reset_time'] > 86400:  # 24 hours
            limit_info['requests'] = 0
            limit_info['reset_time'] = now
        elif source in ['newsapi', 'mediastack'] and now - limit_info['reset_time'] > 2592000:  # 30 days
            limit_info['requests'] = 0
            limit_info['reset_time'] = now
            
        # Check limits
        if source in ['gnews', 'newsdata']:
            return limit_info['requests'] < limit_info['max_per_day']
        else:
            return limit_info['requests'] < limit_info['max_per_month']
    
    async def test_api(self, source: str) -> bool:
        """Test if an API is working"""
        if not self.api_keys[source]:
            self.api_status[source] = 'no_key'
            return False
            
        try:
            if source == 'gnews':
                url = "https://gnews.io/api/v4/search"
                params = {'token': self.api_keys[source], 'q': 'ethereum', 'max': 1}
            elif source == 'newsapi':
                url = "https://newsapi.org/v2/everything"
                params = {'apiKey': self.api_keys[source], 'q': 'ethereum', 'pageSize': 1}
            elif source == 'mediastack':
                url = "http://api.mediastack.com/v1/news"
                params = {'access_key': self.api_keys[source], 'keywords': 'ethereum', 'limit': 1}
            elif source == 'newsdata':
                url = "https://newsdata.io/api/1/news"
                params = {'apikey': self.api_keys[source], 'q': 'ethereum', 'size': 1}
            else:
                return False
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    self.api_status[source] = 'working'
                    logger.info(f"✅ {source.upper()} API test successful")
                    return True
                else:
                    self.api_status[source] = f'error_{response.status}'
                    logger.warning(f"⚠️ {source.upper()} API test failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.api_status[source] = 'error'
            logger.error(f"❌ {source.upper()} API test error: {e}")
            return False
    
    def get_working_apis(self) -> List[str]:
        """Get list of working APIs in priority order"""
        working_apis = []
        for source, priority in sorted(self.api_priority.items(), key=lambda x: x[1]):
            if self.api_status.get(source) == 'working':
                working_apis.append(source)
        return working_apis
    
    async def test_all_apis(self):
        """Test all APIs and update status"""
        logger.info("🔍 Testing all APIs...")
        
        for source in self.api_priority.keys():
            await self.test_api(source)
            await asyncio.sleep(1)  # Rate limiting between tests
        
        working_count = sum(1 for status in self.api_status.values() if status == 'working')
        logger.info(f"✅ {working_count}/4 APIs are working")
        
        # Print API status
        for source, status in self.api_status.items():
            status_emoji = "✅" if status == 'working' else "❌" if status == 'no_key' else "⚠️"
            logger.info(f"   {status_emoji} {source.upper()}: {status}")
    
    def update_rate_limit(self, source: str):
        """Update rate limit counter"""
        self.rate_limits[source]['requests'] += 1
    
    async def crawl_gnews(self) -> List[Dict]:
        """Crawl GNews API for Ethereum news"""
        if not self.api_keys['gnews'] or not self.check_rate_limit('gnews'):
            logger.warning("GNews API key not available or rate limit exceeded")
            return []
            
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                'token': self.api_keys['gnews'],
                'q': 'ethereum OR eth OR "ethereum 2.0" OR "ethereum merge" OR "ethereum upgrade" OR "ethereum staking" OR "ethereum gas" OR "ethereum defi" OR "ethereum ETF" OR "ETH ETF" OR "Ethereum Blackrock" OR "ethereum layer 2" OR "ethereum rollup" OR "ethereum price" OR "ethereum news" OR "ethereum reserve" OR "ethereum sell" OR "ethereum buy" OR "ethereum accumulate"',
                'lang': 'en',
                'country': 'us',
                'max': min(self.max_articles, 10),  # GNews free tier max 10 per request
                'sortby': 'publishedAt'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.update_rate_limit('gnews')
                    
                    articles = []
                    for article in data.get('articles', []):
                        if article.get('url') not in self.crawled_articles:
                            articles.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'url': article.get('url', ''),
                                'publishedAt': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', 'GNews'),
                                'api_source': 'gnews'
                            })
                            self.crawled_articles.add(article.get('url'))
                    
                    logger.info(f"✅ GNews: Found {len(articles)} new articles")
                    return articles
                else:
                    logger.error(f"GNews API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"GNews crawling error: {e}")
            return []
    
    async def crawl_newsapi(self) -> List[Dict]:
        """Crawl NewsAPI for Ethereum news"""
        if not self.api_keys['newsapi'] or not self.check_rate_limit('newsapi'):
            logger.warning("NewsAPI key not available or rate limit exceeded")
            return []
            
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.api_keys['newsapi'],
                'q': 'ethereum OR eth OR "ethereum 2.0" OR "ethereum merge" OR "ethereum upgrade" OR "ethereum staking" OR "ethereum gas" OR "ethereum defi" OR "ethereum ETF" OR "ETH ETF" OR "Ethereum Blackrock" OR "ethereum layer 2" OR "ethereum rollup" OR "ethereum price" OR "ethereum news" OR "ethereum reserve" OR "ethereum sell" OR "ethereum buy" OR "ethereum accumulate"',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': min(self.max_articles, 100)  # NewsAPI max 100 per request
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.update_rate_limit('newsapi')
                    
                    articles = []
                    for article in data.get('articles', []):
                        if article.get('url') not in self.crawled_articles:
                            articles.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'url': article.get('url', ''),
                                'publishedAt': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', 'NewsAPI'),
                                'api_source': 'newsapi'
                            })
                            self.crawled_articles.add(article.get('url'))
                    
                    logger.info(f"✅ NewsAPI: Found {len(articles)} new articles")
                    return articles
                else:
                    logger.error(f"NewsAPI error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"NewsAPI crawling error: {e}")
            return []
    
    async def crawl_mediastack(self) -> List[Dict]:
        """Crawl Mediastack for Ethereum news"""
        if not self.api_keys['mediastack'] or not self.check_rate_limit('mediastack'):
            logger.warning("Mediastack API key not available or rate limit exceeded")
            return []
            
        try:
            url = "http://api.mediastack.com/v1/news"
            params = {
                'access_key': self.api_keys['mediastack'],
                'keywords': 'ethereum,eth,defi',
                'languages': 'en',
                'sort': 'published_desc',
                'limit': min(self.max_articles, 100)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.update_rate_limit('mediastack')
                    
                    articles = []
                    for article in data.get('data', []):
                        if article.get('url') not in self.crawled_articles:
                            articles.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'url': article.get('url', ''),
                                'publishedAt': article.get('published_at', ''),
                                'source': article.get('source', 'Mediastack'),
                                'api_source': 'mediastack'
                            })
                            self.crawled_articles.add(article.get('url'))
                    
                    logger.info(f"✅ Mediastack: Found {len(articles)} new articles")
                    return articles
                else:
                    logger.error(f"Mediastack API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Mediastack crawling error: {e}")
            return []
    
    async def crawl_newsdata(self) -> List[Dict]:
        """Crawl NewsData.io for Ethereum news"""
        if not self.api_keys['newsdata'] or not self.check_rate_limit('newsdata'):
            logger.warning("NewsData API key not available or rate limit exceeded")
            return []
            
        try:
            url = "https://newsdata.io/api/1/news"
            params = {
                'apikey': self.api_keys['newsdata'],
                'q': 'ethereum OR eth OR defi',
                'language': 'en',
                'category': 'technology',
                'size': min(self.max_articles, 10)  # NewsData free tier max 10 per request
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.update_rate_limit('newsdata')
                    
                    articles = []
                    for article in data.get('results', []):
                        if article.get('link') not in self.crawled_articles:
                            articles.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'url': article.get('link', ''),
                                'publishedAt': article.get('pubDate', ''),
                                'source': article.get('source_id', 'NewsData'),
                                'api_source': 'newsdata'
                            })
                            self.crawled_articles.add(article.get('link'))
                    
                    logger.info(f"✅ NewsData: Found {len(articles)} new articles")
                    return articles
                else:
                    logger.error(f"NewsData API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"NewsData crawling error: {e}")
            return []
    
    async def crawl_all_sources(self) -> List[Dict]:
        """Crawl all available news sources with priority-based fallback"""
        logger.info("🔍 J97 starting priority-based news crawl...")
        
        # First test all APIs
        await self.test_all_apis()
        
        # Get working APIs in priority order
        working_apis = self.get_working_apis()
        
        if not working_apis:
            logger.warning("⚠️ No working APIs available")
            return []
        
        logger.info(f"📡 Using {len(working_apis)} working APIs: {', '.join(working_apis)}")
        
        all_articles = []
        
        # Crawl APIs in priority order with fallback
        for source in working_apis:
            try:
                if not self.check_rate_limit(source):
                    logger.warning(f"⚠️ Rate limit exceeded for {source.upper()}, skipping")
                    continue
                
                logger.info(f"🔄 Crawling {source.upper()}...")
                
                if source == 'gnews':
                    articles = await self.crawl_gnews()
                elif source == 'newsapi':
                    articles = await self.crawl_newsapi()
                elif source == 'mediastack':
                    articles = await self.crawl_mediastack()
                elif source == 'newsdata':
                    articles = await self.crawl_newsdata()
                else:
                    continue
                
                if articles:
                    all_articles.extend(articles)
                    logger.info(f"✅ {source.upper()}: Found {len(articles)} articles")
                    
                    # If we have enough articles from high-priority sources, we can stop
                    if len(all_articles) >= self.max_articles and source in ['gnews', 'newsapi']:
                        logger.info(f"🎯 Sufficient articles from high-priority sources, stopping crawl")
                        break
                else:
                    logger.warning(f"⚠️ {source.upper()}: No articles found")
                
                # Rate limiting between API calls
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error crawling {source.upper()}: {e}")
                continue
        
        logger.info(f"📰 Total new articles found: {len(all_articles)}")
        return all_articles
    
    def save_articles(self, articles: List[Dict]):
        """Save articles to buffer and file"""
        if not articles:
            return
            
        self.articles_buffer.extend(articles)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"j97_articles_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(articles)} articles to {filename}")
    
    async def run_crawl_cycle(self):
        """Run one complete crawl cycle"""
        async with self:
            articles = await self.crawl_all_sources()
            if articles:
                self.save_articles(articles)
            return articles

def run_scheduled_crawl():
    """Function to run in scheduler thread"""
    async def crawl():
        crawler = NewsCrawler()
        await crawler.run_crawl_cycle()
    
    asyncio.run(crawl())

def start_j97():
    """Start J97 24/7 news crawler"""
    logger.info("🚀 Starting J97 News Analyst - 24/7 Ethereum News Crawler")
    
    # Schedule crawls every hour
    schedule.every().hour.do(run_scheduled_crawl)
    
    # Run initial crawl
    asyncio.run(NewsCrawler().run_crawl_cycle())
    
    # Start scheduler in separate thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("✅ J97 is now running 24/7! Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 J97 stopped by user")

if __name__ == "__main__":
    start_j97()
