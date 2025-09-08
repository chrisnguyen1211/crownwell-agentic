#!/usr/bin/env python3
"""
🌸 LILY LAUNCHER
Quick launcher for Lily - Social Media Sentiment Crawler Bot
"""

import asyncio
import os
import sys
from datetime import datetime

def print_lily_banner():
    """Print Lily's welcome banner"""
    print("🌸" * 50)
    print("🌸 LILY - SOCIAL MEDIA SENTIMENT CRAWLER BOT 🌸")
    print("🌸" * 50)
    print("")
    print("🎯 ETH Sentiment Analysis Agent")
    print("📱 Multi-Platform Social Media Monitoring")
    print("🧠 Advanced AI-Powered Analysis")
    print("💾 Real-time Database Integration")
    print("")
    print("🚀 Starting Lily...")
    print("=" * 60)

def check_environment():
    """Check if environment is properly configured"""
    print("🔧 Checking environment...")
    
    # Check for Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found!")
        print("💡 Please run: export $(cat ../.env.supabase | xargs)")
        return False
    
    print("✅ Environment configured")
    return True

def main():
    """Main launcher function"""
    print_lily_banner()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Import and run Lily
    try:
        print("🌸 Importing Lily's modules...")
        from standalone_sentiment_bot import LilySentimentBot
        
        print("🌸 Initializing Lily...")
        
        async def run_lily():
            lily = LilySentimentBot()
            await lily.run_complete_analysis()
        
        print("🌸 Starting Lily's analysis...")
        asyncio.run(run_lily())
        
        print("")
        print("🌸" * 50)
        print("🌸 Lily completed her analysis! 🌸")
        print("🌸" * 50)
        
    except KeyboardInterrupt:
        print("\n🌸 Lily was interrupted. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error running Lily: {e}")
        print("💡 Check README.md for troubleshooting")

if __name__ == "__main__":
    main()
