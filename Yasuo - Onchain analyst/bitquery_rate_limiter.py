#!/usr/bin/env python3
"""
Bitquery API Rate Limit Manager
Based on Bitquery documentation: Free tier has daily limits
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

class BitqueryRateLimiter:
    """
    Manages Bitquery API rate limits to prevent exceeding daily quotas
    Based on free tier limits from Bitquery docs
    """
    
    def __init__(self, limit_file: str = "bitquery_usage.json"):
        self.limit_file = limit_file
        self.logger = logging.getLogger(__name__)
        
        # Bitquery Free Tier Limits (conservative estimates)
        self.DAILY_QUERY_LIMIT = 100  # ~100 queries per day for free tier
        self.HOURLY_QUERY_LIMIT = 10  # ~10 queries per hour (burst protection)
        
        # API endpoint weights (different queries cost different amounts)
        self.QUERY_WEIGHTS = {
            'large_transactions': 3,    # Heavy query with filtering
            'exchange_flows': 2,        # Medium query with aggregation  
            'simple_price': 1,          # Light query
            'token_metadata': 1,        # Light query
            'balance_check': 1          # Light query
        }
        
        # Load existing usage
        self.usage_data = self.load_usage_data()
    
    def load_usage_data(self) -> Dict:
        """Load API usage data from file"""
        try:
            if os.path.exists(self.limit_file):
                with open(self.limit_file, 'r') as f:
                    data = json.load(f)
                    self.logger.info(f"Loaded usage data: {data.get('daily_usage', 0)} queries today")
                    return data
            else:
                return self.create_fresh_usage_data()
        except Exception as e:
            self.logger.error(f"Error loading usage data: {e}")
            return self.create_fresh_usage_data()
    
    def create_fresh_usage_data(self) -> Dict:
        """Create fresh usage tracking data"""
        return {
            'daily_usage': 0,
            'hourly_usage': 0,
            'last_reset_date': datetime.now().strftime('%Y-%m-%d'),
            'last_reset_hour': datetime.now().strftime('%Y-%m-%d-%H'),
            'query_history': []
        }
    
    def save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.limit_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving usage data: {e}")
    
    def reset_if_needed(self):
        """Reset counters if day/hour has changed"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        
        # Reset daily counter
        if self.usage_data['last_reset_date'] != current_date:
            self.usage_data['daily_usage'] = 0
            self.usage_data['last_reset_date'] = current_date
            self.logger.info("📅 Daily usage counter reset")
        
        # Reset hourly counter
        if self.usage_data['last_reset_hour'] != current_hour:
            self.usage_data['hourly_usage'] = 0
            self.usage_data['last_reset_hour'] = current_hour
            self.logger.info("🕐 Hourly usage counter reset")
    
    def can_make_query(self, query_type: str = 'simple') -> bool:
        """Check if we can make a query without exceeding limits"""
        self.reset_if_needed()
        
        weight = self.QUERY_WEIGHTS.get(query_type, 1)
        
        # Check daily limit
        if self.usage_data['daily_usage'] + weight > self.DAILY_QUERY_LIMIT:
            self.logger.warning(f"🚫 Daily limit reached: {self.usage_data['daily_usage']}/{self.DAILY_QUERY_LIMIT}")
            return False
        
        # Check hourly limit
        if self.usage_data['hourly_usage'] + weight > self.HOURLY_QUERY_LIMIT:
            self.logger.warning(f"🚫 Hourly limit reached: {self.usage_data['hourly_usage']}/{self.HOURLY_QUERY_LIMIT}")
            return False
        
        return True
    
    def record_query(self, query_type: str = 'simple', success: bool = True):
        """Record a query usage"""
        self.reset_if_needed()
        
        weight = self.QUERY_WEIGHTS.get(query_type, 1)
        
        if success:
            self.usage_data['daily_usage'] += weight
            self.usage_data['hourly_usage'] += weight
            
            # Add to history
            self.usage_data['query_history'].append({
                'timestamp': datetime.now().isoformat(),
                'query_type': query_type,
                'weight': weight,
                'success': success
            })
            
            # Keep only last 100 history entries
            if len(self.usage_data['query_history']) > 100:
                self.usage_data['query_history'] = self.usage_data['query_history'][-100:]
            
            self.logger.info(f"📊 Query recorded: {query_type} (weight: {weight}) - Daily: {self.usage_data['daily_usage']}/{self.DAILY_QUERY_LIMIT}")
        
        self.save_usage_data()
    
    def get_usage_status(self) -> Dict:
        """Get current usage status"""
        self.reset_if_needed()
        
        daily_remaining = max(0, self.DAILY_QUERY_LIMIT - self.usage_data['daily_usage'])
        hourly_remaining = max(0, self.HOURLY_QUERY_LIMIT - self.usage_data['hourly_usage'])
        
        return {
            'daily_used': self.usage_data['daily_usage'],
            'daily_limit': self.DAILY_QUERY_LIMIT,
            'daily_remaining': daily_remaining,
            'daily_percentage': (self.usage_data['daily_usage'] / self.DAILY_QUERY_LIMIT) * 100,
            'hourly_used': self.usage_data['hourly_usage'],
            'hourly_limit': self.HOURLY_QUERY_LIMIT,
            'hourly_remaining': hourly_remaining,
            'hourly_percentage': (self.usage_data['hourly_usage'] / self.HOURLY_QUERY_LIMIT) * 100,
            'can_query': self.can_make_query()
        }
    
    def get_recommended_intervals(self) -> Dict:
        """Get recommended query intervals based on current usage"""
        status = self.get_usage_status()
        
        # Conservative intervals to stay within limits
        if status['daily_percentage'] > 80:
            # High usage - be very conservative
            return {
                'large_transactions': 7200,   # 2 hours
                'exchange_flows': 3600,       # 1 hour  
                'etf_flows': 86400,          # 24 hours
                'liveliness': 7200           # 2 hours
            }
        elif status['daily_percentage'] > 50:
            # Medium usage - moderate intervals
            return {
                'large_transactions': 1800,   # 30 minutes
                'exchange_flows': 1800,       # 30 minutes
                'etf_flows': 86400,          # 24 hours
                'liveliness': 3600           # 1 hour
            }
        else:
            # Low usage - normal intervals
            return {
                'large_transactions': 600,    # 10 minutes
                'exchange_flows': 1800,       # 30 minutes
                'etf_flows': 86400,          # 24 hours  
                'liveliness': 3600           # 1 hour
            }
    
    def log_usage_summary(self):
        """Log current usage summary"""
        status = self.get_usage_status()
        
        self.logger.info("📊 BITQUERY API USAGE SUMMARY:")
        self.logger.info(f"📅 Daily: {status['daily_used']}/{status['daily_limit']} ({status['daily_percentage']:.1f}%)")
        self.logger.info(f"🕐 Hourly: {status['hourly_used']}/{status['hourly_limit']} ({status['hourly_percentage']:.1f}%)")
        self.logger.info(f"✅ Can Query: {status['can_query']}")
        
        if status['daily_percentage'] > 90:
            self.logger.warning("⚠️ Daily limit almost reached - consider reducing query frequency")
        elif status['daily_percentage'] > 70:
            self.logger.info("🟡 Daily usage is high - monitoring carefully")

