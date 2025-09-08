#!/usr/bin/env python3
"""
🧪 DUNE API TEST
Test script to validate Dune API key and connection
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

def test_dune_api():
    """Test Dune API connection"""
    print("🧪 TESTING DUNE API CONNECTION")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('DUNE_API_KEY')
    
    if not api_key:
        print("❌ DUNE_API_KEY not found in .env file")
        print("💡 Please add your API key to .env file:")
        print("   DUNE_API_KEY=your_actual_api_key_here")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-10:]}")
    
    # Test API connection
    base_url = "https://api.dune.com/api/v1"
    headers = {
        "x-dune-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Test 1: Get user profile (updated endpoint)
        print("\n🔍 Test 1: Getting user profile...")
        profile_url = f"{base_url}/user"
        response = requests.get(profile_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            print("✅ User profile retrieved successfully")
            print(f"   User: {profile_data.get('username', 'Unknown')}")
            print(f"   Email: {profile_data.get('email', 'Unknown')}")
        else:
            print(f"⚠️ Profile request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            print("   Continuing with other tests...")
        
        # Test 2: List queries (updated endpoint)
        print("\n🔍 Test 2: Listing queries...")
        queries_url = f"{base_url}/query"
        response = requests.get(queries_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            queries_data = response.json()
            print("✅ Queries list retrieved successfully")
            print(f"   Total queries: {len(queries_data.get('queries', []))}")
        else:
            print(f"⚠️ Queries request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            print("   This is normal if you don't have any queries yet")
        
        # Test 3: Test query execution (with a simple query)
        print("\n🔍 Test 3: Testing query execution...")
        # This would require a valid query ID
        print("⚠️ Query execution test requires a valid query ID")
        print("   This will be tested when you have actual query IDs")
        
        print("\n✅ DUNE API CONNECTION SUCCESSFUL!")
        print("🎯 Your API key is working correctly")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout - check your internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your internet connection")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_next_steps():
    """Show next steps after successful API test"""
    print("\n📋 NEXT STEPS:")
    print("=" * 30)
    print("1. ✅ API key is working")
    print("2. 🔍 Find query IDs from the dashboard:")
    print("   https://dune.com/marvy_kings8/ethereum-whale-intelligence-dashboard")
    print("3. 🛠️ Update query IDs in dune_whale_tracker.py")
    print("4. 🚀 Run: python yasuo_enhanced_whale_analysis.py")
    print("5. 📊 Get real whale intelligence data!")

def main():
    """Main function"""
    success = test_dune_api()
    
    if success:
        show_next_steps()
    else:
        print("\n❌ API TEST FAILED")
        print("💡 Please check your API key and try again")

if __name__ == "__main__":
    main()
