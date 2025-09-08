#!/usr/bin/env python3
"""
Direct Bitquery API test with manual key
"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Manual API key for testing
API_KEY = "ory_at_HXyMLC1J5_4CdM3u5zmZdujaBYEx_VLxo7WpGb98abA.K4TxMK4bt_DewzOLSRAtLgV4V7Vad2qvOg0dav20Yac"

print("🔍 Direct Bitquery API Test")
print("=" * 50)

# Test 1: Simple query with Bearer token
print("Test 1: Simple query with Bearer token")
url = "https://graphql.bitquery.io"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

query = """
{
  ethereum {
    blocks(limit: 1) {
      height
    }
  }
}
"""

data = {"query": query}

try:
    response = requests.post(url, json=data, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    if response.status_code == 200:
        print("✅ Bearer token works!")
    else:
        print("❌ Bearer token failed")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)

# Test 2: Simple query with X-API-KEY
print("Test 2: Simple query with X-API-KEY")
headers2 = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

try:
    response2 = requests.post(url, json=data, headers=headers2, timeout=30)
    print(f"Status Code: {response2.status_code}")
    print(f"Response: {response2.text[:200]}...")
    
    if response2.status_code == 200:
        print("✅ X-API-KEY works!")
    else:
        print("❌ X-API-KEY failed")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)

# Test 3: Check environment variable
print("Test 3: Environment variable check")
env_key = os.getenv("BITQUERY_API_KEY")
print(f"Environment BITQUERY_API_KEY: {env_key[:20] if env_key else 'Not set'}...")

print("\n" + "=" * 50)

# Test 4: Test with different query format
print("Test 4: Different query format")
query2 = """
query {
  ethereum {
    blocks(limit: 1) {
      height
    }
  }
}
"""

data2 = {"query": query2}

try:
    response3 = requests.post(url, json=data2, headers=headers, timeout=30)
    print(f"Status Code: {response3.status_code}")
    print(f"Response: {response3.text[:200]}...")
    
    if response3.status_code == 200:
        print("✅ Query format works!")
    else:
        print("❌ Query format failed")
except Exception as e:
    print(f"❌ Error: {e}")



