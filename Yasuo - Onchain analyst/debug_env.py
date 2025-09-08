#!/usr/bin/env python3
"""
Debug environment variables in Yasuo context
"""

import os
import sys

# Add the current directory to path
sys.path.insert(0, '.')

def debug_environment():
    """Debug environment variables"""

    print("🔍 Environment Variables Debug")
    print("=" * 50)

    # Check environment variables
    api_key = os.getenv("BITQUERY_API_KEY")
    print(f"BITQUERY_API_KEY: {'Set' if api_key else 'Not set'}")
    if api_key:
        print(f"  Key starts with: {api_key[:20]}...")
        print(f"  Key contains 'ory_at_': {'ory_at_' in api_key}")
    else:
        print("❌ API key not found in environment!")
        print("Setting it manually for testing...")
        os.environ["BITQUERY_API_KEY"] = "ory_at_HXyMLC1J5_4CdM3u5zmZdujaBYEx_VLxo7WpGb98abA.K4TxMK4bt_DewzOLSRAtLgV4V7Vad2qvOg0dav20Yac"
        api_key = os.getenv("BITQUERY_API_KEY")
        print(f"✅ Manually set API key: {api_key[:20]}...")

    # Test import and initialization
    try:
        from yasuo_onchain_analyst import BitqueryAPI

        print("\n✅ BitqueryAPI imported successfully")

        bitquery = BitqueryAPI()
        print("✅ BitqueryAPI initialized")

        headers = bitquery._get_headers()
        print(f"Headers keys: {list(headers.keys())}")

        if 'Authorization' in headers:
            auth_value = headers['Authorization']
            print(f"Authorization header: {auth_value[:30]}...")

        # Test the headers with a simple request
        import requests

        test_query = """
        {
          bitcoin {
            blocks {
              count
            }
          }
        }
        """

        response = requests.post(
            bitquery.base_url,
            json={"query": test_query},
            headers=headers,
            timeout=10
        )

        print(f"Test request status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Authentication successful!")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_environment()
