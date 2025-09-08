# 📧 EMAIL SETUP GUIDE

## Quick Setup for Daily Automated Reports

### 1. 📧 Email Configuration

Create environment variables for email authentication:

```bash
# Add to your .bashrc or .zshrc
export SENDER_EMAIL="your-gmail@gmail.com"
export SENDER_PASSWORD="your-app-password"

# Or create .env file
echo "SENDER_EMAIL=your-gmail@gmail.com" > .env.email
echo "SENDER_PASSWORD=your-app-password" >> .env.email
```

### 2. 🔑 Gmail App Password Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account Settings → Security → App passwords
3. Generate new app password for "Mail"
4. Use this app password (not your regular password)

### 3. 🧪 Test Email System

```bash
# Test email configuration
python3 daily_automation.py email-test

# Expected output:
# ✅ Test email sent successfully!
```

### 4. 🤖 Run Automation

```bash
# Option 1: Run as daemon (continuous)
python3 daily_automation.py daemon

# Option 2: Run single test cycle
python3 daily_automation.py test
```

### 5. 📅 Scheduled Reports

The system will automatically:
- **09:00 daily**: Send complete analysis reports to chri@thebees.group
- **Every 4 hours**: Run additional data collection
- **Rate limit compliant**: Respects platform limits to avoid detection

### 6. 📊 Report Contents

Daily emails will include:
- **Lily's Sentiment Report**: ETH social media sentiment analysis
- **Bob's Technical Report**: ETH technical analysis với options data
- **Professional PDF attachments**
- **Summary statistics and insights**

### 7. 📧 Email Example

```
Subject: 📊 Daily ETH Analysis Report - 2025-08-12

Dear Team,

Please find today's automated ETH analysis reports...

🌸 LILY - Social Media Sentiment Analysis
🤖 BOB - Technical Analysis

Attachments:
✅ Lily_Sentiment_Report.pdf
✅ Bob_Technical_Report.pdf
```

## 🛠️ Troubleshooting

### Email Not Sending
- Check Gmail app password is correct
- Verify 2FA is enabled
- Check internet connection
- Review logs in `daily_automation.log`

### Reports Not Generated
- Check Supabase connection for Lily
- Verify TA-Lib installation for Bob
- Check file permissions
- Review individual agent logs

### Rate Limiting Issues
- System automatically handles rate limits
- Check `rate_limit_history.json` for usage tracking
- Adjust collection frequency if needed

## 🎯 Production Deployment

For production deployment:
1. Run on VPS/server với persistent connection
2. Use process manager (PM2, systemd)
3. Monitor logs and performance
4. Set up backup email notifications
5. Configure proper error handling

```bash
# Example systemd service
sudo systemctl enable lily-bob-automation
sudo systemctl start lily-bob-automation
```


























