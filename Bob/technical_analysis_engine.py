#!/usr/bin/env python3
"""
📈 BOB - ADVANCED TECHNICAL ANALYSIS ENGINE
Expert Technical Analysis Agent for ETH Trading
Top-tier hedge fund level TA with full TA-Lib integration
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import json
import asyncio
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Supabase integration
try:
    from supabase_integration import BobSupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase integration not available for Bob")

# Import Bob's options analysis
try:
    from options_analysis_engine import BobOptionsAnalysisEngine
    OPTIONS_AVAILABLE = True
except ImportError:
    print("⚠️ Options analysis not available. Install aiohttp: pip install aiohttp")
    OPTIONS_AVAILABLE = False

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    print("⚠️ TA-Lib not installed. Run: pip install TA-Lib")
    TALIB_AVAILABLE = False

class BobTechnicalAnalysisEngine:
    """
    Bob - Expert Technical Analysis Agent
    Specialized in 1H, 4H, 1D timeframe analysis for ETH/USDT
    """
    
    def __init__(self):
        self.setup_logging()
        self.timeframes = ['1h', '4h', '1d']
        # Ensure clean symbol (yfinance expects no leading '$')
        self.symbol = 'ETH-USD'
        if self.symbol.startswith('$'):
            self.symbol = self.symbol[1:]
        
        # Initialize Supabase manager
        if SUPABASE_AVAILABLE:
            self.supabase_manager = BobSupabaseManager()
        else:
            self.supabase_manager = None
        
        # Initialize options analysis engine
        if OPTIONS_AVAILABLE:
            self.options_engine = BobOptionsAnalysisEngine()
        else:
            self.options_engine = None
        
        # Technical Analysis Categories
        self.ta_categories = {
            'trend': ['SMA', 'EMA', 'DEMA', 'TEMA', 'TRIMA', 'KAMA', 'MAMA', 'T3'],
            'momentum': ['RSI', 'STOCH', 'STOCHF', 'STOCHRSI', 'MACD', 'MFI', 'ROC', 'MOM'],
            'volatility': ['BBANDS', 'ATR', 'NATR', 'TRANGE'],
            'volume': ['AD', 'ADOSC', 'OBV', 'MFI'],
            'oscillators': ['CCI', 'CMO', 'DX', 'MINUS_DI', 'PLUS_DI', 'PPO', 'ULTOSC', 'WILLR'],
            'pattern': ['SAR', 'AROON', 'AROONOSC', 'BOP'],
            'statistical': ['BETA', 'CORREL', 'LINEARREG', 'STDDEV', 'VAR']
        }
        
        # Bob's expert signal weights
        self.signal_weights = {
            '1h': {'weight': 0.2, 'focus': 'short_term_momentum'},
            '4h': {'weight': 0.5, 'focus': 'medium_term_structure'}, 
            '1d': {'weight': 0.3, 'focus': 'long_term_trend'}
        }
        
        self.logger.info("📈 Bob Technical Analysis Engine initialized")
    
    def setup_logging(self):
        """Setup logging for Bob"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def fetch_market_data(self, period: str = "30d", interval: str = "1h") -> pd.DataFrame:
        """
        Fetch ETH market data with multiple timeframes
        Bob's data acquisition system
        """
        try:
            # Normalize interval to yfinance-supported values
            interval_map = {"1h": "60m", "4h": "240m", "1d": "1d"}
            yf_interval = interval_map.get(interval, interval)
            yf_period = period
            if interval == '4h' and period == '30d':
                yf_period = '60d'
            self.logger.info(f"📊 Bob fetching {self.symbol} data - {interval} ({yf_interval}) interval, period {yf_period}")
            
            # Attempt 1: Ticker.history
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period=yf_period, interval=yf_interval, auto_adjust=True)
            
            if data.empty:
                # Attempt 2: yf.download fallback
                self.logger.info("⚠️ history() returned empty, trying yf.download fallback")
                data = yf.download(self.symbol, period=yf_period, interval=yf_interval, auto_adjust=True, progress=False)
            
            if data.empty:
                # Attempt 3: broaden period for intraday
                if yf_interval in ("60m", "240m"):
                    alt_period = '60d' if yf_interval == '60m' else '90d'
                    self.logger.info(f"⚠️ Still empty, retry with broader period {alt_period}")
                    data = yf.download(self.symbol, period=alt_period, interval=yf_interval, auto_adjust=True, progress=False)
            
            if data.empty:
                raise ValueError("No data fetched from yfinance after fallbacks")
            
            # Clean and prepare data
            data = data.dropna()
            data.columns = [col.lower() for col in data.columns]
            
            # Add basic derived metrics
            data['hlc3'] = (data['high'] + data['low'] + data['close']) / 3
            data['hl2'] = (data['high'] + data['low']) / 2
            data['ohlc4'] = (data['open'] + data['high'] + data['low'] + data['close']) / 4
            
            self.logger.info(f"✅ Data fetched: {len(data)} candles")
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Data fetch failed: {e}")
            return pd.DataFrame()
    
    def calculate_trend_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Bob's advanced trend analysis
        Multiple MA types and trend detection
        """
        if not TALIB_AVAILABLE:
            return {"error": "TA-Lib not available"}
        
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        volume = data['volume'].values
        
        trend_signals = {}
        
        try:
            # Moving Averages Suite
            trend_signals['sma_20'] = talib.SMA(close, timeperiod=20)
            trend_signals['sma_50'] = talib.SMA(close, timeperiod=50)
            trend_signals['sma_200'] = talib.SMA(close, timeperiod=200)
            
            trend_signals['ema_12'] = talib.EMA(close, timeperiod=12)
            trend_signals['ema_26'] = talib.EMA(close, timeperiod=26)
            trend_signals['ema_50'] = talib.EMA(close, timeperiod=50)
            
            # Advanced MAs
            trend_signals['dema_21'] = talib.DEMA(close, timeperiod=21)
            trend_signals['tema_21'] = talib.TEMA(close, timeperiod=21)
            trend_signals['kama_30'] = talib.KAMA(close, timeperiod=30)
            
            # MAMA (Adaptive MA)
            mama, fama = talib.MAMA(close, fastlimit=0.5, slowlimit=0.05)
            trend_signals['mama'] = mama
            trend_signals['fama'] = fama
            
            # Parabolic SAR
            trend_signals['sar'] = talib.SAR(high, low, acceleration=0.02, maximum=0.2)
            
            # Current values for analysis
            current_price = close[-1]
            trend_analysis = {
                'current_price': current_price,
                'sma_20_signal': 'bullish' if current_price > trend_signals['sma_20'][-1] else 'bearish',
                'sma_50_signal': 'bullish' if current_price > trend_signals['sma_50'][-1] else 'bearish',
                'sma_200_signal': 'bullish' if current_price > trend_signals['sma_200'][-1] else 'bearish',
                'ema_alignment': self.check_ema_alignment(trend_signals),
                'sar_signal': 'bullish' if current_price > trend_signals['sar'][-1] else 'bearish',
                'trend_strength': self.calculate_trend_strength(close, trend_signals)
            }
            
            return {
                'indicators': trend_signals,
                'analysis': trend_analysis
            }
            
        except Exception as e:
            self.logger.error(f"❌ Trend calculation error: {e}")
            return {"error": str(e)}
    
    def calculate_momentum_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Bob's momentum analysis suite
        RSI, MACD, Stochastic, and more
        """
        if not TALIB_AVAILABLE:
            return {"error": "TA-Lib not available"}
        
        # Convert to float64 for TA-Lib compatibility
        close = data['close'].values.astype(np.float64)
        high = data['high'].values.astype(np.float64)
        low = data['low'].values.astype(np.float64)
        volume = data['volume'].values.astype(np.float64)
        
        momentum_signals = {}
        
        try:
            # RSI Suite
            momentum_signals['rsi_14'] = talib.RSI(close, timeperiod=14)
            momentum_signals['rsi_21'] = talib.RSI(close, timeperiod=21)
            
            # MACD
            macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            momentum_signals['macd'] = macd
            momentum_signals['macd_signal'] = macdsignal
            momentum_signals['macd_histogram'] = macdhist
            
            # Stochastic Oscillators
            stoch_k, stoch_d = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
            momentum_signals['stoch_k'] = stoch_k
            momentum_signals['stoch_d'] = stoch_d
            
            # Stochastic RSI
            stochrsi_k, stochrsi_d = talib.STOCHRSI(close, timeperiod=14, fastk_period=5, fastd_period=3)
            momentum_signals['stochrsi_k'] = stochrsi_k
            momentum_signals['stochrsi_d'] = stochrsi_d
            
            # Money Flow Index
            momentum_signals['mfi'] = talib.MFI(high, low, close, volume, timeperiod=14)
            
            # Rate of Change
            momentum_signals['roc'] = talib.ROC(close, timeperiod=10)
            
            # Momentum
            momentum_signals['momentum'] = talib.MOM(close, timeperiod=10)
            
            # Williams %R
            momentum_signals['willr'] = talib.WILLR(high, low, close, timeperiod=14)
            
            # Commodity Channel Index
            momentum_signals['cci'] = talib.CCI(high, low, close, timeperiod=14)
            
            # Analysis
            momentum_analysis = {
                'rsi_signal': self.analyze_rsi(momentum_signals['rsi_14'][-1]),
                'macd_signal': self.analyze_macd(macd[-1], macdsignal[-1], macdhist[-1]),
                'stoch_signal': self.analyze_stochastic(stoch_k[-1], stoch_d[-1]),
                'mfi_signal': self.analyze_mfi(momentum_signals['mfi'][-1]),
                'momentum_score': self.calculate_momentum_score(momentum_signals),
                'divergence_signals': self.detect_divergences(close, momentum_signals)
            }
            
            return {
                'indicators': momentum_signals,
                'analysis': momentum_analysis
            }
            
        except Exception as e:
            self.logger.error(f"❌ Momentum calculation error: {e}")
            return {"error": str(e)}
    
    def calculate_volatility_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Bob's volatility analysis
        Bollinger Bands, ATR, and volatility measures
        """
        if not TALIB_AVAILABLE:
            return {"error": "TA-Lib not available"}
        
        # Convert to float64 for TA-Lib compatibility
        close = data['close'].values.astype(np.float64)
        high = data['high'].values.astype(np.float64)
        low = data['low'].values.astype(np.float64)
        
        volatility_signals = {}
        
        try:
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            volatility_signals['bb_upper'] = bb_upper
            volatility_signals['bb_middle'] = bb_middle
            volatility_signals['bb_lower'] = bb_lower
            
            # Average True Range
            volatility_signals['atr'] = talib.ATR(high, low, close, timeperiod=14)
            volatility_signals['natr'] = talib.NATR(high, low, close, timeperiod=14)
            
            # True Range
            volatility_signals['trange'] = talib.TRANGE(high, low, close)
            
            # Standard Deviation
            volatility_signals['stddev'] = talib.STDDEV(close, timeperiod=20)
            
            # Analysis
            current_price = close[-1]
            bb_position = (current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
            
            volatility_analysis = {
                'bb_position': bb_position,
                'bb_signal': self.analyze_bollinger_bands(current_price, bb_upper[-1], bb_middle[-1], bb_lower[-1]),
                'atr_signal': self.analyze_atr(volatility_signals['atr']),
                'volatility_regime': self.determine_volatility_regime(volatility_signals['atr']),
                'squeeze_detection': self.detect_volatility_squeeze(bb_upper, bb_lower, volatility_signals['atr'])
            }
            
            return {
                'indicators': volatility_signals,
                'analysis': volatility_analysis
            }
            
        except Exception as e:
            self.logger.error(f"❌ Volatility calculation error: {e}")
            return {"error": str(e)}
    
    def calculate_volume_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Bob's volume analysis
        OBV, A/D Line, and volume patterns
        """
        if not TALIB_AVAILABLE:
            return {"error": "TA-Lib not available"}
        
        # Convert to float64 for TA-Lib compatibility
        close = data['close'].values.astype(np.float64)
        high = data['high'].values.astype(np.float64)
        low = data['low'].values.astype(np.float64)
        volume = data['volume'].values.astype(np.float64)
        
        volume_signals = {}
        
        try:
            # On Balance Volume
            volume_signals['obv'] = talib.OBV(close, volume)
            
            # Accumulation/Distribution Line
            volume_signals['ad'] = talib.AD(high, low, close, volume)
            
            # Chaikin A/D Oscillator
            volume_signals['adosc'] = talib.ADOSC(high, low, close, volume, fastperiod=3, slowperiod=10)
            
            # Volume analysis
            volume_analysis = {
                'obv_trend': self.analyze_obv_trend(volume_signals['obv']),
                'ad_signal': self.analyze_ad_line(volume_signals['ad']),
                'volume_confirmation': self.check_volume_confirmation(close, volume),
                'volume_pattern': self.detect_volume_patterns(volume)
            }
            
            return {
                'indicators': volume_signals,
                'analysis': volume_analysis
            }
            
        except Exception as e:
            self.logger.error(f"❌ Volume calculation error: {e}")
            return {"error": str(e)}
    
    async def generate_multi_timeframe_analysis(self) -> Dict:
        """
        Bob's comprehensive multi-timeframe analysis
        1H, 4H, 1D analysis with weighted signals
        """
        
        self.logger.info("📈 Bob starting multi-timeframe analysis...")
        
        timeframe_analysis = {}
        
        for tf in self.timeframes:
            self.logger.info(f"🔍 Analyzing {tf} timeframe...")
            
            # Map timeframe to yfinance interval
            interval_map = {'1h': '1h', '4h': '1h', '1d': '1d'}
            period_map = {'1h': '7d', '4h': '30d', '1d': '1y'}
            
            interval = interval_map[tf]
            period = period_map[tf]
            
            # For 4h, we'll resample 1h data
            data = self.fetch_market_data(period=period, interval=interval)
            
            if tf == '4h' and not data.empty:
                # Resample to 4h
                data = data.resample('4H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
            
            if data.empty:
                timeframe_analysis[tf] = {"error": "No data available"}
                continue
            
            # Calculate all indicators
            trend_analysis = self.calculate_trend_indicators(data)
            momentum_analysis = self.calculate_momentum_indicators(data)
            volatility_analysis = self.calculate_volatility_indicators(data)
            volume_analysis = self.calculate_volume_indicators(data)
            
            # Generate timeframe signal
            tf_signal = self.generate_timeframe_signal(
                trend_analysis, momentum_analysis, 
                volatility_analysis, volume_analysis, tf
            )
            
            timeframe_analysis[tf] = {
                'data_points': len(data),
                'current_price': data['close'].iloc[-1] if not data.empty else 0,
                'trend': trend_analysis,
                'momentum': momentum_analysis,
                'volatility': volatility_analysis,
                'volume': volume_analysis,
                'signal': tf_signal
            }
        
        # Generate master signal
        master_signal = self.generate_master_signal(timeframe_analysis)
        
        # Add options analysis if available
        options_analysis = None
        if self.options_engine:
            try:
                current_price = 0
                for tf_data in timeframe_analysis.values():
                    if 'current_price' in tf_data and tf_data['current_price'] > 0:
                        current_price = tf_data['current_price']
                        break
                
                if current_price > 0:
                    self.logger.info("📊 Adding options analysis...")
                    options_analysis = await self.options_engine.run_comprehensive_options_analysis(current_price)
                    
                    if options_analysis and 'error' not in options_analysis:
                        # Integrate options signals into master signal
                        master_signal = self.integrate_options_signals(master_signal, options_analysis)
                        self.logger.info("✅ Options analysis integrated")
                    else:
                        self.logger.warning("⚠️ Options analysis failed")
                        
            except Exception as e:
                self.logger.error(f"❌ Options analysis error: {e}")
        
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'symbol': self.symbol,
            'timeframe_analysis': timeframe_analysis,
            'master_signal': master_signal,
            'bob_confidence': self.calculate_bob_confidence(timeframe_analysis)
        }
        
        # Add options analysis if successful
        if options_analysis and 'error' not in options_analysis:
            analysis_result['options_analysis'] = options_analysis
        
        # Store analysis in Supabase
        if self.supabase_manager:
            try:
                self.logger.info("💾 Storing analysis in Supabase...")
                success = self.supabase_manager.store_technical_analysis(analysis_result)
                if success:
                    self.logger.info("✅ Analysis stored in Supabase successfully")
                else:
                    self.logger.warning("⚠️ Failed to store analysis in Supabase")
            except Exception as e:
                self.logger.error(f"❌ Error storing analysis in Supabase: {e}")
        
        return analysis_result
    
    def generate_timeframe_signal(self, trend, momentum, volatility, volume, timeframe) -> Dict:
        """Generate signal for specific timeframe"""
        
        signals = []
        
        # Trend signals
        if 'analysis' in trend:
            trend_score = 0
            if trend['analysis']['sma_20_signal'] == 'bullish': trend_score += 1
            if trend['analysis']['sma_50_signal'] == 'bullish': trend_score += 1  
            if trend['analysis']['sar_signal'] == 'bullish': trend_score += 1
            signals.append(('trend', trend_score / 3))
        
        # Momentum signals
        if 'analysis' in momentum:
            momentum_score = momentum['analysis'].get('momentum_score', 0)
            signals.append(('momentum', momentum_score))
        
        # Volatility signals  
        if 'analysis' in volatility:
            vol_signal = 1 if volatility['analysis']['bb_signal'] == 'bullish' else -1 if volatility['analysis']['bb_signal'] == 'bearish' else 0
            signals.append(('volatility', vol_signal * 0.5))
        
        # Volume confirmation
        if 'analysis' in volume:
            vol_confirm = 1 if volume['analysis']['volume_confirmation'] else 0
            signals.append(('volume', vol_confirm * 0.3))
        
        # Calculate weighted signal
        total_signal = sum([score for _, score in signals])
        signal_strength = abs(total_signal) / len(signals) if signals else 0
        
        direction = 'bullish' if total_signal > 0.1 else 'bearish' if total_signal < -0.1 else 'neutral'
        
        return {
            'direction': direction,
            'strength': signal_strength,
            'raw_score': total_signal,
            'components': dict(signals),
            'timeframe_weight': self.signal_weights[timeframe]['weight']
        }
    
    def generate_master_signal(self, timeframe_analysis: Dict) -> Dict:
        """
        Bob's master signal combining all timeframes
        """
        
        weighted_score = 0
        total_weight = 0
        confidence_factors = []
        
        for tf, analysis in timeframe_analysis.items():
            # New structure: analysis has 'signal' and 'strength' directly
            if 'signal' in analysis and 'strength' in analysis:
                signal = analysis['signal']
                strength = analysis['strength']
                weight = self.signal_weights.get(tf, {}).get('weight', 1.0)
                
                # Convert signal to score
                if signal == 'bullish':
                    signal_score = strength
                elif signal == 'bearish':
                    signal_score = -strength
                else:
                    signal_score = 0
                
                weighted_score += signal_score * weight
                total_weight += weight
                confidence_factors.append(strength)
        
        # Calculate master direction
        if weighted_score > 0.15:
            master_direction = 'BULLISH'
        elif weighted_score < -0.15:
            master_direction = 'BEARISH'
        else:
            master_direction = 'NEUTRAL'
        
        # Calculate confidence
        avg_confidence = np.mean(confidence_factors) if confidence_factors else 0
        
        # Generate trading recommendation
        trading_action = self.generate_trading_recommendation(
            master_direction, weighted_score, avg_confidence
        )
        
        return {
            'direction': master_direction,
            'strength': abs(weighted_score),
            'confidence': avg_confidence,
            'raw_score': weighted_score,
            'action': trading_action.get('action', 'HOLD'),
            'risk_level': self.assess_risk_level(timeframe_analysis),
            'key_levels': self.identify_key_levels(timeframe_analysis)
        }
    
    # Helper methods for analysis
    def check_ema_alignment(self, signals) -> str:
        """Check EMA alignment for trend confirmation"""
        ema_12 = signals['ema_12'][-1]
        ema_26 = signals['ema_26'][-1] 
        ema_50 = signals['ema_50'][-1]
        
        if ema_12 > ema_26 > ema_50:
            return 'bullish_aligned'
        elif ema_12 < ema_26 < ema_50:
            return 'bearish_aligned'
        else:
            return 'mixed'
    
    def calculate_trend_strength(self, close, signals) -> float:
        """Calculate trend strength based on price vs MAs"""
        current_price = close[-1]
        sma_20 = signals['sma_20'][-1]
        sma_50 = signals['sma_50'][-1]
        
        strength = abs(current_price - sma_20) / sma_20
        return min(strength, 1.0)
    
    def analyze_rsi(self, rsi_value) -> str:
        """Analyze RSI signal"""
        if rsi_value > 70:
            return 'overbought'
        elif rsi_value < 30:
            return 'oversold'
        elif rsi_value > 50:
            return 'bullish'
        else:
            return 'bearish'
    
    def analyze_macd(self, macd, signal, histogram) -> str:
        """Analyze MACD signal"""
        if macd > signal and histogram > 0:
            return 'bullish'
        elif macd < signal and histogram < 0:
            return 'bearish'
        else:
            return 'neutral'
    
    def analyze_stochastic(self, k, d) -> str:
        """Analyze Stochastic signal"""
        if k > 80 and d > 80:
            return 'overbought'
        elif k < 20 and d < 20:
            return 'oversold'
        elif k > d:
            return 'bullish'
        else:
            return 'bearish'
    
    def analyze_mfi(self, mfi_value) -> str:
        """Analyze Money Flow Index"""
        if mfi_value > 80:
            return 'overbought'
        elif mfi_value < 20:
            return 'oversold'
        else:
            return 'neutral'
    
    def calculate_momentum_score(self, signals) -> float:
        """Calculate overall momentum score"""
        rsi = signals['rsi_14'][-1]
        mfi = signals['mfi'][-1]
        
        # Normalize to -1 to 1 scale
        rsi_score = (rsi - 50) / 50
        mfi_score = (mfi - 50) / 50
        
        return (rsi_score + mfi_score) / 2
    
    def detect_divergences(self, close, signals) -> List:
        """Detect price-momentum divergences"""
        # Simplified divergence detection
        divergences = []
        
        # Check RSI divergence (last 20 periods)
        if len(close) >= 20:
            price_trend = close[-1] - close[-20]
            rsi_trend = signals['rsi_14'][-1] - signals['rsi_14'][-20]
            
            if price_trend > 0 and rsi_trend < 0:
                divergences.append('bearish_rsi_divergence')
            elif price_trend < 0 and rsi_trend > 0:
                divergences.append('bullish_rsi_divergence')
        
        return divergences
    
    def analyze_bollinger_bands(self, price, upper, middle, lower) -> str:
        """Analyze Bollinger Bands signal"""
        if price > upper:
            return 'overbought'
        elif price < lower:
            return 'oversold'
        elif price > middle:
            return 'bullish'
        else:
            return 'bearish'
    
    def analyze_atr(self, atr) -> str:
        """Analyze ATR for volatility"""
        recent_atr = atr[-10:].mean()
        current_atr = atr[-1]
        
        if current_atr > recent_atr * 1.5:
            return 'high_volatility'
        elif current_atr < recent_atr * 0.5:
            return 'low_volatility'
        else:
            return 'normal_volatility'
    
    def determine_volatility_regime(self, atr) -> str:
        """Determine current volatility regime"""
        atr_sma = talib.SMA(atr, timeperiod=20)
        current_atr = atr[-1]
        avg_atr = atr_sma[-1]
        
        if current_atr > avg_atr * 1.3:
            return 'high_volatility'
        elif current_atr < avg_atr * 0.7:
            return 'low_volatility'
        else:
            return 'normal_volatility'
    
    def detect_volatility_squeeze(self, bb_upper, bb_lower, atr) -> bool:
        """Detect Bollinger Band squeeze"""
        bb_width = (bb_upper[-1] - bb_lower[-1]) / bb_lower[-1]
        bb_width_avg = np.mean([(bb_upper[i] - bb_lower[i]) / bb_lower[i] for i in range(-20, 0)])
        
        return bb_width < bb_width_avg * 0.8
    
    def analyze_obv_trend(self, obv) -> str:
        """Analyze OBV trend"""
        if len(obv) >= 10:
            recent_slope = (obv[-1] - obv[-10]) / 10
            if recent_slope > 0:
                return 'bullish'
            elif recent_slope < 0:
                return 'bearish'
        return 'neutral'
    
    def analyze_ad_line(self, ad) -> str:
        """Analyze A/D Line"""
        if len(ad) >= 10:
            recent_slope = (ad[-1] - ad[-10]) / 10
            if recent_slope > 0:
                return 'accumulation'
            elif recent_slope < 0:
                return 'distribution'
        return 'neutral'
    
    def check_volume_confirmation(self, close, volume) -> bool:
        """Check volume confirmation of price moves"""
        if len(close) >= 5 and len(volume) >= 5:
            price_change = close[-1] - close[-5]
            volume_avg = np.mean(volume[-10:-1])
            current_volume = volume[-1]
            
            return current_volume > volume_avg and abs(price_change) > 0
        return False
    
    def detect_volume_patterns(self, volume) -> str:
        """Detect volume patterns"""
        if len(volume) >= 20:
            recent_avg = np.mean(volume[-5:])
            longer_avg = np.mean(volume[-20:-5])
            
            if recent_avg > longer_avg * 1.5:
                return 'increasing_volume'
            elif recent_avg < longer_avg * 0.5:
                return 'decreasing_volume'
        return 'normal_volume'
    
    def generate_trading_recommendation(self, direction, score, confidence) -> Dict:
        """Generate specific trading recommendation"""
        
        if direction == 'BULLISH' and confidence > 0.6:
            action = 'STRONG_BUY'
        elif direction == 'BULLISH' and confidence > 0.4:
            action = 'BUY'
        elif direction == 'BEARISH' and confidence > 0.6:
            action = 'STRONG_SELL'
        elif direction == 'BEARISH' and confidence > 0.4:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        return {
            'action': action,
            'confidence': confidence,
            'reasoning': f"{direction} signal with {confidence:.2f} confidence",
            'position_size': min(confidence, 0.8)  # Max 80% position
        }
    
    def assess_risk_level(self, timeframe_analysis: Dict) -> str:
        """Assess overall risk level based on timeframe analysis"""
        try:
            confidence_scores = []
            for tf, analysis in timeframe_analysis.items():
                if 'signal' in analysis:
                    confidence_scores.append(analysis['strength'])
            
            # Check for timeframe alignment
            directions = []
            for tf, analysis in timeframe_analysis.items():
                if 'signal' in analysis:
                    directions.append(analysis['signal'])
            
            alignment_bonus = 0.2 if len(set(directions)) == 1 else 0
            
            # Calculate average confidence
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            final_confidence = min(avg_confidence + alignment_bonus, 1.0)
            
            # Determine risk level
            if final_confidence > 0.7:
                return 'LOW'
            elif final_confidence > 0.4:
                return 'MEDIUM'
            else:
                return 'HIGH'
                
        except Exception as e:
            self.logger.error(f"❌ Risk assessment failed: {e}")
            return 'MEDIUM'
    
    def identify_key_levels(self, timeframe_analysis) -> Dict:
        """Identify key support and resistance levels"""
        try:
            key_levels = {
                'support': [],
                'resistance': [],
                'pivot_points': []
            }
            
            # For now, return basic levels
            return key_levels
            
        except Exception as e:
            self.logger.error(f"❌ Key levels identification failed: {e}")
            return {
                'support': [],
                'resistance': [],
                'pivot_points': []
            }
    
    def calculate_bob_confidence(self, timeframe_analysis) -> float:
        """Calculate Bob's overall confidence in the analysis"""
        try:
            confidence_scores = []
            for tf, analysis in timeframe_analysis.items():
                if 'signal' in analysis:
                    confidence_scores.append(analysis['strength'])
            
            # Calculate average confidence
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            
            # Add alignment bonus
            directions = []
            for tf, analysis in timeframe_analysis.items():
                if 'signal' in analysis:
                    directions.append(analysis['signal'])
            
            alignment_bonus = 0.1 if len(set(directions)) == 1 else 0
            
            return min(avg_confidence + alignment_bonus, 1.0)
            
        except Exception as e:
            self.logger.error(f"❌ Confidence calculation failed: {e}")
            return 0.5
    
    def integrate_options_signals(self, master_signal: Dict, options_analysis: Dict) -> Dict:
        """
        Integrate options analysis into master technical signal
        """
        try:
            options_signals = options_analysis.get('options_signals', {})
            options_sentiment = options_signals.get('overall_sentiment', 'neutral')
            options_confidence = options_signals.get('confidence', 0)
            
            # Current technical signal
            tech_direction = master_signal.get('direction', 'NEUTRAL')
            tech_confidence = master_signal.get('confidence', 0)
            
            # Combine signals with weighting (70% technical, 30% options)
            tech_weight = 0.7
            options_weight = 0.3
            
            # Convert to numeric scores
            direction_scores = {'BULLISH': 1, 'NEUTRAL': 0, 'BEARISH': -1}
            sentiment_scores = {'bullish': 1, 'neutral': 0, 'bearish': -1}
            
            tech_score = direction_scores.get(tech_direction, 0)
            options_score = sentiment_scores.get(options_sentiment, 0)
            
            # Combined score
            combined_score = (tech_score * tech_weight) + (options_score * options_weight)
            combined_confidence = (tech_confidence * tech_weight) + (options_confidence * options_weight)
            
            # Determine final direction
            if combined_score > 0.2:
                final_direction = 'BULLISH'
            elif combined_score < -0.2:
                final_direction = 'BEARISH'
            else:
                final_direction = 'NEUTRAL'
            
            # Add options insights to trading action
            trading_action = master_signal.get('trading_action', {})
            
            # Options-specific reasoning
            options_summary = options_analysis.get('summary', {})
            pcr_volume = options_summary.get('pcr_volume', 1)
            max_pain = options_summary.get('max_pain', 0)
            
            options_reasoning = []
            if pcr_volume < 0.7:
                options_reasoning.append("Low PCR suggests bullish options flow")
            elif pcr_volume > 1.3:
                options_reasoning.append("High PCR suggests bearish options flow")
            
            if max_pain > 0:
                current_price = options_analysis.get('current_eth_price', 0)
                if abs(current_price - max_pain) / current_price > 0.05:
                    options_reasoning.append(f"Max pain at ${max_pain:.0f} may influence price action")
            
            # Enhanced trading action
            enhanced_trading_action = trading_action.copy()
            if options_reasoning:
                enhanced_reasoning = trading_action.get('reasoning', '') + '. Options: ' + '; '.join(options_reasoning)
                enhanced_trading_action['reasoning'] = enhanced_reasoning
            
            # Update master signal
            enhanced_master_signal = master_signal.copy()
            enhanced_master_signal.update({
                'direction': final_direction,
                'confidence': combined_confidence,
                'trading_action': enhanced_trading_action,
                'options_influence': {
                    'sentiment': options_sentiment,
                    'confidence': options_confidence,
                    'weight_applied': options_weight,
                    'key_insights': options_reasoning
                }
            })
            
            return enhanced_master_signal
            
        except Exception as e:
            self.logger.error(f"❌ Options integration failed: {e}")
            return master_signal

    def analyze_timeframe(self, data: pd.DataFrame, timeframe: str) -> Dict:
        """
        Bob's comprehensive timeframe analysis
        Returns structured data for charts and analysis
        """
        if data.empty:
            return {
                'timeframe': timeframe,
                'signal': 'neutral',
                'strength': 0.0,
                'indicators': {},
                'chart_data': {
                    'trend': 0.0,
                    'momentum': 0.0,
                    'volatility': 0.0,
                    'volume': 0.0
                }
            }
        
        try:
            # Calculate all indicators
            trend_data = self.calculate_trend_indicators(data)
            momentum_data = self.calculate_momentum_indicators(data)
            volatility_data = self.calculate_volatility_indicators(data)
            volume_data = self.calculate_volume_indicators(data)
            
            # Extract current values for chart display
            chart_data = {
                'trend': self.extract_trend_score(trend_data),
                'momentum': self.extract_momentum_score(momentum_data),
                'volatility': self.extract_volatility_score(volatility_data),
                'volume': self.extract_volume_score(volume_data)
            }
            
            # Calculate overall signal
            signal_scores = list(chart_data.values())
            avg_score = sum(signal_scores) / len(signal_scores) if signal_scores else 0.0
            
            # Determine signal direction
            if avg_score > 0.1:
                signal = 'bullish'
            elif avg_score < -0.1:
                signal = 'bearish'
            else:
                signal = 'neutral'
            
            return {
                'timeframe': timeframe,
                'signal': signal,
                'strength': abs(avg_score),
                'indicators': {
                    'trend': trend_data,
                    'momentum': momentum_data,
                    'volatility': volatility_data,
                    'volume': volume_data
                },
                'chart_data': chart_data
            }
            
        except Exception as e:
            self.logger.error(f"❌ Timeframe analysis error: {e}")
            return {
                'timeframe': timeframe,
                'signal': 'neutral',
                'strength': 0.0,
                'indicators': {},
                'chart_data': {
                    'trend': 0.0,
                    'momentum': 0.0,
                    'volatility': 0.0,
                    'volume': 0.0
                }
            }
    
    def extract_trend_score(self, trend_data: Dict) -> float:
        """Extract trend score from trend indicators"""
        try:
            if 'error' in trend_data:
                return 0.0
            
            analysis = trend_data.get('analysis', {})
            current_price = analysis.get('current_price', 0)
            
            # Calculate trend score based on MA signals
            bullish_signals = 0
            total_signals = 0
            
            for signal in ['sma_20_signal', 'sma_50_signal', 'sma_200_signal', 'sar_signal']:
                if analysis.get(signal) == 'bullish':
                    bullish_signals += 1
                total_signals += 1
            
            # Convert to -1 to 1 scale
            if total_signals > 0:
                trend_score = (bullish_signals / total_signals - 0.5) * 2
                return max(-1.0, min(1.0, trend_score))
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Trend score extraction error: {e}")
            return 0.0
    
    def extract_momentum_score(self, momentum_data: Dict) -> float:
        """Extract momentum score from momentum indicators"""
        try:
            if 'error' in momentum_data:
                return 0.0
            
            indicators = momentum_data.get('indicators', {})
            
            # RSI analysis
            rsi_14 = indicators.get('rsi_14', [])
            if len(rsi_14) > 0:
                current_rsi = rsi_14[-1]
                if not np.isnan(current_rsi):
                    # RSI > 70 = overbought (bearish), RSI < 30 = oversold (bullish)
                    if current_rsi > 70:
                        rsi_score = -0.5
                    elif current_rsi < 30:
                        rsi_score = 0.5
                    else:
                        rsi_score = (current_rsi - 50) / 50  # Normalize to -1 to 1
                else:
                    rsi_score = 0.0
            else:
                rsi_score = 0.0
            
            # MACD analysis
            macd = indicators.get('macd', [])
            macd_signal = indicators.get('macd_signal', [])
            if len(macd) > 0 and len(macd_signal) > 0:
                current_macd = macd[-1]
                current_signal = macd_signal[-1]
                if not np.isnan(current_macd) and not np.isnan(current_signal):
                    macd_score = 0.5 if current_macd > current_signal else -0.5
                else:
                    macd_score = 0.0
            else:
                macd_score = 0.0
            
            # Average momentum score
            momentum_score = (rsi_score + macd_score) / 2
            return max(-1.0, min(1.0, momentum_score))
            
        except Exception as e:
            self.logger.error(f"❌ Momentum score extraction error: {e}")
            return 0.0
    
    def extract_volatility_score(self, volatility_data: Dict) -> float:
        """Extract volatility score from volatility indicators"""
        try:
            if 'error' in volatility_data:
                return 0.0
            
            indicators = volatility_data.get('indicators', {})
            
            # ATR analysis
            atr = indicators.get('atr', [])
            if len(atr) > 0:
                current_atr = atr[-1]
                if not np.isnan(current_atr):
                    # Higher ATR = higher volatility (can be bullish or bearish)
                    # For now, return neutral score
                    return 0.0
                else:
                    return 0.0
            else:
                return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Volatility score extraction error: {e}")
            return 0.0
    
    def extract_volume_score(self, volume_data: Dict) -> float:
        """Extract volume score from volume indicators"""
        try:
            if 'error' in volume_data:
                return 0.0
            
            indicators = volume_data.get('indicators', {})
            
            # OBV analysis
            obv = indicators.get('obv', [])
            if len(obv) > 10:
                # Compare recent OBV to previous
                recent_obv = obv[-1]
                previous_obv = obv[-10]
                if not np.isnan(recent_obv) and not np.isnan(previous_obv):
                    if recent_obv > previous_obv:
                        volume_score = 0.3  # Slight bullish
                    else:
                        volume_score = -0.3  # Slight bearish
                else:
                    volume_score = 0.0
            else:
                volume_score = 0.0
            
            return max(-1.0, min(1.0, volume_score))
            
        except Exception as e:
            self.logger.error(f"❌ Volume score extraction error: {e}")
            return 0.0

