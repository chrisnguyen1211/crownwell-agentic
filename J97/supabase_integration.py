#!/usr/bin/env python3
"""
J97 Supabase Integration - Store news data and analysis
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class J97SupabaseManager:
    """J97 Supabase Integration Manager"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("Supabase credentials not found in environment variables")
            self.client = None
        else:
            try:
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                logger.info("✅ Connected to Supabase")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                self.client = None
    
    def store_articles(self, articles: List[Dict]) -> bool:
        """Store articles in Supabase"""
        if not self.client or not articles:
            return False
        
        try:
            # Prepare articles for insertion
            articles_data = []
            for article in articles:
                article_data = {
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', ''),
                    'api_source': article.get('api_source', ''),
                    'sentiment': article.get('sentiment', {}),
                    'impact_score': article.get('impact_score', 0),
                    'key_phrases': article.get('key_phrases', []),
                    'category': article.get('category', 'general'),
                    'analyzed_at': article.get('analyzed_at', ''),
                    'created_at': datetime.now().isoformat()
                }
                articles_data.append(article_data)
            
            # Insert articles
            result = self.client.table('j97_news_articles').insert(articles_data).execute()
            
            if result.data:
                logger.info(f"✅ Stored {len(articles_data)} articles in Supabase")
                return True
            else:
                logger.error("Failed to store articles in Supabase")
                return False
                
        except Exception as e:
            logger.error(f"Error storing articles: {e}")
            return False
    
    def store_daily_report(self, report: Dict) -> bool:
        """Store daily analysis report in Supabase"""
        if not self.client:
            return False
        
        try:
            report_data = {
                'date': report.get('date', ''),
                'total_articles': report.get('total_articles', 0),
                'trading_signal': report.get('trading_signal', {}),
                'categories': report.get('categories', {}),
                'sentiment_breakdown': report.get('sentiment_breakdown', {}),
                'top_key_phrases': report.get('top_key_phrases', []),
                'high_impact_articles': report.get('high_impact_articles', 0),
                'high_impact_titles': report.get('high_impact_titles', []),
                'created_at': datetime.now().isoformat()
            }
            
            # Insert report
            result = self.client.table('j97_daily_reports').insert([report_data]).execute()
            
            if result.data:
                logger.info(f"✅ Stored daily report for {report_data['date']}")
                return True
            else:
                logger.error("Failed to store daily report")
                return False
                
        except Exception as e:
            logger.error(f"Error storing daily report: {e}")
            return False
    
    def get_recent_articles(self, hours: int = 24) -> List[Dict]:
        """Get recent articles from Supabase"""
        if not self.client:
            return []
        
        try:
            # Calculate timestamp for X hours ago
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            cutoff_iso = datetime.fromtimestamp(cutoff_time).isoformat()
            
            result = self.client.table('j97_news_articles')\
                .select('*')\
                .gte('created_at', cutoff_iso)\
                .order('created_at', desc=True)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching recent articles: {e}")
            return []
    
    def get_daily_reports(self, days: int = 7) -> List[Dict]:
        """Get recent daily reports from Supabase"""
        if not self.client:
            return []
        
        try:
            result = self.client.table('j97_daily_reports')\
                .select('*')\
                .order('date', desc=True)\
                .limit(days)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching daily reports: {e}")
            return []
    
    def get_articles_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get articles by category"""
        if not self.client:
            return []
        
        try:
            result = self.client.table('j97_news_articles')\
                .select('*')\
                .eq('category', category)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching articles by category: {e}")
            return []
    
    def get_high_impact_articles(self, min_impact: float = 5.0, limit: int = 20) -> List[Dict]:
        """Get high impact articles"""
        if not self.client:
            return []
        
        try:
            result = self.client.table('j97_news_articles')\
                .select('*')\
                .gte('impact_score', min_impact)\
                .order('impact_score', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching high impact articles: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """Clean up old data to keep database size manageable"""
        if not self.client:
            return False
        
        try:
            # Calculate cutoff date
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            cutoff_iso = datetime.fromtimestamp(cutoff_time).isoformat()
            
            # Delete old articles
            result_articles = self.client.table('j97_news_articles')\
                .delete()\
                .lt('created_at', cutoff_iso)\
                .execute()
            
            # Delete old reports
            result_reports = self.client.table('j97_daily_reports')\
                .delete()\
                .lt('created_at', cutoff_iso)\
                .execute()
            
            logger.info(f"✅ Cleaned up data older than {days_to_keep} days")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False

if __name__ == "__main__":
    # Test the Supabase integration
    manager = J97SupabaseManager()
    
    if manager.client:
        print("✅ Supabase connection successful")
        
        # Test fetching recent articles
        recent_articles = manager.get_recent_articles(24)
        print(f"Recent articles (24h): {len(recent_articles)}")
        
        # Test fetching daily reports
        daily_reports = manager.get_daily_reports(7)
        print(f"Daily reports (7 days): {len(daily_reports)}")
    else:
        print("❌ Supabase connection failed")









