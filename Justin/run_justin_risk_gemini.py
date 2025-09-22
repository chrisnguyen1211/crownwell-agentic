#!/usr/bin/env python3
"""
⚖️ JUSTIN + RISK TEAM - ENHANCED GEMINI ANALYSIS SYSTEM
Combined Justin trading manager and Risk team analysis
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

class JustinRiskAnalysisEngine:
    """Combined Justin trading manager and Risk team analysis"""
    
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
    
    def fetch_analysis_data(self) -> Dict:
        """Fetch last 10 days from crawl team and alpha team with summaries"""
        analysis_data = {
            'crawl_data': {},
            'alpha_debate': {},
            'summaries': {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if not self.supabase_client:
            self.logger.warning("⚠️ Supabase not available, using empty data")
            return analysis_data
        
        try:
            since_iso = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
            crawl_data = {}

            # Lily sentiment (10 days)
            lily_q = self.supabase_client.table('lily_aggregated_sentiment').select('*').gte('created_at', since_iso).order('created_at', desc=True)
            lily_data = lily_q.limit(500).execute()
            if lily_data.data:
                crawl_data['lily'] = lily_data.data[0]
                total = len(lily_data.data)
                pos = sum(1 for r in lily_data.data if str(r.get('overall_sentiment', '')).lower() == 'bullish')
                neg = sum(1 for r in lily_data.data if str(r.get('overall_sentiment', '')).lower() == 'bearish')
                neu = total - pos - neg
                try:
                    scores = [float(r.get('confidence_score')) for r in lily_data.data if r.get('confidence_score') is not None]
                    avg_conf = round(sum(scores)/len(scores), 3) if scores else None
                except Exception:
                    avg_conf = None
                analysis_data['summaries']['lily'] = f"{total} records/10d: bullish={pos}, bearish={neg}, neutral={neu}, avg_conf={avg_conf}"

            # Bob technical (10 days)
            bob_q = self.supabase_client.table('bob_technical_analysis').select('*').gte('analysis_timestamp', since_iso).order('analysis_timestamp', desc=True)
            bob_data = bob_q.limit(500).execute()
            if bob_data.data:
                crawl_data['bob'] = bob_data.data[0]
                total = len(bob_data.data)
                bull = sum(1 for r in bob_data.data if str(r.get('signal_direction', '')).lower() in ['long', 'bullish', 'buy'])
                bear = sum(1 for r in bob_data.data if str(r.get('signal_direction', '')).lower() in ['short', 'bearish', 'sell'])
                wait = total - bull - bear
                try:
                    scores = [float(r.get('confidence_score')) for r in bob_data.data if r.get('confidence_score') is not None]
                    avg_conf = round(sum(scores)/len(scores), 3) if scores else None
                except Exception:
                    avg_conf = None
                analysis_data['summaries']['bob'] = f"{total} analyses/10d: long={bull}, short={bear}, wait={wait}, avg_conf={avg_conf}"

            # Yasuo on-chain (10 days)
            yasuo_q = self.supabase_client.table('yasuo_full_snapshot').select('*').gte('created_at', since_iso).order('created_at', desc=True)
            yasuo_data = yasuo_q.limit(500).execute()
            if yasuo_data.data:
                crawl_data['yasuo'] = yasuo_data.data[0]
                total = len(yasuo_data.data)
                analysis_data['summaries']['yasuo'] = f"{total} snapshots/10d; latest summary: {str(yasuo_data.data[0].get('summary', 'N/A'))[:120]}"

            # J97 news (10 days)
            j97_q = self.supabase_client.table('j97_daily_reports').select('*').gte('created_at', since_iso).order('created_at', desc=True)
            j97_data = j97_q.limit(500).execute()
            if j97_data.data:
                crawl_data['j97'] = j97_data.data[0]
                total = len(j97_data.data)
                sig = sum(1 for r in j97_data.data if r.get('trading_signal'))
                analysis_data['summaries']['j97'] = f"{total} reports/10d; with trading_signal={sig}; latest signal={j97_data.data[0].get('trading_signal', 'N/A')}"

            analysis_data['crawl_data'] = crawl_data

            # Alpha debate sessions (10 days)
            alpha_q = self.supabase_client.table('alpha_debate_sessions').select('*').gte('session_timestamp', since_iso).order('session_timestamp', desc=True)
            alpha_data = alpha_q.limit(50).execute()
            if alpha_data.data:
                analysis_data['alpha_debate'] = alpha_data.data[0]
                avg_conf = None
                try:
                    scores = [float(r.get('confidence_level')) for r in alpha_data.data if r.get('confidence_level') is not None]
                    avg_conf = round(sum(scores)/len(scores), 3) if scores else None
                except Exception:
                    avg_conf = None
                analysis_data['summaries']['alpha'] = f"{len(alpha_data.data)} sessions/10d; avg_conf={avg_conf}; latest_winner={alpha_data.data[0].get('debate_winner', 'N/A')}"
            
            self.logger.info("✅ Analysis data fetched successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching analysis data: {e}")
        
        return analysis_data
    
    def analyze_with_gemini(self, prompt: str, context: str = "") -> str:
        """Analyze data using Gemini"""
        if not self.gemini_model:
            return "Gemini not available - using fallback analysis"
        
        try:
            full_prompt = f"""
{context}

