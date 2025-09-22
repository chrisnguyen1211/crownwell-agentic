#!/usr/bin/env python3
"""
Options and Open Interest Data Tracker for Yasuo
"""
import requests
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

class OptionsTracker:
    """
    Track ETH options and open interest data
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Deribit API (Free tier available)
        self.deribit_base_url = "https://www.deribit.com/api/v2"
        
        # Binance API (Free tier available)
        self.binance_base_url = "https://fapi.binance.com/fapi/v1"
        
        # CoinGecko API (Free tier available)
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
    
    def get_eth_options_data(self) -> Dict[str, Any]:
        """
        Get ETH options data from Deribit
        """
        try:
            # Get ETH options from Deribit
            url = f"{self.deribit_base_url}/public/get_instruments"
            params = {
                "currency": "ETH",
                "kind": "option",
                "expired": False
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                instruments = data.get("result", [])
                
                # Analyze options data
                options_analysis = self._analyze_options_data(instruments)
                
                # Get open interest
                open_interest = self._get_open_interest()
                
                return {
                    "options_instruments": len(instruments),
                    "options_analysis": options_analysis,
                    "open_interest": open_interest,
                    "data_source": "deribit",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                self.logger.warning(f"Deribit API error: {response.status_code}")
                return self._get_fallback_options_data()
                
        except Exception as e:
            self.logger.error(f"Error getting options data: {e}")
            return self._get_fallback_options_data()
    
    def _analyze_options_data(self, instruments: list) -> Dict[str, Any]:
        """
        Analyze options instruments for market sentiment
        """
        if not instruments:
            return {}
        
        # Count calls vs puts
        calls = [inst for inst in instruments if inst.get("option_type") == "call"]
        puts = [inst for inst in instruments if inst.get("option_type") == "put"]
        
        # Calculate put/call ratio
        put_call_ratio = len(puts) / len(calls) if calls else 0
        
        # Analyze strike prices
        current_price = 4000  # Approximate ETH price
        itm_calls = [inst for inst in calls if inst.get("strike", 0) < current_price]
        otm_calls = [inst for inst in calls if inst.get("strike", 0) > current_price]
        itm_puts = [inst for inst in puts if inst.get("strike", 0) > current_price]
        otm_puts = [inst for inst in puts if inst.get("strike", 0) < current_price]
        
        return {
            "total_instruments": len(instruments),
            "calls": len(calls),
            "puts": len(puts),
            "put_call_ratio": put_call_ratio,
            "itm_calls": len(itm_calls),
            "otm_calls": len(otm_calls),
            "itm_puts": len(itm_puts),
            "otm_puts": len(otm_puts),
            "sentiment": "bullish" if put_call_ratio < 0.7 else "bearish" if put_call_ratio > 1.3 else "neutral"
        }
    
    def _get_open_interest(self) -> Dict[str, Any]:
        """
        Get open interest data from Binance
        """
        try:
            # Get ETH perpetual open interest
            url = f"{self.binance_base_url}/openInterest"
            params = {"symbol": "ETHUSDT"}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "symbol": data.get("symbol", "ETHUSDT"),
                    "open_interest": float(data.get("openInterest", 0)),
                    "open_interest_value": float(data.get("openInterest", 0)) * 4000,  # Approximate ETH price
                    "data_source": "binance"
                }
            else:
                return self._get_fallback_open_interest()
                
        except Exception as e:
            self.logger.error(f"Error getting open interest: {e}")
            return self._get_fallback_open_interest()
    
    def _get_fallback_options_data(self) -> Dict[str, Any]:
        """
        Fallback options data when API fails
        """
        return {
            "options_instruments": 0,
            "options_analysis": {
                "total_instruments": 0,
                "calls": 0,
                "puts": 0,
                "put_call_ratio": 0,
                "sentiment": "unknown"
            },
            "open_interest": self._get_fallback_open_interest(),
            "data_source": "fallback",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_fallback_open_interest(self) -> Dict[str, Any]:
        """
        Fallback open interest data
        """
        return {
            "symbol": "ETHUSDT",
            "open_interest": 0,
            "open_interest_value": 0,
            "data_source": "fallback"
        }
    
    def get_futures_data(self) -> Dict[str, Any]:
        """
        Get ETH futures data including funding rates
        """
        try:
            # Get ETH perpetual funding rate
            url = f"{self.binance_base_url}/premiumIndex"
            params = {"symbol": "ETHUSDT"}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                funding_rate = float(data.get("lastFundingRate", 0))
                
                return {
                    "symbol": "ETHUSDT",
                    "funding_rate": funding_rate,
                    "funding_rate_percent": funding_rate * 100,
                    "next_funding_time": data.get("nextFundingTime", 0),
                    "mark_price": float(data.get("markPrice", 0)),
                    "index_price": float(data.get("indexPrice", 0)),
                    "contango_backwardation": "contango" if funding_rate > 0 else "backwardation",
                    "data_source": "binance",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return self._get_fallback_futures_data()
                
        except Exception as e:
            self.logger.error(f"Error getting futures data: {e}")
            return self._get_fallback_futures_data()
    
    def _get_fallback_futures_data(self) -> Dict[str, Any]:
        """
        Fallback futures data
        """
        return {
            "symbol": "ETHUSDT",
            "funding_rate": 0,
            "funding_rate_percent": 0,
            "contango_backwardation": "unknown",
            "data_source": "fallback",
            "timestamp": datetime.now().isoformat()
        }

# Test the options tracker
if __name__ == "__main__":
    print("🔍 TESTING OPTIONS TRACKER")
    print("=" * 50)
    
    tracker = OptionsTracker()
    
    # Test options data
    print("Test 1: ETH Options Data")
    options_data = tracker.get_eth_options_data()
    print(f"✅ Options Instruments: {options_data.get('options_instruments', 0)}")
    print(f"✅ Data Source: {options_data.get('data_source', 'Unknown')}")
    
    analysis = options_data.get('options_analysis', {})
    print(f"✅ Calls: {analysis.get('calls', 0)}")
    print(f"✅ Puts: {analysis.get('puts', 0)}")
    print(f"✅ Put/Call Ratio: {analysis.get('put_call_ratio', 0):.2f}")
    print(f"✅ Sentiment: {analysis.get('sentiment', 'Unknown')}")
    
    open_interest = options_data.get('open_interest', {})
    print(f"✅ Open Interest: {open_interest.get('open_interest', 0):,.0f} ETH")
    print(f"✅ OI Value: ${open_interest.get('open_interest_value', 0):,.0f}")
    
    print("\n" + "=" * 50)
    
    # Test futures data
    print("Test 2: ETH Futures Data")
    futures_data = tracker.get_futures_data()
    print(f"✅ Funding Rate: {futures_data.get('funding_rate_percent', 0):.4f}%")
    print(f"✅ Contango/Backwardation: {futures_data.get('contango_backwardation', 'Unknown')}")
    print(f"✅ Mark Price: ${futures_data.get('mark_price', 0):,.2f}")
    print(f"✅ Data Source: {futures_data.get('data_source', 'Unknown')}")
    
    print("\n" + "=" * 50)
    print("🎯 MARKET INTERPRETATION:")
    
    put_call_ratio = analysis.get('put_call_ratio', 0)
    funding_rate = futures_data.get('funding_rate_percent', 0)
    
    if put_call_ratio < 0.7 and funding_rate < 0.01:
        print("🟢 BULLISH: Low put/call ratio + Low funding rate")
    elif put_call_ratio > 1.3 and funding_rate > 0.01:
        print("🔴 BEARISH: High put/call ratio + High funding rate")
    else:
        print("⚪ NEUTRAL: Mixed options signals")