def test_rate_limiter():
    """Test the rate limiter functionality"""
    print("🧪 Testing Bitquery Rate Limiter")
    print("=" * 40)
    
    limiter = BitqueryRateLimiter("test_bitquery_usage.json")
    
    # Test status
    status = limiter.get_usage_status()
    print(f"📊 Current Status:")
    print(f"  Daily: {status['daily_used']}/{status['daily_limit']} ({status['daily_percentage']:.1f}%)")
    print(f"  Hourly: {status['hourly_used']}/{status['hourly_limit']} ({status['hourly_percentage']:.1f}%)")
    
    # Test query check
    can_query = limiter.can_make_query('large_transactions')
    print(f"  Can make large_transactions query: {can_query}")
    
    # Test query recording
    if can_query:
        limiter.record_query('large_transactions', success=True)
        print("  ✅ Query recorded")
    
    # Test recommendations
    intervals = limiter.get_recommended_intervals()
    print(f"\n📋 Recommended Intervals:")
    for query_type, interval in intervals.items():
        print(f"  {query_type}: {interval} seconds ({interval/60:.0f} minutes)")
    
    # Cleanup test file
    if os.path.exists("test_bitquery_usage.json"):
        os.remove("test_bitquery_usage.json")

if __name__ == "__main__":
    test_rate_limiter()








