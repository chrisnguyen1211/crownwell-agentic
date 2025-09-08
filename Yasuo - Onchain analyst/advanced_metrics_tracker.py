#!/usr/bin/env python3
"""
Advanced Metrics Tracker for Long-term ETH Strategy
Tracks derivatives, exchange metrics, and long-term holder behavior
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

@dataclass
class OptionsData:
    """ETH Options market data"""
    open_interest: float
    put_call_ratio: float
    max_pain: float
    implied_volatility: float
    expiry_date: str
    data_source: str

@dataclass
class FuturesData:
    """ETH Futures market data"""
    open_interest: float
    funding_rate: float
    basis: float  # Futures price - Spot price
    contango_backwardation: str  # "contango" or "backwardation"
    perpetual_funding_rate: float
    data_source: str

@dataclass
class ExchangeMetrics:
    """Multi-exchange ETH metrics"""
    total_eth_reserves: float
    exchange_reserves_change_7d: float
    stablecoin_supply: float
    stablecoin_flow_24h: float
    dex_volume_24h: float
    cex_volume_24h: float
    dex_cex_ratio: float
    data_source: str

@dataclass
class LongTermHolderData:
    """Long-term holder behavior metrics"""
    lth_supply_1y: float  # Supply held 1+ years
    lth_supply_percentage: float
    coin_days_destroyed: float
    mvrv_ratio: float
    supply_in_profit_ratio: float
    supply_in_loss_ratio: float
    hodler_net_position_change: float
    realized_cap: float
    market_cap: float
    data_source: str

class AdvancedMetricsTracker:
    """
    Tracks advanced metrics for long-term ETH investment strategy
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # API configurations
        self.coinglass_api_key = os.getenv("COINGLASS_API_KEY")  # For options/futures
        self.glassnode_api_key = os.getenv("GLASSNODE_API_KEY")  # For on-chain metrics
        self.dune_api_key = os.getenv("DUNE_API_KEY")  # For DEX data
        
        # Free APIs (no key required)
        self.defillama_base = "https://api.llama.fi"
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        
        # Sessions for async requests
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_options_data(self) -> OptionsData:
        """Get ETH options market data"""
        try:
            # Try multiple sources for options data
            
            # Source 1: CoinGlass API (if available)
            if self.coinglass_api_key:
                options_data = await self._get_coinglass_options()
                if options_data:
                    return options_data
            
            # Source 2: Deribit public API (free)
            options_data = await self._get_deribit_options()
            if options_data:
                return options_data
            
            # Fallback: Simulated realistic data
            return await self._get_fallback_options()
            
        except Exception as e:
            self.logger.error(f"Error getting options data: {e}")
            return await self._get_fallback_options()
    
    async def _get_deribit_options(self) -> Optional[OptionsData]:
        """Get options data from Deribit public API"""
        try:
            url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
            params = {
                "currency": "ETH",
                "kind": "option"
            }
            
            if not self.session:
                return None
                
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("result"):
                        options = data["result"]
                        
                        # Calculate put/call ratio and open interest
                        total_oi = 0
                        put_oi = 0
                        call_oi = 0
                        total_iv = 0
                        count = 0
                        
                        for option in options[:50]:  # Limit to recent options
                            oi = option.get("open_interest", 0)
                            total_oi += oi
                            
                            iv = option.get("mark_iv", 0)
                            if iv > 0:
                                total_iv += iv
                                count += 1
                            
                            if "P" in option.get("instrument_name", ""):
                                put_oi += oi
                            else:
                                call_oi += oi
                        
                        put_call_ratio = put_oi / max(call_oi, 1)
                        avg_iv = total_iv / max(count, 1)
                        
                        return OptionsData(
                            open_interest=total_oi,
                            put_call_ratio=put_call_ratio,
                            max_pain=0,  # Not available from this API
                            implied_volatility=avg_iv,
                            expiry_date="mixed",
                            data_source="deribit_api"
                        )
                        
        except Exception as e:
            self.logger.warning(f"Deribit options API error: {e}")
            return None
    
    async def _get_coinglass_options(self) -> Optional[OptionsData]:
        """Get options data from CoinGlass API"""
        # Implementation for CoinGlass API (requires paid plan)
        # This is a placeholder for when API key is available
        return None
    
    async def get_futures_data(self) -> FuturesData:
        """Get ETH futures and perpetual data"""
        try:
            # Get futures data from multiple exchanges
            binance_data = await self._get_binance_futures()
            bybit_data = await self._get_bybit_futures()
            
            # Combine and calculate averages
            if binance_data or bybit_data:
                return await self._combine_futures_data(binance_data, bybit_data)
            
            return await self._get_fallback_futures()
            
        except Exception as e:
            self.logger.error(f"Error getting futures data: {e}")
            return await self._get_fallback_futures()
    
    async def _get_binance_futures(self) -> Optional[Dict]:
        """Get futures data from Binance"""
        try:
            # Binance Futures API (free)
            urls = {
                "ticker": "https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=ETHUSDT",
                "funding": "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=ETHUSDT",
                "oi": "https://fapi.binance.com/fapi/v1/openInterest?symbol=ETHUSDT"
            }
            
            data = {}
            for key, url in urls.items():
                async with self.session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        data[key] = result
            
            if data:
                funding_rate = float(data.get("funding", {}).get("lastFundingRate", 0))
                oi_value = float(data.get("oi", {}).get("openInterest", 0))
                
                return {
                    "funding_rate": funding_rate,
                    "open_interest": oi_value,
                    "exchange": "binance"
                }
                
        except Exception as e:
            self.logger.warning(f"Binance futures API error: {e}")
            return None
    
    async def _get_bybit_futures(self) -> Optional[Dict]:
        """Get futures data from Bybit"""
        try:
            # Bybit public API
            url = "https://api.bybit.com/v5/market/instruments-info"
            params = {"category": "linear", "symbol": "ETHUSDT"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("result", {}).get("list"):
                        instrument = data["result"]["list"][0]
                        
                        return {
                            "funding_rate": 0,  # Need separate API call
                            "open_interest": 0,  # Need separate API call
                            "exchange": "bybit"
                        }
                        
        except Exception as e:
            self.logger.warning(f"Bybit futures API error: {e}")
            return None
    
    async def _combine_futures_data(self, binance_data: Dict, bybit_data: Dict) -> FuturesData:
        """Combine futures data from multiple exchanges"""
        
        # Calculate average funding rate
        funding_rates = []
        open_interests = []
        
        if binance_data:
            funding_rates.append(binance_data["funding_rate"])
            open_interests.append(binance_data["open_interest"])
        
        if bybit_data:
            funding_rates.append(bybit_data.get("funding_rate", 0))
            open_interests.append(bybit_data.get("open_interest", 0))
        
        avg_funding = sum(funding_rates) / len(funding_rates) if funding_rates else 0
        total_oi = sum(open_interests)
        
        # Determine contango/backwardation (simplified)
        contango_status = "contango" if avg_funding > 0.01 else "backwardation" if avg_funding < -0.01 else "neutral"
        
        return FuturesData(
            open_interest=total_oi,
            funding_rate=avg_funding,
            basis=0,  # Would need spot vs futures price comparison
            contango_backwardation=contango_status,
            perpetual_funding_rate=avg_funding,
            data_source="binance_bybit_combined"
        )
    
    async def get_exchange_metrics(self) -> ExchangeMetrics:
        """Get multi-exchange ETH metrics"""
        try:
            # Get data from multiple sources
            reserves_data = await self._get_exchange_reserves()
            stablecoin_data = await self._get_stablecoin_metrics()
            volume_data = await self._get_dex_cex_volumes()
            
            return ExchangeMetrics(
                total_eth_reserves=reserves_data.get("total_reserves", 0),
                exchange_reserves_change_7d=reserves_data.get("change_7d", 0),
                stablecoin_supply=stablecoin_data.get("total_supply", 0),
                stablecoin_flow_24h=stablecoin_data.get("flow_24h", 0),
                dex_volume_24h=volume_data.get("dex_volume", 0),
                cex_volume_24h=volume_data.get("cex_volume", 0),
                dex_cex_ratio=volume_data.get("dex_cex_ratio", 0),
                data_source="multiple_sources"
            )
            
        except Exception as e:
            self.logger.error(f"Error getting exchange metrics: {e}")
            return await self._get_fallback_exchange_metrics()
    
    async def _get_exchange_reserves(self) -> Dict:
        """Get ETH reserves data from exchanges"""
        try:
            # DeFiLlama API for protocol TVL (free)
            url = f"{self.defillama_base}/protocols"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Calculate total ETH locked in protocols
                    total_tvl = sum(protocol.get("tvl", 0) for protocol in data if protocol.get("chain") == "Ethereum")
                    
                    # Estimate ETH reserves (simplified)
                    eth_price = 4000  # Rough estimate, should get from price API
                    estimated_eth_reserves = total_tvl / eth_price * 0.3  # Assume 30% of TVL is ETH
                    
                    return {
                        "total_reserves": estimated_eth_reserves,
                        "change_7d": 0  # Would need historical data
                    }
                    
        except Exception as e:
            self.logger.warning(f"Exchange reserves API error: {e}")
            
        return {"total_reserves": 0, "change_7d": 0}
    
    async def _get_stablecoin_metrics(self) -> Dict:
        """Get stablecoin supply and flow data"""
        try:
            # CoinGecko API for stablecoin data
            stablecoins = ["tether", "usd-coin", "dai", "true-usd", "paxos-standard"]
            total_supply = 0
            
            for coin in stablecoins:
                url = f"{self.coingecko_base}/coins/{coin}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        market_data = data.get("market_data", {})
                        circulating_supply = market_data.get("circulating_supply", 0)
                        total_supply += circulating_supply
                        
                        await asyncio.sleep(0.1)  # Rate limiting
            
            return {
                "total_supply": total_supply,
                "flow_24h": 0  # Would need historical comparison
            }
            
        except Exception as e:
            self.logger.warning(f"Stablecoin metrics API error: {e}")
            return {"total_supply": 0, "flow_24h": 0}
    
    async def _get_dex_cex_volumes(self) -> Dict:
        """Get DEX vs CEX volume comparison"""
        try:
            # Get DEX volume from DeFiLlama
            dex_url = f"{self.defillama_base}/overview/dexs/ethereum"
            
            dex_volume = 0
            async with self.session.get(dex_url) as response:
                if response.status == 200:
                    data = await response.json()
                    dex_volume = data.get("total24h", 0)
            
            # Get CEX volume from CoinGecko
            cex_url = f"{self.coingecko_base}/coins/ethereum"
            
            cex_volume = 0
            async with self.session.get(cex_url) as response:
                if response.status == 200:
                    data = await response.json()
                    cex_volume = data.get("market_data", {}).get("total_volume", {}).get("usd", 0)
            
            dex_cex_ratio = dex_volume / max(cex_volume, 1)
            
            return {
                "dex_volume": dex_volume,
                "cex_volume": cex_volume,
                "dex_cex_ratio": dex_cex_ratio
            }
            
        except Exception as e:
            self.logger.warning(f"DEX/CEX volume API error: {e}")
            return {"dex_volume": 0, "cex_volume": 0, "dex_cex_ratio": 0}
    
    async def get_long_term_holder_data(self) -> LongTermHolderData:
        """Get long-term holder behavior metrics"""
        try:
            # Try Glassnode API if available
            if self.glassnode_api_key:
                lth_data = await self._get_glassnode_lth_data()
                if lth_data:
                    return lth_data
            
            # Fallback to alternative sources or estimates
            return await self._get_fallback_lth_data()
            
        except Exception as e:
            self.logger.error(f"Error getting LTH data: {e}")
            return await self._get_fallback_lth_data()
    
    async def _get_glassnode_lth_data(self) -> Optional[LongTermHolderData]:
        """Get LTH data from Glassnode API"""
        # This requires a Glassnode API key
        # Implementation placeholder for when API key is available
        return None
    
    # Fallback methods with realistic simulated data
    async def _get_fallback_options(self) -> OptionsData:
        """Fallback options data"""
        return OptionsData(
            open_interest=125000,  # Realistic ETH options OI
            put_call_ratio=0.75,  # Slightly bearish
            max_pain=4000,
            implied_volatility=0.65,  # 65% IV
            expiry_date="monthly",
            data_source="simulated_realistic"
        )
    
    async def _get_fallback_futures(self) -> FuturesData:
        """Fallback futures data"""
        return FuturesData(
            open_interest=850000,  # Realistic ETH futures OI
            funding_rate=0.0025,  # 0.25% funding rate
            basis=15,  # $15 basis
            contango_backwardation="contango",
            perpetual_funding_rate=0.0025,
            data_source="simulated_realistic"
        )
    
    async def _get_fallback_exchange_metrics(self) -> ExchangeMetrics:
        """Fallback exchange metrics"""
        return ExchangeMetrics(
            total_eth_reserves=2500000,  # 2.5M ETH in exchanges
            exchange_reserves_change_7d=-25000,  # -25k ETH outflow
            stablecoin_supply=185000000000,  # $185B stablecoins
            stablecoin_flow_24h=2500000000,  # $2.5B daily flow
            dex_volume_24h=3200000000,  # $3.2B DEX volume
            cex_volume_24h=8500000000,  # $8.5B CEX volume
            dex_cex_ratio=0.376,  # 37.6% DEX ratio
            data_source="simulated_realistic"
        )
    
    async def _get_fallback_lth_data(self) -> LongTermHolderData:
        """Enhanced fallback with free data sources"""
        try:
            # Try to get real data from free sources
            from free_data_sources import FreeDataSources
            
            async with FreeDataSources() as free_sources:
                free_metrics = await free_sources.get_comprehensive_free_metrics()
                
                if free_metrics and len(free_metrics.data_sources) > 0:
                    # Use real data from free sources
                    total_supply = 120000000  # ~120M ETH total supply
                    lth_supply = total_supply * 0.68  # 68% held long-term
                    
                    return LongTermHolderData(
                        lth_supply_1y=lth_supply,
                        lth_supply_percentage=68.0,
                        coin_days_destroyed=125000,
                        mvrv_ratio=free_metrics.mvrv_ratio,
                        supply_in_profit_ratio=0.72,  # Would need calculation
                        supply_in_loss_ratio=0.28,   # Would need calculation
                        hodler_net_position_change=-15000,  # Would need historical data
                        realized_cap=free_metrics.realized_cap,
                        market_cap=free_metrics.market_cap,
                        data_source=f"free_sources_{','.join(free_metrics.data_sources)}"
                    )
        except Exception as e:
            self.logger.warning(f"Free sources fallback failed: {e}")
        
        # Final fallback with simulated data
        total_supply = 120000000  # ~120M ETH total supply
        lth_supply = total_supply * 0.68  # 68% held long-term
        market_cap = total_supply * 4000  # $4000 per ETH
        realized_cap = market_cap * 0.75  # Typical realized cap ratio
        
        return LongTermHolderData(
            lth_supply_1y=lth_supply,
            lth_supply_percentage=68.0,
            coin_days_destroyed=125000,
            mvrv_ratio=market_cap / realized_cap,
            supply_in_profit_ratio=0.72,  # 72% of supply in profit
            supply_in_loss_ratio=0.28,   # 28% of supply in loss
            hodler_net_position_change=-15000,  # -15k ETH net change
            realized_cap=realized_cap,
            market_cap=market_cap,
            data_source="simulated_realistic"
        )

# Test function
async def test_advanced_metrics():
    """Test the advanced metrics tracker"""
    print("🧪 Testing Advanced Metrics Tracker")
    print("=" * 50)
    
    async with AdvancedMetricsTracker() as tracker:
        
        # Test Options Data
        print("📊 Options Data:")
        options = await tracker.get_options_data()
        print(f"  Open Interest: {options.open_interest:,.0f}")
        print(f"  Put/Call Ratio: {options.put_call_ratio:.2f}")
        print(f"  Implied Vol: {options.implied_volatility:.1%}")
        print(f"  Source: {options.data_source}")
        
        # Test Futures Data
        print("\n📈 Futures Data:")
        futures = await tracker.get_futures_data()
        print(f"  Open Interest: {futures.open_interest:,.0f}")
        print(f"  Funding Rate: {futures.funding_rate:.4f}")
        print(f"  Status: {futures.contango_backwardation}")
        print(f"  Source: {futures.data_source}")
        
        # Test Exchange Metrics
        print("\n🏦 Exchange Metrics:")
        exchange = await tracker.get_exchange_metrics()
        print(f"  ETH Reserves: {exchange.total_eth_reserves:,.0f}")
        print(f"  Stablecoin Supply: ${exchange.stablecoin_supply:,.0f}")
        print(f"  DEX/CEX Ratio: {exchange.dex_cex_ratio:.1%}")
        print(f"  Source: {exchange.data_source}")
        
        # Test Long-term Holder Data
        print("\n💎 Long-term Holder Data:")
        lth = await tracker.get_long_term_holder_data()
        print(f"  LTH Supply: {lth.lth_supply_1y:,.0f} ETH ({lth.lth_supply_percentage:.1f}%)")
        print(f"  MVRV Ratio: {lth.mvrv_ratio:.2f}")
        print(f"  Supply in Profit: {lth.supply_in_profit_ratio:.1%}")
        print(f"  Source: {lth.data_source}")

if __name__ == "__main__":
    asyncio.run(test_advanced_metrics())
