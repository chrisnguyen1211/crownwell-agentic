#!/usr/bin/env python3
"""
Yasuo Trend Tracking System
Tracks historical data to identify short-term trends
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics
import logging

@dataclass
class DataSnapshot:
    """Single data point for trend analysis"""
    timestamp: str
    exchange_net_flow: float
    etf_daily_flow: float  
    liveliness_score: float
    large_transfers_count: int
    total_exchanges: int
    total_volume: float

@dataclass 
class TrendAnalysis:
    """Trend analysis results"""
    trend_direction: str  # "bullish", "bearish", "neutral"
    trend_strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    key_indicators: List[str]
    sample_count: int
    timeframe_hours: int
    recommendation: str

class YasuoTrendTracker:
    """
    Tracks and analyzes trends in Yasuo market data
    """
    
    def __init__(self, data_file: str = "yasuo_trend_data.json"):
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)
        
        # Trend analysis parameters - Optimized for new frequencies
        self.MIN_SAMPLES = 3  # Minimum data points for trend analysis (reduced)
        self.MAX_SAMPLES = 48  # Maximum samples to keep (48 x 30min = 24 hours)
        self.TREND_LOOKBACK_HOURS = 12  # Look back 12 hours for trend (longer timeframe)
        
        # Initialize data storage
        self.historical_data: List[DataSnapshot] = []
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.historical_data = [DataSnapshot(**item) for item in data]
                    self.logger.info(f"Loaded {len(self.historical_data)} historical data points")
            else:
                self.historical_data = []
                self.logger.info("No historical data file found - starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            self.historical_data = []
    
    def save_historical_data(self):
        """Save historical data to file"""
        try:
            data = [asdict(snapshot) for snapshot in self.historical_data]
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Saved {len(self.historical_data)} data points")
        except Exception as e:
            self.logger.error(f"Error saving historical data: {e}")
    
    def add_data_point(self, exchange_flows: Dict, etf_flows: Dict, liveliness: Dict):
        """Add new data point to historical tracking"""
        snapshot = DataSnapshot(
            timestamp=datetime.now().isoformat(),
            exchange_net_flow=exchange_flows.get('net_flow', 0),
            etf_daily_flow=etf_flows.get('daily_flow', 0),
            liveliness_score=liveliness.get('liveliness_score', 0.5),
            large_transfers_count=exchange_flows.get('large_transfers_count', 0),
            total_exchanges=exchange_flows.get('total_exchanges_analyzed', 0),
            total_volume=exchange_flows.get('total_volume', 0)
        )
        
        # Add to historical data
        self.historical_data.append(snapshot)
        
        # Keep only recent data (rolling window)
        if len(self.historical_data) > self.MAX_SAMPLES:
            self.historical_data = self.historical_data[-self.MAX_SAMPLES:]
        
        # Save to file
        self.save_historical_data()
        
        self.logger.info(f"Added data point. Total samples: {len(self.historical_data)}")
    
    def get_trend_analysis(self) -> Optional[TrendAnalysis]:
        """Analyze trends in historical data"""
        
        # Check if we have enough data
        if len(self.historical_data) < self.MIN_SAMPLES:
            self.logger.warning(f"Insufficient data for trend analysis. Need {self.MIN_SAMPLES}, have {len(self.historical_data)}")
            return None
        
        # Get recent data for trend analysis
        cutoff_time = datetime.now() - timedelta(hours=self.TREND_LOOKBACK_HOURS)
        cutoff_str = cutoff_time.isoformat()
        
        recent_data = [
            point for point in self.historical_data 
            if point.timestamp >= cutoff_str
        ]
        
        if len(recent_data) < self.MIN_SAMPLES:
            # Use all available data if recent data is insufficient
            recent_data = self.historical_data[-self.MIN_SAMPLES:]
        
        return self._analyze_trend_data(recent_data)
    
    def _analyze_trend_data(self, data_points: List[DataSnapshot]) -> TrendAnalysis:
        """Perform trend analysis on data points"""
        
        # Extract time series for each metric
        exchange_flows = [point.exchange_net_flow for point in data_points]
        etf_flows = [point.etf_daily_flow for point in data_points]
        liveliness_scores = [point.liveliness_score for point in data_points]
        large_transfers = [point.large_transfers_count for point in data_points]
        
        # Calculate trends (linear regression slope)
        exchange_trend = self._calculate_trend_slope(exchange_flows)
        etf_trend = self._calculate_trend_slope(etf_flows)
        liveliness_trend = self._calculate_trend_slope(liveliness_scores)
        transfers_trend = self._calculate_trend_slope(large_transfers)
        
        # Analyze each component
        trend_signals = []
        bullish_signals = 0
        bearish_signals = 0
        
        # Exchange flow trend analysis
        if exchange_trend > 1000:  # Strong positive trend in net outflows
            trend_signals.append("Increasing exchange outflows (accumulation)")
            bullish_signals += 1
        elif exchange_trend < -1000:  # Strong negative trend 
            trend_signals.append("Increasing exchange inflows (selling pressure)")
            bearish_signals += 1
        else:
            trend_signals.append("Stable exchange flows")
        
        # ETF flow trend analysis
        if etf_trend > 10000000:  # $10M+ positive trend
            trend_signals.append("Increasing ETF inflows (institutional buying)")
            bullish_signals += 1
        elif etf_trend < -10000000:  # $10M+ negative trend
            trend_signals.append("Increasing ETF outflows (institutional selling)")
            bearish_signals += 1
        else:
            trend_signals.append("Stable ETF flows")
        
        # Liveliness trend analysis
        if liveliness_trend > 0.05:  # Increasing activity
            trend_signals.append("Increasing holder activity (profit-taking)")
            bearish_signals += 1
        elif liveliness_trend < -0.05:  # Decreasing activity
            trend_signals.append("Decreasing holder activity (accumulation)")
            bullish_signals += 1
        else:
            trend_signals.append("Stable holder activity")
        
        # Large transfers trend
        if transfers_trend > 0.5:
            trend_signals.append("Increasing large transfers (whale activity)")
            bearish_signals += 1
        elif transfers_trend < -0.5:
            trend_signals.append("Decreasing large transfers (calm market)")
            bullish_signals += 1
        
        # Determine overall trend
        if bullish_signals > bearish_signals + 1:
            trend_direction = "bullish"
            trend_strength = min(1.0, (bullish_signals - bearish_signals) / 4)
        elif bearish_signals > bullish_signals + 1:
            trend_direction = "bearish" 
            trend_strength = min(1.0, (bearish_signals - bullish_signals) / 4)
        else:
            trend_direction = "neutral"
            trend_strength = 0.5
        
        # Calculate confidence based on data quality
        confidence = min(1.0, len(data_points) / self.MIN_SAMPLES * 0.8)
        if len(data_points) >= self.MIN_SAMPLES * 2:
            confidence = min(1.0, confidence + 0.2)
        
        # Generate recommendation
        if trend_direction == "bullish" and trend_strength > 0.6:
            recommendation = "BUY - Strong bullish trend detected"
        elif trend_direction == "bearish" and trend_strength > 0.6:
            recommendation = "SELL - Strong bearish trend detected"
        elif trend_direction == "bullish":
            recommendation = "HOLD/BUY - Weak bullish trend"
        elif trend_direction == "bearish":
            recommendation = "HOLD/SELL - Weak bearish trend"
        else:
            recommendation = "HOLD - No clear trend"
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            confidence=confidence,
            key_indicators=trend_signals,
            sample_count=len(data_points),
            timeframe_hours=self.TREND_LOOKBACK_HOURS,
            recommendation=recommendation
        )
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate linear regression slope for trend detection"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope
    
    def get_data_summary(self) -> Dict:
        """Get summary of historical data"""
        if not self.historical_data:
            return {"message": "No historical data available"}
        
        latest = self.historical_data[-1]
        oldest = self.historical_data[0]
        
        return {
            "total_samples": len(self.historical_data),
            "time_range_hours": (datetime.fromisoformat(latest.timestamp) - 
                               datetime.fromisoformat(oldest.timestamp)).total_seconds() / 3600,
            "latest_data": asdict(latest),
            "data_ready_for_analysis": len(self.historical_data) >= self.MIN_SAMPLES,
            "next_sample_needed_in": "Ready for analysis" if len(self.historical_data) >= self.MIN_SAMPLES else f"{self.MIN_SAMPLES - len(self.historical_data)} more samples"
        }
    
    def clear_old_data(self, hours_back: int = 48):
        """Clear data older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        cutoff_str = cutoff_time.isoformat()
        
        original_count = len(self.historical_data)
        self.historical_data = [
            point for point in self.historical_data 
            if point.timestamp >= cutoff_str
        ]
        
        removed_count = original_count - len(self.historical_data)
        if removed_count > 0:
            self.save_historical_data()
            self.logger.info(f"Removed {removed_count} old data points")
        
        return removed_count
