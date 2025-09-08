#!/usr/bin/env python3
"""
📈 BOB LAUNCHER
Quick launcher for Bob - Technical Analysis Agent
Expert Quant Trader for ETH Analysis
"""

import sys
import json
from datetime import datetime

def print_bob_banner():
    """Print Bob's professional banner"""
    print("📈" * 50)
    print("📈 BOB - TECHNICAL ANALYSIS AGENT 📈")
    print("📈" * 50)
    print("")
    print("🎯 Expert Quant Trader from Top Hedge Fund")
    print("📊 Full TA-Lib Integration (100+ Indicators)")  
    print("⏰ Multi-Timeframe Analysis (1H, 4H, 1D)")
    print("🧠 Advanced Pattern Recognition")
    print("💹 Professional Trading Signals")
    print("")
    print("🚀 Starting Bob's Analysis...")
    print("=" * 60)

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔧 Checking Bob's tools...")
    
    missing_deps = []
    
    # Check core dependencies
    try:
        import numpy
        print("✅ NumPy available")
    except ImportError:
        missing_deps.append("numpy")
        
    try:
        import pandas
        print("✅ Pandas available")
    except ImportError:
        missing_deps.append("pandas")
        
    try:
        import yfinance
        print("✅ YFinance available")
    except ImportError:
        missing_deps.append("yfinance")
    
    # Check TA-Lib (critical)
    try:
        import talib
        print("✅ TA-Lib available")
        
        # Test TA-Lib functionality
        import numpy as np
        test_data = np.random.random(50)
        sma = talib.SMA(test_data, timeperiod=10)
        print("✅ TA-Lib working correctly")
        
    except ImportError:
        missing_deps.append("TA-Lib")
        print("❌ TA-Lib not found!")
        print("💡 Run: python3 setup_talib.py")
        
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("📦 Install with: pip install " + " ".join(missing_deps))
        return False
    
    print("✅ All dependencies ready")
    return True

async def run_bob_analysis():
    """Run Bob's technical analysis"""
    
    try:
        print("📈 Importing Bob's analysis engine...")
        from technical_analysis_engine import BobTechnicalAnalysisEngine, run_bob_analysis
        
        print("🧠 Initializing Bob...")
        
        # Run comprehensive analysis
        analysis = await run_bob_analysis()
        
        if analysis:
            # Save analysis to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'bob_analysis_{timestamp}.json'
            
            # Clean analysis for JSON serialization
            clean_analysis = clean_for_json(analysis)
            
            with open(filename, 'w') as f:
                json.dump(clean_analysis, f, indent=2, default=str)
            
            print(f"\n📁 Analysis saved to: {filename}")
            
            # Show quick summary
            print_analysis_summary(analysis)
            
        else:
            print("❌ Analysis failed")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Error running Bob's analysis: {e}")
        import traceback
        traceback.print_exc()

def clean_for_json(obj):
    """Clean analysis object for JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif hasattr(obj, 'tolist'):  # numpy arrays
        return obj.tolist()
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    else:
        return str(obj)

def print_analysis_summary(analysis):
    """Print quick analysis summary"""
    
    print("\n📊 BOB'S QUICK SUMMARY:")
    print("=" * 40)
    
    if 'master_signal' in analysis:
        master = analysis['master_signal']
        print(f"🎯 Direction: {master.get('direction', 'Unknown')}")
        print(f"💪 Strength: {master.get('strength', 0):.3f}")
        print(f"🎲 Confidence: {analysis.get('bob_confidence', 0):.2f}")
        
        if 'action' in master:
            print(f"💹 Action: {master.get('action', 'Unknown')}")
        
        print(f"⚠️ Risk Level: {master.get('risk_level', 'Unknown')}")
    
    if 'timeframe_analysis' in analysis:
        print(f"\n⏰ Timeframe Signals:")
        for tf, tf_data in analysis['timeframe_analysis'].items():
            if 'signal' in tf_data and 'strength' in tf_data:
                signal = tf_data['signal']  # This is now a string
                strength = tf_data['strength']  # This is a float
                print(f"   {tf.upper()}: {signal} ({strength:.2f})")

def main():
    """Main launcher function"""
    print_bob_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)
    
    # Run analysis
    print("📈 Starting Bob's technical analysis...")
    import asyncio
    asyncio.run(run_bob_analysis())
    
    print("\n📈" * 50)
    print("📈 Bob completed his analysis! 📈")
    print("📈" * 50)

if __name__ == "__main__":
    main()
