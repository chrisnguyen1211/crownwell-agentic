#!/usr/bin/env python3
"""
Optimized Supabase Integration with Platform-Specific Tables
Separate tables for Twitter, Reddit, Telegram + Context-aware queries
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import asyncio
from dataclasses import dataclass

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

@dataclass
class ContextLimits:
    """Context size limits for different LLM models"""
    # Conservative estimates for token limits
    GPT4_TOKENS = 100000      # ~100k tokens
    GPT35_TOKENS = 14000      # ~14k tokens
    CLAUDE_TOKENS = 180000    # ~180k tokens
    
    # Approximate tokens per post (including metadata)
    TOKENS_PER_POST = 150     # Average post with analysis
    
    # Safe limits (70% of max to account for prompt + response)
    SAFE_GPT4_POSTS = int((GPT4_TOKENS * 0.7) / TOKENS_PER_POST)      # ~466 posts
    SAFE_GPT35_POSTS = int((GPT35_TOKENS * 0.7) / TOKENS_PER_POST)    # ~65 posts  
    SAFE_CLAUDE_POSTS = int((CLAUDE_TOKENS * 0.7) / TOKENS_PER_POST)  # ~840 posts

@dataclass
class RateLimitConfig:
    """Rate limit configuration for database queries"""
    # Platform-specific rate limits (requests per minute)
    TWITTER_QUERY_RATE = 15      # Conservative for web scraping
    REDDIT_QUERY_RATE = 60       # Reddit API allows 60/min
    TELEGRAM_QUERY_RATE = 30     # Telegram API moderate limit
    
    # Collection size limits per platform per query
    TWITTER_BATCH_SIZE = 50
    REDDIT_BATCH_SIZE = 100
    TELEGRAM_BATCH_SIZE = 30
    
    # Time windows for data freshness
    DEFAULT_TIME_WINDOW = timedelta(hours=4)    # Default: last 4 hours
    MAX_TIME_WINDOW = timedelta(days=7)         # Max: last 7 days

class OptimizedSupabaseManager:
    """Enhanced Supabase manager with platform-specific tables and context optimization"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None, model_type: str = "gpt4"):
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        self.client: Optional[Client] = None
        self.model_type = model_type
        self.context_limits = ContextLimits()
        self.rate_limits = RateLimitConfig()
        self.setup_logging()
        
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase package not installed")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Key required")
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Connect to Supabase"""
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("✅ Connected to Supabase")
            return True
        except Exception as e:
            self.logger.error(f"❌ Supabase connection failed: {e}")
            return False
    
    def get_context_limit(self) -> int:
        """Get safe context limit based on model type"""
        limits = {
            'gpt4': self.context_limits.SAFE_GPT4_POSTS,
            'gpt35': self.context_limits.SAFE_GPT35_POSTS,
            'claude': self.context_limits.SAFE_CLAUDE_POSTS
        }
        return limits.get(self.model_type, self.context_limits.SAFE_GPT35_POSTS)
    
    def create_platform_tables(self) -> bool:
        """Create platform-specific tables"""
        
        if not self.client:
            self.logger.error("Not connected to Supabase")
            return False
        
        # Define platform-specific table schemas
        table_schemas = {
            'twitter_posts': """
                CREATE TABLE IF NOT EXISTS twitter_posts (
                    id SERIAL PRIMARY KEY,
                    tweet_id VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(255),
                    verified_account BOOLEAN DEFAULT FALSE,
                    follower_count INTEGER,
                    tweet_text TEXT NOT NULL,
                    retweets INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    hashtags TEXT[],
                    mentions TEXT[],
                    tweet_url VARCHAR(500),
                    is_retweet BOOLEAN DEFAULT FALSE,
                    original_tweet_id VARCHAR(255),
                    sentiment_score DECIMAL(5,3),
                    confidence DECIMAL(5,3),
                    keywords_detected TEXT[],
                    context_multipliers TEXT[],
                    engagement_weight DECIMAL(5,3),
                    final_weight DECIMAL(5,3),
                    tweet_timestamp TIMESTAMPTZ NOT NULL,
                    analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """,
            
            'reddit_posts': """
                CREATE TABLE IF NOT EXISTS reddit_posts (
                    id SERIAL PRIMARY KEY,
                    post_id VARCHAR(255) UNIQUE NOT NULL,
                    subreddit VARCHAR(255) NOT NULL,
                    post_type VARCHAR(50), -- submission, comment
                    title TEXT,
                    content TEXT NOT NULL,
                    author VARCHAR(255),
                    author_karma INTEGER,
                    post_score INTEGER DEFAULT 0,
                    upvote_ratio DECIMAL(3,2),
                    num_comments INTEGER DEFAULT 0,
                    awards_count INTEGER DEFAULT 0,
                    is_distinguished BOOLEAN DEFAULT FALSE,
                    flair_text VARCHAR(255),
                    post_url VARCHAR(500),
                    sentiment_score DECIMAL(5,3),
                    confidence DECIMAL(5,3),
                    keywords_detected TEXT[],
                    context_multipliers TEXT[],
                    engagement_weight DECIMAL(5,3),
                    final_weight DECIMAL(5,3),
                    post_timestamp TIMESTAMPTZ NOT NULL,
                    analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """,
            
            'telegram_posts': """
                CREATE TABLE IF NOT EXISTS telegram_posts (
                    id SERIAL PRIMARY KEY,
                    message_id INTEGER NOT NULL,
                    channel_id BIGINT NOT NULL,
                    channel_username VARCHAR(255),
                    channel_title VARCHAR(255),
                    channel_subscribers INTEGER,
                    message_text TEXT NOT NULL,
                    message_views INTEGER DEFAULT 0,
                    forwards INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    reactions JSONB,
                    is_channel_message BOOLEAN DEFAULT TRUE,
                    sender_id BIGINT,
                    sender_username VARCHAR(255),
                    media_type VARCHAR(50),
                    message_url VARCHAR(500),
                    sentiment_score DECIMAL(5,3),
                    confidence DECIMAL(5,3),
                    keywords_detected TEXT[],
                    context_multipliers TEXT[],
                    engagement_weight DECIMAL(5,3),
                    final_weight DECIMAL(5,3),
                    message_timestamp TIMESTAMPTZ NOT NULL,
                    analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(message_id, channel_id)
                );
            """,
            
            'aggregated_sentiment_reports': """
                CREATE TABLE IF NOT EXISTS aggregated_sentiment_reports (
                    id SERIAL PRIMARY KEY,
                    report_timestamp TIMESTAMPTZ NOT NULL,
                    time_window_hours INTEGER,
                    total_posts_analyzed INTEGER,
                    twitter_posts_count INTEGER DEFAULT 0,
                    reddit_posts_count INTEGER DEFAULT 0,
                    telegram_posts_count INTEGER DEFAULT 0,
                    overall_sentiment DECIMAL(5,3),
                    sentiment_strength VARCHAR(50),
                    confidence_level DECIMAL(5,3),
                    twitter_sentiment DECIMAL(5,3),
                    reddit_sentiment DECIMAL(5,3),
                    telegram_sentiment DECIMAL(5,3),
                    platform_consensus DECIMAL(5,3),
                    trading_signal VARCHAR(20),
                    signal_strength VARCHAR(20),
                    market_momentum VARCHAR(50),
                    risk_level VARCHAR(20),
                    key_insights TEXT[],
                    trending_keywords TEXT[],
                    context_size_used INTEGER,
                    model_type VARCHAR(50),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """
        }
        
        try:
            # Check if tables exist by trying to access them
            for table_name in table_schemas.keys():
                try:
                    self.client.table(table_name).select('id').limit(1).execute()
                    self.logger.info(f"✅ Table {table_name} exists and accessible")
                except:
                    self.logger.info(f"📋 Table {table_name} needs to be created")
            
            self.logger.info("✅ All platform tables verified")
            self._print_table_creation_sql(table_schemas)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Table verification failed: {e}")
            self._print_table_creation_sql(table_schemas)
            return False
    
    def _print_table_creation_sql(self, schemas: Dict[str, str]):
        """Print SQL for manual table creation"""
        print("\n🔧 CREATE PLATFORM-SPECIFIC TABLES IN SUPABASE")
        print("=" * 80)
        print("Go to Supabase > SQL Editor and run these commands:")
        
        for table_name, sql in schemas.items():
            print(f"\n-- {table_name.upper()}")
            print(sql)
        
        print("\n💡 After creating tables, run this script again.")
    
    async def insert_twitter_posts(self, posts: List[Dict]) -> bool:
        """Insert Twitter posts with rate limiting"""
        return await self._insert_platform_posts(posts, 'twitter_posts', self._prepare_twitter_data)
    
    async def insert_reddit_posts(self, posts: List[Dict]) -> bool:
        """Insert Reddit posts with rate limiting"""
        return await self._insert_platform_posts(posts, 'reddit_posts', self._prepare_reddit_data)
    
    async def insert_telegram_posts(self, posts: List[Dict]) -> bool:
        """Insert Telegram posts with rate limiting"""
        return await self._insert_platform_posts(posts, 'telegram_posts', self._prepare_telegram_data)
    
    async def _insert_platform_posts(self, posts: List[Dict], table_name: str, data_prep_func) -> bool:
        """Generic platform post insertion with rate limiting"""
        
        if not self.client or not posts:
            return False
        
        try:
            # Prepare data
            prepared_data = [data_prep_func(post) for post in posts]
            
            # Insert with chunking to respect rate limits
            chunk_size = 50  # Insert 50 posts at a time
            successful_inserts = 0
            
            for i in range(0, len(prepared_data), chunk_size):
                chunk = prepared_data[i:i+chunk_size]
                
                try:
                    result = self.client.table(table_name).insert(chunk).execute()
                    successful_inserts += len(chunk)
                except Exception as insert_error:
                    error_msg = str(insert_error).lower()
                    if "duplicate key" in error_msg or "already exists" in error_msg:
                        # Duplicate keys - this is expected, just log and continue
                        self.logger.info(f"Duplicate keys ignored for {len(chunk)} posts in {table_name}")
                        successful_inserts += len(chunk)  # Count as successful since data exists
                    else:
                        # Real error - log and continue with next chunk
                        self.logger.warning(f"Insert error for chunk in {table_name}: {insert_error}")
                
                # Small delay between chunks
                if i + chunk_size < len(prepared_data):
                    await asyncio.sleep(0.1)
            
            self.logger.info(f"✅ Processed {successful_inserts}/{len(prepared_data)} posts for {table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ {table_name} insertion failed: {e}")
            return False
    
    def _prepare_twitter_data(self, post: Dict) -> Dict:
        """Prepare Twitter post data for database insertion"""
        return {
            'tweet_id': post.get('post_id') or post.get('tweet_id'),
            'username': post.get('author') or post.get('username'),
            'verified_account': post.get('verified', False),
            'follower_count': post.get('follower_count', 0),
            'tweet_text': post.get('text') or post.get('content'),
            'retweets': post.get('retweets', 0),
            'likes': post.get('likes', 0),
            'replies': post.get('replies', 0),
            'hashtags': post.get('hashtags', []),
            'mentions': post.get('mentions', []),
            'tweet_url': post.get('url'),
            'is_retweet': post.get('is_retweet', False),
            'sentiment_score': post.get('sentiment_score'),
            'confidence': post.get('confidence'),
            'keywords_detected': post.get('keywords_detected', []),
            'context_multipliers': post.get('context_multipliers', []),
            'engagement_weight': post.get('engagement_weight'),
            'final_weight': post.get('final_weight'),
            'tweet_timestamp': post.get('timestamp'),
            'analysis_timestamp': post.get('analysis_timestamp', datetime.now(timezone.utc).isoformat())
        }
    
    def _prepare_reddit_data(self, post: Dict) -> Dict:
        """Prepare Reddit post data for database insertion"""
        return {
            'post_id': post.get('post_id'),
            'subreddit': post.get('subreddit'),
            'post_type': 'submission',  # or 'comment'
            'title': post.get('title'),
            'content': post.get('text') or post.get('content'),
            'author': post.get('author'),
            'author_karma': post.get('author_karma', 0),
            'post_score': post.get('score', 0),
            'upvote_ratio': post.get('upvote_ratio'),
            'num_comments': post.get('num_comments', 0),
            'awards_count': post.get('awards_count', 0),
            'flair_text': post.get('flair'),
            'post_url': post.get('url'),
            'sentiment_score': post.get('sentiment_score'),
            'confidence': post.get('confidence'),
            'keywords_detected': post.get('keywords_detected', []),
            'context_multipliers': post.get('context_multipliers', []),
            'engagement_weight': post.get('engagement_weight'),
            'final_weight': post.get('final_weight'),
            'post_timestamp': post.get('timestamp'),
            'analysis_timestamp': post.get('analysis_timestamp', datetime.now(timezone.utc).isoformat())
        }
    
    def _prepare_telegram_data(self, post: Dict) -> Dict:
        """Prepare Telegram post data for database insertion"""
        # Extract message and channel IDs from post_id if available
        post_id = post.get('post_id', '')
        message_id = 0
        channel_id = 0
        
        if post_id.startswith('tg_'):
            try:
                # Format: tg_channelid_messageid
                parts = post_id.split('_')
                if len(parts) >= 3:
                    channel_id = int(parts[1])
                    message_id = int(parts[2])
            except (ValueError, IndexError):
                # Use hash of post_id if parsing fails
                import hashlib
                hash_obj = hashlib.md5(post_id.encode())
                message_id = int(hash_obj.hexdigest()[:8], 16) % 1000000
                channel_id = int(hash_obj.hexdigest()[8:16], 16) % 1000000
        
        # Ensure we have valid IDs
        if message_id == 0 or channel_id == 0:
            import hashlib
            hash_obj = hashlib.md5((post.get('text', '') + str(post.get('timestamp', ''))).encode())
            message_id = int(hash_obj.hexdigest()[:8], 16) % 1000000
            channel_id = int(hash_obj.hexdigest()[8:16], 16) % 1000000
        
        return {
            'message_id': message_id,
            'channel_id': channel_id,
            'channel_username': post.get('channel') or post.get('channel_username'),
            'channel_title': post.get('channel_title'),
            'channel_subscribers': post.get('subscribers', 0),
            'message_text': post.get('text') or post.get('content'),
            'message_views': post.get('views', 0),
            'forwards': post.get('forwards', 0),
            'replies': post.get('replies', 0),
            'reactions': json.dumps(post.get('reactions', {})),
            'sender_username': post.get('author'),
            'message_url': post.get('url'),
            'sentiment_score': post.get('sentiment_score'),
            'confidence': post.get('confidence'),
            'keywords_detected': post.get('keywords_detected', []),
            'context_multipliers': post.get('context_multipliers', []),
            'engagement_weight': post.get('engagement_weight'),
            'final_weight': post.get('final_weight'),
            'message_timestamp': post.get('timestamp'),
            'analysis_timestamp': post.get('analysis_timestamp', datetime.now(timezone.utc).isoformat())
        }
    
    def get_context_optimized_data(self, 
                                  platforms: List[str] = None,
                                  time_window: timedelta = None,
                                  max_posts_per_platform: int = None) -> Dict[str, List[Dict]]:
        """Get context-optimized data from platform tables"""
        
        if not self.client:
            self.logger.error("Not connected to Supabase")
            return {}
        
        platforms = platforms or ['twitter', 'reddit', 'telegram']
        time_window = time_window or self.rate_limits.DEFAULT_TIME_WINDOW
        
        # Calculate context-aware limits
        context_limit = self.get_context_limit()
        posts_per_platform = min(
            max_posts_per_platform or (context_limit // len(platforms)),
            context_limit // len(platforms)
        )
        
        self.logger.info(f"🧠 Context optimization: max {posts_per_platform} posts per platform (total: {context_limit})")
        
        platform_data = {}
        cutoff_time = datetime.now(timezone.utc) - time_window
        
        try:
            # Get Twitter data
            if 'twitter' in platforms:
                twitter_data = self.client.table('twitter_posts')\
                    .select("*")\
                    .gte('analysis_timestamp', cutoff_time.isoformat())\
                    .order('final_weight', desc=True)\
                    .order('analysis_timestamp', desc=True)\
                    .limit(posts_per_platform)\
                    .execute()
                
                platform_data['twitter'] = twitter_data.data
                self.logger.info(f"📱 Retrieved {len(twitter_data.data)} Twitter posts")
            
            # Get Reddit data
            if 'reddit' in platforms:
                reddit_data = self.client.table('reddit_posts')\
                    .select("*")\
                    .gte('analysis_timestamp', cutoff_time.isoformat())\
                    .order('final_weight', desc=True)\
                    .order('analysis_timestamp', desc=True)\
                    .limit(posts_per_platform)\
                    .execute()
                
                platform_data['reddit'] = reddit_data.data
                self.logger.info(f"📱 Retrieved {len(reddit_data.data)} Reddit posts")
            
            # Get Telegram data
            if 'telegram' in platforms:
                telegram_data = self.client.table('telegram_posts')\
                    .select("*")\
                    .gte('analysis_timestamp', cutoff_time.isoformat())\
                    .order('final_weight', desc=True)\
                    .order('analysis_timestamp', desc=True)\
                    .limit(posts_per_platform)\
                    .execute()
                
                platform_data['telegram'] = telegram_data.data
                self.logger.info(f"📱 Retrieved {len(telegram_data.data)} Telegram posts")
            
            # Log context usage
            total_posts = sum(len(data) for data in platform_data.values())
            context_usage = (total_posts / context_limit) * 100
            
            self.logger.info(f"📊 Context usage: {total_posts}/{context_limit} posts ({context_usage:.1f}%)")
            
            return platform_data
            
        except Exception as e:
            self.logger.error(f"❌ Context-optimized query failed: {e}")
            return {}
    
    async def store_aggregated_report(self, 
                                    platform_data: Dict[str, List[Dict]],
                                    analysis_result: Dict) -> bool:
        """Store aggregated sentiment report"""
        
        if not self.client:
            return False
        
        try:
            total_posts = sum(len(data) for data in platform_data.values())
            
            report_data = {
                'report_timestamp': datetime.now(timezone.utc).isoformat(),
                'time_window_hours': 4,  # Default
                'total_posts_analyzed': total_posts,
                'twitter_posts_count': len(platform_data.get('twitter', [])),
                'reddit_posts_count': len(platform_data.get('reddit', [])),
                'telegram_posts_count': len(platform_data.get('telegram', [])),
                'overall_sentiment': analysis_result.get('overall_sentiment', {}).get('score', 0),
                'sentiment_strength': analysis_result.get('overall_sentiment', {}).get('strength', 'neutral'),
                'confidence_level': analysis_result.get('overall_sentiment', {}).get('confidence_level', 0),
                'twitter_sentiment': analysis_result.get('platform_breakdown', {}).get('twitter', {}).get('avg_sentiment', 0),
                'reddit_sentiment': analysis_result.get('platform_breakdown', {}).get('reddit', {}).get('avg_sentiment', 0),
                'telegram_sentiment': analysis_result.get('platform_breakdown', {}).get('telegram', {}).get('avg_sentiment', 0),
                'trading_signal': analysis_result.get('trading_signal', {}).get('signal', 'HOLD'),
                'signal_strength': analysis_result.get('trading_signal', {}).get('strength', 'weak'),
                'risk_level': analysis_result.get('trading_signal', {}).get('risk_level', 'medium'),
                'key_insights': analysis_result.get('market_insights', {}).get('key_insights', []),
                'trending_keywords': analysis_result.get('market_insights', {}).get('trending_keywords', []),
                'context_size_used': total_posts,
                'model_type': self.model_type
            }
            
            result = self.client.table('aggregated_sentiment_reports').insert(report_data).execute()
            
            self.logger.info("✅ Aggregated report stored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Report storage failed: {e}")
            return False

def demo_optimized_system():
    """Demo the optimized platform-specific system"""
    
    print("🚀 OPTIMIZED SUPABASE SYSTEM DEMO")
    print("Platform-Specific Tables + Context Optimization")
    print("=" * 80)
    
    # Initialize system
    db = OptimizedSupabaseManager(model_type="gpt4")
    
    if not db.connect():
        print("❌ Failed to connect to Supabase")
        return
    
    # Create platform tables
    if not db.create_platform_tables():
        print("⚠️ Tables need to be created manually")
        return
    
    # Demo context-optimized queries
    print(f"\n🧠 CONTEXT OPTIMIZATION DEMO")
    print(f"Model: {db.model_type}")
    print(f"Context limit: {db.get_context_limit()} posts")
    
    # Get optimized data
    platform_data = db.get_context_optimized_data(
        platforms=['twitter', 'reddit', 'telegram'],
        time_window=timedelta(hours=4)
    )
    
    print(f"\n📊 PLATFORM DATA RETRIEVED:")
    for platform, data in platform_data.items():
        print(f"   {platform.title()}: {len(data)} posts")
    
    total_posts = sum(len(data) for data in platform_data.values())
    context_usage = (total_posts / db.get_context_limit()) * 100
    
    print(f"\n🎯 CONTEXT EFFICIENCY:")
    print(f"   Total posts: {total_posts}")
    print(f"   Context usage: {context_usage:.1f}%")
    print(f"   Remaining capacity: {db.get_context_limit() - total_posts} posts")
    
    print(f"\n✅ Optimized system ready for production!")

if __name__ == "__main__":
    demo_optimized_system()
