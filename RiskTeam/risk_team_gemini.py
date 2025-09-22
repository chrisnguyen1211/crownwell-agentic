#!/usr/bin/env python3
"""
Risk Team with Gemini LLM Integration
Enhanced with detailed risk assessment and specific trade actions
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

class RiskTeamGemini:
    def __init__(self, mode: str = "neutral"):
        try:
            self.gemini = get_gemini_llm()
            self.gemini_available = True
        except Exception as e:
            # Fail fast: no mock usage allowed
            logger.error(f"Gemini not available: {e}")
            raise
            
        self.mode = mode.lower()  # aggressive, neutral, conservative
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def load_justin_analysis(self) -> Dict[str, Any]:
        """Load latest Justin analysis"""
        justin_dir = os.path.join(self.base_dir, 'Justin')
        justin_files = [f for f in os.listdir(justin_dir) if f.startswith('justin_verdict_gemini_') and f.endswith('.json')]
        
        if not justin_files:
            # Fallback to regular justin verdict
            justin_files = [f for f in os.listdir(justin_dir) if f.startswith('justin_verdict_') and f.endswith('.json')]
        
        if justin_files:
            latest_file = sorted(justin_files)[-1]
            with open(os.path.join(justin_dir, latest_file), 'r') as f:
                return json.load(f)
        
        return {}
    
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
    
    def assess_risk_levels(self, data: Dict[str, Any]) -> str:
        """Assess risk across short, medium, and long-term horizons using Gemini"""
        if self.gemini_available and self.gemini:
            try:
                task = f"""
As a senior risk manager in {self.mode} mode, assess ETH risk across all time horizons.

Evaluate:
1. Short-term risk (1-7 days)
2. Medium-term risk (1-4 weeks) 
3. Long-term risk (1-6 months)

Consider:
- Market volatility and liquidity
- Technical support/resistance levels
- Fundamental developments
- Regulatory risks
- Macroeconomic factors
- Onchain metrics and whale activity

