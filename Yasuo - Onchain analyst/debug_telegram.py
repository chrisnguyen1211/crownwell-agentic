#!/usr/bin/env python3
"""
Debug Telegram API Bot
"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 DEBUG TELEGRAM API BOT")
print("=" * 50)

# Get credentials
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

print(f"Bot Token: {token[:20] if token else 'Not set'}...")
print(f"Chat ID: {chat_id if chat_id else 'Not set'}")

if not token or not chat_id:
    print("❌ Missing Telegram credentials in .env")
    exit(1)

# Test 1: Get bot info
print("\nTest 1: Get bot info")
url1 = f'https://api.telegram.org/bot{token}/getMe'

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
url2 = f'https://api.telegram.org/bot{token}/sendMessage'
data2 = {
    'chat_id': chat_id,
    'text': '🧪 Telegram API Test - Yasuo Debug'
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

# Test 3: Get updates (check if bot can receive messages)
print("Test 3: Get updates")
url3 = f'https://api.telegram.org/bot{token}/getUpdates'

try:
    response3 = requests.get(url3, timeout=10)
    print(f"Status Code: {response3.status_code}")
    
    if response3.status_code == 200:
        data = response3.json()
        updates = data.get('result', [])
        print(f"✅ Found {len(updates)} updates")
        
        if updates:
            latest = updates[-1]
            message = latest.get('message', {})
            print(f"✅ Latest message: {message.get('text', 'No text')[:50]}...")
        else:
            print("✅ No recent messages")
    else:
        print(f"❌ Error: {response3.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)

# Test 4: Test with different timeout
print("Test 4: Test with longer timeout")
url4 = f'https://api.telegram.org/bot{token}/sendMessage'
data4 = {
    'chat_id': chat_id,
    'text': '🕐 Long timeout test - Yasuo Debug'
}

try:
    response4 = requests.post(url4, data=data4, timeout=30)
    print(f"Status Code: {response4.status_code}")
    
    if response4.status_code == 200:
        print(f"✅ Long timeout works!")
    else:
        print(f"❌ Error: {response4.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("🎯 CONCLUSION:")
print("• If Test 1 works: Bot token valid")
print("• If Test 2 works: Chat ID valid, can send messages")
print("• If Test 3 works: Bot can receive updates")
print("• If Test 4 works: Network timeout issue resolved")