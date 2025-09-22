#!/usr/bin/env python3
"""
Justin Ly - Skeptical Market Veteran with Gemini LLM
Enhanced with detailed analysis and specific trade recommendations
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gemini_config import get_gemini_llm, PERSONAS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JustinGemini:
    def __init__(self):
        try:
            self.gemini = get_gemini_llm()
            self.gemini_available = True
        except Exception as e:
            # Fail fast: no mock usage allowed
            logger.error(f"Gemini not available: {e}")
            raise
            
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def load_alpha_debate(self) -> Dict[str, Any]:
        """Load latest Alpha team debate"""
        alpha_dir = os.path.join(self.base_dir, 'AlphaTeam')
        alpha_files = [f for f in os.listdir(alpha_dir) if f.startswith('alpha_debate_gemini_') and f.endswith('.json')]
        
        if not alpha_files:
            # Fallback to regular alpha debate
            alpha_files = [f for f in os.listdir(alpha_dir) if f.startswith('alpha_debate_') and f.endswith('.json')]
        
        if alpha_files:
            latest_file = sorted(alpha_files)[-1]
            with open(os.path.join(alpha_dir, latest_file), 'r') as f:
                return json.load(f)
        
        return {}
    
    def analyze_manipulation_risk(self, data: Dict[str, Any]) -> str:
        """Analyze potential market manipulation using Gemini"""
        if self.gemini_available and self.gemini:
            try:
                task = """
As a 15+ year market veteran, analyze the provided data for potential market manipulation.
Focus on:
1. News sentiment vs actual fundamentals
2. Social media sentiment patterns
3. Onchain data anomalies
4. Technical analysis reliability
5. ETF flow patterns

Provide specific manipulation indicators and risk assessment.
"""
                
                return self.gemini.analyze_with_persona(
                    PERSONAS["justin_skeptical"],
                    data,
                    task
                )
            except Exception as e:
                # Fail fast
                logger.error(f"Gemini manipulation analysis failed: {e}")
                raise
    
    def assess_eth_fundamental_value(self, data: Dict[str, Any]) -> str:
        """Assess ETH's fundamental value using Gemini"""
        if self.gemini_available and self.gemini:
            try:
                task = """
As a market veteran who understands ETH's true value, assess the fundamental value proposition.
Consider:
1. Technical utility and adoption
2. Network effects and ecosystem growth
3. Regulatory environment
4. Competitive landscape
5. Long-term sustainability

Provide a balanced assessment of ETH's intrinsic value vs current market price.
"""
                
                return self.gemini.analyze_with_persona(
                    PERSONAS["justin_skeptical"],
                    data,
                    task
                )
            except Exception as e:
                logger.error(f"Gemini fundamental assessment failed: {e}")
                raise
    
    def generate_portfolio_recommendation(self, data: Dict[str, Any]) -> str:
        """Generate long-term portfolio recommendation using Gemini"""
        if self.gemini_available and self.gemini:
            try:
                task = """
Based on your analysis, provide a detailed portfolio recommendation including:
1. Long-term portfolio decision (BUY/SELL/HOLD/DCA)
2. Position sizing rationale
3. Time horizon considerations
4. Risk management approach
5. Specific allocation percentages

Be specific and actionable with your recommendations.
"""
                
                return self.gemini.analyze_with_persona(
                    PERSONAS["justin_skeptical"],
                    data,
                    task
                )
            except Exception as e:
                logger.error(f"Gemini portfolio recommendation failed: {e}")
                raise
    
    def generate_trade_ideas(self, data: Dict[str, Any]) -> str:
        """Generate specific trade ideas using Gemini"""
        if self.gemini_available and self.gemini:
            try:
                task = """
Based on your analysis, provide specific short-term trade ideas including:
1. Entry strategies (scaled entry, single entry, etc.)
2. Specific entry price levels
3. Stop-loss levels with rationale
4. Take-profit targets with rationale
5. Risk-reward ratios
6. Position sizing for each trade
7. Time frames for each trade

Provide concrete, actionable trade setups.
"""
                
                return self.gemini.analyze_with_persona(
                    PERSONAS["justin_skeptical"],
                    data,
                    task
                )
            except Exception as e:
                logger.error(f"Gemini trade ideas failed: {e}")
                raise
    
    def make_final_judgment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make comprehensive final judgment using Gemini"""
        logger.info("🔍 Justin analyzing with 15+ years of skeptical experience...")
        
        # Load debate data
        debate_data = self.load_alpha_debate()
        if not debate_data:
            logger.warning("No Alpha debate data found, using provided data")
            debate_data = data
        
        # Combine all data for analysis
        full_data = {
            'alpha_debate': debate_data,
            'crawl_data': debate_data.get('full_crawl_data', {}),
            'bullish_thesis': debate_data.get('bullish', {}),
            'bearish_thesis': debate_data.get('bearish', {})
        }
        
        # Perform comprehensive analysis
        manipulation_analysis = self.analyze_manipulation_risk(full_data)
        fundamental_assessment = self.assess_eth_fundamental_value(full_data)
        portfolio_recommendation = self.generate_portfolio_recommendation(full_data)
        trade_ideas = self.generate_trade_ideas(full_data)
        
        # Generate overall verdict
        if self.gemini_available and self.gemini:
            try:
                verdict_task = """