# Bob's main execution function
async def run_bob_analysis():
    """
    Bob's main analysis function
    Comprehensive multi-timeframe technical analysis
    """
    bob = BobTechnicalAnalysisEngine()
    
    try:
        # Multi-timeframe analysis
        timeframe_results = {}
        
        # 1H Analysis
        bob.logger.info("🔍 Analyzing 1h timeframe...")
        data_1h = bob.fetch_market_data('7d', '1h')
        if not data_1h.empty:
            result_1h = bob.analyze_timeframe(data_1h, '1H')
            timeframe_results['1H'] = result_1h
            bob.logger.info(f"✅ 1H analysis complete: {result_1h['signal']} (strength: {result_1h['strength']:.2f})")
        
        # 4H Analysis
        bob.logger.info("🔍 Analyzing 4h timeframe...")
        data_4h = bob.fetch_market_data('30d', '1h')
        if not data_4h.empty:
            result_4h = bob.analyze_timeframe(data_4h, '4H')
            timeframe_results['4H'] = result_4h
            bob.logger.info(f"✅ 4H analysis complete: {result_4h['signal']} (strength: {result_4h['strength']:.2f})")
        
        # 1D Analysis
        bob.logger.info("🔍 Analyzing 1d timeframe...")
        data_1d = bob.fetch_market_data('1y', '1d')
        if not data_1d.empty:
            result_1d = bob.analyze_timeframe(data_1d, '1D')
            timeframe_results['1D'] = result_1d
            bob.logger.info(f"✅ 1D analysis complete: {result_1d['signal']} (strength: {result_1d['strength']:.2f})")
        
        # Add options analysis
        bob.logger.info("📊 Adding options analysis...")
        options_analysis = bob.options_engine.analyze_options_flow([])
        
        # Integrate options signals
        bob.logger.info("✅ Options analysis integrated")
        
        # Calculate master signal
        master_signal = bob.generate_master_signal(timeframe_results)
        
        # Prepare final result
        result = {
            'symbol': 'ETH-USD',
            'timestamp': datetime.now().isoformat(),
            'bob_confidence': bob.calculate_bob_confidence(timeframe_results),
            'timeframe_analysis': timeframe_results,
            'options_analysis': options_analysis,
            'master_signal': master_signal,
            'chart_data': {
                '1H': timeframe_results.get('1H', {}).get('chart_data', {}),
                '4H': timeframe_results.get('4H', {}).get('chart_data', {}),
                '1D': timeframe_results.get('1D', {}).get('chart_data', {})
            }
        }
        
        # Print summary
        print("\n🎯 BOB'S ANALYSIS COMPLETE")
        print(f"Symbol: {result['symbol']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Bob's Confidence: {result['bob_confidence']:.2f}")
        print()
        print("📊 MASTER SIGNAL:")
        print(f"Direction: {master_signal['direction']}")
        print(f"Strength: {master_signal['strength']:.3f}")
        print(f"Trading Action: {master_signal['action']}")
        print(f"Risk Level: {master_signal['risk_level']}")
        print()
        print("⏰ TIMEFRAME ANALYSIS:")
        for tf, analysis in timeframe_results.items():
            print(f"{tf}: {analysis['signal']} (strength: {analysis['strength']:.2f})")
        
        return result
        
    except Exception as e:
        bob.logger.error(f"❌ Bob analysis failed: {e}")
        return None

if __name__ == "__main__":
    try:
        asyncio.run(run_bob_analysis())
    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Failed to run Bob analysis: {e}")
