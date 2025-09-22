#!/usr/bin/env python3
"""
Justin Ly - Skeptical Market Veteran Judge
A seasoned trader with 15+ years of experience who approaches all data with healthy skepticism.
Understands market manipulation tactics and the true value proposition of ETH.
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load shared env from J97
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'J97', 'api_keys.env'))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('justin_judge')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
client = create_client(SUPABASE_URL, SUPABASE_KEY)

class JustinSkepticalJudge:
    """
    Justin Ly - A veteran trader with 15+ years of experience
    Known for his skeptical approach to market data and manipulation detection
    """
    
    def __init__(self):
        self.name = "Justin Ly"
        self.experience_years = 15
        self.specialty = "Market Manipulation Detection & ETH Value Analysis"
        self.risk_tolerance = "Neutral - Neither fearful nor greedy"
        self.analysis_style = "Deep, methodical, and skeptical"
        
        logger.info(f"🏛️ {self.name} - {self.experience_years}+ year market veteran initialized")
        logger.info(f"🎯 Specialty: {self.specialty}")
        logger.info(f"⚖️ Risk Profile: {self.risk_tolerance}")
    
    def read_latest_alpha_json(self):
        """Read the latest Alpha team debate file"""
        alpha_dir = os.path.join(os.path.dirname(__file__), '..', 'AlphaTeam')
        files = sorted([f for f in os.listdir(alpha_dir) if f.startswith('alpha_debate_') and f.endswith('.json')])
        if not files:
            return None
        path = os.path.join(alpha_dir, files[-1])
        with open(path, 'r') as f:
            return json.load(f)
    
    def analyze_news_manipulation_risk(self, news_data):
        """
        Analyze news data for potential manipulation signals
        Justin is highly skeptical of positive news and looks for manipulation patterns
        """
        if not isinstance(news_data, dict):
            return {"risk_level": "unknown", "manipulation_signals": [], "analysis": "No news data available"}
        
        manipulation_signals = []
        risk_factors = []
        
        # Check for suspicious patterns
        sentiment = news_data.get('sentiment', '')
        confidence = news_data.get('confidence', 0)
        total_articles = news_data.get('articles_processed', 0)
        high_impact = news_data.get('high_impact_articles', 0)
        
        # High bullish sentiment with low confidence = potential manipulation
        if sentiment.lower() == 'bullish' and confidence < 0.6:
            manipulation_signals.append("High bullish sentiment with low confidence - potential pump")
            risk_factors.append("confidence_disconnect")
        
        # Too many high-impact articles = coordinated effort
        if high_impact > total_articles * 0.7:
            manipulation_signals.append("Excessive high-impact articles - possible coordinated narrative")
            risk_factors.append("narrative_coordination")
        
        # Check category distribution for manipulation patterns
        categories = news_data.get('categories', {})
        if categories:
            market_news = categories.get('market', 0)
            general_news = categories.get('general', 0)
            total_categorized = sum(categories.values())
            
            # Too much market-focused news = potential manipulation
            if market_news > total_categorized * 0.6:
                manipulation_signals.append("Excessive market-focused news - possible price manipulation")
                risk_factors.append("market_focus_bias")
        
        # Determine overall risk level
        if len(manipulation_signals) >= 3:
            risk_level = "HIGH"
        elif len(manipulation_signals) >= 2:
            risk_level = "MEDIUM"
        elif len(manipulation_signals) >= 1:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        return {
            "risk_level": risk_level,
            "manipulation_signals": manipulation_signals,
            "risk_factors": risk_factors,
            "analysis": f"News data shows {risk_level.lower()} manipulation risk with {len(manipulation_signals)} warning signals"
        }
    
    def analyze_social_sentiment_reliability(self, social_data):
        """
        Analyze social sentiment for bot activity and manipulation
        Justin knows social media is easily manipulated
        """
        if not isinstance(social_data, dict):
            return {"reliability": "unknown", "bot_risk": "unknown", "analysis": "No social data available"}
        
        bot_indicators = []
        reliability_factors = []
        
        total_posts = social_data.get('total_posts', 0)
        avg_sentiment = social_data.get('avg_sentiment', 0)
        platform_breakdown = social_data.get('platform_breakdown', {})
        
        # Check for bot-like patterns
        if total_posts > 0:
            # Extremely high sentiment scores = potential bot activity
            if avg_sentiment > 0.8:
                bot_indicators.append("Extremely high sentiment - possible bot amplification")
                reliability_factors.append("sentiment_inflation")
            
            # Check platform distribution for manipulation
            if platform_breakdown:
                twitter_count = platform_breakdown.get('twitter', {}).get('count', 0)
                reddit_count = platform_breakdown.get('reddit', {}).get('count', 0)
                
                # Suspicious platform distribution
                if twitter_count > reddit_count * 3:
                    bot_indicators.append("Twitter dominance - potential bot farm activity")
                    reliability_factors.append("platform_bias")
        
        # Determine reliability
        if len(bot_indicators) >= 2:
            reliability = "LOW"
        elif len(bot_indicators) >= 1:
            reliability = "MEDIUM"
        else:
            reliability = "HIGH"
        
        return {
            "reliability": reliability,
            "bot_indicators": bot_indicators,
            "reliability_factors": reliability_factors,
            "analysis": f"Social sentiment shows {reliability.lower()} reliability with {len(bot_indicators)} bot indicators"
        }
    
    def analyze_onchain_data_authenticity(self, onchain_data):
        """
        Analyze onchain data for authentic vs manipulated flows
        Justin understands that onchain data can also be manipulated
        """
        if not isinstance(onchain_data, dict):
            return {"authenticity": "unknown", "manipulation_risk": "unknown", "analysis": "No onchain data available"}
        
        manipulation_indicators = []
        authenticity_factors = []
        
        net_flow = onchain_data.get('net_flow', 0)
        exchanges = onchain_data.get('exchanges', {})
        
        # Check for suspicious flow patterns
        if abs(net_flow) > 1000000:  # Very large flows
            if net_flow > 0:
                manipulation_indicators.append("Massive accumulation - possible whale manipulation")
            else:
                manipulation_indicators.append("Massive distribution - possible dump preparation")
            authenticity_factors.append("extreme_flows")
        
        # Check exchange distribution for manipulation
        if exchanges:
            exchange_flows = []
            for exchange, data in exchanges.items():
                if isinstance(data, dict):
                    inflow = data.get('inflow', 0)
                    outflow = data.get('outflow', 0)
                    exchange_flows.append((inflow, outflow))
            
            # Check for coordinated exchange activity
            if len(exchange_flows) > 5:
                # If most exchanges show similar patterns = coordinated
                similar_patterns = 0
                for i, (in1, out1) in enumerate(exchange_flows):
                    for j, (in2, out2) in enumerate(exchange_flows[i+1:], i+1):
                        if abs(in1 - in2) < max(in1, in2) * 0.1 and abs(out1 - out2) < max(out1, out2) * 0.1:
                            similar_patterns += 1
                
                if similar_patterns > len(exchange_flows) * 0.6:
                    manipulation_indicators.append("Coordinated exchange activity - possible manipulation")
                    authenticity_factors.append("coordinated_activity")
        
        # Determine authenticity
        if len(manipulation_indicators) >= 2:
            authenticity = "LOW"
        elif len(manipulation_indicators) >= 1:
            authenticity = "MEDIUM"
        else:
            authenticity = "HIGH"
        
        return {
            "authenticity": authenticity,
            "manipulation_indicators": manipulation_indicators,
            "authenticity_factors": authenticity_factors,
            "analysis": f"Onchain data shows {authenticity.lower()} authenticity with {len(manipulation_indicators)} manipulation indicators"
        }
    
    def analyze_technical_analysis_reliability(self, technical_data):
        """
        Analyze technical analysis for reliability and market context
        Justin knows TA can be misleading in manipulated markets
        """
        if not isinstance(technical_data, dict):
            return {"reliability": "unknown", "market_context": "unknown", "analysis": "No technical data available"}
        
        reliability_factors = []
        market_context_notes = []
        
        # Check for conflicting signals across timeframes
        timeframe_analysis = technical_data.get('timeframe_analysis', {})
        if timeframe_analysis:
            signals = []
            for tf, data in timeframe_analysis.items():
                if isinstance(data, dict):
                    signal = data.get('signal', '')
                    strength = data.get('strength', 0)
                    signals.append((tf, signal, strength))
            
            # Check for conflicting signals
            bullish_signals = [s for s in signals if s[1].lower() == 'bullish']
            bearish_signals = [s for s in signals if s[1].lower() == 'bearish']
            
            if bullish_signals and bearish_signals:
                reliability_factors.append("Conflicting signals across timeframes")
                market_context_notes.append("Market showing mixed signals - proceed with caution")
        
        # Check confidence levels
        confidence = technical_data.get('bob_confidence', 0)
        if confidence < 0.4:
            reliability_factors.append("Low confidence in technical analysis")
            market_context_notes.append("Technical signals lack conviction")
        
        # Determine reliability
        if len(reliability_factors) >= 2:
            reliability = "LOW"
        elif len(reliability_factors) >= 1:
            reliability = "MEDIUM"
        else:
            reliability = "HIGH"
        
        return {
            "reliability": reliability,
            "reliability_factors": reliability_factors,
            "market_context": market_context_notes,
            "analysis": f"Technical analysis shows {reliability.lower()} reliability with {len(reliability_factors)} concerns"
        }
    
    def assess_eth_fundamental_value(self, all_data):
        """
        Assess ETH's fundamental value proposition
        Justin understands ETH's true value beyond price speculation
        """
        value_factors = []
        fundamental_score = 0
        
        # Check for real utility indicators
        onchain_data = all_data.get('onchain', {})
        if onchain_data:
            # High transaction activity = real utility
            exchanges = onchain_data.get('exchanges', {})
            if exchanges and len(exchanges) > 5:
                value_factors.append("Active exchange ecosystem - real utility")
                fundamental_score += 1
        
        # Check for development activity (from news)
        news_data = all_data.get('news', {})
        if news_data:
            categories = news_data.get('categories', {})
            if categories:
                defi_news = categories.get('defi', 0)
                scaling_news = categories.get('scaling', 0)
                if defi_news > 5 or scaling_news > 2:
                    value_factors.append("Active development ecosystem - fundamental value")
                    fundamental_score += 1
        
        # Check social sentiment for real adoption vs speculation
        social_data = all_data.get('social', {})
        if social_data:
            avg_sentiment = social_data.get('avg_sentiment', 0)
            if avg_sentiment is not None and avg_sentiment != 0:
                if 0.3 <= avg_sentiment <= 0.7:  # Moderate sentiment = real adoption
                    value_factors.append("Moderate social sentiment - real adoption vs speculation")
                    fundamental_score += 1
                elif avg_sentiment > 0.8:  # Too bullish = speculation
                    value_factors.append("Excessive bullish sentiment - speculation risk")
                    fundamental_score -= 1
        
        # Determine fundamental strength
        if fundamental_score >= 2:
            fundamental_strength = "STRONG"
        elif fundamental_score >= 1:
            fundamental_strength = "MODERATE"
        elif fundamental_score >= 0:
            fundamental_strength = "WEAK"
        else:
            fundamental_strength = "NEGATIVE"
        
        return {
            "fundamental_strength": fundamental_strength,
            "fundamental_score": fundamental_score,
            "value_factors": value_factors,
            "analysis": f"ETH shows {fundamental_strength.lower()} fundamental value with {fundamental_score} positive factors"
        }
    
    def make_judgment(self, debate_data):
        """
        Make final judgment based on all analysis
        Justin's decision-making process
        """
        logger.info("🔍 Justin analyzing debate data with skeptical approach...")
        
        # Extract data from both sides
        bullish_evidence = debate_data.get('bullish', {}).get('evidence', {})
        bearish_evidence = debate_data.get('bearish', {}).get('evidence', {})
        
        # Analyze each data source with skepticism
        news_analysis = self.analyze_news_manipulation_risk(bullish_evidence.get('news', {}))
        social_analysis = self.analyze_social_sentiment_reliability(bullish_evidence.get('social', {}))
        onchain_analysis = self.analyze_onchain_data_authenticity(bullish_evidence.get('onchain', {}))
        technical_analysis = self.analyze_technical_analysis_reliability(bullish_evidence.get('technicals', {}))
        
        # Assess fundamental value
        fundamental_analysis = self.assess_eth_fundamental_value(bullish_evidence)
        
        # Calculate weighted scores
        scores = {
            'bullish': 0,
            'bearish': 0,
            'neutral': 0
        }
        
        # News analysis scoring
        if news_analysis['risk_level'] == 'MINIMAL':
            scores['bullish'] += 1
        elif news_analysis['risk_level'] == 'LOW':
            scores['neutral'] += 1
        elif news_analysis['risk_level'] == 'MEDIUM':
            scores['bearish'] += 1
        else:  # HIGH
            scores['bearish'] += 2
        
        # Social analysis scoring
        if social_analysis['reliability'] == 'HIGH':
            scores['bullish'] += 1
        elif social_analysis['reliability'] == 'MEDIUM':
            scores['neutral'] += 1
        else:  # LOW
            scores['bearish'] += 1
        
        # Onchain analysis scoring
        if onchain_analysis['authenticity'] == 'HIGH':
            scores['bullish'] += 1
        elif onchain_analysis['authenticity'] == 'MEDIUM':
            scores['neutral'] += 1
        else:  # LOW
            scores['bearish'] += 1
        
        # Technical analysis scoring
        if technical_analysis['reliability'] == 'HIGH':
            scores['bullish'] += 1
        elif technical_analysis['reliability'] == 'MEDIUM':
            scores['neutral'] += 1
        else:  # LOW
            scores['bearish'] += 1
        
        # Fundamental value scoring
        if fundamental_analysis['fundamental_strength'] == 'STRONG':
            scores['bullish'] += 2
        elif fundamental_analysis['fundamental_strength'] == 'MODERATE':
            scores['neutral'] += 1
        elif fundamental_analysis['fundamental_strength'] == 'WEAK':
            scores['bearish'] += 1
        else:  # NEGATIVE
            scores['bearish'] += 2
        
        # Determine verdict
        max_score = max(scores.values())
        if scores['bullish'] == max_score:
            verdict = 'BUY'
            confidence = min(0.8, 0.5 + (scores['bullish'] - scores['bearish']) * 0.1)
        elif scores['bearish'] == max_score:
            verdict = 'SELL'
            confidence = min(0.8, 0.5 + (scores['bearish'] - scores['bullish']) * 0.1)
        else:
            verdict = 'HOLD'
            confidence = 0.5
        
        # Generate detailed recommendation
        recommendation = self.generate_recommendation(verdict, confidence, {
            'news': news_analysis,
            'social': social_analysis,
            'onchain': onchain_analysis,
            'technical': technical_analysis,
            'fundamental': fundamental_analysis
        })
        
        # Build Justin's concrete proposal (portfolio + trading entries)
        proposal = self.build_concrete_proposal(verdict, confidence, fundamental_analysis, onchain_analysis, technical_analysis)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'judge': self.name,
            'experience_years': self.experience_years,
            'analysis_style': self.analysis_style,
            'scores': scores,
            'verdict': verdict,
            'confidence': confidence,
            'detailed_analysis': {
                'news_manipulation_risk': news_analysis,
                'social_reliability': social_analysis,
                'onchain_authenticity': onchain_analysis,
                'technical_reliability': technical_analysis,
                'fundamental_value': fundamental_analysis
            },
            'recommendation': recommendation,
            'proposal': proposal,
            'justin_notes': self.generate_justin_notes(verdict, confidence, scores)
        }
    
    def generate_recommendation(self, verdict, confidence, analyses):
        """Generate detailed trading recommendation"""
        
        # Base recommendation structure
        base_rec = {
            'action': verdict,
            'confidence': confidence,
            'position_sizing': 'Conservative',
            'risk_management': 'High',
            'time_horizon': 'Medium-term'
        }
        
        # Customize based on analysis
        if verdict == 'BUY':
            base_rec.update({
                'entry_strategy': 'Scale in on pullbacks - 3 tranches',
                'exit_strategy': 'Scale out at resistance levels',
                'stop_loss': 'Below key support levels',
                'take_profit': 'At major resistance or 2:1 R/R',
                'risk_factors': 'Monitor for manipulation signals',
                'justin_advice': 'Only buy if fundamental value is strong and manipulation risk is low'
            })
        elif verdict == 'SELL':
            base_rec.update({
                'entry_strategy': 'Scale out of positions',
                'exit_strategy': 'Complete exit on any bounce',
                'stop_loss': 'Above recent highs',
                'take_profit': 'At support levels or 1:1 R/R',
                'risk_factors': 'High manipulation risk detected',
                'justin_advice': 'Sell if manipulation signals are strong or fundamental value is weak'
            })
        else:  # HOLD
            base_rec.update({
                'entry_strategy': 'Wait for clearer signals',
                'exit_strategy': 'Hold current positions',
                'stop_loss': 'Tight stops on any new positions',
                'take_profit': 'Take profits on any spikes',
                'risk_factors': 'Mixed signals - high uncertainty',
                'justin_advice': 'Wait for more data - current signals are unreliable'
            })
        
        return base_rec
    
    def generate_justin_notes(self, verdict, confidence, scores):
        """Generate Justin's personal notes and insights"""
        
        notes = []
        
        # Add general market wisdom
        notes.append(f"After {self.experience_years} years in this market, I've seen every trick in the book.")
        notes.append("ETH is inherently manipulatable - that's both its strength and weakness.")
        notes.append("Real value comes from utility, not price speculation.")
        
        # Add specific insights based on scores
        if scores['bearish'] > scores['bullish']:
            notes.append("The data suggests manipulation is high - be very careful.")
            notes.append("When everyone is bullish, that's usually when the rug gets pulled.")
        elif scores['bullish'] > scores['bearish']:
            notes.append("The data looks relatively clean - but stay vigilant.")
            notes.append("Even clean data can be misleading in this market.")
        else:
            notes.append("Mixed signals everywhere - this is when you need to be most careful.")
            notes.append("When in doubt, wait it out.")
        
        # Add confidence-based advice
        if confidence < 0.6:
            notes.append("My confidence is low - reduce position sizes accordingly.")
        else:
            notes.append("I'm reasonably confident in this call - but never bet the farm.")
        
        return notes

    def build_concrete_proposal(self, verdict, confidence, fundamental_analysis, onchain_analysis, technical_analysis):
        """Produce concrete portfolio and trading plan per user's spec."""
        # Portfolio long-horizon action
        portfolio_action = {
            'decision': verdict,  # BUY/SELL/HOLD (Justin base)
            'style': 'DCA buy' if verdict == 'BUY' and confidence >= 0.6 else ('partial sell' if verdict == 'SELL' and confidence < 0.6 else verdict.lower()),
            'confidence': confidence,
            'horizon': 'long-term',
        }

        # Trading short-term entries based on TA context
        base_risk = 'conservative' if confidence < 0.6 else 'neutral'
        trade_plan = {
            'mode': 'swing' if technical_analysis.get('reliability') == 'HIGH' else 'short-term',
            'entry': {
                'type': 'scaled',
                'tranches': 3,
                'risk_profile': base_risk,
            },
            'risk': {
                'stop_loss_pct': 0.015 if base_risk == 'conservative' else 0.02,
                'take_profit_pct': 0.03 if base_risk == 'conservative' else 0.05,
                'rr_min': 1.5
            }
        }

        # Adjust entries by onchain flows: strong outflows = allow wider TP
        try:
            net_flow = onchain_analysis.get('net_flow', 0)
            if isinstance(net_flow, (int, float)) and net_flow > 10000:
                trade_plan['risk']['take_profit_pct'] += 0.01
        except Exception:
            pass

        return {
            'portfolio': portfolio_action,
            'trading': trade_plan
        }

def main():
    """Main execution function"""
    print("🏛️ JUSTIN LY - SKEPTICAL MARKET VETERAN JUDGE")
    print("=" * 60)
    
    justin = JustinSkepticalJudge()
    
    # Read latest debate
    debate = justin.read_latest_alpha_json()
    if not debate:
        logger.error('No Alpha debate file found. Run Alpha first.')
        raise SystemExit(1)
    
    print("🔍 Analyzing debate with 15+ years of skeptical experience...")
    
    # Make judgment
    result = justin.make_judgment(debate)
    
    # Save result
    fn = os.path.join(os.path.dirname(__file__), f"justin_verdict_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    with open(fn, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Justin's verdict saved to {fn}")
    
    # Print summary
    print("\n📊 JUSTIN'S VERDICT SUMMARY:")
    print(f"🎯 Verdict: {result['verdict']}")
    print(f"🎲 Confidence: {result['confidence']:.2f}")
    print(f"📈 Scores: Bullish {result['scores']['bullish']}, Bearish {result['scores']['bearish']}, Neutral {result['scores']['neutral']}")
    
    print("\n💭 JUSTIN'S NOTES:")
    for note in result['justin_notes']:
        print(f"   • {note}")
    
    return result

if __name__ == '__main__':
    main()
