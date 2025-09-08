#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Create comprehensive report
report = '''📊 YASUO COMPREHENSIVE ETH ANALYSIS REPORT

🔍 MARKET CONTEXT (Last 24h):
• Exchange Net Flow: 16,106 ETH (OUTFLOW - BULLISH)
• ETF Daily Flow: -$117,657,205 (OUTFLOW)
• Liveliness: 0.50 (MODERATE)
• Trend Analysis: NEUTRAL (50% strength)

📈 EXCHANGE FLOW DETAILS:
• Total Inflows: 321.88 ETH
• Total Outflows: 16,428.27 ETH
• Net Flow: 16,106.39 ETH (OUTFLOW)
• Large Transfers (100+ ETH): 8
• Detected Exchange-like Addresses: 19

🎯 PORTFOLIO RECOMMENDATION:
• Action: HOLD
• Reason: No clear trend, mixed signals
• Confidence: Moderate

📊 TREND DATA:
• Historical Samples: 3 data points
• Trend Direction: Neutral
• Market Consolidation Phase

🔄 NEXT STEPS:
• Monitor for large whale transactions
• Watch ETF flow reversals
• Track exchange flow patterns'''

# Send to Telegram
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if token and chat_id:
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {'chat_id': chat_id, 'text': report}
    r = requests.post(url, data=data)
    
    if r.status_code == 200:
        print('✅ Comprehensive report sent to Telegram!')
        print(f'Message ID: {r.json()["result"]["message_id"]}')
    else:
        print(f'❌ Failed to send: {r.status_code}')
        print(r.text)
else:
    print('❌ Missing Telegram credentials in .env')





