#!/usr/bin/env python3
"""
Yasuo Supabase Integration
Store daily analysis data for 7-day trend analysis
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not available - install with: pip install supabase")

class YasuoSupabaseManager:
    """
    Manage Yasuo data storage in Supabase for trend analysis
    """
    
    def __init__(self):
        self.setup_logging()
        
        if not SUPABASE_AVAILABLE:
            self.logger.error("❌ Supabase not available")
            self.client = None
            return
        
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            self.logger.error("❌ Supabase credentials not configured")
            self.client = None
            return
        
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("✅ Connected to Supabase")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Supabase: {e}")
            self.client = None
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def store_daily_analysis(self, analysis_data: Dict) -> bool:
        """
        Store daily Yasuo analysis data
        """
        if not self.client:
            self.logger.error("❌ Supabase client not available")
            return False
        
        try:
            # Extract analysis from the data
            analysis = analysis_data.get('analysis', {})
            data_sources = analysis_data.get('data_sources', {})
            
            # Prepare data for storage matching the table structure
            daily_record = {
                "overall_sentiment": analysis.get('market_sentiment', 'neutral'),
                "primary_signal": analysis.get('trading_signal', 'HOLD'),
                "confidence": analysis.get('confidence', 0.0),
                "etf_daily_flow": data_sources.get('etf_flows', {}).get('daily_flow', 0),
                "exchange_inflow_eth": data_sources.get('exchange_flows', {}).get('inflow', 0),
                "exchange_outflow_eth": data_sources.get('exchange_flows', {}).get('outflow', 0),
                "exchange_net_flow_eth": data_sources.get('exchange_flows', {}).get('net_flow', 0),
                "whale_intelligence": data_sources.get('dune_whales', {}),
                "etf_flows": data_sources.get('etf_flows', {}),
                "exchange_flows": data_sources.get('exchange_flows', {}),
                "large_transactions": data_sources.get('dune_whales', {}),
                "market_context": {
                    "liveliness_score": data_sources.get('liveliness', {}).get('score', 0),
                    "timestamp": analysis_data.get('timestamp', datetime.now().isoformat())
                },
                "summary": analysis,
                "raw_run": analysis_data
            }
            
            # Insert into Supabase
            result = self.client.table('yasuo_full_snapshot').insert(daily_record).execute()
            
            if result.data:
                self.logger.info("✅ Daily analysis stored in Supabase")
                return True
            else:
                self.logger.error("❌ Failed to store daily analysis")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error storing daily analysis: {e}")
            return False
    
    def get_7_day_analysis(self) -> List[Dict]:
        """
        Get last 7 days of analysis data for trend analysis
        """
        if not self.client:
            self.logger.error("❌ Supabase client not available")
            return []
        
        try:
            # Get exactly the latest 7 snapshots by analysis_date
            result = (
                self.client
                .table('yasuo_full_snapshot')
                .select('*')
                .order('analysis_date', desc=True)
                .limit(7)
                .execute()
            )
            
            if result.data:
                # Return in chronological order (oldest -> newest)
                ordered = list(sorted(result.data, key=lambda x: x.get('analysis_date', '')))
                self.logger.info(f"✅ Retrieved {len(ordered)} most recent daily snapshots (max 7)")
                return ordered
            else:
                self.logger.warning("⚠️ No historical data found")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error retrieving 7-day analysis: {e}")
            return []
    
    def analyze_7_day_trends(self, historical_data: List[Dict]) -> Dict:
        """
        Analyze 7-day trends from historical data
        """
        if not historical_data:
            return {"status": "no_data", "message": "No historical data available"}
        
        try:
            # Calculate trends
            etf_flows = [float(day.get('etf_daily_flow', 0)) for day in historical_data]
            exchange_flows = [float(day.get('exchange_net_flow', 0)) for day in historical_data]
            large_tx_counts = [int(day.get('large_transactions_count', 0)) for day in historical_data]
            funding_rates = [float(day.get('funding_rate_percent', 0)) for day in historical_data]
            
            # Calculate averages
            avg_etf_flow = sum(etf_flows) / len(etf_flows) if etf_flows else 0
            avg_exchange_flow = sum(exchange_flows) / len(exchange_flows) if exchange_flows else 0
            avg_large_tx = sum(large_tx_counts) / len(large_tx_counts) if large_tx_counts else 0
            avg_funding_rate = sum(funding_rates) / len(funding_rates) if funding_rates else 0
            
            # Calculate trends (simple linear trend)
            etf_trend = self._calculate_trend(etf_flows)
            exchange_trend = self._calculate_trend(exchange_flows)
            large_tx_trend = self._calculate_trend(large_tx_counts)
            funding_trend = self._calculate_trend(funding_rates)
            
            # Count recommendation actions
            actions = [day.get('recommendation_action', 'UNKNOWN') for day in historical_data]
            action_counts = {
                'BUY': actions.count('BUY'),
                'SELL': actions.count('SELL'),
                'HOLD': actions.count('HOLD')
            }
            
            # Calculate confidence trends
            confidences = [float(day.get('recommendation_confidence', 0)) for day in historical_data]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            confidence_trend = self._calculate_trend(confidences)
            
            return {
                "status": "success",
                "period_days": len(historical_data),
                "averages": {
                    "etf_daily_flow": avg_etf_flow,
                    "exchange_net_flow": avg_exchange_flow,
                    "large_transactions": avg_large_tx,
                    "funding_rate": avg_funding_rate,
                    "confidence": avg_confidence
                },
                "trends": {
                    "etf_flow_trend": etf_trend,
                    "exchange_flow_trend": exchange_trend,
                    "large_tx_trend": large_tx_trend,
                    "funding_rate_trend": funding_trend,
                    "confidence_trend": confidence_trend
                },
                "action_distribution": action_counts,
                "trend_interpretation": self._interpret_trends(etf_trend, exchange_trend, large_tx_trend, funding_trend)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing trends: {e}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate simple linear trend
        """
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _interpret_trends(self, etf_trend: str, exchange_trend: str, large_tx_trend: str, funding_trend: str) -> Dict:
        """
        Interpret trend combinations
        """
        bullish_signals = 0
        bearish_signals = 0
        
        # ETF flow trend
        if etf_trend == "increasing":
            bullish_signals += 1
        elif etf_trend == "decreasing":
            bearish_signals += 1
        
        # Exchange flow trend (outflow = bullish)
        if exchange_trend == "increasing":
            bullish_signals += 1
        elif exchange_trend == "decreasing":
            bearish_signals += 1
        
        # Large transactions trend
        if large_tx_trend == "increasing":
            bullish_signals += 1
        elif large_tx_trend == "decreasing":
            bearish_signals += 1
        
        # Funding rate trend (lower = bullish)
        if funding_trend == "decreasing":
            bullish_signals += 1
        elif funding_trend == "increasing":
            bearish_signals += 1
        
        if bullish_signals > bearish_signals:
            overall_trend = "bullish"
        elif bearish_signals > bullish_signals:
            overall_trend = "bearish"
        else:
            overall_trend = "neutral"
        
        return {
            "overall_trend": overall_trend,
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "trend_strength": abs(bullish_signals - bearish_signals) / 4.0
        }

    def store_whale_intelligence(self, whale_data: Dict[str, Any]) -> bool:
        """Store whale intelligence snapshot fetched from Dune into Supabase"""
        if not self.client:
            self.logger.error("❌ Supabase client not available")
            return False
        try:
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                "data_source": whale_data.get("data_source", "unknown"),
                "total_whales_tracked": whale_data.get("total_whales_tracked", 0),
                "total_whale_balance_eth": whale_data.get("total_whale_balance_eth", 0),
                "total_whale_balance_usd": whale_data.get("total_whale_balance_usd", 0),
                "recent_transactions": whale_data.get("recent_transactions", 0),
                "market_sentiment": whale_data.get("market_sentiment", {}),
                "institutional_behavior": whale_data.get("institutional_behavior", {}),
                "risk_assessment": whale_data.get("risk_assessment", {}),
                "market_impact": whale_data.get("market_impact", {}),
                "raw_payload": whale_data,
            }
            result = self.client.table('yasuo_whale_intelligence').insert(snapshot).execute()
            if result.data:
                self.logger.info("✅ Whale intelligence snapshot stored in Supabase")
                return True
            else:
                self.logger.error("❌ Failed to store whale intelligence snapshot")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error storing whale intelligence: {e}")
            return False

# Test function
def main():
    print("🛡️ YASUO SUPABASE INTEGRATION TEST")
    print("=" * 50)
    
    manager = YasuoSupabaseManager()
    
    if not manager.client:
        print("❌ Supabase not available - check credentials")
        return
    
    # Test getting 7-day data
    historical_data = manager.get_7_day_analysis()
    print(f"📊 Retrieved {len(historical_data)} days of data")
    
    if historical_data:
        # Test trend analysis
        trends = manager.analyze_7_day_trends(historical_data)
        print(f"📈 Trend analysis: {trends}")

if __name__ == "__main__":
    main()