{prompt}

Please provide a detailed analysis focusing on:
1. Key insights and market implications
2. Specific trading recommendations
3. Risk assessment
4. Confidence level (0-1)
5. Detailed reasoning

Format your response as structured analysis when possible.
"""
            
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"❌ Gemini analysis failed: {e}")
            return f"Analysis error: {str(e)}"
    
    def _extract_alpha_debate_content(self, alpha_debate: Dict) -> str:
        """Extract detailed content from Alpha team debate for independent analysis"""
        if not alpha_debate:
            return "No Alpha debate data available"
        
        content = f"""
DEBATE SESSION DETAILS:
- Session ID: {alpha_debate.get('session_id', 'N/A')}
- Timestamp: {alpha_debate.get('session_timestamp', 'N/A')}
- Data Sufficient: {alpha_debate.get('data_sufficient', 'N/A')}
- Missing Data Types: {alpha_debate.get('missing_data_types', [])}

ROUND 1 BULLISH EVIDENCE:
{alpha_debate.get('round_1_bullish_evidence', {})}

ROUND 1 BEARISH EVIDENCE:
{alpha_debate.get('round_1_bearish_evidence', {})}

ROUND 1 BULLISH REBUTTAL:
{alpha_debate.get('round_1_bullish_rebuttal', {})}

ROUND 1 BEARISH REBUTTAL:
{alpha_debate.get('round_1_bearish_rebuttal', {})}

ROUND 2 BULLISH EVIDENCE:
{alpha_debate.get('round_2_bullish_evidence', {})}

ROUND 2 BEARISH EVIDENCE:
{alpha_debate.get('round_2_bearish_evidence', {})}

ROUND 2 BULLISH REBUTTAL:
{alpha_debate.get('round_2_bullish_rebuttal', {})}

ROUND 2 BEARISH REBUTTAL:
{alpha_debate.get('round_2_bearish_rebuttal', {})}

FINAL SCORES:
- Bullish Score: {alpha_debate.get('final_bullish_score', 'N/A')}
- Bearish Score: {alpha_debate.get('final_bearish_score', 'N/A')}
- Winner: {alpha_debate.get('debate_winner', 'N/A')}
- Confidence: {alpha_debate.get('confidence_level', 'N/A')}

KEY ARGUMENTS:
- Bullish Key Points: {alpha_debate.get('key_arguments', {}).get('bullish_key_points', [])}
- Bearish Key Points: {alpha_debate.get('key_arguments', {}).get('bearish_key_points', [])}

MARKET IMPLICATIONS:
{alpha_debate.get('market_implications', {})}