Based on all your analysis, provide a final verdict with:
1. Overall market assessment (BULLISH/BEARISH/NEUTRAL)
2. Confidence level (0-1)
3. Key reasoning
4. Main risks and opportunities
5. Final recommendation summary
"""
                
                final_verdict = self.gemini.analyze_with_persona(
                    PERSONAS["justin_skeptical"],
                    full_data,
                    verdict_task
                )
            except Exception as e:
                logger.error(f"Gemini final verdict failed: {e}")
                raise
        
        # Compile comprehensive result
        result = {
            'timestamp': datetime.now().isoformat(),
            'justin_analysis': {
                'manipulation_risk_analysis': manipulation_analysis,
                'fundamental_value_assessment': fundamental_assessment,
                'portfolio_recommendation': portfolio_recommendation,
                'trade_ideas': trade_ideas,
                'final_verdict': final_verdict
            },
            'data_sources': {
                'alpha_debate_available': bool(debate_data),
                'crawl_data_sources': len([k for k, v in full_data.get('crawl_data', {}).items() if v])
            }
        }
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"justin_verdict_gemini_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"✅ Justin's verdict saved to {filename}")
        return result
    
    def _generate_mock_manipulation_analysis(self, data: Dict[str, Any]) -> str:
        """Generate mock manipulation analysis"""
        alpha_data = data.get('alpha_debate', {})
        crawl_data = data.get('crawl_data', {})
        
        return f"""
