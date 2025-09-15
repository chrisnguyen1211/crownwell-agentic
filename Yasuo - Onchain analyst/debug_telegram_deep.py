#!/usr/bin/env python3
"""
Deep debug Telegram API - Fix connection timeout issues
"""
import requests
import os
import socket
import subprocess
from dotenv import load_dotenv

load_dotenv()

print("🔍 DEEP DEBUG TELEGRAM API")
print("=" * 60)

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

print(f"Bot Token: {token[:20] if token else 'Not set'}...")
print(f"Chat ID: {chat_id if chat_id else 'Not set'}")

if not token or not chat_id:
    print("❌ Missing credentials")
    exit(1)

# Test 1: DNS Resolution
print("\nTest 1: DNS Resolution")
try:
    ip = socket.gethostbyname('api.telegram.org')
    print(f"✅ api.telegram.org resolves to: {ip}")
except Exception as e:
    print(f"❌ DNS Error: {e}")

# Test 2: Ping test
print("\nTest 2: Ping test")
try:
    result = subprocess.run(['ping', '-c', '3', 'api.telegram.org'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print("✅ Ping successful")
    else:
        print(f"❌ Ping failed: {result.stderr}")
except Exception as e:
    print(f"❌ Ping error: {e}")

# Test 3: HTTP connection test
print("\nTest 3: HTTP connection test")
try:
    response = requests.get('https://api.telegram.org', timeout=5)
    print(f"✅ HTTP connection: {response.status_code}")
except Exception as e:
    print(f"❌ HTTP Error: {e}")

# Test 4: Bot info with different timeouts
print("\nTest 4: Bot info with different timeouts")
url = f'https://api.telegram.org/bot{token}/getMe'

timeouts = [1, 5, 10, 30]
for timeout in timeouts:
    try:
        response = requests.get(url, timeout=timeout)
        print(f"✅ Timeout {timeout}s: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            bot_info = data.get('result', {})
            print(f"   Bot: {bot_info.get('first_name', 'Unknown')}")
            break
    except requests.exceptions.ConnectTimeout:
        print(f"❌ Timeout {timeout}s: Connect timeout")
    except requests.exceptions.ReadTimeout:
        print(f"❌ Timeout {timeout}s: Read timeout")
    except Exception as e:
        print(f"❌ Timeout {timeout}s: {e}")

# Test 5: Try with session and keep-alive
print("\nTest 5: Session with keep-alive")
try:
    session = requests.Session()
    session.headers.update({
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    response = session.get(url, timeout=30)
    print(f"✅ Session request: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        bot_info = data.get('result', {})
        print(f"✅ Bot Name: {bot_info.get('first_name', 'Unknown')}")
        print(f"✅ Bot Username: @{bot_info.get('username', 'Unknown')}")
        
        # Test sending message
        print("\nTest 6: Send test message")
        send_url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': '🧪 Telegram API Test - Connection Fixed!'
        }
        
        response = session.post(send_url, data=data, timeout=30)
        print(f"✅ Send message: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('result', {}).get('message_id', 'Unknown')
            print(f"✅ Message ID: {message_id}")
        
except Exception as e:
    print(f"❌ Session error: {e}")

# Test 7: Try alternative endpoints
print("\nTest 7: Alternative endpoints")
endpoints = [
    'https://api.telegram.org',
    'https://api.telegram.org/bot',
    'https://api.telegram.org/bot/',
]

for endpoint in endpoints:
    try:
        test_url = f'{endpoint}{token}/getMe'
        response = requests.get(test_url, timeout=10)
        print(f"✅ {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"❌ {endpoint}: {e}")

print("\n" + "=" * 60)
print("🎯 DIAGNOSIS:")
print("• If DNS fails: Network configuration issue")
print("• If ping fails: Firewall/proxy blocking")
print("• If HTTP fails: SSL/TLS issue")
print("• If session works: Connection pooling helps")
print("• If alternatives work: Endpoint-specific issue")






