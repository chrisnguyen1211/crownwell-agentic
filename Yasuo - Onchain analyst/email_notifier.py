#!/usr/bin/env python3
"""
Email fallback for Telegram notifications
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from dotenv import load_dotenv

load_dotenv()

class EmailNotifier:
    """
    Email fallback for Telegram notifications
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Email configuration (Gmail example)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = os.getenv("EMAIL_ADDRESS")
        self.password = os.getenv("EMAIL_PASSWORD")
        
    def send_alert(self, subject: str, message: str, to_email: Optional[str] = None) -> bool:
        """
        Send email alert
        """
        if not self.email or not self.password:
            self.logger.warning("Email credentials not configured")
            return False
        
        if not to_email:
            to_email = self.email  # Send to self if no recipient specified
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = f"🛡️ YASUO ALERT: {subject}"
            
            # Add body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            
            text = msg.as_string()
            server.sendmail(self.email, to_email, text)
            server.quit()
            
            self.logger.info(f"Email alert sent to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False

# Test email notifier
if __name__ == "__main__":
    print("📧 Testing Email Notifier")
    print("=" * 40)
    
    notifier = EmailNotifier()
    
    test_message = """
🛡️ YASUO ETH ANALYSIS REPORT

🔍 MARKET CONTEXT:
• ETF Daily Flow: -$316,100,000 (OUTFLOWS)
• Data Source: farside.co.uk (Real Data ✅)
• Latest Day: 04 Sep 2025

🎯 PORTFOLIO RECOMMENDATION:
• Action: HOLD
• Reason: Moderate institutional selling pressure
• Confidence: MODERATE (0.7)

✅ DATA QUALITY: 
• ETF Data: REAL from farside.co.uk
• No Simulated Data Used
• High Confidence Level

🛡️ YASUO STATUS: OPERATIONAL
    """
    
    success = notifier.send_alert("Test Alert", test_message)
    
    if success:
        print("✅ Email sent successfully!")
    else:
        print("❌ Email failed - check credentials in .env")
        print("Add to .env:")
        print("EMAIL_ADDRESS=your_email@gmail.com")
        print("EMAIL_PASSWORD=your_app_password")



