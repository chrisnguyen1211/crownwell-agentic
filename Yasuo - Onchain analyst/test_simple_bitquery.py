#!/usr/bin/env python3
"""
Test simple Bitquery queries in Yasuo context
"""

import asyncio
import sys
import requests

# Add the current directory to path
sys.path.insert(0, '.')

async def test_simple_bitquery_in_yasuo():
    """Test simple Bitquery query using Yasuo's BitqueryAPI class"""

    try:
        from yasuo_onchain_analyst import BitqueryAPI

        # Initialize Bitquery API
        bitquery = BitqueryAPI()

        print("🔍 Testing simple Bitquery query in Yasuo context...")

        # Simple query to test
        simple_query = """
        {
          bitcoin {
            blocks {
              count
            }
          }
        }
        """

        # Make the request
        response = requests.post(
            bitquery.base_url,
            json={"query": simple_query},
            headers=bitquery._get_headers(),
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Simple Bitquery query successful!")
            print(f"Response: {data}")

            # Check rate limit info
            remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            print(f"Rate limit remaining: {remaining}")

        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"Response: {response.text}")

        # Test the complex exchange query
        print("\n🔍 Testing complex exchange query...")
        complex_query = """
        query GetExchangeETHFlows($addresses: [String!]!, $hoursBack: Int!) {
          ethereum(network: ethereum) {
            transfers(
              currency: {is: "ETH"}
              any: [{sender: {in: $addresses}}, {receiver: {in: $addresses}}]
              time: {since: {hoursAgo: $hoursBack}}
              options: {limit: 10}
            ) {
              sender { address }
              receiver { address }
              amount
            }
          }
        }
        """

        variables = {
            "addresses": ["0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE"],
            "hoursBack": 1
        }

        response2 = requests.post(
            bitquery.base_url,
            json={"query": complex_query, "variables": variables},
            headers=bitquery._get_headers(),
            timeout=30
        )

        print(f"Complex query status: {response2.status_code}")

        if response2.status_code == 200:
            print("✅ Complex query also successful!")
        else:
            print(f"❌ Complex query failed: {response2.status_code}")
            print(f"Response: {response2.text[:200]}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_bitquery_in_yasuo())











