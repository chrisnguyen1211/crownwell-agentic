# 📧 DAILY EMAIL AUTOMATION SETUP GUIDE

## 🎯 OVERVIEW

This system automatically sends comprehensive ETH analysis reports from all three agents (Bob, Lily, Yasuo) to your email at **10:00 AM Vietnam time** daily.

## 🔧 SETUP INSTRUCTIONS

### 1. 📧 Gmail App Password Setup

**IMPORTANT**: You need to use Gmail App Password, not your regular password!

1. **Enable 2-Factor Authentication** on your Gmail account
2. Go to **Google Account Settings** → **Security** → **App passwords**
3. Generate new app password for "Mail"
4. Copy the 16-character app password (e.g., `abcd efgh ijkl mnop`)

### 2. 🔑 Configure Environment Variables

Update your `.env` file with the correct credentials:

```bash
# Daily Email Automation
SENDER_EMAIL=mutoryai@gmail.com
SENDER_PASSWORD=your_16_character_app_password_here
RECIPIENT_EMAIL=chris@thebees.group
```

**Example:**
```bash
SENDER_EMAIL=mutoryai@gmail.com
SENDER_PASSWORD=abcd efgh ijkl mnop
RECIPIENT_EMAIL=chris@thebees.group
```

### 3. 🧪 Test Email Configuration

```bash
# Test email setup
python daily_email_automation.py email-test

# Expected output:
# ✅ Test email sent successfully!
```

### 4. 🚀 Run Daily Automation

```bash
# Option 1: Run as daemon (continuous, scheduled)
python daily_email_automation.py daemon

# Option 2: Run single test cycle
python daily_email_automation.py test
```

## 📅 SCHEDULE DETAILS

- **Report Time**: 10:00 AM Vietnam time (UTC+7)
- **Analysis Period**: Last 24 hours
- **Recipients**: chris@thebees.group
- **Frequency**: Daily

## 📊 REPORT CONTENTS

Each daily email includes:

### 🤖 BOB - Technical Analysis
- Multi-timeframe technical analysis (1H, 4H, 1D)
- Options interest analysis
- Master signal generation
- Risk assessment

### 🌸 LILY - Sentiment Analysis
- Social media sentiment analysis
- ETH mention tracking
- Trading signal generation
- Confidence scoring

### 🛡️ YASUO - On-Chain Analysis
- ETF flow analysis
- Exchange flow tracking
- Large transaction monitoring
- Portfolio recommendations

### 📈 COMBINED MARKET OUTLOOK
- Combined signal from all agents
- Risk assessment
- Time horizon recommendations
- Portfolio actions

## 🔍 DATA PERIODS

All data reflects **24-hour periods**:
- **Technical Analysis**: Last 24 hours of price data
- **Sentiment Analysis**: Last 24 hours of social media posts
- **On-Chain Analysis**: Last 24 hours of blockchain transactions
- **ETF Flows**: Daily ETF flow data
- **Exchange Flows**: 24-hour exchange in/out flows

## 🛠️ TROUBLESHOOTING

### Email Not Sending
1. **Check Gmail App Password**: Must be 16-character app password, not regular password
2. **Verify 2FA**: Two-factor authentication must be enabled
3. **Check Internet**: Ensure stable internet connection
4. **Review Logs**: Check `daily_automation.log` for errors

### Reports Not Generated
1. **Check Agent Dependencies**: Ensure Bob, Lily, Yasuo are properly configured
2. **Verify API Keys**: Check all API keys are valid and active
3. **Check File Permissions**: Ensure write permissions for log files
4. **Review Individual Logs**: Check agent-specific error logs

### Schedule Issues
1. **Timezone**: System uses Vietnam timezone (UTC+7)
2. **System Time**: Ensure system clock is accurate
3. **Process Management**: Use process manager for production deployment

## 🎯 PRODUCTION DEPLOYMENT

For production deployment:

```bash
# Install process manager
pip install supervisor

# Create systemd service
sudo systemctl enable daily-eth-automation
sudo systemctl start daily-eth-automation

# Monitor logs
tail -f daily_automation.log
```

## 📧 EMAIL EXAMPLE

```
Subject: 📊 Daily ETH Analysis Report - 2025-09-05

📊 DAILY ETH ANALYSIS REPORT - 2025-09-05 10:00 (Vietnam Time)
================================================================================

🎯 EXECUTIVE SUMMARY:
• Report Time: 2025-09-05 10:00:00 (UTC+7)
• Analysis Period: Last 24 hours
• All Agents: ✅ Operational

🤖 BOB - TECHNICAL ANALYSIS:
• Status: success
• Symbol: ETH-USD
• Bob's Confidence: 0.75
• Master Signal: bullish
• Trading Action: BUY
• Risk Level: medium

🌸 LILY - SENTIMENT ANALYSIS:
• Status: success
• Overall Sentiment: Bullish
• Trading Signal: BUY
• Total Mentions: 45
• Average Confidence: 0.68

🛡️ YASUO - ON-CHAIN ANALYSIS:
• Status: success
• ETF Daily Flow: $-167,300,000
• Exchange Net Flow: 0.00 ETH
• Large Transactions: 0
• Recommendation: SELL
• Confidence: 0.6

📈 COMBINED MARKET OUTLOOK:
• Technical Signal: bullish
• Sentiment Signal: Bullish
• On-Chain Signal: SELL

🎯 PORTFOLIO RECOMMENDATION:
Based on the combined analysis of all three agents:
• Primary Signal: NEUTRAL
• Risk Assessment: MEDIUM
• Time Horizon: SHORT-TERM (Technical) + SHORT-TERM (Sentiment) + MEDIUM-TERM (On-Chain)

📊 DATA QUALITY:
• Bob Technical Data: ✅ Real-time market data
• Lily Sentiment Data: ✅ Live social media feeds
• Yasuo On-Chain Data: ✅ Real blockchain data
• All Sources: ✅ 24-hour period coverage
```

## ✅ VERIFICATION CHECKLIST

- [ ] Gmail 2FA enabled
- [ ] App password generated and configured
- [ ] Environment variables set correctly
- [ ] Email test successful
- [ ] All agents (Bob, Lily, Yasuo) operational
- [ ] Schedule set for 10:00 AM Vietnam time
- [ ] Log files accessible
- [ ] Internet connection stable

## 🆘 SUPPORT

If you encounter issues:
1. Check the logs in `daily_automation.log`
2. Verify all environment variables
3. Test individual agents separately
4. Check Gmail security settings
5. Ensure all dependencies are installed