MANIPULATION RISK ANALYSIS (Mock - Justin's Perspective):

After 15+ years in this market, I've seen every trick in the book. Here's my assessment:

NEWS SENTIMENT ANALYSIS:
- Articles processed: {crawl_data.get('j97', {}).get('articles_processed', 'N/A')}
- High impact articles: {crawl_data.get('j97', {}).get('high_impact_articles', 'N/A')}
- Risk Level: MEDIUM - High volume of positive news could indicate coordinated narrative

SOCIAL MEDIA PATTERNS:
- Total posts: {crawl_data.get('lily', {}).get('total_posts', 'N/A')}
- Average sentiment: {crawl_data.get('lily', {}).get('avg_sentiment', 'N/A')}
- Risk Level: HIGH - Extremely bullish sentiment across all platforms suggests potential manipulation

ONCHAIN ANOMALIES:
- ETF flows: ${crawl_data.get('yasuo', {}).get('etf_flows', {}).get('daily_flow', 0):,.0f}
- Exchange flows: {crawl_data.get('yasuo', {}).get('exchange_flows', {}).get('net_flow', 'N/A')} ETH
- Risk Level: MEDIUM - Mixed signals require careful monitoring

TECHNICAL RELIABILITY:
- Current signal: {crawl_data.get('bob', {}).get('trading_signal', 'N/A')}
- Risk Level: LOW - Technical analysis appears reliable

OVERALL MANIPULATION RISK: MEDIUM-HIGH
- Coordinated positive narrative across multiple channels
- Social sentiment appears artificially inflated
- Recommend caution and position sizing accordingly
"""
    
    def _generate_mock_fundamental_assessment(self, data: Dict[str, Any]) -> str:
        """Generate mock fundamental assessment"""
        return """
ETH FUNDAMENTAL VALUE ASSESSMENT (Mock - Justin's Perspective):

As someone who's been in this market for 15+ years, I understand ETH's true value:

TECHNICAL UTILITY:
- Strong network effects and developer adoption
- Robust DeFi ecosystem with real-world applications
- Scalability improvements through Layer 2 solutions

NETWORK EFFECTS:
- Largest smart contract platform by TVL
- Strong developer community and ecosystem
- Institutional adoption increasing

REGULATORY ENVIRONMENT:
- Clearer regulatory framework emerging
- ETF approvals show institutional acceptance
- Long-term regulatory clarity positive

COMPETITIVE LANDSCAPE:
- First-mover advantage in smart contracts
- Strong network effects create moat
- Continuous innovation and upgrades

LONG-TERM SUSTAINABILITY:
- Strong fundamentals support long-term value
- Real utility beyond speculation
- Network effects create sustainable competitive advantage

CONCLUSION: ETH has strong fundamental value with real utility and network effects. Current price may be influenced by speculation, but underlying value proposition remains solid.
"""
    
    def _generate_mock_portfolio_recommendation(self, data: Dict[str, Any]) -> str:
        """Generate mock portfolio recommendation"""
        return """
PORTFOLIO RECOMMENDATION (Mock - Justin's Perspective):

Based on my 15+ years of market experience:

LONG-TERM PORTFOLIO DECISION: HOLD with DCA
- ETH has strong fundamental value
- Current market conditions suggest caution
- Dollar-cost averaging recommended for long-term positions

POSITION SIZING:
- Core position: 5-10% of portfolio
- DCA allocation: 2-3% monthly
- Risk management: Never more than 15% total exposure

TIME HORIZON CONSIDERATIONS:
- Long-term (6+ months): Bullish on fundamentals
- Medium-term (1-6 months): Neutral with volatility
- Short-term (1-4 weeks): Cautious due to manipulation risks

RISK MANAGEMENT APPROACH:
- Diversification across crypto and traditional assets
- Regular rebalancing based on market conditions
- Stop-losses for short-term positions only

SPECIFIC ALLOCATION:
- 60% in core ETH position (long-term hold)
- 25% in DCA strategy (monthly purchases)
- 15% in trading capital (short-term opportunities)
"""
    
    def _generate_mock_trade_ideas(self, data: Dict[str, Any]) -> str:
        """Generate mock trade ideas"""
        return """
SPECIFIC TRADE IDEAS (Mock - Justin's Perspective):

Based on current market analysis:

ENTRY STRATEGIES:
1. SCALED ENTRY (Recommended):
   - Entry 1: Current price - 2% (25% of position)
   - Entry 2: Current price - 5% (35% of position)
   - Entry 3: Current price - 8% (40% of position)

2. SINGLE ENTRY (Conservative):
   - Entry: Current price - 3%
   - Position size: 50% of allocated capital

STOP-LOSS LEVELS:
- Conservative: -8% from entry
- Moderate: -12% from entry
- Aggressive: -15% from entry

TAKE-PROFIT TARGETS:
- Target 1: +6% (25% of position)
- Target 2: +12% (35% of position)
- Target 3: +20% (40% of position)

RISK-REWARD RATIOS:
- Minimum R:R: 1:1.5
- Target R:R: 1:2
- Maximum R:R: 1:3

POSITION SIZING:
- Conservative: 2-3% of portfolio per trade
- Moderate: 3-5% of portfolio per trade
- Aggressive: 5-8% of portfolio per trade

TIME FRAMES:
- Short-term trades: 1-2 weeks
- Medium-term trades: 2-4 weeks
- Long-term positions: 3+ months

MONITORING REQUIREMENTS:
- Daily price action review
- Weekly fundamental updates
- Monthly position rebalancing
"""
    
    def _generate_mock_final_verdict(self, data: Dict[str, Any]) -> str:
        """Generate mock final verdict"""
        return """
FINAL VERDICT (Mock - Justin's Perspective):

After comprehensive analysis with 15+ years of market experience:

OVERALL MARKET ASSESSMENT: NEUTRAL-BULLISH
- Mixed signals across all data sources
- Strong fundamentals but elevated manipulation risks
- Cautious optimism with risk management focus

CONFIDENCE LEVEL: 0.65
- High confidence in fundamental value assessment
- Medium confidence in short-term price direction
- Low confidence in manipulation risk timing

KEY REASONING:
1. ETH has strong fundamental value and utility
2. Current sentiment appears potentially manipulated
3. Technical analysis shows mixed signals
4. Onchain metrics suggest cautious optimism

MAIN RISKS:
- Social sentiment manipulation
- Coordinated positive narrative
- Technical breakdown potential
- Regulatory uncertainty

MAIN OPPORTUNITIES:
- Strong fundamental value proposition
- Network effects and adoption
- Long-term utility growth
- Institutional acceptance

FINAL RECOMMENDATION SUMMARY:
- Long-term: HOLD with DCA strategy
- Short-term: Cautious trading with strict risk management
- Position sizing: Conservative approach recommended
- Monitoring: Daily review of manipulation indicators

Remember: In this market, patience and risk management are more valuable than perfect timing.
"""

def main():
    """Main execution function"""
    try:
        justin = JustinGemini()
        result = justin.make_final_judgment({})
        
        print("\n" + "="*60)
        print("🏛️ JUSTIN LY - SKEPTICAL MARKET VETERAN")
        print("="*60)
        print("🔍 Analysis completed with 15+ years of experience")
        print(f"📊 Data sources analyzed: {result['data_sources']['crawl_data_sources']}")
        print("✅ Comprehensive verdict saved successfully!")
        
    except Exception as e:
        logger.error(f"Justin analysis failed: {e}")
        return None

if __name__ == "__main__":
    main()
