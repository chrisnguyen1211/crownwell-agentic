#!/usr/bin/env python3
"""
J97 News Analyst - Main Runner
24/7 Ethereum News Analysis Agent
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_crawler import NewsCrawler
from news_analyzer import NewsAnalyzer
from supabase_integration import J97SupabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('j97_news_analyst.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class J97NewsAnalyst:
    """J97 - 24/7 Ethereum News Analyst"""
    
    def __init__(self):
        self.crawler = NewsCrawler()
        self.analyzer = NewsAnalyzer()
        self.supabase = J97SupabaseManager()
        
        logger.info("🕵️ J97 News Analyst initialized")
        logger.info("📰 Ready to analyze Ethereum news 24/7")
    
    async def run_analysis_cycle(self) -> Dict:
        """Run one complete analysis cycle"""
        logger.info("🔍 Starting J97 analysis cycle...")
        
        try:
            # Step 1: Crawl news from all sources
            logger.info("📡 Crawling news from all sources...")
            async with self.crawler:
                articles = await self.crawler.crawl_all_sources()
            
            if not articles:
                logger.warning("⚠️ No new articles found")
                return {
                    'status': 'no_articles',
                    'message': 'No new articles found in this cycle',
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"📰 Found {len(articles)} new articles")
            
            # Step 2: Analyze articles
            logger.info("🧠 Analyzing articles...")
            analyzed_articles = self.analyzer.analyze_articles(articles)
            
            # Step 3: Generate daily report
            logger.info("📊 Generating daily report...")
            daily_report = self.analyzer.generate_daily_report(analyzed_articles)
            
            # Step 4: Store in Supabase
            if self.supabase.client:
                logger.info("💾 Storing data in Supabase...")
                
                # Store articles
                articles_stored = self.supabase.store_articles(analyzed_articles)
                
                # Store daily report
                report_stored = self.supabase.store_daily_report(daily_report)
                
                if articles_stored and report_stored:
                    logger.info("✅ Data successfully stored in Supabase")
                else:
                    logger.warning("⚠️ Some data storage operations failed")
            else:
                logger.warning("⚠️ Supabase not available, skipping storage")
            
            # Step 5: Generate summary
            trading_signal = daily_report.get('trading_signal', {})
            
            summary = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'articles_processed': len(analyzed_articles),
                'trading_signal': trading_signal.get('signal', 'HOLD'),
                'sentiment': trading_signal.get('sentiment', 'neutral'),
                'confidence': trading_signal.get('confidence', 0.0),
                'categories': daily_report.get('categories', {}),
                'high_impact_articles': daily_report.get('high_impact_articles', 0),
                'top_key_phrases': daily_report.get('top_key_phrases', [])[:5]
            }
            
            logger.info("✅ J97 analysis cycle completed successfully")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error in analysis cycle: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def print_report(self, summary: Dict):
        """Print formatted report"""
        print("\n" + "="*80)
        print("🕵️ J97 NEWS ANALYST REPORT")
        print("="*80)
        print(f"📅 Date: {summary.get('timestamp', 'Unknown')}")
        print(f"📊 Status: {summary.get('status', 'Unknown')}")
        
        if summary.get('status') == 'success':
            print(f"📰 Articles Processed: {summary.get('articles_processed', 0)}")
            print(f"💹 Trading Signal: {summary.get('trading_signal', 'HOLD')}")
            print(f"😊 Sentiment: {summary.get('sentiment', 'neutral')}")
            print(f"🎯 Confidence: {summary.get('confidence', 0.0):.2f}")
            print(f"🔥 High Impact Articles: {summary.get('high_impact_articles', 0)}")
            
            print("\n📈 Categories:")
            for category, count in summary.get('categories', {}).items():
                print(f"   {category}: {count}")
            
            print("\n🔑 Top Key Phrases:")
            for phrase, count in summary.get('top_key_phrases', [])[:5]:
                print(f"   {phrase}: {count}")
        
        elif summary.get('status') == 'no_articles':
            print("ℹ️ No new articles found in this cycle")
        
        else:
            print(f"❌ Error: {summary.get('message', 'Unknown error')}")
        
        print("="*80)
    
    async def run_single_analysis(self):
        """Run a single analysis cycle"""
        logger.info("🚀 Starting J97 single analysis...")
        
        summary = await self.run_analysis_cycle()
        self.print_report(summary)
        
        # Save summary to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"j97_analysis_summary_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Summary saved to {filename}")
        return summary
    
    async def run_continuous_analysis(self, interval_hours: int = 1):
        """Run continuous analysis every X hours"""
        logger.info(f"🔄 Starting J97 continuous analysis (every {interval_hours} hours)")
        
        while True:
            try:
                summary = await self.run_analysis_cycle()
                self.print_report(summary)
                
                # Wait for next cycle
                logger.info(f"⏰ Waiting {interval_hours} hours until next analysis...")
                await asyncio.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("🛑 J97 continuous analysis stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous analysis: {e}")
                logger.info("⏰ Waiting 5 minutes before retry...")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='J97 News Analyst - 24/7 Ethereum News Analysis')
    parser.add_argument('--mode', choices=['single', 'continuous'], default='single',
                       help='Run mode: single analysis or continuous monitoring')
    parser.add_argument('--interval', type=int, default=1,
                       help='Interval in hours for continuous mode (default: 1)')
    
    args = parser.parse_args()
    
    # Create J97 instance
    j97 = J97NewsAnalyst()
    
    if args.mode == 'single':
        # Run single analysis
        asyncio.run(j97.run_single_analysis())
    else:
        # Run continuous analysis
        asyncio.run(j97.run_continuous_analysis(args.interval))

if __name__ == "__main__":
    main()



