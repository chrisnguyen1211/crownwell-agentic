#!/usr/bin/env python3
"""
🏛️ ALPHA TEAM - ENHANCED GEMINI DEBATE SYSTEM
Separate Alpha team file with Gemini-powered debate analysis
"""

import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('gemini_config.env')  # Load Gemini config

# Gemini imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Supabase imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

class AlphaTeamDebateEngine:
    """Enhanced Alpha Team with Gemini-powered debate analysis"""
    
    def __init__(self, gemini_api_key: str = None, supabase_url: str = None, supabase_key: str = None):
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        self.supabase_client: Optional[Client] = None
        self.gemini_model = None
        self.gemini_model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        self.setup_logging()
        self.initialize_services()
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def initialize_services(self):
        """Initialize Gemini and Supabase services"""
        # Initialize Gemini
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
                self.logger.info(f"✅ Gemini initialized (model: {self.gemini_model_name})")
            except Exception as e:
                self.logger.error(f"❌ Gemini initialization failed: {e}")
                self.gemini_model = None
        else:
            self.logger.warning("⚠️ Gemini not available")
        
        # Initialize Supabase
        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
                self.logger.info("✅ Supabase connected")
            except Exception as e:
                self.logger.error(f"❌ Supabase connection failed: {e}")
                self.supabase_client = None
        else:
            self.logger.warning("⚠️ Supabase not available")
    
    def fetch_crawl_data(self) -> Dict:
        """Fetch last 10 days of data from all crawl agents with simple summaries"""
        crawl_data = {
            'lily': {},
            'bob': {},
            'yasuo': {},
            'j97': {},
            'lily_summary': '',
            'bob_summary': '',
            'yasuo_summary': '',
            'j97_summary': '',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if not self.supabase_client:
            self.logger.warning("⚠️ Supabase not available, using empty data")
            return crawl_data
        
        try:
            since_iso = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

            # Fetch Lily sentiment data (last 10 days)
            lily_q = self.supabase_client.table('lily_aggregated_sentiment').select('*').gte('created_at', since_iso).order('created_at', desc=True)
            lily_data = lily_q.limit(500).execute()
            if lily_data.data:
                crawl_data['lily'] = lily_data.data[0]
                total = len(lily_data.data)
                pos = sum(1 for r in lily_data.data if str(r.get('overall_sentiment', '')).lower() == 'bullish')
                neg = sum(1 for r in lily_data.data if str(r.get('overall_sentiment', '')).lower() == 'bearish')
                neu = total - pos - neg
                avg_conf = None
                try:
                    scores = [float(r.get('confidence_score')) for r in lily_data.data if r.get('confidence_score') is not None]
                    avg_conf = round(sum(scores)/len(scores), 3) if scores else None
                except Exception:
                    avg_conf = None
                crawl_data['lily_summary'] = f"{total} records/10d: bullish={pos}, bearish={neg}, neutral={neu}, avg_conf={avg_conf}"

            # Fetch Bob technical analysis (last 10 days)
            bob_q = self.supabase_client.table('bob_technical_analysis').select('*').gte('analysis_timestamp', since_iso).order('analysis_timestamp', desc=True)
            bob_data = bob_q.limit(500).execute()
            if bob_data.data:
                crawl_data['bob'] = bob_data.data[0]
                total = len(bob_data.data)
                bull = sum(1 for r in bob_data.data if str(r.get('signal_direction', '')).lower() in ['long', 'bullish', 'buy'])
                bear = sum(1 for r in bob_data.data if str(r.get('signal_direction', '')).lower() in ['short', 'bearish', 'sell'])
                wait = total - bull - bear
                avg_conf = None
                try:
                    scores = [float(r.get('confidence_score')) for r in bob_data.data if r.get('confidence_score') is not None]
                    avg_conf = round(sum(scores)/len(scores), 3) if scores else None
                except Exception:
                    avg_conf = None
                crawl_data['bob_summary'] = f"{total} analyses/10d: long={bull}, short={bear}, wait={wait}, avg_conf={avg_conf}"

            # Fetch Yasuo on-chain data (last 10 days)
            yasuo_q = self.supabase_client.table('yasuo_full_snapshot').select('*').gte('created_at', since_iso).order('created_at', desc=True)
            yasuo_data = yasuo_q.limit(500).execute()
            if yasuo_data.data:
                crawl_data['yasuo'] = yasuo_data.data[0]
                total = len(yasuo_data.data)
                crawl_data['yasuo_summary'] = f"{total} snapshots/10d; latest summary: {str(yasuo_data.data[0].get('summary', 'N/A'))[:120]}"

            # Fetch J97 news data (last 10 days)
            j97_q = self.supabase_client.table('j97_daily_reports').select('*').gte('created_at', since_iso).order('created_at', desc=True)
            j97_data = j97_q.limit(500).execute()
            if j97_data.data:
                crawl_data['j97'] = j97_data.data[0]
                total = len(j97_data.data)
                sig = sum(1 for r in j97_data.data if r.get('trading_signal'))
                crawl_data['j97_summary'] = f"{total} reports/10d; with trading_signal={sig}; latest signal={j97_data.data[0].get('trading_signal', 'N/A')}"

            self.logger.info("✅ Crawl data (10d window) fetched successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching crawl data: {e}")
        
        return crawl_data
    
    def analyze_with_gemini(self, prompt: str, context: str = "") -> str:
        """Analyze data using Gemini"""
        if not self.gemini_model:
            return "Gemini not available - using fallback analysis"
        
        try:
            full_prompt = f"""
{context}

{prompt}

Please provide a detailed analysis focusing on:
1. Key evidence and data points
2. Market implications
3. Confidence level (0-1)
4. Specific reasoning

Format your response as structured JSON when possible.
"""
            
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"❌ Gemini analysis failed: {e}")
            return f"Analysis error: {str(e)}"
    
    def run_bullish_analysis(self, crawl_data: Dict) -> Dict:
        """Run bullish agent analysis"""
        context = f"""
Crawl Team Data Summary:
- Lily Sentiment: {crawl_data.get('lily', {}).get('overall_sentiment', 'N/A')}
- Bob Technical: {crawl_data.get('bob', {}).get('signal_direction', 'N/A')}
- Yasuo On-chain: {crawl_data.get('yasuo', {}).get('summary', 'N/A')}
- J97 News: {crawl_data.get('j97', {}).get('trading_signal', 'N/A')}
"""
        
        prompt = """
As a BULLISH ETH analyst, analyze the provided data and present your strongest arguments for why ETH price will go UP.

Focus on:
1. Positive sentiment indicators
2. Bullish technical patterns
3. On-chain metrics showing accumulation
4. Positive news catalysts
5. Market structure advantages

Provide specific evidence and reasoning for each point.
"""
        
        analysis = self.analyze_with_gemini(prompt, context)
        
        return {
            'agent_name': 'Bullish Agent',
            'analysis': analysis,
            'evidence_points': self.extract_evidence_points(analysis),
            'confidence': self.extract_confidence(analysis),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def run_bearish_analysis(self, crawl_data: Dict) -> Dict:
        """Run bearish agent analysis"""
        context = f"""
Crawl Team Data Summary:
- Lily Sentiment: {crawl_data.get('lily', {}).get('overall_sentiment', 'N/A')}
- Bob Technical: {crawl_data.get('bob', {}).get('signal_direction', 'N/A')}
- Yasuo On-chain: {crawl_data.get('yasuo', {}).get('summary', 'N/A')}
- J97 News: {crawl_data.get('j97', {}).get('trading_signal', 'N/A')}
"""
        
        prompt = """
As a BEARISH ETH analyst, analyze the provided data and present your strongest arguments for why ETH price will go DOWN.

Focus on:
1. Negative sentiment indicators
2. Bearish technical patterns
3. On-chain metrics showing distribution
4. Negative news catalysts
5. Market structure disadvantages

Provide specific evidence and reasoning for each point.
"""
        
        analysis = self.analyze_with_gemini(prompt, context)
        
        return {
            'agent_name': 'Bearish Agent',
            'analysis': analysis,
            'evidence_points': self.extract_evidence_points(analysis),
            'confidence': self.extract_confidence(analysis),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def run_rebuttal_round(self, initial_analysis: Dict, opposing_analysis: Dict, round_number: int) -> Dict:
        """Run rebuttal round"""
        context = f"""
Round {round_number} Rebuttal Context:

Initial Analysis ({initial_analysis['agent_name']}):
{initial_analysis['analysis']}

Opposing Analysis ({opposing_analysis['agent_name']}):
{opposing_analysis['analysis']}
"""
        
        prompt = f"""
As the {initial_analysis['agent_name']}, provide a strong rebuttal to the opposing arguments.

Your task:
1. Address each opposing point directly
2. Provide counter-evidence
3. Highlight weaknesses in their analysis
4. Strengthen your original position
5. Maintain professional debate standards

Be specific and evidence-based in your rebuttal.
"""
        
        rebuttal = self.analyze_with_gemini(prompt, context)
        
        return {
            'round': round_number,
            'agent_name': initial_analysis['agent_name'],
            'rebuttal': rebuttal,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def extract_evidence_points(self, analysis: str) -> List[str]:
        """Extract key evidence points from analysis"""
        # Simple extraction - in production, use more sophisticated NLP
        lines = analysis.split('\n')
        evidence_points = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('1.') or line.startswith('2.')):
                evidence_points.append(line)
        
        return evidence_points[:5]  # Limit to top 5 points
    
    def extract_confidence(self, analysis: str) -> float:
        """Extract confidence score from analysis"""
        # Simple extraction - look for confidence mentions
        analysis_lower = analysis.lower()
        
        if 'high confidence' in analysis_lower or 'very confident' in analysis_lower:
            return 0.8
        elif 'moderate confidence' in analysis_lower or 'somewhat confident' in analysis_lower:
            return 0.6
        elif 'low confidence' in analysis_lower or 'uncertain' in analysis_lower:
            return 0.3
        else:
            return 0.5  # Default moderate confidence
    
    def determine_winner(self, bullish_data: Dict, bearish_data: Dict) -> Tuple[str, float]:
        """Determine debate winner and confidence"""
        bullish_score = bullish_data.get('confidence', 0.5)
        bearish_score = bearish_data.get('confidence', 0.5)
        
        # Simple scoring - in production, use more sophisticated analysis
        if abs(bullish_score - bearish_score) < 0.1:
            return 'TIE', 0.5
        elif bullish_score > bearish_score:
            return 'BULLISH', bullish_score
        else:
            return 'BEARISH', bearish_score
    
    def check_data_sufficiency(self, crawl_data: Dict) -> Tuple[bool, List[str]]:
        """Check if crawl data is sufficient for meaningful debate"""
        missing_data = []
        
        # Check each data source
        if not crawl_data.get('lily'):
            missing_data.append('sentiment_data')
        if not crawl_data.get('bob'):
            missing_data.append('technical_analysis')
        if not crawl_data.get('yasuo'):
            missing_data.append('onchain_data')
        if not crawl_data.get('j97'):
            missing_data.append('news_data')
        
        # Consider data sufficient if we have at least 2 sources
        sufficient = len(missing_data) <= 2
        
        return sufficient, missing_data
    
    def save_debate_session(self, session_data: Dict) -> bool:
        """Save debate session to Supabase"""
        if not self.supabase_client:
            self.logger.warning("⚠️ Supabase not available, skipping save")
            return False
        
        try:
            result = self.supabase_client.table('alpha_debate_sessions').insert(session_data).execute()
            self.logger.info("✅ Debate session saved to Supabase")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving debate session: {e}")
            return False
    
    def run_full_debate(self) -> Dict:
        """Run complete Alpha team debate process"""
        self.logger.info("🏛️ Starting Alpha Team Debate Session")
        
        # Generate session ID
        session_id = f"alpha_debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Step 1: Fetch crawl data
        self.logger.info("📊 Fetching crawl team data...")
        crawl_data = self.fetch_crawl_data()
        
        # Step 2: Check data sufficiency
        sufficient, missing_data = self.check_data_sufficiency(crawl_data)
        
        if not sufficient:
            self.logger.warning(f"⚠️ Insufficient data: {missing_data}")
            # Create a basic debate session even with insufficient data
            basic_session = {
                'session_id': session_id,
                'session_timestamp': datetime.now(timezone.utc).isoformat(),
                'bullish_agent_name': 'Bullish Agent',
                'bearish_agent_name': 'Bearish Agent',
                'crawl_data_sources': list(crawl_data.keys()),
                'round_1_bullish_evidence': {'analysis': 'Insufficient data for detailed analysis', 'confidence': 0.3},
                'round_1_bearish_evidence': {'analysis': 'Insufficient data for detailed analysis', 'confidence': 0.3},
                'round_1_bullish_rebuttal': {'rebuttal': 'Limited data available', 'round': 1},
                'round_1_bearish_rebuttal': {'rebuttal': 'Limited data available', 'round': 1},
                'round_2_bullish_evidence': {'analysis': 'Insufficient data for detailed analysis', 'confidence': 0.3},
                'round_2_bearish_evidence': {'analysis': 'Insufficient data for detailed analysis', 'confidence': 0.3},
                'round_2_bullish_rebuttal': {'rebuttal': 'Limited data available', 'round': 2},
                'round_2_bearish_rebuttal': {'rebuttal': 'Limited data available', 'round': 2},
                'final_bullish_score': 0.3,
                'final_bearish_score': 0.3,
                'debate_winner': 'TIE',
                'confidence_level': 0.3,
                'data_sufficient': False,
                'missing_data_types': missing_data,
                'dispatcher_activated': True,
                'debate_summary': 'Alpha team debate completed with limited data. Winner: TIE',
                'key_arguments': {'bullish_key_points': [], 'bearish_key_points': []},
                'market_implications': {'winner': 'TIE', 'confidence': 0.3, 'next_steps': 'Request more data'}
            }
            
            # Save to Supabase if available
            self.save_debate_session(basic_session)
            
            self.logger.info(f"✅ Alpha Team Debate completed with limited data. Winner: TIE")
            return basic_session
        
        # Step 3: Run initial analysis
        self.logger.info("🔍 Running initial bullish analysis...")
        bullish_analysis = self.run_bullish_analysis(crawl_data)
        
        self.logger.info("🔍 Running initial bearish analysis...")
        bearish_analysis = self.run_bearish_analysis(crawl_data)
        
        # Step 4: Run rebuttal rounds
        self.logger.info("⚔️ Running Round 1 rebuttals...")
        bullish_rebuttal_1 = self.run_rebuttal_round(bullish_analysis, bearish_analysis, 1)
        bearish_rebuttal_1 = self.run_rebuttal_round(bearish_analysis, bullish_analysis, 1)
        
        self.logger.info("⚔️ Running Round 2 rebuttals...")
        bullish_rebuttal_2 = self.run_rebuttal_round(bullish_analysis, bearish_analysis, 2)
        bearish_rebuttal_2 = self.run_rebuttal_round(bearish_analysis, bullish_analysis, 2)
        
        # Step 5: Determine winner
        winner, confidence = self.determine_winner(bullish_analysis, bearish_analysis)
        
        # Step 6: Compile session data
        session_data = {
            'session_id': session_id,
            'session_timestamp': datetime.now(timezone.utc).isoformat(),
            'bullish_agent_name': 'Bullish Agent',
            'bearish_agent_name': 'Bearish Agent',
            'crawl_data_sources': list(crawl_data.keys()),
            
            'round_1_bullish_evidence': bullish_analysis,
            'round_1_bearish_evidence': bearish_analysis,
            'round_1_bullish_rebuttal': bullish_rebuttal_1,
            'round_1_bearish_rebuttal': bearish_rebuttal_1,
            
            'round_2_bullish_evidence': bullish_analysis,  # Could be updated with new evidence
            'round_2_bearish_evidence': bearish_analysis,   # Could be updated with new evidence
            'round_2_bullish_rebuttal': bullish_rebuttal_2,
            'round_2_bearish_rebuttal': bearish_rebuttal_2,
            
            'final_bullish_score': bullish_analysis.get('confidence', 0.5),
            'final_bearish_score': bearish_analysis.get('confidence', 0.5),
            'debate_winner': winner,
            'confidence_level': confidence,
            
            'data_sufficient': sufficient,
            'missing_data_types': missing_data,
            'dispatcher_activated': not sufficient,
            
            'debate_summary': f"Alpha team debate completed. Winner: {winner} with {confidence:.2f} confidence.",
            'key_arguments': {
                'bullish_key_points': bullish_analysis.get('evidence_points', []),
                'bearish_key_points': bearish_analysis.get('evidence_points', [])
            },
            'market_implications': {
                'winner': winner,
                'confidence': confidence,
                'next_steps': 'Proceed to Justin analysis' if sufficient else 'Request more data'
            }
        }
        
        # Step 7: Save to Supabase
        self.save_debate_session(session_data)
        
        self.logger.info(f"✅ Alpha Team Debate completed. Winner: {winner}")
        
        return session_data

def main():
    """Main function to run Alpha Team debate"""
    print("🏛️" * 50)
    print("🏛️ ALPHA TEAM - ENHANCED GEMINI DEBATE SYSTEM 🏛️")
    print("🏛️" * 50)
    print("")
    print("🎯 Bullish vs Bearish Agent Debate")
    try:
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    except Exception:
        model_name = 'gemini-2.5-flash'
    print(f"🧠 Powered by {model_name}")
    print("💾 Data stored in Supabase")
    print("")
    print("🚀 Starting debate session...")
    print("=" * 60)
    
    # Initialize debate engine
    engine = AlphaTeamDebateEngine()
    
    # Run full debate
    result = engine.run_full_debate()
    
    # Print results
    print("\n📊 DEBATE RESULTS:")
    print("=" * 40)
    print(f"Session ID: {result['session_id']}")
    print(f"Winner: {result['debate_winner']}")
    print(f"Confidence: {result['confidence_level']:.2f}")
    print(f"Data Sufficient: {result['data_sufficient']}")
    # Emit full debate session JSON for downstream capture
    try:
        print("\n=== ALPHA_DEBATE_SESSION_JSON_START ===")
        print(json.dumps(result))
        print("=== ALPHA_DEBATE_SESSION_JSON_END ===")
    except Exception as _:
        pass
    
    if result.get('dispatcher_needed'):
        print("🔄 Dispatcher activation needed for more data")
    
    print("\n🏛️" * 50)
    print("🏛️ Alpha Team Debate Session Complete! 🏛️")
    print("🏛️" * 50)

if __name__ == "__main__":
    main()
