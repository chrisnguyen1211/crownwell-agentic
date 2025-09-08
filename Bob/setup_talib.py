#!/usr/bin/env python3
"""
TA-Lib Setup Guide for Bob
Install TA-Lib properly on different systems
"""

import sys
import platform
import subprocess
import os

def check_talib_installation():
    """Check if TA-Lib is properly installed"""
    try:
        import talib
        print("✅ TA-Lib is already installed!")
        
        # Test a basic function
        import numpy as np
        test_data = np.random.random(50)
        sma = talib.SMA(test_data, timeperiod=10)
        print("✅ TA-Lib is working correctly!")
        return True
        
    except ImportError:
        print("❌ TA-Lib is not installed")
        return False

def install_talib():
    """Install TA-Lib based on platform"""
    
    system = platform.system().lower()
    print(f"🔧 Installing TA-Lib on {system}...")
    
    if system == "darwin":  # macOS
        install_talib_macos()
    elif system == "linux":
        install_talib_linux() 
    elif system == "windows":
        install_talib_windows()
    else:
        print(f"❌ Unsupported platform: {system}")

def install_talib_macos():
    """Install TA-Lib on macOS"""
    print("🍎 Installing TA-Lib on macOS...")
    
    try:
        # Check if Homebrew is installed
        subprocess.run(["brew", "--version"], check=True, capture_output=True)
        print("✅ Homebrew detected")
        
        # Install ta-lib via Homebrew
        print("📦 Installing ta-lib C library...")
        subprocess.run(["brew", "install", "ta-lib"], check=True)
        
        # Install Python wrapper
        print("🐍 Installing Python TA-Lib wrapper...")
        subprocess.run([sys.executable, "-m", "pip", "install", "TA-Lib"], check=True)
        
        print("✅ TA-Lib installation completed!")
        
    except subprocess.CalledProcessError:
        print("❌ Homebrew not found. Please install Homebrew first:")
        print("🔗 https://brew.sh/")
        print("Then run: brew install ta-lib")
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        print("📋 Manual installation steps:")
        print("1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("2. Install ta-lib: brew install ta-lib")
        print("3. Install Python wrapper: pip install TA-Lib")

def install_talib_linux():
    """Install TA-Lib on Linux"""
    print("🐧 Installing TA-Lib on Linux...")
    
    print("📋 Manual installation required:")
    print("1. Download TA-Lib source:")
    print("   wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz")
    print("   tar -xzf ta-lib-0.4.0-src.tar.gz")
    print("   cd ta-lib/")
    print("   ./configure --prefix=/usr")
    print("   make")
    print("   sudo make install")
    print("2. Install Python wrapper:")
    print("   pip install TA-Lib")

def install_talib_windows():
    """Install TA-Lib on Windows"""
    print("🪟 Installing TA-Lib on Windows...")
    
    print("📋 Windows installation options:")
    print("Option 1 - Using conda (recommended):")
    print("   conda install -c conda-forge ta-lib")
    print()
    print("Option 2 - Using pip with pre-compiled wheel:")
    print("   pip install TA-Lib")
    print()
    print("Option 3 - Manual compilation:")
    print("   1. Download TA-Lib C library")
    print("   2. Extract to C:\\ta-lib")
    print("   3. pip install TA-Lib")

def main():
    """Main setup function"""
    print("🔧 BOB'S TA-LIB SETUP ASSISTANT")
    print("=" * 40)
    
    if check_talib_installation():
        print("🎉 TA-Lib is ready for Bob's analysis!")
        return
    
    print("📦 TA-Lib installation required...")
    response = input("Would you like to attempt automatic installation? (y/n): ")
    
    if response.lower() == 'y':
        install_talib()
        
        # Recheck installation
        print("\n🔍 Verifying installation...")
        if check_talib_installation():
            print("🎉 TA-Lib successfully installed!")
        else:
            print("❌ Installation may have failed. Please follow manual steps.")
    else:
        print("📋 Please install TA-Lib manually and run this script again.")

if __name__ == "__main__":
    main()
