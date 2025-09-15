#!/usr/bin/env python3
"""
Test New Telegram Bot API Key
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 TESTING NEW TELEGRAM BOT API")
print("=" * 50)

# New bot credentials
NEW_TOKEN = "8442668476:AAH080y_wB7Clr1YxXsrpLv47QF4KEnFJcM"
CHAT_ID = "5238358385"  # Same user ID

print(f"New Bot Token: {NEW_TOKEN[:20]}...")
print(f"Chat ID: {CHAT_ID}")

# Test 1: Get bot info
print("\nTest 1: Get bot info")
url1 = f'https://api.telegram.org/bot{NEW_TOKEN}/getMe'

try:
    response1 = requests.get(url1, timeout=10)
    print(f"Status Code: {response1.status_code}")
    
    if response1.status_code == 200:
        data = response1.json()
        bot_info = data.get('result', {})
        print(f"✅ Bot Name: {bot_info.get('first_name', 'Unknown')}")
        print(f"✅ Bot Username: @{bot_info.get('username', 'Unknown')}")
        print(f"✅ Bot ID: {bot_info.get('id', 'Unknown')}")
    else:
        print(f"❌ Error: {response1.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)

# Test 2: Send test message
print("Test 2: Send test message")
url2 = f'https://api.telegram.org/bot{NEW_TOKEN}/sendMessage'
data2 = {
    'chat_id': CHAT_ID,
    'text': '🛡️ YASUO NEW BOT TEST - Connection Successful!'
}

try:
    response2 = requests.post(url2, data=data2, timeout=10)
    print(f"Status Code: {response2.status_code}")
    
    if response2.status_code == 200:
        result = response2.json()
        message_id = result.get('result', {}).get('message_id', 'Unknown')
        print(f"✅ Message sent successfully!")
        print(f"✅ Message ID: {message_id}")
    else:
        print(f"❌ Error: {response2.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)

# Test 3: Send formatted Yasuo report
print("Test 3: Send formatted Yasuo report")
url3 = f'https://api.telegram.org/bot{NEW_TOKEN}/sendMessage'

report = """
🛡️ YASUO ETH ANALYSIS REPORT

📊 MARKET OVERVIEW:
• Analysis Time: 2025-09-05 11:00:00
• Data Sources: etherscan, farside, bitquery
• Status: SUCCESS

💰 ETF FLOWS:
• Daily Flow: -$167,300,000 (OUTFLOWS)
• Data Quality: Real from farside.co.uk

📈 EXCHANGE FLOWS (CORRECTED):
• Net Flow: +12,597 ETH (ACCUMULATION)
• Interpretation: More people withdrawing than depositing
• Market Signal: BULLISH

🎯 PORTFOLIO RECOMMENDATION:
• Action: BUY
• Confidence: 0.8
• Reason: Strong accumulation + ETF outflows = Contrarian opportunity

✅ DATA QUALITY: 
• ETF Data: Real from farside.co.uk
• Exchange Data: Real from Etherscan
• No Simulated Data Used

🛡️ YASUO STATUS: OPERATIONAL
"""

data3 = {
    'chat_id': CHAT_ID,
    'text': report,
    'parse_mode': 'HTML'
}

try:
    response3 = requests.post(url3, data=data3, timeout=10)
    print(f"Status Code: {response3.status_code}")
    
    if response3.status_code == 200:
        result = response3.json()
        message_id = result.get('result', {}).get('message_id', 'Unknown')
        print(f"✅ Yasuo report sent successfully!")
        print(f"✅ Message ID: {message_id}")
    else:
        print(f"❌ Error: {response3.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("🎯 CONCLUSION:")
print("• If Test 1 works: New bot token is valid")
print("• If Test 2 works: Can send messages to same chat")
print("• If Test 3 works: Can send formatted reports")
print("• If all work: New bot is ready for Yasuo!")






