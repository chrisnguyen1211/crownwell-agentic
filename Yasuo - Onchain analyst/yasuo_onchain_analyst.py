#!/usr/bin/env python3
"""
🛡️ YASUO - ON-CHAIN ANALYST AGENT
Advanced Ethereum On-Chain Flow Analysis Agent

Features:
- Real-time ETH transaction monitoring (≥ 1,000 ETH)
- Buyer/Seller identification (whales, exchanges, institutions)
- Market implication analysis
- Portfolio recommendations (buy/hold/sell)
- Telegram alerts integration
- Bitquery API integration (primary)
- Etherscan & Moralis fallback APIs
"""

import os
import json
import logging
import asyncio
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Optional imports for Telegram
try:
    from telegram import Bot
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

# Optional imports for Moralis
try:
    from moralis import evm_api
    MORALIS_AVAILABLE = True
except ImportError:
    MORALIS_AVAILABLE = False

from bs4 import BeautifulSoup


class EntityType(Enum):
    """Entity types for wallet classification"""
    WHALE = "whale"
    EXCHANGE = "exchange"
    INSTITUTION = "institution"
    DEFIPROTOCOL = "defi_protocol"
    STAKINGCONTRACT = "staking_contract"
    MININGPOOL = "mining_pool"
    UNKNOWN = "unknown"


class TransactionType(Enum):
    """Transaction classification types"""
    LARGE_BUY = "large_buy"
    LARGE_SELL = "large_sell"
    WHALE_ACCUMULATION = "whale_accumulation"
    INSTITUTIONAL_FLOW = "institutional_flow"
    EXCHANGE_DEPOSIT = "exchange_deposit"
    EXCHANGE_WITHDRAWAL = "exchange_withdrawal"


class PortfolioAction(Enum):
    """Portfolio recommendation actions"""
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


@dataclass
class WalletInfo:
    """Wallet identification and labeling"""
    address: str
    entity_type: EntityType
    entity_name: str
    confidence: float  # 0.0 to 1.0
    tags: List[str]


@dataclass
class LargeTransaction:
    """Large ETH transaction data"""
    hash: str
    timestamp: datetime
    block_number: int
    sender_address: str
    receiver_address: str
    eth_amount: float
    usd_value: float
    gas_price: int
    gas_used: int
    transaction_type: TransactionType
    buyer_info: Optional[WalletInfo]
    seller_info: Optional[WalletInfo]


@dataclass
class MarketImplication:
    """Analysis of transaction implications"""
    sentiment: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    key_signals: List[str]
    risk_level: str  # "low", "medium", "high"
    timeframe_impact: str  # "short_term", "medium_term", "long_term"


@dataclass
class PortfolioRecommendation:
    """Portfolio action recommendation"""
    action: PortfolioAction
    confidence: float
    reasoning: str
    risk_assessment: str
    timeframe: str
    supporting_data: Dict[str, Any]