Provide specific risk levels (LOW/MEDIUM/HIGH) with detailed reasoning for each horizon.
"""
                
                return self.gemini.analyze_with_persona(
                    PERSONAS["risk_manager"],
                    data,
                    task
                )
            except Exception as e:
                logger.error(f"Gemini risk assessment failed: {e}")
                raise
    
    def adjust_justin_proposal(self, justin_data: Dict[str, Any], risk_assessment: str) -> str:
        """Adjust Justin's proposal based on risk assessment using Gemini"""
        if self.gemini_available and self.gemini:
            try:
                task = f"""
As a risk manager in {self.mode} mode, review Justin's proposal and adjust it based on risk assessment.

Justin's Analysis:
{justin_data.get('justin_analysis', {})}

Risk Assessment:
{risk_assessment}

Provide:
1. Adjusted portfolio recommendation
2. Risk-adjusted position sizing
3. Modified trade ideas with updated risk parameters
4. Specific risk management measures
5. Whether re-dispatch is needed for more data

Be specific about adjustments and reasoning.
"""
                
                return self.gemini.analyze_with_persona(
                    PERSONAS["risk_manager"],
                    justin_data,
                    task
                )
            except Exception as e:
                logger.error(f"Gemini adjust proposal failed: {e}")
                raise
    
    def generate_final_actions(self, adjusted_proposal: str, risk_assessment: str) -> str:
        """Generate final concrete actions using Gemini"""
        if self.gemini_available and self.gemini:
            try:
                task = f"""
Based on the risk-adjusted proposal, provide specific final actions:

Adjusted Proposal:
{adjusted_proposal}

Risk Assessment:
{risk_assessment}

Provide concrete actions for:
1. Portfolio Management:
   - Long-term holding decisions
   - Position sizing percentages
   - DCA strategies if applicable

2. Trading Actions:
   - Specific entry prices
   - Stop-loss levels
   - Take-profit targets
   - Risk allocation per trade
   - Time frames for each action

3. Risk Management:
   - Maximum portfolio exposure
   - Risk per trade limits
   - Monitoring requirements
   - Exit strategies

Be extremely specific with numbers, percentages, and time frames.
"""
                
                return self.gemini.analyze_with_persona(
                    PERSONAS["risk_manager"],
                    {'adjusted_proposal': adjusted_proposal, 'risk_assessment': risk_assessment},
                    task
                )
            except Exception as e:
                logger.error(f"Gemini final actions failed: {e}")
                raise
    
    def determine_redispatch_need(self, data: Dict[str, Any]) -> str:
        """Determine if re-dispatch is needed using Gemini"""
        if self.gemini_available and self.gemini:
            try:
                task = f"""
As a risk manager, determine if we need to re-dispatch the Crawl agents for more data.

Consider:
- Data quality and completeness
- Risk assessment confidence level
- Market conditions and volatility
- Time sensitivity of decisions
- Cost vs benefit of additional data

Provide a clear recommendation: REDISPATCH or NO_REDISPATCH with detailed reasoning.
"""
                
                return self.gemini.analyze_with_persona(
                    PERSONAS["risk_manager"],
                    data,
                    task
                )
            except Exception as e:
                logger.error(f"Gemini redispatch decision failed: {e}")
                raise
    
    def run_risk_assessment(self) -> Dict[str, Any]:
        """Run complete risk assessment using Gemini"""
        logger.info(f"🛡️ Risk Team starting assessment in {self.mode} mode...")
        
        # Load data
        justin_data = self.load_justin_analysis()
        alpha_data = self.load_alpha_debate()
        
        if not justin_data and not alpha_data:
            logger.error("No data available for risk assessment")
            return {}
        
        # Combine all data
        full_data = {
            'justin_analysis': justin_data,
            'alpha_debate': alpha_data,
            'risk_mode': self.mode
        }
        
        # Perform risk assessment
        logger.info("📊 Assessing risk levels...")
        risk_assessment = self.assess_risk_levels(full_data)
        
        # Adjust Justin's proposal
        logger.info("🔄 Adjusting proposal based on risk...")
        adjusted_proposal = self.adjust_justin_proposal(justin_data, risk_assessment)
        
        # Generate final actions
        logger.info("🎯 Generating final actions...")
        final_actions = self.generate_final_actions(adjusted_proposal, risk_assessment)
        
        # Determine re-dispatch need
        logger.info("🔍 Evaluating re-dispatch need...")
        redispatch_decision = self.determine_redispatch_need(full_data)
        
        # Compile results
        result = {
            'timestamp': datetime.now().isoformat(),
            'risk_mode': self.mode,
            'risk_assessment': {
                'detailed_analysis': risk_assessment,
                'adjusted_proposal': adjusted_proposal,
                'final_actions': final_actions,
                'redispatch_decision': redispatch_decision
            },
            'data_sources': {
                'justin_analysis_available': bool(justin_data),
                'alpha_debate_available': bool(alpha_data)
            }
        }
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"risk_assessment_gemini_{self.mode}_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"✅ Risk assessment saved to {filename}")
        return result
    
    def _generate_mock_risk_assessment(self, data: Dict[str, Any]) -> str:
        """Generate mock risk assessment"""
        return f"""
RISK ASSESSMENT (Mock - Risk Manager {self.mode.upper()} Mode):

SHORT-TERM RISK (1-7 days): MEDIUM
- High volatility expected due to market conditions
- Technical levels showing mixed signals
- Social sentiment manipulation risks elevated
- Recommendation: Cautious position sizing

MEDIUM-TERM RISK (1-4 weeks): MEDIUM-HIGH
- Regulatory uncertainty remains elevated
- Market structure concerns persist
- Onchain metrics showing mixed signals
- Recommendation: Conservative approach recommended

LONG-TERM RISK (1-6 months): LOW-MEDIUM
- Strong fundamental value proposition
- Network effects and adoption trends positive
- Institutional acceptance increasing
- Recommendation: Long-term positions acceptable with proper risk management

OVERALL RISK LEVEL: MEDIUM
- Balanced risk profile across time horizons
- Requires active monitoring and position management
- Risk-adjusted approach essential for success
"""
    
    def _generate_mock_adjusted_proposal(self, justin_data: Dict[str, Any], risk_assessment: str) -> str:
        """Generate mock adjusted proposal"""
        return f"""
RISK-ADJUSTED PROPOSAL (Mock - {self.mode.upper()} Mode):

ADJUSTED PORTFOLIO RECOMMENDATION:
- Core position: 3-5% (reduced from Justin's 5-10%)
- DCA allocation: 1-2% monthly (reduced from 2-3%)
- Trading capital: 2-3% (reduced from 5-8%)
- Maximum total exposure: 10% (reduced from 15%)

RISK-ADJUSTED POSITION SIZING:
- Conservative approach due to elevated risks
- Smaller position sizes to manage volatility
- Increased diversification requirements
- Regular rebalancing mandatory

MODIFIED TRADE IDEAS:
- Entry levels: More conservative (current price - 5% minimum)
- Stop-losses: Tighter (6-8% instead of 8-15%)
- Take-profits: Lower targets (8-12% instead of 12-20%)
- Risk per trade: Maximum 1-2% of portfolio

SPECIFIC RISK MANAGEMENT MEASURES:
- Daily monitoring of manipulation indicators
- Weekly risk assessment reviews
- Monthly position rebalancing
- Quarterly strategy review

RE-DISPATCH DECISION: NO_REDISPATCH
- Current data sufficient for risk assessment
- Additional data would not significantly improve analysis
- Cost-benefit analysis favors proceeding with current data
"""
    
    def _generate_mock_final_actions(self, adjusted_proposal: str, risk_assessment: str) -> str:
        """Generate mock final actions"""
        return f"""
FINAL ACTIONS (Mock - {self.mode.upper()} Mode):

PORTFOLIO MANAGEMENT:
1. Long-term Holdings:
   - ETH Core Position: 3-5% of total portfolio
   - DCA Strategy: $100-200 monthly (1-2% of portfolio)
   - Rebalancing: Monthly review and adjustment

2. Position Sizing:
   - Maximum single position: 2% of portfolio
   - Maximum total crypto exposure: 10% of portfolio
   - Cash allocation: 20-30% for opportunities

TRADING ACTIONS:
1. Entry Strategy:
   - Entry 1: Current price - 5% (1% of portfolio)
   - Entry 2: Current price - 8% (1% of portfolio)
   - Entry 3: Current price - 12% (1% of portfolio)

2. Risk Management:
   - Stop-loss: 6-8% from entry
   - Take-profit 1: +8% (50% of position)
   - Take-profit 2: +15% (50% of position)
   - Maximum risk per trade: 1-2% of portfolio

3. Time Frames:
   - Short-term trades: 1-2 weeks
   - Medium-term positions: 2-4 weeks
   - Long-term holds: 3+ months

MONITORING REQUIREMENTS:
- Daily: Price action and manipulation indicators
- Weekly: Risk assessment and position review
- Monthly: Portfolio rebalancing and strategy review
- Quarterly: Full strategy assessment and adjustment

EXIT STRATEGIES:
- Technical breakdown: Immediate exit
- Fundamental deterioration: Gradual reduction
- Risk threshold breach: Automatic position closure
- Time-based: Regular position rotation
"""
    
    def _generate_mock_redispatch_decision(self, data: Dict[str, Any]) -> str:
        """Generate mock re-dispatch decision"""
        # Check data quality to determine if re-dispatch is needed
        justin_data = data.get('justin_analysis', {})
        alpha_data = data.get('alpha_debate', {})
        
        # Check if we have sufficient data
        has_bob = bool(alpha_data.get('crawl_data_summary', {}).get('bob', False))
        has_lily = bool(alpha_data.get('crawl_data_summary', {}).get('lily', False))
        has_j97 = bool(alpha_data.get('crawl_data_summary', {}).get('j97', False))
        has_yasuo = bool(alpha_data.get('crawl_data_summary', {}).get('yasuo', False))
        
        completed_agents = sum([has_bob, has_lily, has_j97, has_yasuo])
        
        # Determine if re-dispatch is needed
        if completed_agents < 3:  # Less than 3 agents completed
            recommendation = "REDISPATCH"
            reasoning = f"Only {completed_agents}/4 agents completed successfully. Need more data for comprehensive risk assessment."
            agents_needed = []
            if not has_bob:
                agents_needed.append("BOB (technical analysis)")
            if not has_lily:
                agents_needed.append("LILY (sentiment analysis)")
            if not has_j97:
                agents_needed.append("J97 (news analysis)")
            if not has_yasuo:
                agents_needed.append("YASUO (onchain analysis)")
        else:
            recommendation = "NO_REDISPATCH"
            reasoning = "Sufficient data available for risk assessment"
            agents_needed = []
        
        return f"""
RE-DISPATCH DECISION (Mock - {self.mode.upper()} Mode):

RECOMMENDATION: {recommendation}

REASONING:
{reasoning}

CURRENT DATA STATUS:
- Crawl agents: {completed_agents}/4 completed successfully
- Bob: {'✅' if has_bob else '❌'}
- Lily: {'✅' if has_lily else '❌'}
- J97: {'✅' if has_j97 else '❌'}
- Yasuo: {'✅' if has_yasuo else '❌'}
- Alpha debate: Completed with comprehensive analysis
- Justin analysis: Completed with detailed assessment

AGENTS NEEDED FOR RE-DISPATCH:
{chr(10).join(f"- {agent}" for agent in agents_needed) if agents_needed else "- None"}

CONCLUSION:
{recommendation} - {reasoning}
"""

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Risk Team Gemini Assessment')
    parser.add_argument('--mode', choices=['aggressive', 'neutral', 'conservative'], 
                       default='neutral', help='Risk assessment mode')
    
    args = parser.parse_args()
    
    try:
        risk_team = RiskTeamGemini(mode=args.mode)
        result = risk_team.run_risk_assessment()
        
        print("\n" + "="*60)
        print(f"🛡️ RISK TEAM GEMINI ASSESSMENT ({args.mode.upper()})")
        print("="*60)
        print(f"📊 Justin analysis: {'✅' if result['data_sources']['justin_analysis_available'] else '❌'}")
        print(f"📊 Alpha debate: {'✅' if result['data_sources']['alpha_debate_available'] else '❌'}")
        print("✅ Risk assessment completed successfully!")
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        return None

if __name__ == "__main__":
    main()
