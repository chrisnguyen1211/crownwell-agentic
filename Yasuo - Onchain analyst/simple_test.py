#!/usr/bin/env python3
"""
Simple Test for Yasuo Data Sources
"""

import requests
from bs4 import BeautifulSoup

def test_bitquery_formats():
    """Test different Bitquery authentication formats"""
    print("🔍 Testing Bitquery authentication formats...")

    # Test different API key formats
    api_keys = [
        "ory_at_HXyMLC1J5_4CdM3u5zmZdujaBYEx_VLxo7WpGb98abA.K4TxMK4bt_DewzOLSRAtLgV4V7Vad2qvOg0dav20Yac",
        "HXyMLC1J5_4CdM3u5zmZdujaBYEx_VLxo7WpGb98abA.K4TxMK4bt_DewzOLSRAtLgV4V7Vad2qvOg0dav20Yac"
    ]

    # Simple query
    query = """
    {
      bitcoin {
        blocks {
          count
        }
      }
    }
    """

    for i, api_key in enumerate(api_keys):
        print(f"\nTesting API Key {i+1}...")

        # Try different header formats
        header_formats = [
            {"X-API-KEY": api_key},
            {"Authorization": f"Bearer {api_key}"},
            {"Authorization": f"Token {api_key}"},
        ]

        for j, headers in enumerate(header_formats):
            headers["Content-Type"] = "application/json"

            try:
                response = requests.post(
                    "https://graphql.bitquery.io",
                    json={"query": query},
                    headers=headers,
                    timeout=10
                )

                print(f"  Format {j+1}: Status {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    if 'errors' not in data:
                        print(f"  ✅ SUCCESS with API Key {i+1}, Format {j+1}")
                        print(f"  Response: {data}")
                        return True
                    else:
                        print(f"  ⚠️ GraphQL errors: {data.get('errors', [])}")
                elif response.status_code == 401:
                    print("  ❌ 401 Unauthorized")
                else:
                    print(f"  ❌ HTTP {response.status_code}: {response.text[:100]}")

            except Exception as e:
                print(f"  ❌ Exception: {e}")

    return False

def test_farside_scraping():
    """Test farside.co.uk scraping with proper headers"""
    print("\n🔍 Testing farside.co.uk scraping...")

    urls = [
        "https://farside.co.uk/eth/",
        "https://farside.co.uk/btc/"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

    for url in urls:
        try:
            print(f"\nTesting {url}...")
            response = requests.get(url, headers=headers, timeout=15)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Look for tables or data
                tables = soup.find_all('table')
                print(f"Found {len(tables)} tables")

                # Look for specific data patterns
                text_content = soup.get_text()
                if '$' in text_content:
                    print("✅ Found dollar signs (likely financial data)")
                if 'ETF' in text_content:
                    print("✅ Found ETF references")
                if 'flow' in text_content.lower():
                    print("✅ Found flow references")

                # Try to extract some basic data
                lines = text_content.split('\n')
                data_lines = [line for line in lines if '$' in line and any(char.isdigit() for char in line)]
                if data_lines:
                    print(f"📊 Sample data lines: {data_lines[:3]}")

            else:
                print(f"❌ Failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Exception: {e}")

def main():
    print("🛡️ YASUO SIMPLE DATA SOURCE TEST")
    print("=" * 50)

    # Test Bitquery
    bitquery_success = test_bitquery_formats()

    # Test farside
    test_farside_scraping()

    print("\n" + "=" * 50)
    if bitquery_success:
        print("✅ Bitquery: Working!")
    else:
        print("❌ Bitquery: All authentication methods failed")

    print("🎯 Next steps:")
    print("  1. Check Bitquery API key validity")
    print("  2. Inspect farside.co.uk HTML structure for scraping")
    print("  3. Consider alternative data sources if needed")

if __name__ == "__main__":
    main()