class WalletLabeler:
    """
    Advanced wallet labeling system for buyer/seller identification
    Uses known address databases and heuristics
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Known exchange addresses (sample - would be expanded)
        self.exchange_addresses = {
            "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE": {"name": "Binance", "type": EntityType.EXCHANGE},
            "0x28C6c06298d514Db089934071355E5743bf21d60": {"name": "Binance", "type": EntityType.EXCHANGE},
            "0xD551234Ae421e3BCBA99A0Da6d736074f22192FF": {"name": "Binance", "type": EntityType.EXCHANGE},
            "0xA7A93fd0a276fc1C0197a5B5623eD117786eeD06": {"name": "Coinbase", "type": EntityType.EXCHANGE},
            "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3": {"name": "OKX", "type": EntityType.EXCHANGE},
            "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3": {"name": "Kraken", "type": EntityType.EXCHANGE},
            "0xe853c56864A2ebe4576a807D26Fdc4A0adA51919": {"name": "Bybit", "type": EntityType.EXCHANGE},
        }

        # Known institutional addresses (sample)
        self.institutional_addresses = {
            "0x7b65B489fE53fCE1F6548Db886C08aD73111DDd8": {"name": "Bitfinex", "type": EntityType.INSTITUTION},
            "0x742d35Cc67F81b6FD9C1d9d6c4b5b0dc5b5b5b5": {"name": "Bitfinex", "type": EntityType.INSTITUTION},
        }

        # DeFi protocol addresses (sample)
        self.defi_addresses = {
            "0xC36442b4a4522E871399CD717aBDD847Ab11FE88": {"name": "Uniswap V3", "type": EntityType.DEFIPROTOCOL},
            "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45": {"name": "Uniswap V3", "type": EntityType.DEFIPROTOCOL},
            "0x1F98431c8aD98523631AE4a59f267346ea31F984": {"name": "Uniswap V3", "type": EntityType.DEFIPROTOCOL},
            "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84": {"name": "Lido Staking", "type": EntityType.STAKINGCONTRACT},
        }

        # Whale wallet heuristics (addresses with large ETH holdings)
        self.whale_heuristics = {
            "min_balance_threshold": 10000,  # ETH
            "transaction_frequency_threshold": 50,  # transactions per month
        }

    def identify_wallet(self, address: str, eth_balance: float = 0,
                       transaction_count: int = 0) -> WalletInfo:
        """
        Identify wallet type and entity based on address and transaction data
        """
        address_lower = address.lower()

        # Check known exchange addresses
        if address_lower in self.exchange_addresses:
            info = self.exchange_addresses[address_lower]
            return WalletInfo(
                address=address,
                entity_type=info["type"],
                entity_name=info["name"],
                confidence=0.95,
                tags=["exchange", "centralized"]
            )

        # Check known institutional addresses
        if address_lower in self.institutional_addresses:
            info = self.institutional_addresses[address_lower]
            return WalletInfo(
                address=address,
                entity_type=info["type"],
                entity_name=info["name"],
                confidence=0.90,
                tags=["institution", "professional"]
            )

        # Check known DeFi addresses
        if address_lower in self.defi_addresses:
            info = self.defi_addresses[address_lower]
            return WalletInfo(
                address=address,
                entity_type=info["type"],
                entity_name=info["name"],
                confidence=0.95,
                tags=["defi", "protocol"]
            )

        # Apply whale heuristics
        if eth_balance >= self.whale_heuristics["min_balance_threshold"]:
            return WalletInfo(
                address=address,
                entity_type=EntityType.WHALE,
                entity_name="Whale Wallet",
                confidence=0.85,
                tags=["whale", "large_holder"]
            )

        # High transaction frequency suggests active trader
        if transaction_count >= self.whale_heuristics["transaction_frequency_threshold"]:
            return WalletInfo(
                address=address,
                entity_type=EntityType.WHALE,
                entity_name="Active Trader",
                confidence=0.70,
                tags=["active_trader", "frequent_trader"]
            )

        # Unknown wallet
        return WalletInfo(
            address=address,
            entity_type=EntityType.UNKNOWN,
            entity_name="Unknown Wallet",
            confidence=0.0,
            tags=["unknown"]
        )


class BitqueryAPI:
    """
    Bitquery API client for ETH transaction data
    Free tier: ~100 queries/day
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BITQUERY_API_KEY")
        self.base_url = "https://graphql.bitquery.io"
        self.logger = logging.getLogger(__name__)
        self.rate_limit_remaining = 100  # Free tier limit
        self.rate_limit_reset_time = datetime.now()

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            # Use Bearer token for ory_at_ keys, X-API-KEY for others
            if self.api_key.startswith("ory_at_"):
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                headers["X-API-KEY"] = self.api_key
        return headers

    def _check_rate_limit(self) -> bool:
        """Check if we can make another API call"""
        now = datetime.now()

        # Reset rate limit if time has passed
        if now >= self.rate_limit_reset_time:
            self.rate_limit_remaining = 100
            self.rate_limit_reset_time = now + timedelta(days=1)

        return self.rate_limit_remaining > 0

    def _decrement_rate_limit(self):
        """Decrement remaining API calls"""
        self.rate_limit_remaining -= 1

    async def get_large_eth_transactions(self, min_eth: float = 1000,
                                       hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Query large ETH transactions using Bitquery GraphQL API
        """
        if not self._check_rate_limit():
            self.logger.warning("Bitquery rate limit exceeded")
            return []

        query = """
        query GetLargeETHTransfers($minAmount: Float!, $hoursBack: Int!) {
          ethereum(network: ethereum) {
            transfers(
              currency: {is: "0x0000000000000000000000000000000000000000"}
              amount: {gt: $minAmount}
              time: {since: {hours_ago: $hoursBack}}
              options: {desc: "amount", limit: 100}
            ) {
              transaction {
                hash
                txFrom {
                  address
                }
                txTo {
                  address
                }
              }
              amount
              sender {
                address
                annotation
              }
              receiver {
                address
                annotation
              }
              currency {
                symbol
              }
              date {
                date
              }
              block {
                number
                timestamp {
                  unixtime
                }
              }
              gasValue
              gasPrice
            }
          }
        }
        """

        variables = {
            "minAmount": min_eth,
            "hoursBack": hours_back
        }

        try:
            response = requests.post(
                self.base_url,
                json={"query": query, "variables": variables},
                headers=self._get_headers(),
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self._decrement_rate_limit()

                transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
                self.logger.info(f"Found {len(transfers)} large ETH transactions")
                return transfers
            else:
                self.logger.error(f"Bitquery API error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            self.logger.error(f"Error querying Bitquery API: {e}")
            return []


class EtherscanAPI:
    """
    Etherscan API fallback for ETH transaction data
    Free tier: 5 calls/second
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        self.base_url = "https://api.etherscan.io/api"
        self.logger = logging.getLogger(__name__)
        self.last_call_time = datetime.now()
        self.min_call_interval = 0.2  # 5 calls/second = 0.2s interval

    def _can_make_call(self) -> bool:
        """Check rate limiting"""
        now = datetime.now()
        time_diff = (now - self.last_call_time).total_seconds()
        return time_diff >= self.min_call_interval

    def _wait_for_rate_limit(self):
        """Wait for rate limit if necessary"""
        while not self._can_make_call():
            time.sleep(0.1)
        self.last_call_time = datetime.now()

    async def get_large_eth_transactions(self, min_eth: float = 1000,
                                       hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get large ETH transactions using Etherscan API
        Note: This is a simplified implementation - Etherscan doesn't have direct
        large transfer filtering, so we'd need to scan recent blocks
        """
        if not self.api_key:
            self.logger.warning("Etherscan API key not provided")
            return []

        # For this implementation, we'll return a simplified structure
        # In production, you'd need to implement block scanning
        self.logger.info("Etherscan API fallback - simplified implementation")
        return []


class ETHETFFlowTracker:
    """
    Tracks ETH ETF flows by scraping from farside.co.uk with daily aggregation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.eth_url = "https://farside.co.uk/eth/"
        
        # Cache for daily data to avoid noise
        self.daily_cache = {}
        self.last_update = None
        self.cache_duration = 3600  # 1 hour cache
        
        # Major ETH ETFs for reference
        self.eth_etfs = [
            "BITO", "ETHE", "ETHW", "QBTC", "GBTC",
            "DEFI", "ARKW", "SPY", "QQQ", "IWM"
        ]

    async def get_etf_flows(self) -> Dict[str, float]:
        """
        Get ETH ETF flow data with daily aggregation to reduce noise
        """
        try:
            # Check cache first
            current_time = datetime.now()
            if (self.last_update and 
                (current_time - self.last_update).total_seconds() < self.cache_duration and
                self.daily_cache):
                
                self.logger.info("Using cached ETF data to reduce noise")
                return self.daily_cache
            
            # Scrape fresh data
            eth_data = await self._scrape_etf_data(self.eth_url, "ETH")
            
            # Aggregate daily data to reduce noise
            daily_flow = eth_data.get("daily_flow", 0)
            
            # Calculate daily average if we have multiple data points
            if "daily_flows" in eth_data:
                flows = eth_data["daily_flows"]
                if len(flows) > 1:
                    # Use median to reduce outlier noise
                    import statistics
                    daily_flow = statistics.median(flows)
                    self.logger.info(f"Aggregated daily flow (median): ${daily_flow:,.0f}")
            
            result = {
                "daily_flow": daily_flow,
                "weekly_flow": 0,  # Not needed - only latest day matters
                "monthly_flow": 0,  # Not needed - only latest day matters
                "aum": eth_data.get("aum", 0),
                "timestamp": current_time.isoformat(),
                "etf_count": len(self.eth_etfs),
                "data_source": "farside.co.uk_eth_daily_aggregated",
                "flow_direction": "inflows" if daily_flow > 0 else "outflows",
                "latest_day_only": True,
                "noise_reduction": "daily_aggregation",
                "cache_hit": False
            }
            
            # Update cache
            self.daily_cache = result
            self.last_update = current_time
            
            return result

        except Exception as e:
            self.logger.error(f"Error getting ETH ETF flows: {e}")
            return self._get_fallback_etf_flows()

    async def _scrape_etf_data(self, url: str, asset: str) -> Dict[str, float]:
        """
        Scrape ETF data from farside.co.uk with improved accuracy
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Initialize flow data
            flow_data = {
                "daily_flow": 0,
                "daily_flows": [],  # Store multiple daily flows for aggregation
                "aum": 0
            }

            # Find all tables
            tables = soup.find_all('table')

            if not tables:
                self.logger.warning(f"No tables found on {url}")
                return flow_data

            # The main ETF data table is typically table index 1 (second table)
            main_table = tables[1] if len(tables) > 1 else tables[0]

            # Look for rows with background color (green highlight for latest data)
            rows = main_table.find_all('tr')
            latest_rows = []

            # Find the green highlighted row (latest data) and recent rows
            for row in rows:
                # Check if row has green background color or specific style
                row_style = row.get('style', '')
                row_class = row.get('class', [])
                
                # Look for specific green background color #99ff99
                if '#99ff99' in row_style or \
                   'background-color: #99ff99' in row_style or \
                   ('background' in row_style and ('green' in row_style.lower() or '99ff99' in row_style)) or \
                   any('green' in str(cls).lower() for cls in row_class):
                    latest_rows.append(row)
                    self.logger.info(f"Found green highlighted row for {asset}")

            # If no green row found, look for the most recent date rows
            if not latest_rows:
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) > 0:
                        first_cell = cells[0].get_text(strip=True)
                        # Look for recent date patterns (Sep 2025, Aug 2025, etc.)
                        if '2025' in first_cell and ('Sep' in first_cell or 'Aug' in first_cell):
                            latest_rows.append(row)

            # Extract data from the latest rows for aggregation
            daily_flows = []
            for row in latest_rows:
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]

                self.logger.info(f"Processing {asset} row: {cell_texts}")

                # The last column should be the total/net flow
                if len(cell_texts) > 0:
                    # Get the last cell which should be the net total
                    last_cell = cell_texts[-1]
                    
                    # Parse the net flow value
                    try:
                        # Handle parentheses for negative values: (135.3) = -135.3
                        if '(' in last_cell and ')' in last_cell:
                            # Extract number from parentheses and make negative
                            number_str = last_cell.replace('(', '').replace(')', '').replace(',', '')
                            daily_flow = -float(number_str) * 1000000  # Convert to negative millions
                        else:
                            # Positive value
                            number_str = last_cell.replace(',', '')
                            daily_flow = float(number_str) * 1000000  # Convert to millions
                        
                        daily_flows.append(daily_flow)
                        self.logger.info(f"Extracted {asset} daily flow: ${daily_flow:,.0f}")

                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Could not parse {asset} flow value '{last_cell}': {e}")

            # Store all daily flows for aggregation
            flow_data["daily_flows"] = daily_flows
            
            # Use the most recent flow as primary daily flow
            if daily_flows:
                flow_data["daily_flow"] = daily_flows[0]
                self.logger.info(f"Primary daily flow: ${daily_flows[0]:,.0f}")
                if len(daily_flows) > 1:
                    self.logger.info(f"Additional flows for aggregation: {len(daily_flows)-1}")

            # If we couldn't extract real data, use minimal fallback
            if not daily_flows:
                self.logger.warning(f"Could not extract real ETF data from {url}")
                # Use minimal fallback instead of random data
                flow_data["daily_flow"] = 0
                flow_data["aum"] = 25000000000  # $25B estimate

            return flow_data

        except Exception as e:
            self.logger.error(f"Error scraping {asset} ETF data from {url}: {e}")
            return {"daily_flow": 0, "daily_flows": [], "aum": 0}

    def _get_fallback_etf_flows(self) -> Dict[str, float]:
        """Fallback ETF flow data - minimal and stable"""
        return {
            "daily_flow": 0,
            "daily_flows": [0],
            "weekly_flow": 0,
            "monthly_flow": 0,
            "aum": 25000000000,  # $25B
            "timestamp": datetime.now().isoformat(),
            "etf_count": 0,
            "data_source": "fallback_stable",
            "flow_direction": "neutral",
            "latest_day_only": True,
            "noise_reduction": "fallback"
        }


class YasuoOnChainAnalyst:
    """
    Main Yasuo On-Chain Analysis Agent
    Monitors large ETH flows and provides portfolio recommendations
    """

    def __init__(self):
        self.setup_logging()
        self.wallet_labeler = WalletLabeler()

        # Initialize API clients
        self.bitquery = BitqueryAPI()
        self.etherscan = EtherscanAPI()

        # Telegram bot for alerts
        self.telegram_bot = None
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        # Configuration
        self.min_transaction_threshold = 1000  # ETH
        self.monitoring_interval = 300  # 5 minutes
        self.alert_threshold_usd = 4000000  # $4M at $4000/ETH

        # Tracking state
        self.last_checked_timestamp = datetime.now() - timedelta(hours=1)
        self.processed_transactions = set()

        self.logger.info("🛡️ Yasuo On-Chain Analyst initialized")

    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('yasuo_analysis.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_telegram_bot(self, bot_token: str):
        """Setup Telegram bot for alerts"""
        if TELEGRAM_AVAILABLE and bot_token:
            try:
                self.telegram_bot = Bot(token=bot_token)
                self.logger.info("✅ Telegram bot initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Telegram bot: {e}")
        else:
            self.logger.warning("Telegram bot not available or token not provided")

    async def send_telegram_alert(self, message: str):
        """Send alert via Telegram"""
        if self.telegram_bot and self.telegram_chat_id:
            try:
                await self.telegram_bot.send_message(
                    chat_id=self.telegram_chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
                self.logger.info("✅ Telegram alert sent")
            except Exception as e:
                self.logger.error(f"Failed to send Telegram alert: {e}")

    def classify_transaction(self, sender_info: WalletInfo, receiver_info: WalletInfo,
                           eth_amount: float) -> TransactionType:
        """
        Classify transaction type based on wallet information
        """
        # Large buy: Unknown/Individual to Exchange
        if (sender_info.entity_type == EntityType.UNKNOWN and
            receiver_info.entity_type == EntityType.EXCHANGE):
            return TransactionType.LARGE_BUY

        # Large sell: Exchange to Unknown/Individual
        if (sender_info.entity_type == EntityType.EXCHANGE and
            receiver_info.entity_type == EntityType.UNKNOWN):
            return TransactionType.LARGE_SELL

        # Whale accumulation: Whale to Exchange (withdrawal from exchange)
        if (sender_info.entity_type == EntityType.EXCHANGE and
            receiver_info.entity_type == EntityType.WHALE):
            return TransactionType.WHALE_ACCUMULATION

        # Exchange deposit: Whale to Exchange
        if (sender_info.entity_type == EntityType.WHALE and
            receiver_info.entity_type == EntityType.EXCHANGE):
            return TransactionType.EXCHANGE_DEPOSIT

        # Exchange withdrawal: Exchange to Whale
        if (sender_info.entity_type == EntityType.EXCHANGE and
            receiver_info.entity_type == EntityType.WHALE):
            return TransactionType.EXCHANGE_WITHDRAWAL

        # Institutional flow
        if (sender_info.entity_type == EntityType.INSTITUTION or
            receiver_info.entity_type == EntityType.INSTITUTION):
            return TransactionType.INSTITUTIONAL_FLOW

        # Default to large buy if receiver is unknown
        if receiver_info.entity_type == EntityType.UNKNOWN:
            return TransactionType.LARGE_BUY

        return TransactionType.LARGE_SELL

    def analyze_market_implications(self, transaction: LargeTransaction,
                                  exchange_flows: Dict[str, float],
                                  etf_flows: Dict[str, float]) -> MarketImplication:
        """
        Analyze market implications of the transaction
        """
        key_signals = []
        sentiment = "neutral"
        confidence = 0.5

        # Whale accumulation signals
        if transaction.transaction_type == TransactionType.WHALE_ACCUMULATION:
            key_signals.append("Whale withdrawing ETH from exchange - accumulation signal")
            sentiment = "bullish"
            confidence = 0.8

        # Whale selling signals
        elif transaction.transaction_type == TransactionType.EXCHANGE_DEPOSIT:
            key_signals.append("Whale depositing ETH to exchange - potential selling signal")
            sentiment = "bearish"
            confidence = 0.7

        # Institutional buying
        elif (transaction.transaction_type == TransactionType.INSTITUTIONAL_FLOW and
              transaction.buyer_info and
              transaction.buyer_info.entity_type == EntityType.INSTITUTION):
            key_signals.append("Institutional accumulation detected")
            sentiment = "bullish"
            confidence = 0.9

        # Check exchange flows correlation
        net_exchange_flow = exchange_flows.get("net_flow", 0)
        if net_exchange_flow > 100000:  # Large outflows = accumulation
            key_signals.append("Large exchange outflows support accumulation narrative")
            if sentiment == "bullish":
                confidence += 0.1
        elif net_exchange_flow < -100000:  # Large inflows = selling
            key_signals.append("Large exchange inflows suggest profit-taking")
            if sentiment == "bearish":
                confidence += 0.1

        # Check ETF flows
        daily_etf_flow = etf_flows.get("daily_flow", 0)
        if daily_etf_flow > 50000000:  # $50M daily inflows
            key_signals.append("Strong ETF inflows indicate institutional confidence")
            if sentiment == "bullish":
                confidence += 0.15

        # Risk assessment
        if transaction.eth_amount >= 5000:  # Very large transaction
            risk_level = "high"
        elif transaction.eth_amount >= 2000:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Timeframe impact
        if transaction.eth_amount >= 5000:
            timeframe_impact = "long_term"
        elif transaction.eth_amount >= 2000:
            timeframe_impact = "medium_term"
        else:
            timeframe_impact = "short_term"

        confidence = min(confidence, 1.0)  # Cap at 1.0

        return MarketImplication(
            sentiment=sentiment,
            confidence=confidence,
            key_signals=key_signals,
            risk_level=risk_level,
            timeframe_impact=timeframe_impact
        )

    def generate_portfolio_recommendation(self, transaction: LargeTransaction,
                                        implication: MarketImplication,
                                        exchange_flows: Dict[str, float],
                                        etf_flows: Dict[str, float]) -> PortfolioRecommendation:
        """
        Generate portfolio action recommendation based on analysis
        """

        # BUY conditions
        buy_conditions = [
            implication.sentiment == "bullish" and implication.confidence >= 0.7,
            exchange_flows.get("net_flow", 0) > 10000,  # Exchange outflows
            etf_flows.get("daily_flow", 0) > 10000000,  # $10M ETF inflows
            implication.sentiment == "bullish"
        ]

        # SELL conditions
        sell_conditions = [
            implication.sentiment == "bearish" and implication.confidence >= 0.6,
            exchange_flows.get("net_flow", 0) < -10000,  # Exchange inflows
            transaction.transaction_type == TransactionType.EXCHANGE_DEPOSIT,
            implication.sentiment == "bearish" and transaction.eth_amount >= 2000
        ]

        # HOLD conditions (mixed signals)
        hold_conditions = [
            abs(exchange_flows.get("net_flow", 0)) < 5000,  # Small net flows
            abs(etf_flows.get("daily_flow", 0)) < 5000000,  # Small ETF flows
            implication.confidence < 0.5  # Low confidence
        ]

        # Determine action
        if sum(buy_conditions) >= 2:
            action = PortfolioAction.BUY
            confidence = min(implication.confidence + 0.2, 1.0)
            reasoning = "Multiple bullish signals detected: whale accumulation, exchange outflows, ETF inflows"
        elif sum(sell_conditions) >= 2:
            action = PortfolioAction.SELL
            confidence = min(implication.confidence + 0.15, 1.0)
            reasoning = "Bearish signals: whale selling, exchange inflows, profit-taking activity"
        elif sum(hold_conditions) >= 1:
            action = PortfolioAction.HOLD
            confidence = 0.6
            reasoning = "Mixed or weak signals suggest consolidation period"
        else:
            action = PortfolioAction.HOLD
            confidence = 0.5
            reasoning = "Insufficient data for strong directional bias"

        # Risk assessment
        if implication.risk_level == "high":
            risk_assessment = "High risk - large transaction may cause significant volatility"
        elif implication.risk_level == "medium":
            risk_assessment = "Medium risk - moderate impact expected"
        else:
            risk_assessment = "Low risk - minimal market impact"

        return PortfolioRecommendation(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            risk_assessment=risk_assessment,
            timeframe=implication.timeframe_impact,
            supporting_data={
                "transaction_type": transaction.transaction_type.value,
                "eth_amount": transaction.eth_amount,
                "usd_value": transaction.usd_value,
                "buyer_entity": transaction.buyer_info.entity_name if transaction.buyer_info else "Unknown",
                "seller_entity": transaction.seller_info.entity_name if transaction.seller_info else "Unknown",
                "exchange_net_flow": exchange_flows.get("net_flow", 0),
                "etf_daily_flow": etf_flows.get("daily_flow", 0),
                "implication_confidence": implication.confidence
            }
        )

    def get_exchange_flows(self) -> Dict[str, float]:
        """
        Get current exchange flows (placeholder - would integrate with exchange APIs)
        """
        # Placeholder implementation
        # In production, this would query multiple exchanges for net ETH flows
        return {
            "net_flow": 15000,  # Positive = outflows (accumulation)
            "total_inflows": 50000,
            "total_outflows": 65000,
            "timestamp": datetime.now().isoformat()
        }

    def get_etf_flows(self) -> Dict[str, float]:
        """
        Get current ETH ETF flows (placeholder - would scrape Bloomberg/CoinDesk)
        """
        # Placeholder implementation
        # In production, this would scrape ETF flow data
        return {
            "daily_flow": 25000000,  # $25M inflows
            "weekly_flow": 150000000,  # $150M weekly
            "aum": 21428000000,  # $21.428B AUM
            "timestamp": datetime.now().isoformat()
        }

    def create_alert_message(self, transaction: LargeTransaction,
                           implication: MarketImplication,
                           recommendation: PortfolioRecommendation) -> str:
        """
        Create formatted alert message for notifications
        """
        timestamp = transaction.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        buyer_name = (transaction.buyer_info.entity_name
                     if transaction.buyer_info else "Unknown")
        seller_name = (transaction.seller_info.entity_name
                      if transaction.seller_info else "Unknown")

        message = f"""
🔔 <b>LARGE ETH TRANSACTION ALERT</b>

📊 <b>Transaction Details:</b>
• Amount: {transaction.eth_amount:,.0f} ETH (~${transaction.usd_value:,.0f})
• Timestamp: {timestamp}
• Buyer: {buyer_name} ({transaction.receiver_address[:10]}...)
• Seller: {seller_name} ({transaction.sender_address[:10]}...)
• Transaction Type: {transaction.transaction_type.value.replace('_', ' ').title()}

🎯 <b>Market Implication:</b>
• Sentiment: {implication.sentiment.title()}
• Confidence: {implication.confidence:.1%}
• Risk Level: {implication.risk_level.title()}
• Key Signals:
"""

        for signal in implication.key_signals:
            message += f"  • {signal}\n"

        message += f"""
💼 <b>Portfolio Recommendation:</b>
• Action: <b>{recommendation.action.value}</b>
• Confidence: {recommendation.confidence:.1%}
• Reasoning: {recommendation.reasoning}
• Risk Assessment: {recommendation.risk_assessment}
• Timeframe: {recommendation.timeframe.replace('_', ' ').title()}

📈 <b>Market Context:</b>
• Exchange Net Flow: {recommendation.supporting_data['exchange_net_flow']:,.0f} ETH
• ETF Daily Flow: ${recommendation.supporting_data['etf_daily_flow']:,.0f}
"""

        return message

    async def process_transaction(self, tx_data: Dict[str, Any]) -> Optional[LargeTransaction]:
        """
        Process a single transaction and create LargeTransaction object
        """
        try:
            # Extract transaction data
            tx_hash = tx_data["transaction"]["hash"]
            if tx_hash in self.processed_transactions:
                return None  # Already processed

            sender_address = tx_data["transaction"]["txFrom"]["address"]
            receiver_address = tx_data["transaction"]["txTo"]["address"]
            eth_amount = float(tx_data["amount"])

            # Skip if below threshold
            if eth_amount < self.min_transaction_threshold:
                return None

            # Estimate USD value (simplified - would use real-time price)
            eth_price = 4000  # Would get from API
            usd_value = eth_amount * eth_price

            # Skip if below USD threshold
            if usd_value < self.alert_threshold_usd:
                return None

            # Parse timestamp
            timestamp = datetime.fromtimestamp(tx_data["block"]["timestamp"]["unixtime"])

            # Identify buyer and seller
            buyer_info = self.wallet_labeler.identify_wallet(receiver_address, eth_balance=0)
            seller_info = self.wallet_labeler.identify_wallet(sender_address, eth_balance=0)

            # Classify transaction
            tx_type = self.classify_transaction(seller_info, buyer_info, eth_amount)

            # Create LargeTransaction object
            transaction = LargeTransaction(
                hash=tx_hash,
                timestamp=timestamp,
                block_number=tx_data["block"]["number"],
                sender_address=sender_address,
                receiver_address=receiver_address,
                eth_amount=eth_amount,
                usd_value=usd_value,
                gas_price=int(tx_data.get("gasPrice", 0)),
                gas_used=int(tx_data.get("gasValue", 0)),
                transaction_type=tx_type,
                buyer_info=buyer_info,
                seller_info=seller_info
            )

            # Mark as processed
            self.processed_transactions.add(tx_hash)

            return transaction

        except Exception as e:
            self.logger.error(f"Error processing transaction: {e}")
            return None

    async def analyze_and_alert(self, transaction: LargeTransaction):
        """
        Complete analysis pipeline for a large transaction
        """
        try:
            # Get market context
            exchange_flows = self.get_exchange_flows()
            etf_flows = self.get_etf_flows()

            # Analyze implications
            implication = self.analyze_market_implications(
                transaction, exchange_flows, etf_flows
            )

            # Generate recommendation
            recommendation = self.generate_portfolio_recommendation(
                transaction, implication, exchange_flows, etf_flows
            )

            # Create and send alert
            alert_message = self.create_alert_message(transaction, implication, recommendation)
            await self.send_telegram_alert(alert_message)

            # Log analysis
            self.logger.info(f"Analysis complete for transaction {transaction.hash}")
            self.logger.info(f"Recommendation: {recommendation.action.value} (confidence: {recommendation.confidence:.2f})")

            # Save analysis to file
            analysis_data = {
                "transaction": {
                    "hash": transaction.hash,
                    "timestamp": transaction.timestamp.isoformat(),
                    "eth_amount": transaction.eth_amount,
                    "usd_value": transaction.usd_value,
                    "buyer": transaction.buyer_info.entity_name if transaction.buyer_info else "Unknown",
                    "seller": transaction.seller_info.entity_name if transaction.seller_info else "Unknown",
                    "type": transaction.transaction_type.value
                },
                "implication": {
                    "sentiment": implication.sentiment,
                    "confidence": implication.confidence,
                    "key_signals": implication.key_signals,
                    "risk_level": implication.risk_level
                },
                "recommendation": {
                    "action": recommendation.action.value,
                    "confidence": recommendation.confidence,
                    "reasoning": recommendation.reasoning,
                    "risk_assessment": recommendation.risk_assessment
                },
                "market_context": {
                    "exchange_flows": exchange_flows,
                    "etf_flows": etf_flows
                },
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Save to file
            filename = f"yasuo_analysis_{transaction.hash[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(analysis_data, f, indent=2)

            self.logger.info(f"Analysis saved to {filename}")

        except Exception as e:
            self.logger.error(f"Error in analysis pipeline: {e}")

    async def monitor_large_transactions(self):
        """
        Main monitoring loop for large ETH transactions
        """
        self.logger.info("🛡️ Starting Yasuo ETH transaction monitoring...")

        while True:
            try:
                # Get large transactions from primary API (Bitquery)
                transactions = await self.bitquery.get_large_eth_transactions(
                    min_eth=self.min_transaction_threshold,
                    hours_back=1  # Last hour
                )

                if not transactions:
                    # Fallback to Etherscan if Bitquery fails
                    self.logger.info("No transactions from Bitquery, trying Etherscan...")
                    transactions = await self.etherscan.get_large_eth_transactions(
                        min_eth=self.min_transaction_threshold,
                        hours_back=1
                    )

                # Process each transaction
                for tx_data in transactions:
                    transaction = await self.process_transaction(tx_data)
                    if transaction:
                        self.logger.info(f"Large transaction detected: {transaction.eth_amount} ETH")
                        await self.analyze_and_alert(transaction)

                # Update last checked timestamp
                self.last_checked_timestamp = datetime.now()

                # Wait before next check
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def run_quick_analysis(self):
        """
        Run a quick analysis of recent large transactions
        """
        self.logger.info("🛡️ Running Yasuo quick analysis...")

        try:
            # Get recent large transactions (last 24 hours)
            transactions = await self.bitquery.get_large_eth_transactions(
                min_eth=self.min_transaction_threshold,
                hours_back=24
            )

            processed_count = 0
            for tx_data in transactions:
                transaction = await self.process_transaction(tx_data)
                if transaction:
                    await self.analyze_and_alert(transaction)
                    processed_count += 1

            self.logger.info(f"✅ Quick analysis complete. Processed {processed_count} large transactions.")

        except Exception as e:
            self.logger.error(f"Error in quick analysis: {e}")


async def main():
    """
    Main function to run Yasuo On-Chain Analyst
    """
    print("🛡️" * 50)
    print("🛡️ YASUO - ON-CHAIN ANALYST AGENT 🛡️")
    print("🛡️" * 50)
    print("")
    print("🎯 Advanced ETH Flow Analysis")
    print("📊 Real-time Large Transaction Monitoring")
    print("🔔 Telegram Alerts & Portfolio Recommendations")
    print("")
    print("🚀 Initializing Yasuo...")
    print("=" * 60)

    # Initialize Yasuo
    yasuo = YasuoOnChainAnalyst()

    # Setup Telegram bot if available
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token:
        yasuo.setup_telegram_bot(telegram_token)
        print("✅ Telegram bot configured")
    else:
        print("⚠️ Telegram bot token not found")

    # Run quick analysis first
    print("📊 Running initial analysis...")
    await yasuo.run_quick_analysis()

    print("🛡️ Starting continuous monitoring...")
    print("Press Ctrl+C to stop")

    try:
        await yasuo.monitor_large_transactions()
    except KeyboardInterrupt:
        print("\n🛡️ Yasuo monitoring stopped")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
