#!/usr/bin/env python3
"""
Bob Supabase Integration
Store technical analysis data in Supabase
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not available - install with: pip install supabase")

class BobSupabaseManager:
    """Bob Supabase Integration Manager"""
    
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
    
    def store_technical_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """Store technical analysis data in Supabase"""
        if not self.client:
            self.logger.warning("⚠️ Supabase client not available")
            return False
        
        try:
            # Extract timeframe analysis
            timeframe_analysis = analysis_data.get('timeframe_analysis', {})
            master_signal = analysis_data.get('master_signal', {})
            
            # Store each timeframe analysis
            for timeframe, tf_data in timeframe_analysis.items():
                if 'error' in tf_data:
                    continue
                
                # Extract indicators data
                indicators = tf_data.get('indicators', {})
                trend_data = indicators.get('trend', {})
                momentum_data = indicators.get('momentum', {})
                volatility_data = indicators.get('volatility', {})
                volume_data = indicators.get('volume', {})
                
                # Prepare data for insertion
                analysis_record = {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'timeframe': timeframe,
                    'current_price': tf_data.get('current_price', 0),
                    'price_change_24h': 0,  # Will be calculated if needed
                    'volume_24h': 0,  # Will be calculated if needed
                    
                    # Technical indicators
                    'rsi_14': self._extract_latest_value(momentum_data.get('indicators', {}).get('rsi_14', [])),
                    'macd_line': self._extract_latest_value(momentum_data.get('indicators', {}).get('macd', [])),
                    'macd_signal': self._extract_latest_value(momentum_data.get('indicators', {}).get('macd_signal', [])),
                    'macd_histogram': self._extract_latest_value(momentum_data.get('indicators', {}).get('macd_histogram', [])),
                    
                    # Bollinger Bands
                    'bb_upper': self._extract_latest_value(volatility_data.get('indicators', {}).get('bb_upper', [])),
                    'bb_middle': self._extract_latest_value(volatility_data.get('indicators', {}).get('bb_middle', [])),
                    'bb_lower': self._extract_latest_value(volatility_data.get('indicators', {}).get('bb_lower', [])),
                    'bb_position': volatility_data.get('analysis', {}).get('bb_position', 0),
                    
                    # Moving averages
                    'sma_20': self._extract_latest_value(trend_data.get('indicators', {}).get('sma_20', [])),
                    'sma_50': self._extract_latest_value(trend_data.get('indicators', {}).get('sma_50', [])),
                    'sma_200': self._extract_latest_value(trend_data.get('indicators', {}).get('sma_200', [])),
                    'ema_12': self._extract_latest_value(trend_data.get('indicators', {}).get('ema_12', [])),
                    'ema_26': self._extract_latest_value(trend_data.get('indicators', {}).get('ema_26', [])),
                    
                    # Patterns and levels
                    'patterns': json.dumps(trend_data.get('analysis', {}).get('patterns', [])),
                    'support_levels': json.dumps(master_signal.get('key_levels', {}).get('support', [])),
                    'resistance_levels': json.dumps(master_signal.get('key_levels', {}).get('resistance', [])),
                    
                    # Trading signals
                    'signal_direction': tf_data.get('signal', 'NEUTRAL').upper(),
                    'signal_strength': tf_data.get('strength', 0),
                    'confidence_score': analysis_data.get('bob_confidence', 0),
                    'risk_level': master_signal.get('risk_level', 'MEDIUM'),
                    
                    # Analysis metadata
                    'analysis_summary': f"Bob's {timeframe} analysis: {tf_data.get('signal', 'neutral')} signal with {tf_data.get('strength', 0):.2f} strength",
                    'key_insights': json.dumps({
                        'trend_analysis': trend_data.get('analysis', {}),
                        'momentum_analysis': momentum_data.get('analysis', {}),
                        'volatility_analysis': volatility_data.get('analysis', {}),
                        'volume_analysis': volume_data.get('analysis', {})
                    })
                }
                
                # Insert into Supabase
                result = self.client.table('bob_technical_analysis').insert(analysis_record).execute()
                
                if result.data:
                    self.logger.info(f"✅ Stored {timeframe} analysis in Supabase")
                else:
                    self.logger.error(f"❌ Failed to store {timeframe} analysis")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing technical analysis: {e}")
            return False
    
    def _extract_latest_value(self, data_array: List) -> Optional[float]:
        """Extract the latest non-null value from an array"""
        if not data_array or len(data_array) == 0:
            return None
        
        # Find the last non-null value
        for value in reversed(data_array):
            if value is not None and not (isinstance(value, float) and (value != value)):  # Check for NaN
                return float(value)
        
        return None
    
    def get_latest_analysis(self, timeframe: str = None) -> Optional[Dict]:
        """Get latest technical analysis from Supabase"""
        if not self.client:
            return None
        
        try:
            query = self.client.table('bob_technical_analysis').select('*').order('analysis_timestamp', desc=True)
            
            if timeframe:
                query = query.eq('timeframe', timeframe)
            
            result = query.limit(1).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching latest analysis: {e}")
            return None
    
    def get_analysis_history(self, timeframe: str = None, limit: int = 10) -> List[Dict]:
        """Get technical analysis history from Supabase"""
        if not self.client:
            return []
        
        try:
            query = self.client.table('bob_technical_analysis').select('*').order('analysis_timestamp', desc=True)
            
            if timeframe:
                query = query.eq('timeframe', timeframe)
            
            result = query.limit(limit).execute()
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching analysis history: {e}")
            return []
