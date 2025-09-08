#!/usr/bin/env python3
"""
📊 BOB'S OPTIONS ANALYSIS ENGINE
Advanced Options Interest & Derivatives Analysis for ETH
Institutional-grade options flow analysis
"""

import numpy as np
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import asyncio
import aiohttp

class BobOptionsAnalysisEngine:
    """
    Bob's Options Analysis Engine
    Advanced options interest analysis for ETH derivatives
    """
    
    def __init__(self):
        self.setup_logging()
        
        # Options data sources
        self.data_sources = {
            'deribit': {
                'base_url': 'https://www.deribit.com/api/v2',
                'instrument': 'ETH',
                'supported': ['options', 'futures']
            },
            'binance': {
                'base_url': 'https://eapi.binance.com',
                'instrument': 'ETH',
                'supported': ['options']
            },
            'okx': {
                'base_url': 'https://www.okx.com/api/v5',
                'instrument': 'ETH-USD',
                'supported': ['options', 'futures']
            }
        }
        
        # Options analysis parameters
        self.analysis_params = {
            'min_volume': 10,  # Minimum volume for significant options
            'max_dte': 90,     # Maximum days to expiration
            'min_oi': 50,      # Minimum open interest
            'significance_threshold': 0.1  # 10% of total volume
        }
        
        self.logger.info("📊 Bob Options Analysis Engine initialized")
    
    def setup_logging(self):
        """Setup logging for options analysis"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def fetch_deribit_options_data(self) -> Dict:
        """
        Fetch ETH options data from Deribit
        Primary source for ETH options analysis
        """
        try:
            self.logger.info("📊 Fetching Deribit ETH options data...")
            
            async with aiohttp.ClientSession() as session:
                # Get all ETH options instruments
                instruments_url = f"{self.data_sources['deribit']['base_url']}/public/get_instruments"
                params = {
                    'currency': 'ETH',
                    'kind': 'option',
                    'expired': 'false'
                }
                
                async with session.get(instruments_url, params=params) as response:
                    instruments_data = await response.json()
                
                if 'result' not in instruments_data:
                    raise ValueError("No instruments data received")
                
                instruments = instruments_data['result']
                self.logger.info(f"✅ Found {len(instruments)} ETH options instruments")
                
                # Get options data for each instrument
                options_data = []
                
                for instrument in instruments[:50]:  # Limit to top 50 for performance
                    instrument_name = instrument['instrument_name']
                    
                    # Get order book for each option
                    orderbook_url = f"{self.data_sources['deribit']['base_url']}/public/get_order_book"
                    ob_params = {'instrument_name': instrument_name}
                    
                    try:
                        async with session.get(orderbook_url, params=ob_params) as ob_response:
                            orderbook_data = await ob_response.json()
                        
                        if 'result' in orderbook_data:
                            result = orderbook_data['result']
                            
                            option_info = {
                                'instrument_name': instrument_name,
                                'strike_price': instrument.get('strike'),
                                'option_type': instrument.get('option_type'),  # call/put
                                'expiration_timestamp': instrument.get('expiration_timestamp'),
                                'bid_price': result.get('best_bid_price', 0),
                                'ask_price': result.get('best_ask_price', 0),
                                'bid_size': result.get('best_bid_amount', 0),
                                'ask_size': result.get('best_ask_amount', 0),
                                'mark_price': result.get('mark_price', 0),
                                'open_interest': result.get('open_interest', 0),
                                'volume_24h': result.get('stats', {}).get('volume', 0),
                                'implied_volatility': result.get('mark_iv', 0),
                                'delta': result.get('greeks', {}).get('delta', 0),
                                'gamma': result.get('greeks', {}).get('gamma', 0),
                                'theta': result.get('greeks', {}).get('theta', 0),
                                'vega': result.get('greeks', {}).get('vega', 0)
                            }
                            
                            options_data.append(option_info)
                    
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error fetching {instrument_name}: {e}")
                        continue
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                
                return {
                    'source': 'deribit',
                    'timestamp': datetime.now().isoformat(),
                    'total_instruments': len(instruments),
                    'analyzed_instruments': len(options_data),
                    'options_data': options_data
                }
        
        except Exception as e:
            self.logger.error(f"❌ Deribit options fetch failed: {e}")
            return {'error': str(e)}
    
    def analyze_options_flow(self, options_data: List[Dict]) -> Dict:
        """
        Analyze options flow for trading insights
        """
        if not options_data:
            return {'error': 'No options data to analyze'}
        
        try:
            df = pd.DataFrame(options_data)
            
            # Filter significant options
            df_filtered = df[
                (df['volume_24h'] >= self.analysis_params['min_volume']) &
                (df['open_interest'] >= self.analysis_params['min_oi'])
            ]
            
            if df_filtered.empty:
                return {'error': 'No significant options found'}
            
            # Calculate expiration dates
            df_filtered['expiration_date'] = pd.to_datetime(df_filtered['expiration_timestamp'], unit='ms')
            df_filtered['days_to_expiration'] = (df_filtered['expiration_date'] - datetime.now()).dt.days
            
            # Filter by DTE
            df_filtered = df_filtered[df_filtered['days_to_expiration'] <= self.analysis_params['max_dte']]
            
            # Separate calls and puts
            calls = df_filtered[df_filtered['option_type'] == 'call']
            puts = df_filtered[df_filtered['option_type'] == 'put']
            
            # Volume analysis
            total_call_volume = calls['volume_24h'].sum()
            total_put_volume = puts['volume_24h'].sum()
            total_volume = total_call_volume + total_put_volume
            
            # Open Interest analysis
            total_call_oi = calls['open_interest'].sum()
            total_put_oi = puts['open_interest'].sum()
            total_oi = total_call_oi + total_put_oi
            
            # Put/Call ratios
            pcr_volume = total_put_volume / total_call_volume if total_call_volume > 0 else 0
            pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            # Strike analysis
            call_strikes = calls['strike_price'].value_counts()
            put_strikes = puts['strike_price'].value_counts()
            
            # Most active strikes
            most_active_call_strike = call_strikes.index[0] if not call_strikes.empty else 0
            most_active_put_strike = put_strikes.index[0] if not put_strikes.empty else 0
            
            # Implied Volatility analysis
            avg_iv_calls = calls['implied_volatility'].mean() if not calls.empty else 0
            avg_iv_puts = puts['implied_volatility'].mean() if not puts.empty else 0
            
            # Greeks analysis
            total_delta = df_filtered['delta'].sum()
            total_gamma = df_filtered['gamma'].sum()
            
            # Max pain calculation (approximate)
            max_pain_strike = self.calculate_max_pain(df_filtered)
            
            return {
                'volume_analysis': {
                    'total_volume': total_volume,
                    'call_volume': total_call_volume,
                    'put_volume': total_put_volume,
                    'pcr_volume': pcr_volume
                },
                'open_interest_analysis': {
                    'total_oi': total_oi,
                    'call_oi': total_call_oi,
                    'put_oi': total_put_oi,
                    'pcr_oi': pcr_oi
                },
                'strike_analysis': {
                    'most_active_call_strike': most_active_call_strike,
                    'most_active_put_strike': most_active_put_strike,
                    'max_pain_strike': max_pain_strike
                },
                'volatility_analysis': {
                    'avg_iv_calls': avg_iv_calls,
                    'avg_iv_puts': avg_iv_puts,
                    'iv_skew': avg_iv_puts - avg_iv_calls
                },
                'greeks_analysis': {
                    'total_delta': total_delta,
                    'total_gamma': total_gamma,
                    'delta_neutral_level': self.calculate_delta_neutral_level(df_filtered)
                }
            }
        
        except Exception as e:
            self.logger.error(f"❌ Options flow analysis failed: {e}")
            return {'error': str(e)}
    
    def calculate_max_pain(self, df: pd.DataFrame) -> float:
        """
        Calculate max pain level for options
        """
        try:
            if df.empty:
                return 0
            
            # Get unique strikes
            strikes = sorted(df['strike_price'].unique())
            
            max_pain_values = {}
            
            for strike in strikes:
                total_pain = 0
                
                # Calculate pain for each option at this strike level
                for _, option in df.iterrows():
                    option_strike = option['strike_price']
                    option_type = option['option_type']
                    oi = option['open_interest']
                    
                    if option_type == 'call' and strike > option_strike:
                        # ITM call pain
                        total_pain += (strike - option_strike) * oi
                    elif option_type == 'put' and strike < option_strike:
                        # ITM put pain
                        total_pain += (option_strike - strike) * oi
                
                max_pain_values[strike] = total_pain
            
            # Find strike with maximum pain
            if max_pain_values:
                max_pain_strike = max(max_pain_values, key=max_pain_values.get)
                return max_pain_strike
            
            return 0
        
        except Exception as e:
            self.logger.error(f"❌ Max pain calculation failed: {e}")
            return 0
    
    def calculate_delta_neutral_level(self, df: pd.DataFrame) -> float:
        """
        Calculate delta neutral level
        """
        try:
            if df.empty:
                return 0
            
            # Weighted average strike by delta and OI
            weighted_strikes = []
            weights = []
            
            for _, option in df.iterrows():
                strike = option['strike_price']
                delta = abs(option['delta'])
                oi = option['open_interest']
                
                if delta > 0 and oi > 0:
                    weighted_strikes.append(strike)
                    weights.append(delta * oi)
            
            if weights:
                delta_neutral = np.average(weighted_strikes, weights=weights)
                return delta_neutral
            
            return 0
        
        except Exception as e:
            self.logger.error(f"❌ Delta neutral calculation failed: {e}")
            return 0
    
    def generate_options_signals(self, analysis: Dict, current_price: float) -> Dict:
        """
        Generate trading signals from options analysis
        """
        try:
            signals = {
                'bullish_signals': [],
                'bearish_signals': [],
                'neutral_signals': [],
                'overall_sentiment': 'neutral',
                'confidence': 0.0
            }
            
            if 'error' in analysis:
                return signals
            
            vol_analysis = analysis.get('volume_analysis', {})
            oi_analysis = analysis.get('open_interest_analysis', {})
            strike_analysis = analysis.get('strike_analysis', {})
            iv_analysis = analysis.get('volatility_analysis', {})
            
            # PCR Analysis
            pcr_volume = vol_analysis.get('pcr_volume', 1)
            pcr_oi = oi_analysis.get('pcr_oi', 1)
            
            if pcr_volume < 0.7:  # Low PCR = bullish
                signals['bullish_signals'].append('Low Put/Call Ratio (Volume)')
            elif pcr_volume > 1.3:  # High PCR = bearish
                signals['bearish_signals'].append('High Put/Call Ratio (Volume)')
            
            if pcr_oi < 0.7:
                signals['bullish_signals'].append('Low Put/Call Ratio (OI)')
            elif pcr_oi > 1.3:
                signals['bearish_signals'].append('High Put/Call Ratio (OI)')
            
            # Max Pain Analysis
            max_pain = strike_analysis.get('max_pain_strike', 0)
            if max_pain > 0:
                if current_price < max_pain * 0.95:
                    signals['bullish_signals'].append('Price below Max Pain - potential upward pull')
                elif current_price > max_pain * 1.05:
                    signals['bearish_signals'].append('Price above Max Pain - potential downward pull')
                else:
                    signals['neutral_signals'].append('Price near Max Pain - sideways pressure')
            
            # IV Skew Analysis
            iv_skew = iv_analysis.get('iv_skew', 0)
            if iv_skew > 0.1:  # Put skew
                signals['bearish_signals'].append('Put skew - fear premium')
            elif iv_skew < -0.1:  # Call skew
                signals['bullish_signals'].append('Call skew - greed premium')
            
            # Delta Analysis
            greeks = analysis.get('greeks_analysis', {})
            total_delta = greeks.get('total_delta', 0)
            
            if total_delta > 1000:  # Net long delta
                signals['bullish_signals'].append('Net long delta position')
            elif total_delta < -1000:  # Net short delta
                signals['bearish_signals'].append('Net short delta position')
            
            # Overall sentiment
            bullish_count = len(signals['bullish_signals'])
            bearish_count = len(signals['bearish_signals'])
            
            if bullish_count > bearish_count:
                signals['overall_sentiment'] = 'bullish'
                signals['confidence'] = min((bullish_count / (bullish_count + bearish_count)), 0.8)
            elif bearish_count > bullish_count:
                signals['overall_sentiment'] = 'bearish'
                signals['confidence'] = min((bearish_count / (bullish_count + bearish_count)), 0.8)
            else:
                signals['overall_sentiment'] = 'neutral'
                signals['confidence'] = 0.3
            
            return signals
        
        except Exception as e:
            self.logger.error(f"❌ Options signals generation failed: {e}")
            return {'error': str(e)}
    
    async def run_comprehensive_options_analysis(self, current_eth_price: float) -> Dict:
        """
        Run comprehensive options analysis
        """
        self.logger.info("📊 Starting comprehensive options analysis...")
        
        try:
            # Fetch options data
            options_data = await self.fetch_deribit_options_data()
            
            if 'error' in options_data:
                return options_data
            
            # Analyze options flow
            flow_analysis = self.analyze_options_flow(options_data['options_data'])
            
            if 'error' in flow_analysis:
                return flow_analysis
            
            # Generate signals
            signals = self.generate_options_signals(flow_analysis, current_eth_price)
            
            # Combine all analysis
            comprehensive_analysis = {
                'timestamp': datetime.now().isoformat(),
                'data_source': options_data['source'],
                'current_eth_price': current_eth_price,
                'instruments_analyzed': options_data['analyzed_instruments'],
                'options_flow': flow_analysis,
                'options_signals': signals,
                'summary': {
                    'pcr_volume': flow_analysis.get('volume_analysis', {}).get('pcr_volume', 0),
                    'pcr_oi': flow_analysis.get('open_interest_analysis', {}).get('pcr_oi', 0),
                    'max_pain': flow_analysis.get('strike_analysis', {}).get('max_pain_strike', 0),
                    'iv_skew': flow_analysis.get('volatility_analysis', {}).get('iv_skew', 0),
                    'overall_sentiment': signals.get('overall_sentiment', 'neutral'),
                    'confidence': signals.get('confidence', 0)
                }
            }
            
            return comprehensive_analysis
        
        except Exception as e:
            self.logger.error(f"❌ Comprehensive options analysis failed: {e}")
            return {'error': str(e)}

# Test function
async def test_options_analysis():
    """Test Bob's options analysis"""
    
    print("📊 TESTING BOB'S OPTIONS ANALYSIS ENGINE")
    print("=" * 60)
    
    # Initialize options engine
    options_engine = BobOptionsAnalysisEngine()
    
    # Current ETH price (would get from main system)
    current_eth_price = 4300.0
    
    try:
        # Run analysis
        analysis = await options_engine.run_comprehensive_options_analysis(current_eth_price)
        
        if 'error' not in analysis:
            print("✅ Options analysis completed successfully!")
            
            summary = analysis['summary']
            print(f"\n📊 OPTIONS ANALYSIS SUMMARY:")
            print(f"PCR Volume: {summary['pcr_volume']:.3f}")
            print(f"PCR Open Interest: {summary['pcr_oi']:.3f}")
            print(f"Max Pain Strike: ${summary['max_pain']:.0f}")
            print(f"IV Skew: {summary['iv_skew']:.3f}")
            print(f"Overall Sentiment: {summary['overall_sentiment']}")
            print(f"Confidence: {summary['confidence']:.2f}")
            
            signals = analysis['options_signals']
            if signals.get('bullish_signals'):
                print(f"\n🐂 Bullish Signals:")
                for signal in signals['bullish_signals']:
                    print(f"   • {signal}")
            
            if signals.get('bearish_signals'):
                print(f"\n🐻 Bearish Signals:")
                for signal in signals['bearish_signals']:
                    print(f"   • {signal}")
        
        else:
            print(f"❌ Analysis failed: {analysis['error']}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_options_analysis())
