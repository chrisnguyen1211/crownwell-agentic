#!/usr/bin/env python3
"""
Yasuo Configuration Module
Centralized configuration management for the On-Chain Analyst Agent
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YasuoConfig:
    """
    Configuration class for Yasuo On-Chain Analyst
    """

    # API Keys
    BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY")
    ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
    MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Transaction Monitoring Settings
    MIN_TRANSACTION_THRESHOLD = float(os.getenv("YASUO_MIN_TRANSACTION_THRESHOLD", "1000"))  # ETH
    MONITORING_INTERVAL = int(os.getenv("YASUO_MONITORING_INTERVAL", "300"))  # seconds
    ALERT_THRESHOLD_USD = float(os.getenv("YASUO_ALERT_THRESHOLD_USD", "4000000"))  # $4M
    HOURS_BACK = int(os.getenv("YASUO_HOURS_BACK", "24"))  # hours

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "yasuo_analysis.log")

    # Analysis Parameters
    ETH_PRICE_ESTIMATE = 4000  # USD per ETH (fallback - would be updated from API)

    # Rate Limiting
    BITQUERY_RATE_LIMIT = 100  # requests per day
    ETHERSCAN_RATE_LIMIT = 5   # requests per second

    # Wallet Labeling Thresholds
    WHALE_BALANCE_THRESHOLD = 10000  # ETH
    ACTIVE_TRADER_THRESHOLD = 50     # transactions per month

    # Market Analysis Weights
    ANALYSIS_WEIGHTS = {
        "transaction_size": 0.4,
        "entity_type": 0.3,
        "market_context": 0.2,
        "historical_pattern": 0.1
    }

    # Portfolio Recommendation Thresholds
    BUY_CONFIDENCE_THRESHOLD = 0.7
    SELL_CONFIDENCE_THRESHOLD = 0.6
    HOLD_CONFIDENCE_THRESHOLD = 0.5

    # Exchange Flow Thresholds
    LARGE_OUTFLOW_THRESHOLD = 100000   # ETH (accumulation signal)
    LARGE_INFLOW_THRESHOLD = -100000   # ETH (selling signal)

    # ETF Flow Thresholds
    STRONG_ETF_INFLOW = 50000000       # $50M daily (bullish)
    MODERATE_ETF_INFLOW = 10000000     # $10M daily
    SMALL_ETF_FLOW = 5000000          # $5M daily

    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """
        Validate configuration and return status
        """
        issues = []
        warnings = []

        # Check required API keys
        if not cls.BITQUERY_API_KEY:
            warnings.append("BITQUERY_API_KEY not set - using fallback APIs only")

        if not cls.ETHERSCAN_API_KEY:
            warnings.append("ETHERSCAN_API_KEY not set - Etherscan fallback unavailable")

        # Check Telegram configuration
        if not cls.TELEGRAM_BOT_TOKEN:
            issues.append("TELEGRAM_BOT_TOKEN not set - Telegram alerts disabled")
        elif not cls.TELEGRAM_CHAT_ID:
            issues.append("TELEGRAM_CHAT_ID not set - Telegram alerts disabled")

        # Validate thresholds
        if cls.MIN_TRANSACTION_THRESHOLD < 100:
            warnings.append("MIN_TRANSACTION_THRESHOLD is very low - may generate too many alerts")

        if cls.MONITORING_INTERVAL < 60:
            warnings.append("MONITORING_INTERVAL is very short - may hit API rate limits")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "config_summary": {
                "primary_api": "Bitquery" if cls.BITQUERY_API_KEY else "Etherscan",
                "telegram_enabled": bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID),
                "min_threshold": f"{cls.MIN_TRANSACTION_THRESHOLD} ETH",
                "monitoring_interval": f"{cls.MONITORING_INTERVAL}s",
                "alert_threshold": f"${cls.ALERT_THRESHOLD_USD:,.0f}"
            }
        }

    @classmethod
    def get_api_status(cls) -> Dict[str, bool]:
        """
        Get status of available APIs
        """
        return {
            "bitquery": bool(cls.BITQUERY_API_KEY),
            "etherscan": bool(cls.ETHERSCAN_API_KEY),
            "moralis": bool(cls.MORALIS_API_KEY),
            "telegram": bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID)
        }

    @classmethod
    def print_config_summary(cls):
        """
        Print configuration summary
        """
        print("🛡️ YASUO CONFIGURATION SUMMARY")
        print("=" * 40)

        validation = cls.validate_config()

        print(f"📊 Monitoring: {cls.MIN_TRANSACTION_THRESHOLD} ETH+ transactions")
        print(f"⏰ Check Interval: {cls.MONITORING_INTERVAL} seconds")
        print(f"💰 Alert Threshold: ${cls.ALERT_THRESHOLD_USD:,.0f}")

        print("\n🔑 API Status:")
        api_status = cls.get_api_status()
        for api, available in api_status.items():
            status = "✅" if available else "❌"
            print(f"  {status} {api.title()}: {'Available' if available else 'Not configured'}")

        if validation["issues"]:
            print("\n❌ Issues:")
            for issue in validation["issues"]:
                print(f"  • {issue}")

        if validation["warnings"]:
            print("\n⚠️ Warnings:")
            for warning in validation["warnings"]:
                print(f"  • {warning}")

        print("\n✅ Configuration loaded successfully!")


# Global configuration instance
config = YasuoConfig()
