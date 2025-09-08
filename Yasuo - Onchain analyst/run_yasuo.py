#!/usr/bin/env python3
"""
🛡️ YASUO LAUNCHER
Quick launcher for Yasuo - On-Chain ETH Analyst Agent
Advanced Real-time ETH Flow Analysis & Portfolio Recommendations
"""

import sys
import asyncio
import argparse
from datetime import datetime

def print_yasuo_banner():
    """Print Yasuo's professional banner"""
    print("🛡️" * 50)
    print("🛡️ YASUO - ON-CHAIN ETH ANALYST 🛡️")
    print("🛡️" * 50)
    print("")
    print("🎯 Advanced Ethereum Flow Analysis")
    print("📊 Real-time Large Transaction Monitoring")
    print("🔍 Buyer/Seller Entity Identification")
    print("📈 Market Implication Analysis")
    print("💼 Portfolio Action Recommendations")
    print("🔔 Telegram Alert Integration")
    print("")
    print("🚀 Starting Yasuo's Analysis...")
    print("=" * 60)

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔧 Checking Yasuo's tools...")

    missing_deps = []
    optional_deps = []

    # Check core dependencies
    try:
        import requests
        print("✅ Requests available")
    except ImportError:
        missing_deps.append("requests")

    try:
        import asyncio
        print("✅ AsyncIO available")
    except ImportError:
        missing_deps.append("asyncio")

    # Check Telegram bot
    try:
        from telegram import Bot
        print("✅ Python Telegram Bot available")
    except ImportError:
        optional_deps.append("python-telegram-bot (for alerts)")

    # Check data processing
    try:
        import pandas
        print("✅ Pandas available")
    except ImportError:
        optional_deps.append("pandas")

    try:
        import numpy
        print("✅ NumPy available")
    except ImportError:
        optional_deps.append("numpy")

    # Check dotenv
    try:
        from dotenv import load_dotenv
        print("✅ Python-dotenv available")
    except ImportError:
        optional_deps.append("python-dotenv")

    # Check Moralis (optional)
    try:
        import moralis
        print("✅ Moralis available")
    except ImportError:
        optional_deps.append("moralis (optional fallback API)")

    if missing_deps:
        print(f"\n❌ Missing critical dependencies: {', '.join(missing_deps)}")
        print("📦 Install with: pip install " + " ".join(missing_deps))
        return False

    if optional_deps:
        print(f"\n⚠️ Optional dependencies not found: {', '.join(optional_deps)}")
        print("📦 Install with: pip install " + " ".join([d.split()[0] for d in optional_deps]))

    print("✅ Core dependencies ready")
    return True

def setup_environment():
    """Setup environment and validate configuration"""
    print("🔧 Setting up environment...")

    try:
        from config import YasuoConfig
        config_status = YasuoConfig.validate_config()

        if config_status["issues"]:
            print("\n❌ Configuration Issues:")
            for issue in config_status["issues"]:
                print(f"  • {issue}")
            return False

        if config_status["warnings"]:
            print("\n⚠️ Configuration Warnings:")
            for warning in config_status["warnings"]:
                print(f"  • {warning}")

        print("✅ Environment configured")
        return True

    except ImportError:
        print("❌ Could not import configuration module")
        return False
    except Exception as e:
        print(f"❌ Error setting up environment: {e}")
        return False

async def run_yasuo_analysis(mode="monitor", hours_back=24):
    """Run Yasuo's analysis"""

    try:
        print("📊 Importing Yasuo's analysis engine...")
        from yasuo_onchain_analyst import YasuoOnChainAnalyst

        print("🛡️ Initializing Yasuo...")
        yasuo = YasuoOnChainAnalyst()

        # Setup Telegram if configured
        telegram_token = YasuoConfig.TELEGRAM_BOT_TOKEN if 'YasuoConfig' in globals() else None
        if not telegram_token:
            from config import YasuoConfig
            telegram_token = YasuoConfig.TELEGRAM_BOT_TOKEN

        if telegram_token:
            yasuo.setup_telegram_bot(telegram_token)
            print("✅ Telegram alerts enabled")
        else:
            print("⚠️ Telegram alerts disabled (no token configured)")

        if mode == "quick":
            print(f"📊 Running quick analysis (last {hours_back} hours)...")
            await yasuo.run_quick_analysis()
            print("✅ Quick analysis completed")

        elif mode == "monitor":
            print("🛡️ Starting continuous monitoring...")
            print("Press Ctrl+C to stop monitoring")

            try:
                await yasuo.monitor_large_transactions()
            except KeyboardInterrupt:
                print("\n🛡️ Monitoring stopped by user")

        else:
            print(f"❌ Unknown mode: {mode}")
            print("Available modes: quick, monitor")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Error running Yasuo's analysis: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description="Yasuo - On-Chain ETH Analyst")
    parser.add_argument(
        "mode",
        choices=["quick", "monitor"],
        default="quick",
        nargs="?",
        help="Analysis mode: quick (one-time analysis) or monitor (continuous)"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours to look back for quick analysis (default: 24)"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Show configuration summary only"
    )

    args = parser.parse_args()

    print_yasuo_banner()

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)

    # Setup environment
    if not setup_environment():
        print("\n❌ Please fix configuration issues first")
        sys.exit(1)

    # Show config if requested
    if args.config:
        try:
            from config import YasuoConfig
            YasuoConfig.print_config_summary()
        except Exception as e:
            print(f"❌ Error loading config: {e}")
        sys.exit(0)

    # Run analysis
    print("📈 Starting Yasuo's analysis...")
    asyncio.run(run_yasuo_analysis(args.mode, args.hours))

    print("\n🛡️" * 50)
    print("🛡️ Yasuo analysis completed! 🛡️")
    print("🛡️" * 50)

if __name__ == "__main__":
    main()
