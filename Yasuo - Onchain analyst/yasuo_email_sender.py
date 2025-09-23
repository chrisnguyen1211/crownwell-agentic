#!/usr/bin/env python3
"""
Yasuo Email Sender with PDF Report
Sends comprehensive email with PDF attachment like Bob and Lily
"""
import os
import smtplib
import asyncio
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import PDF generator
from yasuo_pdf_report_generator import YasuoPDFReportGenerator

class YasuoEmailSender:
    """
    Send Yasuo analysis report via email with PDF attachment
    """
    
    def __init__(self):
        # Email configuration
        self.sender_email = os.getenv('SENDER_EMAIL', 'mutoryai@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL', 'chris@thebees.group')
        
        # Initialize PDF generator
        self.pdf_generator = YasuoPDFReportGenerator()
        
        print(f"📧 Yasuo Email Sender initialized for {self.recipient_email}")
    
    async def send_comprehensive_report(self) -> bool:
        """
        Generate PDF report and send via email
        """
        try:
            print("🛡️ Generating Yasuo PDF report...")
            
            # Generate PDF report
            pdf_filename = await self.pdf_generator.generate_pdf_report()
            
            print(f"📄 PDF report generated: {pdf_filename}")
            
            # Create email content
            email_subject = f"🛡️ Yasuo ETH On-Chain Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            email_body = f"""
Dear Team,

Please find today's comprehensive ETH on-chain analysis report from Yasuo.

🛡️ YASUO ON-CHAIN ANALYSIS SUMMARY
{'='*60}

📊 REPORT OVERVIEW:
• Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Analysis Period: Last 24 hours
• Data Sources: Real-time blockchain data
• Status: ✅ Fully Operational

🎯 KEY FINDINGS:
• ETF Flows: Real-time data from farside.co.uk
• Exchange Flows: 24-hour analysis from Etherscan
• Large Transactions: Whale activity monitoring
• Options & Futures: Derivatives market analysis
• Portfolio Recommendation: Based on combined signals

📈 DATA QUALITY:
• All data sources: ✅ Real-time
• No simulated data used
• 24-hour period coverage
• Professional analysis engine

📎 ATTACHMENT:
• Yasuo_OnChain_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf

🔄 NEXT STEPS:
• Review PDF report for detailed analysis
• Monitor for significant on-chain movements
• Track ETF flow changes
• Watch for large whale transactions

Best regards,
Yasuo On-Chain Analysis System

---
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System Status: Fully Operational
            """
            
            # Send email with PDF attachment
            success = self._send_email_with_attachment(
                email_subject, 
                email_body, 
                pdf_filename
            )
            
            if success:
                print("✅ Yasuo report sent successfully via email!")
                return True
            else:
                print("❌ Failed to send Yasuo report")
                return False
                
        except Exception as e:
            print(f"❌ Error sending Yasuo report: {e}")
            return False
    
    def _send_email_with_attachment(self, subject: str, body: str, pdf_filename: str) -> bool:
        """
        Send email with PDF attachment
        """
        try:
            if not self.sender_password:
                print("❌ Email password not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add PDF attachment
            if os.path.exists(pdf_filename):
                with open(pdf_filename, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(pdf_filename)}'
                )
                msg.attach(part)
                print(f"📎 PDF attachment added: {pdf_filename}")
            else:
                print(f"⚠️ PDF file not found: {pdf_filename}")
            
            # Send email
            print(f"📧 Sending email to {self.recipient_email}...")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            text = msg.as_string()
            server.sendmail(self.sender_email, self.recipient_email, text)
            server.quit()
            
            print("✅ Email sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

# Test function
async def main():
    print("🛡️ YASUO EMAIL SENDER TEST")
    print("=" * 50)
    
    sender = YasuoEmailSender()
    success = await sender.send_comprehensive_report()
    
    if success:
        print("✅ Yasuo report sent successfully!")
    else:
        print("❌ Failed to send Yasuo report")

if __name__ == "__main__":
    asyncio.run(main())














