#!/usr/bin/env python3
"""
Test Bitquery with correct GraphQL syntax
"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Manual API key for testing
API_KEY = "ory_at_HXyMLC1J5_4CdM3u5zmZdujaBYEx_VLxo7WpGb98abA.K4TxMK4bt_DewzOLSRAtLgV4V7Vad2qvOg0dav20Yac"

print("🔍 Bitquery API Test - Correct Syntax")
print("=" * 50)

url = "https://graphql.bitquery.io"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Test 1: Correct blocks query
print("Test 1: Correct blocks query")
query1 = """
query {
  ethereum {
    blocks(limit: 1) {
      height
      timestamp {
        iso8601
      }
    }
  }
}
"""

data1 = {"query": query1}

try:
    response = requests.post(url, json=data1, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
    
    if response.status_code == 200:
        print("✅ Blocks query works!")
    else:
        print("❌ Blocks query failed")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)

# Test 2: Large transactions query
print("Test 2: Large transactions query")
query2 = """
query {
  ethereum {
    transfers(
      options: {limit: 10}
      amount: {gt: "1000000000000000000000"}
      currency: {is: "0x0000000000000000000000000000000000000000"}
    ) {
      amount
      sender {
        address
      }
      receiver {
        address
      }
      transaction {
        hash
      }
    }
  }
}
"""

data2 = {"query": query2}

try:
    response2 = requests.post(url, json=data2, headers=headers, timeout=30)
    print(f"Status Code: {response2.status_code}")
    print(f"Response: {response2.text[:300]}...")
    
    if response2.status_code == 200:
        print("✅ Large transactions query works!")
    else:
        print("❌ Large transactions query failed")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)

# Test 3: Exchange flows query
print("Test 3: Exchange flows query")
query3 = """
query {
  ethereum {
    transfers(
      options: {limit: 5}
      amount: {gt: "100000000000000000000"}
      currency: {is: "0x0000000000000000000000000000000000000000"}
    ) {
      amount
      sender {
        address
        annotation
      }
      receiver {
        address
        annotation
      }
    }
  }
}
"""

data3 = {"query": query3}

try:
    response3 = requests.post(url, json=data3, headers=headers, timeout=30)
    print(f"Status Code: {response3.status_code}")
    print(f"Response: {response3.text[:300]}...")
    
    if response3.status_code == 200:
        print("✅ Exchange flows query works!")
    else:
        print("❌ Exchange flows query failed")
except Exception as e:
    print(f"❌ Error: {e}")






