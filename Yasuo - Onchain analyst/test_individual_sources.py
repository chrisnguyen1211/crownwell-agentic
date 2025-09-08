#!/usr/bin/env python3
"""
Test Individual Data Sources for Yasuo
"""

import asyncio
import sys
import requests
from bs4 import BeautifulSoup

# Add the current directory to path
sys.path.insert(0, '.')

async def test_bitquery_basic():
    """Test basic Bitquery connectivity"""
    print("🔍 Testing Bitquery API...")

    # Test basic query
    query = """
    query {
      ethereum(network: ethereum) {
        blocks(height: {min: 18000000}) {
          height
          timestamp {
            unixtime
          }
        }
      }
    }
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer ory_at_HXyMLC1J5_4CdM3u5zmZdujaBYEx_VLxo7WpGb98abA.K4TxMK4bt_DewzOLSRAtLgV4V7Vad2qvOg0dav20Yac"
    }

    try:
        response = requests.post(
            "https://graphql.bitquery.io",
            json={"query": query},
            headers=headers,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Bitquery API working!")
            print(f"Response: {data}")
        else:
            print(f"❌ Bitquery API error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Bitquery test failed: {e}")

def test_farside_basic():
    """Test basic farside.co.uk connectivity"""
    print("\n🔍 Testing farside.co.uk...")

    urls = [
        "https://farside.co.uk/eth/",
        "https://farside.co.uk/btc/"
    ]

    for url in urls:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)
            print(f"{url}: Status {response.status_code}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                print(f"✅ {url} accessible")
                print(f"Title: {soup.title.string if soup.title else 'No title'}")
            else:
                print(f"❌ {url} blocked: {response.status_code}")

        except Exception as e:
            print(f"❌ {url} failed: {e}")

async def test_yasuo_components():
    """Test individual Yasuo components"""
    print("\n🔍 Testing Yasuo components...")

    try:
        from yasuo_onchain_analyst import YasuoOnChainAnalyst

        yasuo = YasuoOnChainAnalyst()

        print("✅ Yasuo initialized")

        # Test each component individually
        print("\n📊 Testing Exchange Tracker...")
        try:
            exchange_data = await yasuo.get_exchange_flows()
            print(f"Exchange data keys: {list(exchange_data.keys())}")
            print(f"Data source: {exchange_data.get('data_source')}")
        except Exception as e:
            print(f"❌ Exchange tracker failed: {e}")

        print("\n📊 Testing ETF Tracker...")
        try:
            etf_data = await yasuo.get_etf_flows()
            print(f"ETF data keys: {list(etf_data.keys())}")
            print(f"Data source: {etf_data.get('data_source')}")
        except Exception as e:
            print(f"❌ ETF tracker failed: {e}")

        print("\n🎯 Testing Liveliness Tracker...")
        try:
            liveliness_data = await yasuo.get_liveliness_metrics()
            print(f"Liveliness data keys: {list(liveliness_data.keys())}")
            print(f"Data source: {liveliness_data.get('data_source')}")
        except Exception as e:
            print(f"❌ Liveliness tracker failed: {e}")

    except Exception as e:
        print(f"❌ Yasuo components test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("🛡️ YASUO DATA SOURCES TEST")
    print("=" * 50)

    # Test basic connectivity
    await test_bitquery_basic()
    test_farside_basic()

    # Test Yasuo components
    await test_yasuo_components()

    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())

