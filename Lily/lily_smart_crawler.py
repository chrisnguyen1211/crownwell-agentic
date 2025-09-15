#!/usr/bin/env python3
"""
🌸 LILY SMART CRAWLER
Rate-limit compliant ETH data collection
Intelligent scheduling to avoid bot detection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import json
import os

from rate_limit_manager import RateLimitManager, safe_platform_request
from optimized_supabase_integration import OptimizedSupabaseManager

# Import existing crawling modules
try:
    from telegram_eth_mention_analyzer import TelegramETHMentionAnalyzer
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

class LilySmartCrawler:
    """
    Lily's intelligent crawler with rate limit compliance
    Focuses on ETH data collection with smart scheduling
    """
    
    def __init__(self):
        self.setup_logging()
        self.rate_manager = RateLimitManager()
        
        # Initialize database
        try:
            self.db_manager = OptimizedSupabaseManager()
            self.db_manager.connect()
            self.logger.info("✅ Connected to Supabase")
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            self.db_manager = None
        
        # Initialize analyzers
        if TELEGRAM_AVAILABLE:
            self.telegram_analyzer = TelegramETHMentionAnalyzer()
        else:
            self.telegram_analyzer = None
        
        # Collection statistics
        self.daily_stats = {
            'twitter': {'collected': 0, 'errors': 0},
            'reddit': {'collected': 0, 'errors': 0},
            'telegram': {'collected': 0, 'errors': 0}
        }
        
        self.logger.info("🌸 Lily Smart Crawler initialized")
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def collect_twitter_data(self) -> List[Dict]:
        """Collect Twitter data with rate limit compliance"""
        
        async def twitter_request():
            # Placeholder for Twitter scraping logic
            # This would implement the actual Twitter scraping
            self.logger.info("📱 Collecting Twitter ETH mentions...")
            
            # Simulate data collection (replace with actual implementation)
            await asyncio.sleep(2)  # Simulate request time
            
            # Return sample data structure
            return [
                {
                    'platform': 'twitter',
                    'text': 'ETH is looking bullish today! 🚀',
                    'timestamp': datetime.now().isoformat(),
                    'engagement_score': 150,
                    'sentiment_score': 0.8,
                    'confidence': 0.7,
                    'keywords_detected': ['bullish', 'ETH'],
                    'final_weight': 1.2
                }
            ]
        
        try:
            # Use rate limit manager for safe request
            data = await safe_platform_request(
                self.rate_manager, 
                'twitter', 
                twitter_request
            )
            
            if data:
                self.daily_stats['twitter']['collected'] += len(data)
                self.logger.info(f"📱 Twitter: collected {len(data)} posts")
                return data
            else:
                self.logger.warning("📱 Twitter: no data collected (rate limited)")
                return []
                
        except Exception as e:
            self.daily_stats['twitter']['errors'] += 1
            self.logger.error(f"❌ Twitter collection error: {e}")
            return []
    
    async def collect_reddit_data(self) -> List[Dict]:
        """Collect Reddit data with rate limit compliance"""
        
        async def reddit_request():
            self.logger.info("🔴 Collecting Reddit ETH mentions...")
            
            # Simulate Reddit API collection
            await asyncio.sleep(1)
            
            return [
                {
                    'platform': 'reddit',
                    'text': 'ETH analysis shows strong support levels',
                    'timestamp': datetime.now().isoformat(),
                    'score': 45,
                    'sentiment_score': 0.6,
                    'confidence': 0.8,
                    'keywords_detected': ['ETH', 'support'],
                    'final_weight': 1.0
                }
            ]
        
        try:
            data = await safe_platform_request(
                self.rate_manager,
                'reddit',
                reddit_request
            )
            
            if data:
                self.daily_stats['reddit']['collected'] += len(data)
                self.logger.info(f"🔴 Reddit: collected {len(data)} posts")
                return data
            else:
                self.logger.warning("🔴 Reddit: no data collected (rate limited)")
                return []
                
        except Exception as e:
            self.daily_stats['reddit']['errors'] += 1
            self.logger.error(f"❌ Reddit collection error: {e}")
            return []
    
    async def collect_telegram_data(self) -> List[Dict]:
        """Collect Telegram data with rate limit compliance"""
        
        if not self.telegram_analyzer:
            self.logger.warning("📞 Telegram analyzer not available")
            return []
        
        async def telegram_request():
            self.logger.info("📞 Collecting Telegram ETH mentions...")
            
            # Use existing Telegram analyzer
            try:
                # This would call the actual Telegram analysis
                result = await self.telegram_analyzer.search_and_analyze_eth_mentions()
                
                if result and 'analyzed_messages' in result:
                    return result['analyzed_messages']
                else:
                    return []
                    
            except Exception as e:
                self.logger.error(f"❌ Telegram analysis error: {e}")
                return []
        
        try:
            data = await safe_platform_request(
                self.rate_manager,
                'telegram',
                telegram_request
            )
            
            if data:
                self.daily_stats['telegram']['collected'] += len(data)
                self.logger.info(f"📞 Telegram: collected {len(data)} posts")
                return data
            else:
                self.logger.warning("📞 Telegram: no data collected (rate limited)")
                return []
                
        except Exception as e:
            self.daily_stats['telegram']['errors'] += 1
            self.logger.error(f"❌ Telegram collection error: {e}")
            return []
    
    async def store_collected_data(self, platform_data: Dict[str, List[Dict]]):
        """Store collected data in Supabase"""
        
        if not self.db_manager:
            self.logger.error("❌ Database not available for storage")
            return
        
        try:
            # Store Twitter data
            if platform_data.get('twitter'):
                await self.db_manager.insert_twitter_posts(platform_data['twitter'])
                self.logger.info(f"💾 Stored {len(platform_data['twitter'])} Twitter posts")
            
            # Store Reddit data
            if platform_data.get('reddit'):
                await self.db_manager.insert_reddit_posts(platform_data['reddit'])
                self.logger.info(f"💾 Stored {len(platform_data['reddit'])} Reddit posts")
            
            # Store Telegram data
            if platform_data.get('telegram'):
                await self.db_manager.insert_telegram_posts(platform_data['telegram'])
                self.logger.info(f"💾 Stored {len(platform_data['telegram'])} Telegram posts")
                
        except Exception as e:
            self.logger.error(f"❌ Data storage error: {e}")
    
    async def run_collection_cycle(self) -> Dict:
        """Run one complete collection cycle across all platforms"""
        
        self.logger.info("🔄 Starting collection cycle...")
        
        collected_data = {
            'twitter': [],
            'reddit': [],
            'telegram': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Collect from each platform with rate limit compliance
        collected_data['twitter'] = await self.collect_twitter_data()
        collected_data['reddit'] = await self.collect_reddit_data()
        collected_data['telegram'] = await self.collect_telegram_data()
        
        # Store collected data
        await self.store_collected_data(collected_data)
        
        # Calculate cycle statistics
        total_collected = sum(len(data) for data in collected_data.values() if isinstance(data, list))
        
        cycle_stats = {
            'total_posts': total_collected,
            'twitter_posts': len(collected_data['twitter']),
            'reddit_posts': len(collected_data['reddit']),
            'telegram_posts': len(collected_data['telegram']),
            'timestamp': collected_data['timestamp']
        }
        
        self.logger.info(f"✅ Collection cycle complete: {total_collected} posts collected")
        
        return cycle_stats
    
    def get_daily_statistics(self) -> Dict:
        """Get daily collection statistics"""
        
        total_collected = sum(stats['collected'] for stats in self.daily_stats.values())
        total_errors = sum(stats['errors'] for stats in self.daily_stats.values())
        
        # Get rate limit status
        rate_status = self.rate_manager.get_platform_status()
        
        return {
            'daily_collection': self.daily_stats,
            'total_collected': total_collected,
            'total_errors': total_errors,
            'success_rate': (total_collected / (total_collected + total_errors)) * 100 if (total_collected + total_errors) > 0 else 0,
            'rate_limit_status': rate_status,
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_smart_scheduler(self, duration_hours: int = 24):
        """Run smart scheduler for specified duration"""
        
        self.logger.info(f"🤖 Starting Lily smart scheduler for {duration_hours} hours")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        cycle_count = 0
        
        while datetime.now() < end_time:
            try:
                # Run collection cycle
                cycle_stats = await self.run_collection_cycle()
                cycle_count += 1
                
                self.logger.info(f"📊 Cycle {cycle_count}: {cycle_stats['total_posts']} posts")
                
                # Wait before next cycle (based on rate limits)
                # Calculate optimal wait time
                wait_time = self.calculate_optimal_wait_time()
                self.logger.info(f"⏰ Waiting {wait_time}s before next cycle...")
                
                await asyncio.sleep(wait_time)
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Scheduler stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
        
        # Final statistics
        final_stats = self.get_daily_statistics()
        self.logger.info(f"📊 Final statistics: {final_stats['total_collected']} posts collected")
        
        return final_stats
    
    def calculate_optimal_wait_time(self) -> int:
        """Calculate optimal wait time based on rate limits"""
        
        # Get next available times for all platforms
        next_times = []
        for platform in ['twitter', 'reddit', 'telegram']:
            next_time = self.rate_manager.get_next_available_time(platform)
            next_times.append(next_time)
        
        # Wait until at least one platform is available
        earliest_time = min(next_times)
        wait_seconds = max(0, int((earliest_time - datetime.now()).total_seconds()))
        
        # Minimum wait time of 30 seconds to avoid being too aggressive
        return max(wait_seconds, 30)

# Main execution function
async def main():
    """Main function to run Lily's smart crawler"""
    
    print("🌸 LILY SMART CRAWLER")
    print("=" * 50)
    print("📊 ETH-focused data collection with rate limit compliance")
    print()
    
    # Initialize crawler
    crawler = LilySmartCrawler()
    
    # Show initial rate limit status
    status = crawler.rate_manager.get_platform_status()
    print("📊 Rate Limit Status:")
    for platform, info in status.items():
        print(f"   {platform}: {info['daily_usage']}/{info['daily_limit']} ({info['usage_percentage']:.1f}%)")
    print()
    
    try:
        # Run for 1 hour as test
        print("🚀 Starting smart collection (1 hour test)...")
        final_stats = await crawler.run_smart_scheduler(duration_hours=1)
        
        print("\n✅ Collection complete!")
        print(f"📊 Total collected: {final_stats['total_collected']} posts")
        print(f"📈 Success rate: {final_stats['success_rate']:.1f}%")
        
    except KeyboardInterrupt:
        print("\n⏹️ Collection stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())





























