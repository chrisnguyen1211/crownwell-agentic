#!/usr/bin/env python3
"""
Deep debug Bitquery API - Fix GraphQL queries and data access
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = "ory_at_HXyMLC1J5_4CdM3u5zmZdujaBYEx_VLxo7WpGb98abA.K4TxMK4bt_DewzOLSRAtLgV4V7Vad2qvOg0dav20Yac"

print("🔍 DEEP DEBUG BITQUERY API")
print("=" * 60)

url = "https://graphql.bitquery.io"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Test 1: Basic blocks query (simplest possible)
print("Test 1: Basic blocks query")
query1 = """
query {
  ethereum {
    blocks {
      height
    }
  }
}
"""

try:
    response = requests.post(url, json={"query": query1}, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print(f"❌ GraphQL Errors: {data['errors']}")
        else:
            blocks = data.get("data", {}).get("ethereum", {}).get("blocks", [])
            print(f"✅ Found {len(blocks)} blocks")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

# Test 2: Simple transfers query
print("Test 2: Simple transfers query")
query2 = """
query {
  ethereum {
    transfers {
      amount
      sender {
        address
      }
      receiver {
        address
      }
    }
  }
}
"""

try:
    response = requests.post(url, json={"query": query2}, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print(f"❌ GraphQL Errors: {data['errors']}")
        else:
            transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
            print(f"✅ Found {len(transfers)} transfers")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

# Test 3: Transfers with limit
print("Test 3: Transfers with limit")
query3 = """
query {
  ethereum {
    transfers(options: {limit: 5}) {
      amount
      sender {
        address
      }
      receiver {
        address
      }
    }
  }
}
"""

try:
    response = requests.post(url, json={"query": query3}, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print(f"❌ GraphQL Errors: {data['errors']}")
        else:
            transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
            print(f"✅ Found {len(transfers)} transfers")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

# Test 4: Check API key permissions
print("Test 4: Check API key info")
query4 = """
query {
  __schema {
    queryType {
      name
    }
  }
}
"""

try:
    response = requests.post(url, json={"query": query4}, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print(f"❌ GraphQL Errors: {data['errors']}")
        else:
            print(f"✅ Schema accessible")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

# Test 5: Try different network
print("Test 5: Try different network")
query5 = """
query {
  bitcoin {
    blocks {
      height
    }
  }
}
"""

try:
    response = requests.post(url, json={"query": query5}, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print(f"❌ GraphQL Errors: {data['errors']}")
        else:
            blocks = data.get("data", {}).get("bitcoin", {}).get("blocks", [])
            print(f"✅ Found {len(blocks)} Bitcoin blocks")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("🎯 DIAGNOSIS:")
print("• If all queries return 0 results: API key has limited access")
print("• If queries have GraphQL errors: Syntax issues")
print("• If Bitcoin works but Ethereum doesn't: Ethereum data restricted")
print("• If schema works: API key valid but data access limited")






