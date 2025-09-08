#!/usr/bin/env python3
"""
Debug Large Transactions - Check threshold, API, and whale activity
"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Manual API key for testing
API_KEY = "ory_at_HXyMLC1J5_4CdM3u5zmZdujaBYEx_VLxo7WpGb98abA.K4TxMK4bt_DewzOLSRAtLgV4V7Vad2qvOg0dav20Yac"

print("🔍 DEBUG LARGE TRANSACTIONS")
print("=" * 60)

url = "https://graphql.bitquery.io"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Test 1: Very low threshold (100 ETH)
print("Test 1: Low threshold (100 ETH)")
query1 = """
query {
  ethereum(network: ethereum) {
    transfers(
      currency: {is: "0x0000000000000000000000000000000000000000"}
      amount: {gt: 100.0}
      time: {since: {hours_ago: 24}}
      options: {desc: "amount", limit: 10}
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
      transaction {
        hash
      }
    }
  }
}
"""

data1 = {"query": query1}

try:
    response = requests.post(url, json=data1, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
        print(f"✅ Found {len(transfers)} transactions > 100 ETH")
        
        for i, tx in enumerate(transfers[:3]):
            amount = float(tx.get("amount", 0))
            sender = tx.get("sender", {}).get("address", "Unknown")
            receiver = tx.get("receiver", {}).get("address", "Unknown")
            print(f"  {i+1}. {amount:.2f} ETH: {sender[:10]}... -> {receiver[:10]}...")
    else:
        print(f"❌ Error: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

# Test 2: Medium threshold (1000 ETH)
print("Test 2: Medium threshold (1000 ETH)")
query2 = """
query {
  ethereum(network: ethereum) {
    transfers(
      currency: {is: "0x0000000000000000000000000000000000000000"}
      amount: {gt: 1000.0}
      time: {since: {hours_ago: 24}}
      options: {desc: "amount", limit: 10}
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

data2 = {"query": query2}

try:
    response2 = requests.post(url, json=data2, headers=headers, timeout=30)
    print(f"Status Code: {response2.status_code}")
    
    if response2.status_code == 200:
        data = response2.json()
        transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
        print(f"✅ Found {len(transfers)} transactions > 1000 ETH")
        
        for i, tx in enumerate(transfers[:3]):
            amount = float(tx.get("amount", 0))
            sender = tx.get("sender", {}).get("address", "Unknown")
            receiver = tx.get("receiver", {}).get("address", "Unknown")
            print(f"  {i+1}. {amount:.2f} ETH: {sender[:10]}... -> {receiver[:10]}...")
    else:
        print(f"❌ Error: {response2.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

# Test 3: Very high threshold (10000 ETH)
print("Test 3: High threshold (10000 ETH)")
query3 = """
query {
  ethereum(network: ethereum) {
    transfers(
      currency: {is: "0x0000000000000000000000000000000000000000"}
      amount: {gt: 10000.0}
      time: {since: {hours_ago: 24}}
      options: {desc: "amount", limit: 10}
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
    
    if response3.status_code == 200:
        data = response3.json()
        transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
        print(f"✅ Found {len(transfers)} transactions > 10000 ETH")
        
        for i, tx in enumerate(transfers[:3]):
            amount = float(tx.get("amount", 0))
            sender = tx.get("sender", {}).get("address", "Unknown")
            receiver = tx.get("receiver", {}).get("address", "Unknown")
            print(f"  {i+1}. {amount:.2f} ETH: {sender[:10]}... -> {receiver[:10]}...")
    else:
        print(f"❌ Error: {response3.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

# Test 4: Check recent blocks for any activity
print("Test 4: Recent blocks activity")
query4 = """
query {
  ethereum(network: ethereum) {
    blocks(limit: 5) {
      height
      timestamp {
        iso8601
      }
      transactionCount
    }
  }
}
"""

data4 = {"query": query4}

try:
    response4 = requests.post(url, json=data4, headers=headers, timeout=30)
    print(f"Status Code: {response4.status_code}")
    
    if response4.status_code == 200:
        data = response4.json()
        blocks = data.get("data", {}).get("ethereum", {}).get("blocks", [])
        print(f"✅ Found {len(blocks)} recent blocks")
        
        for i, block in enumerate(blocks[:3]):
            height = block.get("height", "Unknown")
            tx_count = block.get("transactionCount", 0)
            timestamp = block.get("timestamp", {}).get("iso8601", "Unknown")
            print(f"  {i+1}. Block {height}: {tx_count} transactions at {timestamp}")
    else:
        print(f"❌ Error: {response4.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("🎯 CONCLUSION:")
print("• If Test 1 shows transactions: Threshold too high")
print("• If Test 1 shows 0: No whale activity or API issue")
print("• If Test 4 shows blocks: API working, check transfers")
print("• If Test 4 fails: API connection issue")



