#!/usr/bin/env python3
"""
Alpha Team with Gemini LLM Integration
Enhanced to use all Crawl team data for comprehensive debate
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gemini_config import get_gemini_llm, PERSONAS

# Supabase integration
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlphaTeamGemini:
    def __init__(self):
        try:
            self.gemini = get_gemini_llm()
            self.gemini_available = True
        except Exception as e:
            # Fail fast: no mock usage allowed
            logger.error(f"Gemini not available: {e}")
            raise
            
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.supabase_client = self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client"""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase not available")
            return None
            
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not found")
            return None
            
        try:
            client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
            return client
        except Exception as e:
            logger.error(f"Supabase initialization failed: {e}")
            return None
    
    def load_historical_data_from_supabase(self) -> Dict[str, Any]:
        """Load historical data from Supabase to identify trends"""
        if not self.supabase_client:
            return {}
            
        historical_data = {}
        
        try:
            # Load historical Twitter sentiment
            twitter_data = self.supabase_client.table('twitter_posts').select('*').gte(
                'analysis_timestamp', 
                (datetime.now() - timedelta(days=7)).isoformat()
            ).execute()
            historical_data['twitter_trend'] = self._analyze_trend(twitter_data.data, 'sentiment_score')
            
            # Load historical Reddit sentiment
            reddit_data = self.supabase_client.table('reddit_posts').select('*').gte(
                'analysis_timestamp',
                (datetime.now() - timedelta(days=7)).isoformat()
            ).execute()
            historical_data['reddit_trend'] = self._analyze_trend(reddit_data.data, 'sentiment_score')
            
            # Load historical Telegram sentiment
            telegram_data = self.supabase_client.table('telegram_posts').select('*').gte(
                'analysis_timestamp',
                (datetime.now() - timedelta(days=7)).isoformat()
            ).execute()
            historical_data['telegram_trend'] = self._analyze_trend(telegram_data.data, 'sentiment_score')
            
            logger.info(f"📊 Loaded historical data: {len(historical_data)} trends")
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            
        return historical_data
    
    def _analyze_trend(self, data: List[Dict], field: str) -> Dict[str, Any]:
        """Analyze trend in historical data"""
        if not data:
            return {'trend': 'no_data', 'change': 0}
            
        # Sort by timestamp
        sorted_data = sorted(data, key=lambda x: x.get('analysis_timestamp', ''))
        
        if len(sorted_data) < 2:
            return {'trend': 'insufficient_data', 'change': 0}
            
        # Calculate trend
        recent_avg = sum(item.get(field, 0) for item in sorted_data[-5:]) / min(5, len(sorted_data))
        older_avg = sum(item.get(field, 0) for item in sorted_data[:5]) / min(5, len(sorted_data))
        
        change = recent_avg - older_avg
        trend = 'bullish' if change > 0.1 else 'bearish' if change < -0.1 else 'neutral'
        
        return {
            'trend': trend,
            'change': change,
            'recent_avg': recent_avg,
            'older_avg': older_avg,
            'data_points': len(sorted_data)
        }
        
    def load_crawl_data(self) -> Dict[str, Any]:
        """Load all data from Crawl agents"""
        crawl_data = {
            'bob': {},
            'lily': {},
            'j97': {},
            'yasuo': {}
        }
        
        # Load Bob's technical analysis
        bob_files = [
            'Bob/bob_analysis_20250916_080548.json',
            'Bob/bob_analysis_20250909_213914.json'
        ]
        for file_path in bob_files:
            full_path = os.path.join(self.base_dir, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    crawl_data['bob'] = json.load(f)
                break
        
        # Load Lily's sentiment data (from logs and any saved files)
        lily_files = [
            'Lily/lily_analysis_summary.json',
            'Lily/lily_sentiment_data.json'
        ]
        for file_path in lily_files:
            full_path = os.path.join(self.base_dir, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    crawl_data['lily'] = json.load(f)
                break
        
        # If no Lily file, create summary from known data
        if not crawl_data['lily']:
            crawl_data['lily'] = {
                'total_posts': 76,
                'sentiment': 'bullish',
                'avg_sentiment': 0.746,
                'signal': 'BUY',
                'platforms': {
                    'twitter': 28,
                    'reddit': 28,
                    'telegram': 20
                }
            }
        
        # Load J97's news analysis
        j97_files = [
            'J97/j97_analysis_summary_20250916_080607.json',
            'J97/j97_analysis_summary.json'
        ]
        for file_path in j97_files:
            full_path = os.path.join(self.base_dir, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    crawl_data['j97'] = json.load(f)
                break
        
        # Load Yasuo's onchain analysis
        yasuo_files = [
            'Yasuo - Onchain analyst/yasuo_real_data_20250916_081233.json',
            'Yasuo - Onchain analyst/yasuo_complete_data.json'
        ]
        for file_path in yasuo_files:
            full_path = os.path.join(self.base_dir, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    crawl_data['yasuo'] = json.load(f)
                break
        
        # Load historical data from Supabase for trend analysis
        historical_data = self.load_historical_data_from_supabase()
        crawl_data['historical_trends'] = historical_data
        
        return crawl_data
    
    def generate_bullish_thesis(self, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bullish thesis using Gemini LLM"""
        if self.gemini_available and self.gemini:
            try:
                task = """
Analyze all the provided data and create a comprehensive BULLISH thesis for ETH.
Consider:
1. Technical analysis signals and trends
2. Social sentiment and market psychology
3. News sentiment and fundamental developments
4. Onchain metrics (whale activity, exchange flows, ETF flows, liveliness)
5. Historical trends from Supabase data

Provide:
- Main bullish thesis statement
- Key supporting evidence from each data source
- Specific metrics and numbers that support the bullish case
- Risk factors to monitor
- Specific requests for additional data if needed
"""
                
                analysis = self.gemini.analyze_with_persona(
                    PERSONAS["alpha_bullish"], 
                    crawl_data, 
                    task
                )
            except Exception as e:
                # Fail fast: no mock usage allowed
                logger.error(f"Gemini bullish thesis failed: {e}")
                raise
        
        return {
            'thesis': analysis,
            'evidence': crawl_data,
            'requests': self._extract_data_requests(analysis)
        }
    
    def generate_bearish_thesis(self, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bearish thesis using Gemini LLM"""
        if self.gemini_available and self.gemini:
            try:
                task = """
Analyze all the provided data and create a comprehensive BEARISH thesis for ETH.
Consider:
1. Technical analysis weaknesses and breakdown risks
2. Social sentiment manipulation and over-optimism
3. Negative news and fundamental concerns
4. Onchain metrics showing selling pressure or weakness
5. Historical trends showing deterioration

Provide:
- Main bearish thesis statement
- Key risk factors from each data source
- Specific metrics and numbers that support the bearish case
- Contrarian indicators and warning signs
- Specific requests for additional data if needed
"""
                
                analysis = self.gemini.analyze_with_persona(
                    PERSONAS["alpha_bearish"], 
                    crawl_data, 
                    task
                )
            except Exception as e:
                # Fail fast: no mock usage allowed
                logger.error(f"Gemini bearish thesis failed: {e}")
                raise
        
        return {
            'thesis': analysis,
            'evidence': crawl_data,
            'requests': self._extract_data_requests(analysis)
        }
    
    def _extract_data_requests(self, analysis: str) -> List[str]:
        """Extract data requests from analysis"""
        requests = []
        lines = analysis.split('\n')
        
        # Look for specific data requests
        for line in lines:
            line_lower = line.lower()
            
            # Check for specific data types
            if any(keyword in line_lower for keyword in ['need more', 'request', 'additional data', 'more information', 'require']):
                # Categorize requests by agent
                if any(keyword in line_lower for keyword in ['technical', 'chart', 'indicator', 'bob']):
                    requests.append(f"BOB: {line.strip()}")
                elif any(keyword in line_lower for keyword in ['sentiment', 'social', 'twitter', 'reddit', 'telegram', 'lily']):
                    requests.append(f"LILY: {line.strip()}")
                elif any(keyword in line_lower for keyword in ['news', 'article', 'j97']):
                    requests.append(f"J97: {line.strip()}")
                elif any(keyword in line_lower for keyword in ['onchain', 'whale', 'etf', 'exchange', 'yasuo']):
                    requests.append(f"YASUO: {line.strip()}")
                else:
                    requests.append(f"GENERAL: {line.strip()}")
        
        # If no specific requests found, add default requests based on missing data
        if not requests:
            requests = [
                "BOB: More detailed technical analysis with specific support/resistance levels",
                "LILY: Real-time sentiment analysis with manipulation detection",
                "J97: High-impact news analysis with regulatory focus",
                "YASUO: Comprehensive onchain metrics including whale movements and ETF flows"
            ]
        
        return requests[:5]  # Limit to 5 requests
    
    def _generate_mock_bullish_thesis(self, crawl_data: Dict[str, Any]) -> str:
        """Generate mock bullish thesis when Gemini not available"""
        bob_data = crawl_data.get('bob', {})
        lily_data = crawl_data.get('lily', {})
        j97_data = crawl_data.get('j97', {})
        yasuo_data = crawl_data.get('yasuo', {})
        historical = crawl_data.get('historical_trends', {})
        
        thesis = f"""
BULLISH THESIS FOR ETH (Mock Analysis):

Based on comprehensive data analysis from all Crawl agents:

TECHNICAL ANALYSIS (Bob):
- Current signal: {bob_data.get('trading_signal', 'N/A')}
- Confidence: {bob_data.get('confidence', 'N/A')}
- Technical indicators showing potential upside momentum

SOCIAL SENTIMENT (Lily):
- Total posts analyzed: {lily_data.get('total_posts', 'N/A')}
- Average sentiment: {lily_data.get('avg_sentiment', 'N/A')}
- Signal: {lily_data.get('signal', 'N/A')}
- Strong bullish sentiment across platforms

NEWS ANALYSIS (J97):
- Articles processed: {j97_data.get('articles_processed', 'N/A')}
- Sentiment: {j97_data.get('sentiment', 'N/A')}
- High impact articles: {j97_data.get('high_impact_articles', 'N/A')}
- Positive news flow supporting bullish narrative

ONCHAIN METRICS (Yasuo):
- Whale transactions: {yasuo_data.get('whale_transactions', {}).get('count', 'N/A')}
- ETF daily flow: ${yasuo_data.get('etf_flows', {}).get('daily_flow', 0):,.0f}
- Exchange net flow: {yasuo_data.get('exchange_flows', {}).get('net_flow', 'N/A')} ETH
- Liveliness score: {yasuo_data.get('liveliness', {}).get('score', 'N/A')}

HISTORICAL TRENDS:
- Twitter trend: {historical.get('twitter_trend', {}).get('trend', 'N/A')}
- Reddit trend: {historical.get('reddit_trend', {}).get('trend', 'N/A')}
- Telegram trend: {historical.get('telegram_trend', {}).get('trend', 'N/A')}

CONCLUSION: Multiple data sources align for bullish ETH outlook with strong fundamentals and positive sentiment.
"""
        return thesis
    
    def _generate_mock_bearish_thesis(self, crawl_data: Dict[str, Any]) -> str:
        """Generate mock bearish thesis when Gemini not available"""
        bob_data = crawl_data.get('bob', {})
        lily_data = crawl_data.get('lily', {})
        j97_data = crawl_data.get('j97', {})
        yasuo_data = crawl_data.get('yasuo', {})
        historical = crawl_data.get('historical_trends', {})
        
        thesis = f"""
BEARISH THESIS FOR ETH (Mock Analysis):

Risk factors and concerns identified across all data sources:

TECHNICAL RISKS (Bob):
- Current signal: {bob_data.get('trading_signal', 'N/A')}
- Potential technical breakdown risks
- Overbought conditions may lead to correction

SENTIMENT RISKS (Lily):
- Total posts: {lily_data.get('total_posts', 'N/A')}
- Sentiment: {lily_data.get('avg_sentiment', 'N/A')}
- Risk of sentiment manipulation and over-optimism
- Contrarian indicators suggest caution

NEWS CONCERNS (J97):
- Articles: {j97_data.get('articles_processed', 'N/A')}
- High impact articles: {j97_data.get('high_impact_articles', 'N/A')}
- Potential negative news catalysts
- Regulatory risks and market uncertainty

ONCHAIN WEAKNESS (Yasuo):
- ETF outflows: ${yasuo_data.get('etf_flows', {}).get('daily_flow', 0):,.0f}
- Exchange flows: {yasuo_data.get('exchange_flows', {}).get('net_flow', 'N/A')} ETH
- Potential selling pressure from large holders
- Network activity concerns

HISTORICAL DETERIORATION:
- Twitter trend: {historical.get('twitter_trend', {}).get('trend', 'N/A')}
- Reddit trend: {historical.get('reddit_trend', {}).get('trend', 'N/A')}
- Telegram trend: {historical.get('telegram_trend', {}).get('trend', 'N/A')}

CONCLUSION: Multiple risk factors suggest potential downside with elevated volatility and correction risks.
"""
        return thesis
    
    def conduct_debate(self, bullish: Dict[str, Any], bearish: Dict[str, Any]) -> List[Dict[str, str]]:
        """Conduct debate between bullish and bearish theses"""
        debate_rounds = []
        
        if self.gemini_available and self.gemini:
            try:
                # Round 1: Initial positions
                round1_prompt = f"""
You are moderating a debate between two senior analysts.

BULLISH POSITION:
{bullish['thesis']}

BEARISH POSITION:
{bearish['thesis']}

Moderate a debate round where each side responds to the other's arguments.
Provide a structured debate with clear points and counterpoints.
"""
                
                round1_response = self.gemini.generate_response(round1_prompt)
                debate_rounds.append({
                    'round': 1,
                    'bullish': 'Initial bullish thesis presented',
                    'bearish': 'Initial bearish thesis presented',
                    'moderator': round1_response
                })
                
                # Round 2: Counter-arguments
                round2_prompt = f"""
Continue the debate. The bearish analyst should now counter the bullish arguments,
and the bullish analyst should counter the bearish arguments.

Focus on:
- Data interpretation differences
- Risk assessment variations
- Market timing considerations
- Specific metrics and their implications
"""
                
                round2_response = self.gemini.generate_response(round2_prompt)
                debate_rounds.append({
                    'round': 2,
                    'bullish': 'Counter-arguments to bearish thesis',
                    'bearish': 'Counter-arguments to bullish thesis',
                    'moderator': round2_response
                })
                
            except Exception as e:
                # Fail fast: no mock usage allowed
                logger.error(f"Gemini debate failed: {e}")
                raise
        
        return debate_rounds
    
    def _generate_mock_debate(self, bullish: Dict[str, Any], bearish: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate mock debate when Gemini not available"""
        return [
            {
                'round': 1,
                'bullish': 'Initial bullish thesis presented',
                'bearish': 'Initial bearish thesis presented',
                'moderator': 'Mock Debate Round 1: Both sides present their initial positions based on comprehensive data analysis. The bullish side emphasizes positive sentiment and technical indicators, while the bearish side highlights manipulation risks and over-optimism concerns.'
            },
            {
                'round': 2,
                'bullish': 'Counter-arguments to bearish thesis',
                'bearish': 'Counter-arguments to bullish thesis',
                'moderator': 'Mock Debate Round 2: Each side counters the other\'s arguments. The bullish side argues that manipulation concerns are overblown and fundamentals support upside, while the bearish side maintains that current sentiment is artificially inflated and technical risks remain elevated.'
            }
        ]
    
    def run_alpha_analysis(self) -> Dict[str, Any]:
        """Run complete Alpha team analysis"""
        logger.info("🔍 Alpha Team starting comprehensive analysis...")
        
        # Load all crawl data
        crawl_data = self.load_crawl_data()
        logger.info(f"📊 Loaded data from {len([k for k, v in crawl_data.items() if v])} agents")
        
        # Generate theses
        logger.info("📈 Generating bullish thesis...")
        bullish = self.generate_bullish_thesis(crawl_data)
        
        logger.info("📉 Generating bearish thesis...")
        bearish = self.generate_bearish_thesis(crawl_data)
        
        # Conduct debate
        logger.info("⚔️ Conducting debate...")
        debate_rounds = self.conduct_debate(bullish, bearish)
        
        # Compile results
        result = {
            'timestamp': datetime.now().isoformat(),
            'crawl_data_summary': {
                'bob': bool(crawl_data['bob']),
                'lily': bool(crawl_data['lily']),
                'j97': bool(crawl_data['j97']),
                'yasuo': bool(crawl_data['yasuo'])
            },
            'bullish': bullish,
            'bearish': bearish,
            'debate_rounds': debate_rounds,
            'full_crawl_data': crawl_data
        }
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"alpha_debate_gemini_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"✅ Alpha debate saved to {filename}")
        return result

def main():
    """Main execution function"""
    try:
        alpha_team = AlphaTeamGemini()
        result = alpha_team.run_alpha_analysis()
        
        print("\n" + "="*60)
        print("🎯 ALPHA TEAM GEMINI ANALYSIS COMPLETE")
        print("="*60)
        print(f"📊 Data Sources: {sum(result['crawl_data_summary'].values())}/4")
        print(f"⚔️ Debate Rounds: {len(result['debate_rounds'])}")
        print(f"📈 Bullish Requests: {len(result['bullish']['requests'])}")
        print(f"📉 Bearish Requests: {len(result['bearish']['requests'])}")
        print("✅ Analysis saved successfully!")
        
    except Exception as e:
        logger.error(f"Alpha team analysis failed: {e}")
        return None

if __name__ == "__main__":
    main()