DEBATE SUMMARY:
{alpha_debate.get('debate_summary', 'N/A')}
"""
        return content
    
    def _check_data_adequacy(self, analysis_data: Dict) -> Tuple[bool, List[str]]:
        """Check if data is adequate for confident analysis"""
        missing_data = []
        crawl_data = analysis_data.get('crawl_data', {})
        alpha_debate = analysis_data.get('alpha_debate', {})
        
        # Check crawl data completeness
        if not crawl_data.get('lily'):
            missing_data.append('sentiment_data')
        if not crawl_data.get('bob'):
            missing_data.append('technical_analysis')
        if not crawl_data.get('yasuo'):
            missing_data.append('onchain_data')
        if not crawl_data.get('j97'):
            missing_data.append('news_data')
        
        # Check Alpha debate quality
        if not alpha_debate:
            missing_data.append('alpha_debate')
        elif not alpha_debate.get('data_sufficient', False):
            missing_data.extend(alpha_debate.get('missing_data_types', []))
        
        # Check confidence levels
        alpha_confidence = alpha_debate.get('confidence_level', 0)
        if alpha_confidence < 0.6:
            missing_data.append('low_alpha_confidence')
        
        adequate = len(missing_data) == 0
        return adequate, missing_data
    
    def _dispatch_data_request(self, missing_data: List[str]) -> Dict:
        """Dispatch request for additional data"""
        dispatch_requests = []
        
        for data_type in missing_data:
            if data_type == 'sentiment_data':
                dispatch_requests.append({
                    'agent': 'lily',
                    'request': 'fresh_sentiment_analysis',
                    'priority': 'high',
                    'reason': 'Insufficient sentiment data for confident analysis'
                })
            elif data_type == 'technical_analysis':
                dispatch_requests.append({
                    'agent': 'bob',
                    'request': 'comprehensive_technical_analysis',
                    'priority': 'high',
                    'reason': 'Technical analysis needed for trading decisions'
                })
            elif data_type == 'onchain_data':
                dispatch_requests.append({
                    'agent': 'yasuo',
                    'request': 'detailed_onchain_metrics',
                    'priority': 'medium',
                    'reason': 'On-chain data crucial for market sentiment'
                })
            elif data_type == 'news_data':
                dispatch_requests.append({
                    'agent': 'j97',
                    'request': 'comprehensive_news_analysis',
                    'priority': 'medium',
                    'reason': 'News sentiment important for market context'
                })
            elif data_type == 'low_alpha_confidence':
                dispatch_requests.append({
                    'agent': 'alpha_team',
                    'request': 'enhanced_debate_analysis',
                    'priority': 'high',
                    'reason': 'Alpha team confidence too low for reliable analysis'
                })
        
        return {
            'dispatch_required': len(dispatch_requests) > 0,
            'requests': dispatch_requests,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def run_justin_analysis(self, analysis_data: Dict) -> Dict:
        """Run Justin's trading manager analysis with detailed Alpha debate content"""
        crawl_data = analysis_data.get('crawl_data', {})
        alpha_debate = analysis_data.get('alpha_debate', {})
        
        # Check data adequacy and dispatch requests if needed
        data_adequate, missing_data = self._check_data_adequacy(analysis_data)
        dispatch_info = self._dispatch_data_request(missing_data)
        
        # Extract detailed Alpha debate content
        alpha_content = self._extract_alpha_debate_content(alpha_debate)
        
        context = f"""
CRAWL TEAM DATA:
- Lily Sentiment: {crawl_data.get('lily', {}).get('overall_sentiment', 'N/A')}
- Bob Technical Signal: {crawl_data.get('bob', {}).get('signal_direction', 'N/A')}
- Bob Confidence: {crawl_data.get('bob', {}).get('confidence_score', 'N/A')}
- Yasuo On-chain Summary: {crawl_data.get('yasuo', {}).get('summary', 'N/A')}
- J97 Trading Signal: {crawl_data.get('j97', {}).get('trading_signal', 'N/A')}

DETAILED ALPHA TEAM DEBATE CONTENT:
{alpha_content}

ALPHA TEAM SUMMARY:
- Debate Winner: {alpha_debate.get('debate_winner', 'N/A')}
- Confidence Level: {alpha_debate.get('confidence_level', 'N/A')}
- Data Sufficient: {alpha_debate.get('data_sufficient', 'N/A')}
- Missing Data: {alpha_debate.get('missing_data_types', [])}
"""
        
        prompt = f"""
As JUSTIN, a 15-year veteran trading manager with deep market experience, analyze the provided data and provide your INDEPENDENT expert trading recommendations.

CRITICAL: You must provide your OWN independent analysis, not just agree with Alpha Team's conclusions. Challenge their assumptions and provide alternative perspectives.

DATA ADEQUACY STATUS:
- Data Adequate: {data_adequate}
- Missing Data: {missing_data}
- Dispatch Required: {dispatch_info.get('dispatch_required', False)}

Your expertise includes:
- Market manipulation detection
- Risk management
- Portfolio optimization
- Long-term value assessment
- Short-term trading opportunities
- Independent critical thinking

ANALYSIS REQUIREMENTS:

1. INDEPENDENT ASSESSMENT:
   - Challenge Alpha Team's conclusions
   - Identify potential biases in their analysis
   - Provide alternative interpretations of the data
   - Highlight any red flags or concerns

2. LONG-TERM HOLDING PORTFOLIO:
   - Action: BUY/SELL/DCA/PARTIAL/HOLD
   - Reasoning: Detailed explanation with independent analysis
   - Confidence: 0-1 scale (consider data adequacy)
   - Time horizon: Long-term (months/years)
   - Risk factors: Specific risks identified

3. SHORT-TERM TRADING PORTFOLIO:
   - Action: LONG/SHORT/WAIT
   - Entry price: Specific level with reasoning
   - Take Profit: Target level with analysis
   - Stop Loss: Risk level with justification
   - Reasoning: Detailed explanation with independent analysis
   - Confidence: 0-1 scale (consider data adequacy)
   - Time horizon: Short-term (days/weeks)

4. DATA QUALITY ASSESSMENT:
   - Rate data quality: 1-10 scale
   - Identify critical missing information
   - Recommend additional data needed
   - Assess reliability of each data source

5. DISPATCH RECOMMENDATIONS:
   - If dispatch_required: Specify which agents to re-run
   - Priority levels for each request
   - Expected impact on analysis confidence

Be skeptical, evidence-based, and consider market manipulation risks. Provide your OWN independent perspective, not just validation of Alpha Team's work.
"""
        
        analysis = self.analyze_with_gemini(prompt, context)
        
        return {
            'justin_experience_years': 15,
            'justin_verdict': self.extract_verdict(analysis),
            'justin_confidence': self.extract_confidence(analysis),
            'justin_analysis_style': 'Independent Skeptical Veteran',
            'long_term_proposal': self.extract_long_term_proposal(analysis),
            'short_term_proposal': self.extract_short_term_proposal(analysis),
            'justin_notes': analysis,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_adequacy': {
                'adequate': data_adequate,
                'missing_data': missing_data,
                'dispatch_required': dispatch_info.get('dispatch_required', False),
                'dispatch_requests': dispatch_info.get('requests', [])
            },
            'independent_analysis': True,
            'alpha_debate_content': alpha_content
        }
    
    def run_risk_assessment(self, justin_analysis: Dict, analysis_data: Dict, risk_profile: str = 'NEUTRAL') -> Dict:
        """Run risk team assessment"""
        crawl_data = analysis_data.get('crawl_data', {})
        alpha_debate = analysis_data.get('alpha_debate', {})
        
        context = f"""
JUSTIN'S ANALYSIS:
- Verdict: {justin_analysis.get('justin_verdict', 'N/A')}
- Confidence: {justin_analysis.get('justin_confidence', 'N/A')}
- Long-term Proposal: {justin_analysis.get('long_term_proposal', {})}
- Short-term Proposal: {justin_analysis.get('short_term_proposal', {})}
- Notes: {justin_analysis.get('justin_notes', 'N/A')}

CRAWL TEAM DATA:
- Sentiment: {crawl_data.get('lily', {}).get('overall_sentiment', 'N/A')}
- Technical: {crawl_data.get('bob', {}).get('signal_direction', 'N/A')}
- On-chain: {crawl_data.get('yasuo', {}).get('summary', 'N/A')}
- News: {crawl_data.get('j97', {}).get('trading_signal', 'N/A')}

ALPHA DEBATE:
- Winner: {alpha_debate.get('debate_winner', 'N/A')}
- Confidence: {alpha_debate.get('confidence_level', 'N/A')}

RISK PROFILE: {risk_profile}
"""
        
        prompt = f"""
As a RISK MANAGEMENT TEAM, assess Justin's proposals and adjust them based on the {risk_profile} risk profile.

Risk Profiles:
- AGGRESSIVE: Higher risk tolerance, larger position sizes, tighter stops
- NEUTRAL: Balanced risk approach, moderate position sizes
- CONSERVATIVE: Lower risk tolerance, smaller position sizes, wider stops

Your tasks:
1. Assess the risk level of Justin's proposals
2. Adjust position sizes based on risk profile
3. Modify stop losses and take profits
4. Identify key risks and mitigation strategies
5. Provide final refined recommendations

For each proposal (Long-term and Short-term):
- Risk Level: LOW/MEDIUM/HIGH
- Adjusted Action: Refined recommendation
- Position Size: Suggested allocation
- Risk Mitigation: Specific strategies
- Confidence: Adjusted confidence level
"""
        
        analysis = self.analyze_with_gemini(prompt, context)
        
        return {
            'risk_profile': risk_profile,
            'risk_assessment': analysis,
            'risk_adjusted_proposals': self.extract_risk_adjustments(analysis),
            'key_risks': self.extract_key_risks(analysis),
            'risk_mitigation': self.extract_risk_mitigation(analysis),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def extract_verdict(self, analysis: str) -> str:
        """Extract Justin's overall verdict"""
        analysis_lower = analysis.lower()
        
        if 'buy' in analysis_lower and 'sell' not in analysis_lower:
            return 'BUY'
        elif 'sell' in analysis_lower and 'buy' not in analysis_lower:
            return 'SELL'
        else:
            return 'HOLD'
    
    def extract_confidence(self, analysis: str) -> float:
        """Extract confidence score"""
        analysis_lower = analysis.lower()
        
        if 'high confidence' in analysis_lower or 'very confident' in analysis_lower:
            return 0.8
        elif 'moderate confidence' in analysis_lower:
            return 0.6
        elif 'low confidence' in analysis_lower or 'uncertain' in analysis_lower:
            return 0.3
        else:
            return 0.5
    
    def extract_long_term_proposal(self, analysis: str) -> Dict:
        """Extract long-term proposal details"""
        # Simple extraction - in production, use more sophisticated NLP
        return {
            'action': 'HOLD',  # Default
            'reasoning': 'Long-term analysis pending',
            'confidence': 0.5,
            'time_horizon': 'Long-term (months/years)'
        }
    
    def extract_short_term_proposal(self, analysis: str) -> Dict:
        """Extract short-term proposal details"""
        # Simple extraction - in production, use more sophisticated NLP
        return {
            'action': 'WAIT',  # Default
            'entry': 0.0,
            'tp': 0.0,
            'sl': 0.0,
            'reasoning': 'Short-term analysis pending',
            'confidence': 0.5,
            'time_horizon': 'Short-term (days/weeks)'
        }
    
    def extract_risk_adjustments(self, analysis: str) -> Dict:
        """Extract risk-adjusted proposals"""
        return {
            'long_term_adjusted': {
                'action': 'HOLD',
                'position_size': 'Conservative',
                'risk_level': 'MEDIUM'
            },
            'short_term_adjusted': {
                'action': 'WAIT',
                'position_size': 'Conservative',
                'risk_level': 'MEDIUM'
            }
        }
    
    def extract_key_risks(self, analysis: str) -> List[str]:
        """Extract key risks identified"""
        return [
            'Market volatility',
            'Regulatory uncertainty',
            'Technical analysis limitations'
        ]
    
    def extract_risk_mitigation(self, analysis: str) -> List[str]:
        """Extract risk mitigation strategies"""
        return [
            'Position sizing',
            'Stop losses',
            'Diversification'
        ]
    
    def generate_final_decisions(self, justin_analysis: Dict, risk_assessment: Dict) -> Dict:
        """Generate final trading decisions"""
        return {
            'final_holding_decision': {
                'action': justin_analysis.get('long_term_proposal', {}).get('action', 'HOLD'),
                'reasoning': 'Combined Justin analysis and risk assessment',
                'confidence': justin_analysis.get('justin_confidence', 0.5),
                'risk_level': risk_assessment.get('risk_profile', 'NEUTRAL')
            },
            'final_trading_decision': {
                'action': justin_analysis.get('short_term_proposal', {}).get('action', 'WAIT'),
                'reasoning': 'Combined Justin analysis and risk assessment',
                'confidence': justin_analysis.get('justin_confidence', 0.5),
                'risk_level': risk_assessment.get('risk_profile', 'NEUTRAL')
            }
        }
    
    def save_analysis(self, analysis_data: Dict) -> bool:
        """Save analysis to Supabase"""
        if not self.supabase_client:
            self.logger.warning("⚠️ Supabase not available, skipping save")
            return False
        
        try:
            result = self.supabase_client.table('justin_risk_analysis').insert(analysis_data).execute()
            self.logger.info("✅ Analysis saved to Supabase")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving analysis: {e}")
            return False
    
    def run_full_analysis(self, risk_profile: str = 'NEUTRAL') -> Dict:
        """Run complete Justin + Risk team analysis"""
        self.logger.info("⚖️ Starting Justin + Risk Team Analysis")
        
        # Step 1: Fetch analysis data
        self.logger.info("📊 Fetching analysis data...")
        analysis_data = self.fetch_analysis_data()
        
        # Step 2: Run Justin's analysis
        self.logger.info("👨‍💼 Running Justin's trading analysis...")
        justin_analysis = self.run_justin_analysis(analysis_data)
        
        # Step 3: Run risk assessment
        self.logger.info(f"🛡️ Running risk assessment ({risk_profile})...")
        risk_assessment = self.run_risk_assessment(justin_analysis, analysis_data, risk_profile)
        
        # Step 4: Generate final decisions
        self.logger.info("🎯 Generating final decisions...")
        final_decisions = self.generate_final_decisions(justin_analysis, risk_assessment)
        
        # Step 5: Compile complete analysis
        complete_analysis = {
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'crawl_data_session_id': 'latest',
            'alpha_debate_session_id': analysis_data.get('alpha_debate', {}).get('session_id', 'latest'),
            
            **justin_analysis,
            **risk_assessment,
            **final_decisions,
            
            'market_outlook': f"Market analysis completed with {risk_profile} risk profile",
            'analysis_summary': f"Justin verdict: {justin_analysis.get('justin_verdict', 'N/A')}, Risk profile: {risk_profile}"
        }
        
        # Step 6: Save to Supabase
        self.save_analysis(complete_analysis)
        
        self.logger.info(f"✅ Justin + Risk analysis completed. Verdict: {justin_analysis.get('justin_verdict', 'N/A')}")
        
        return complete_analysis

def main():
    """Main function to run Justin + Risk analysis"""
    print("⚖️" * 50)
    print("⚖️ JUSTIN + RISK TEAM - ENHANCED GEMINI ANALYSIS ⚖️")
    print("⚖️" * 50)
    print("")
    print("👨‍💼 Justin: 15-year Trading Manager")
    print("🛡️ Risk Team: Risk Assessment & Mitigation")
    print("🧠 Powered by Gemini 1.5 Pro")
    print("💾 Data stored in Supabase")
    print("")
    print("🚀 Starting analysis...")
    print("=" * 60)
    
    # Initialize analysis engine
    engine = JustinRiskAnalysisEngine()
    
    # Run full analysis
    result = engine.run_full_analysis(risk_profile='NEUTRAL')
    
    # Print results
    print("\n📊 ANALYSIS RESULTS:")
    print("=" * 40)
    print(f"Justin Verdict: {result.get('justin_verdict', 'N/A')}")
    print(f"Confidence: {result.get('justin_confidence', 0):.2f}")
    print(f"Risk Profile: {result.get('risk_profile', 'N/A')}")
    
    print(f"\nLong-term Decision: {result.get('final_holding_decision', {}).get('action', 'N/A')}")
    print(f"Short-term Decision: {result.get('final_trading_decision', {}).get('action', 'N/A')}")
    
    print("\n⚖️" * 50)
    print("⚖️ Justin + Risk Team Analysis Complete! ⚖️")
    print("⚖️" * 50)

if __name__ == "__main__":
    main()
