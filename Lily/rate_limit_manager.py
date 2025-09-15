#!/usr/bin/env python3
"""
🌸 LILY'S RATE LIMIT MANAGER
Smart rate limit compliance to avoid bot detection
Intelligent scheduling based on platform limits
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import logging
import json
import os

class RateLimitManager:
    """
    Intelligent rate limit management for social media platforms
    Ensures Lily stays under rate limits and avoids detection
    """
    
    def __init__(self):
        self.setup_logging()
        
        # Platform rate limits (conservative to avoid detection)
        self.platform_limits = {
            'twitter': {
                'requests_per_hour': 15,        # Very conservative for scraping
                'min_interval': 240,            # 4 minutes between requests
                'burst_limit': 3,               # Max 3 requests in burst
                'burst_cooldown': 600,          # 10 min cooldown after burst
                'daily_limit': 300              # Max requests per day
            },
            'reddit': {
                'requests_per_minute': 30,      # Reddit API limit is 60/min
                'min_interval': 2,              # 2 seconds between requests
                'burst_limit': 10,              # Max 10 requests in burst
                'burst_cooldown': 60,           # 1 min cooldown after burst
                'daily_limit': 10000            # Reddit is generous
            },
            'telegram': {
                'requests_per_second': 1,       # Telegram limit is higher but be safe
                'min_interval': 1,              # 1 second between requests
                'burst_limit': 20,              # Max 20 requests in burst
                'burst_cooldown': 30,           # 30 sec cooldown after burst
                'daily_limit': 5000             # Conservative daily limit
            }
        }
        
        # Track usage for each platform
        self.usage_tracking = {
            'twitter': {'requests': [], 'last_request': None, 'daily_count': 0},
            'reddit': {'requests': [], 'last_request': None, 'daily_count': 0},
            'telegram': {'requests': [], 'last_request': None, 'daily_count': 0}
        }
        
        # Load previous day's usage if exists
        self.load_usage_history()
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_usage_history(self):
        """Load usage history from file"""
        try:
            if os.path.exists('rate_limit_history.json'):
                with open('rate_limit_history.json', 'r') as f:
                    data = json.load(f)
                    
                # Only keep today's data
                today = datetime.now().date().isoformat()
                for platform in self.usage_tracking:
                    if platform in data and data[platform].get('date') == today:
                        self.usage_tracking[platform]['daily_count'] = data[platform].get('daily_count', 0)
                        
                self.logger.info("📊 Loaded rate limit history")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load rate limit history: {e}")
    
    def save_usage_history(self):
        """Save usage history to file"""
        try:
            save_data = {}
            today = datetime.now().date().isoformat()
            
            for platform, tracking in self.usage_tracking.items():
                save_data[platform] = {
                    'date': today,
                    'daily_count': tracking['daily_count']
                }
            
            with open('rate_limit_history.json', 'w') as f:
                json.dump(save_data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save rate limit history: {e}")
    
    def can_make_request(self, platform: str) -> tuple[bool, int]:
        """
        Check if we can make a request to platform
        Returns (can_request, wait_time_seconds)
        """
        if platform not in self.platform_limits:
            return False, 0
        
        limits = self.platform_limits[platform]
        tracking = self.usage_tracking[platform]
        now = datetime.now()
        
        # Check daily limit
        if tracking['daily_count'] >= limits['daily_limit']:
            wait_until_tomorrow = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
            wait_seconds = int((wait_until_tomorrow - now).total_seconds())
            self.logger.warning(f"🚫 {platform} daily limit reached. Wait until tomorrow ({wait_seconds}s)")
            return False, wait_seconds
        
        # Check minimum interval since last request
        if tracking['last_request']:
            time_since_last = (now - tracking['last_request']).total_seconds()
            min_interval = limits['min_interval']
            
            if time_since_last < min_interval:
                wait_time = int(min_interval - time_since_last)
                self.logger.info(f"⏰ {platform} rate limit: wait {wait_time}s")
                return False, wait_time
        
        # Check burst limits
        if 'requests_per_hour' in limits:
            # Remove requests older than 1 hour
            hour_ago = now - timedelta(hours=1)
            tracking['requests'] = [req for req in tracking['requests'] if req > hour_ago]
            
            if len(tracking['requests']) >= limits['requests_per_hour']:
                oldest_request = min(tracking['requests'])
                wait_until = oldest_request + timedelta(hours=1)
                wait_seconds = int((wait_until - now).total_seconds())
                self.logger.warning(f"⏰ {platform} hourly limit reached. Wait {wait_seconds}s")
                return False, wait_seconds
        
        if 'requests_per_minute' in limits:
            # Remove requests older than 1 minute
            minute_ago = now - timedelta(minutes=1)
            recent_requests = [req for req in tracking['requests'] if req > minute_ago]
            
            if len(recent_requests) >= limits['requests_per_minute']:
                wait_seconds = 61  # Wait just over a minute
                self.logger.warning(f"⏰ {platform} minute limit reached. Wait {wait_seconds}s")
                return False, wait_seconds
        
        return True, 0
    
    def record_request(self, platform: str):
        """Record that we made a request to platform"""
        if platform not in self.usage_tracking:
            return
        
        now = datetime.now()
        tracking = self.usage_tracking[platform]
        
        # Record the request
        tracking['requests'].append(now)
        tracking['last_request'] = now
        tracking['daily_count'] += 1
        
        # Clean old requests (keep last 24 hours)
        day_ago = now - timedelta(hours=24)
        tracking['requests'] = [req for req in tracking['requests'] if req > day_ago]
        
        # Save updated usage
        self.save_usage_history()
        
        self.logger.info(f"📊 {platform} request recorded. Daily: {tracking['daily_count']}")
    
    async def wait_for_rate_limit(self, platform: str) -> bool:
        """
        Wait for rate limit to reset if needed
        Returns True if ready to proceed, False if should skip
        """
        can_request, wait_time = self.can_make_request(platform)
        
        if can_request:
            return True
        
        if wait_time > 3600:  # More than 1 hour
            self.logger.warning(f"⏰ {platform} rate limit requires {wait_time//3600}h wait. Skipping for now.")
            return False
        
        if wait_time > 0:
            self.logger.info(f"⏰ Waiting {wait_time}s for {platform} rate limit...")
            await asyncio.sleep(wait_time)
        
        return True
    
    def get_platform_status(self) -> Dict:
        """Get current status of all platforms"""
        status = {}
        
        for platform in self.platform_limits:
            can_request, wait_time = self.can_make_request(platform)
            tracking = self.usage_tracking[platform]
            limits = self.platform_limits[platform]
            
            status[platform] = {
                'can_request': can_request,
                'wait_time': wait_time,
                'daily_usage': tracking['daily_count'],
                'daily_limit': limits['daily_limit'],
                'usage_percentage': (tracking['daily_count'] / limits['daily_limit']) * 100
            }
        
        return status
    
    def get_next_available_time(self, platform: str) -> datetime:
        """Get the next time we can make a request to platform"""
        can_request, wait_time = self.can_make_request(platform)
        
        if can_request:
            return datetime.now()
        
        return datetime.now() + timedelta(seconds=wait_time)
    
    def reset_daily_limits(self):
        """Reset daily limits (call at midnight)"""
        for platform in self.usage_tracking:
            self.usage_tracking[platform]['daily_count'] = 0
            
        self.save_usage_history()
        self.logger.info("🔄 Daily rate limits reset")

# Usage example
async def safe_platform_request(rate_manager: RateLimitManager, platform: str, request_func):
    """
    Safely make a request to platform with rate limit compliance
    """
    
    # Wait for rate limit if needed
    ready = await rate_manager.wait_for_rate_limit(platform)
    
    if not ready:
        return None
    
    try:
        # Record the request
        rate_manager.record_request(platform)
        
        # Make the actual request
        result = await request_func()
        
        return result
        
    except Exception as e:
        logging.error(f"❌ {platform} request failed: {e}")
        return None

if __name__ == "__main__":
    # Test the rate limit manager
    manager = RateLimitManager()
    status = manager.get_platform_status()
    
    print("📊 RATE LIMIT STATUS")
    print("=" * 40)
    for platform, info in status.items():
        print(f"{platform.upper()}:")
        print(f"  Can request: {info['can_request']}")
        print(f"  Wait time: {info['wait_time']}s")
        print(f"  Daily usage: {info['daily_usage']}/{info['daily_limit']} ({info['usage_percentage']:.1f}%)")
        print()





























