#!/usr/bin/env python3
"""
Debug both farside scraping and exchange flows issues
"""

import asyncio
import sys
import requests
from bs4 import BeautifulSoup

# Add the current directory to path
sys.path.insert(0, '.')

async def debug_farside_detailed():
    """Debug farside scraping in detail"""
    print("🔍 DEBUGGING FARSIDE SCRAPING")
    print("=" * 50)

    url = "https://farside.co.uk/eth/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all tables
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")

        if len(tables) > 1:
            main_table = tables[1]
            rows = main_table.find_all('tr')
            print(f"Main table has {len(rows)} rows")

            # Look for rows with any styling or highlighting
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Check row attributes
                row_style = row.get('style', '')
                row_class = row.get('class', [])
                row_bgcolor = row.get('bgcolor', '')

                # Look for recent dates and any styling
                if len(cell_texts) > 0:
                    first_cell = cell_texts[0]
                    last_cell = cell_texts[-1] if len(cell_texts) > 1 else ""
                    
                    # Check if this could be the latest data
                    is_recent = '2025' in first_cell and ('Sep' in first_cell or 'Aug' in first_cell)
                    has_styling = row_style or row_class or row_bgcolor
                    has_parentheses = '(' in last_cell and ')' in last_cell
                    
                    if is_recent or has_styling or has_parentheses:
                        print(f"\nRow {i}: {cell_texts}")
                        print(f"  Style: {row_style}")
                        print(f"  Class: {row_class}")
                        print(f"  BGColor: {row_bgcolor}")
                        
                        # Try to parse the last cell as net flow
                        if last_cell and ('(' in last_cell or any(c.isdigit() for c in last_cell)):
                            print(f"  Potential net flow: {last_cell}")

    except Exception as e:
        print(f"Error: {e}")

async def debug_bitquery_exchange():
    """Debug Bitquery exchange flows"""
    print("\n🔍 DEBUGGING BITQUERY EXCHANGE FLOWS")
    print("=" * 50)

    try:
        from yasuo_onchain_analyst import YasuoOnChainAnalyst

        # Initialize Yasuo
        yasuo = YasuoOnChainAnalyst()

        print("Testing exchange flows...")
        exchange_flows = await yasuo.get_exchange_flows()
        
        print(f"Exchange flows result:")
        for key, value in exchange_flows.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run both debug tests"""
    await debug_farside_detailed()
    await debug_bitquery_exchange()

if __name__ == "__main__":
    asyncio.run(main())





