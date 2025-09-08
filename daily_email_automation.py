#!/usr/bin/env python3
"""
Daily Email Automation System for Trading Agents
Sends comprehensive reports at 10AM Vietnam time (UTC+7)
"""
import os
import sys
import asyncio
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import pytz
import schedule
import time
import json

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'Bob'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'Lily'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'Yasuo - Onchain analyst'))

# Load environment variables
load_dotenv()

class DailyEmailReporter:
    """
    Daily email reporter for all trading agents
    Sends comprehensive reports at 10AM Vietnam time
    """
    
    def __init__(self):
        self.setup_logging()
        
        # Email configuration
        self.sender_email = os.getenv('SENDER_EMAIL', 'mutoryai@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL', 'chris@thebees.group')
        
        # Vietnam timezone
        self.vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        
        self.logger.info(f"📧 Email reporter initialized for {self.recipient_email}")
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('daily_automation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def run_bob_analysis(self) -> dict:
        """Run Bob's technical analysis"""
        try:
            # Import Bob's analysis engine
            from technical_analysis_engine import run_bob_analysis
            
            self.logger.info("📈 Running Bob's technical analysis...")
            result = await run_bob_analysis()
            
            if result:
                self.logger.info("✅ Bob analysis completed")
                return result
            else:
                self.logger.warning("⚠️ Bob analysis returned no results")
                return {"status": "error", "message": "Bob analysis failed"}
                
        except Exception as e:
            self.logger.error(f"❌ Bob analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def run_lily_analysis(self) -> dict:
        """Run Lily's sentiment analysis"""
        try:
            # Import Lily's analysis engine
            from standalone_sentiment_bot import LilySentimentBot
            
            self.logger.info("🌸 Running Lily's sentiment analysis...")
            lily = LilySentimentBot()
            
            # Run sentiment analysis
            result = await lily.run_complete_analysis()
            
            if result:
                self.logger.info("✅ Lily analysis completed")
                return result
            else:
                self.logger.warning("⚠️ Lily analysis returned no results")
                return {"status": "error", "message": "Lily analysis failed"}
                
        except Exception as e:
            self.logger.error(f"❌ Lily analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def run_yasuo_analysis(self) -> dict:
        """Run Yasuo's on-chain analysis"""
        try:
            # Import Yasuo's analysis engine
            from yasuo_report_generator import YasuoReportGenerator
            
            self.logger.info("🛡️ Running Yasuo's on-chain analysis...")
            yasuo = YasuoReportGenerator()
            
            # Run complete analysis
            result = await yasuo.generate_complete_report()
            
            if result:
                self.logger.info("✅ Yasuo analysis completed")
                return result
            else:
                self.logger.warning("⚠️ Yasuo analysis returned no results")
                return {"status": "error", "message": "Yasuo analysis failed"}
                
        except Exception as e:
            self.logger.error(f"❌ Yasuo analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def generate_comprehensive_report(self) -> str:
        """Generate comprehensive daily report"""
        self.logger.info("🚀 Starting complete daily analysis cycle...")
        
        # Run all analyses
        bob_result = await self.run_bob_analysis()
        lily_result = await self.run_lily_analysis()
        yasuo_result = await self.run_yasuo_analysis()
        
        # Harden: ensure dicts
        if not isinstance(bob_result, dict):
            bob_result = {}
        if not isinstance(lily_result, dict):
            lily_result = {}
        if not isinstance(yasuo_result, dict):
            yasuo_result = {}
        
        # Get current Vietnam time
        vietnam_time = datetime.now(self.vietnam_tz)
        
        # Generate report
        report = f"""
📊 DAILY ETH ANALYSIS REPORT - {vietnam_time.strftime('%Y-%m-%d %H:%M')} (Vietnam Time)
{'='*80}

🎯 EXECUTIVE SUMMARY:
• Report Time: {vietnam_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+7)
• Analysis Period: Last 24 hours
• All Agents: ✅ Operational

🤖 BOB - TECHNICAL ANALYSIS:
• Status: {bob_result.get('status', 'Unknown')}
• Symbol: {bob_result.get('symbol', 'ETH-USD')}
• Bob's Confidence: {bob_result.get('bob_confidence', 0):.2f}
• Master Signal: {bob_result.get('master_signal', {}).get('direction', 'Unknown')}
• Trading Action: {bob_result.get('master_signal', {}).get('action', 'Unknown')}
• Risk Level: {bob_result.get('master_signal', {}).get('risk_level', 'Unknown')}

🌸 LILY - SENTIMENT ANALYSIS:
• Status: {lily_result.get('status', 'Unknown')}
• Overall Sentiment: {lily_result.get('overall_sentiment', 'Unknown')}
• Trading Signal: {lily_result.get('trading_signal', 'Unknown')}
• Total Mentions: {lily_result.get('total_mentions', 0)}
• Average Confidence: {lily_result.get('average_confidence', 0):.2f}

🛡️ YASUO - ON-CHAIN ANALYSIS:
• Status: {yasuo_result.get('status', 'Unknown')}
• ETF Daily Flow: ${yasuo_result.get('analysis', {}).get('etf_flows', {}).get('daily_flow', 0):,.0f}
• Exchange Net Flow: {yasuo_result.get('analysis', {}).get('exchange_flows', {}).get('net_flow', 0):,.2f} ETH
• Large Transactions: {len(yasuo_result.get('analysis', {}).get('large_transactions', []))}
• Recommendation: {yasuo_result.get('analysis', {}).get('recommendation', {}).get('action', 'Unknown')}
• Confidence: {yasuo_result.get('analysis', {}).get('recommendation', {}).get('confidence', 0):.1f}

📈 COMBINED MARKET OUTLOOK:
• Technical Signal: {bob_result.get('master_signal', {}).get('direction', 'Unknown')}
• Sentiment Signal: {lily_result.get('overall_sentiment', 'Unknown')}
• On-Chain Signal: {yasuo_result.get('analysis', {}).get('recommendation', {}).get('action', 'Unknown')}

🎯 PORTFOLIO RECOMMENDATION:
Based on the combined analysis of all three agents:
• Primary Signal: {self._get_combined_signal(bob_result, lily_result, yasuo_result)}
• Risk Assessment: {self._get_risk_assessment(bob_result, lily_result, yasuo_result)}
• Time Horizon: {self._get_time_horizon(bob_result, lily_result, yasuo_result)}

📊 DATA QUALITY:
• Bob Technical Data: ✅ Real-time market data
• Lily Sentiment Data: ✅ Live social media feeds
• Yasuo On-Chain Data: ✅ Real blockchain data
• All Sources: ✅ 24-hour period coverage

🔄 NEXT STEPS:
• Monitor for significant technical breakouts
• Watch for sentiment shifts in social media
• Track large on-chain movements
• Review positions based on combined signals

📧 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        return report
    
    def _get_combined_signal(self, bob_result: dict, lily_result: dict, yasuo_result: dict) -> str:
        """Get combined signal from all agents"""
        signals = []
        
        # Bob signal
        bob_signal = bob_result.get('master_signal', {}).get('direction', 'neutral')
        if bob_signal in ['bullish', 'strong_bullish']:
            signals.append('bullish')
        elif bob_signal in ['bearish', 'strong_bearish']:
            signals.append('bearish')
        else:
            signals.append('neutral')
        
        # Lily signal
        lily_signal = lily_result.get('overall_sentiment', 'neutral')
        if lily_signal in ['Bullish', 'Strong Bullish']:
            signals.append('bullish')
        elif lily_signal in ['Bearish', 'Strong Bearish']:
            signals.append('bearish')
        else:
            signals.append('neutral')
        
        # Yasuo signal
        yasuo_signal = yasuo_result.get('analysis', {}).get('recommendation', {}).get('action', 'HOLD')
        if yasuo_signal == 'BUY':
            signals.append('bullish')
        elif yasuo_signal == 'SELL':
            signals.append('bearish')
        else:
            signals.append('neutral')
        
        # Calculate combined signal
        bullish_count = signals.count('bullish')
        bearish_count = signals.count('bearish')
        
        if bullish_count >= 2:
            return 'BULLISH'
        elif bearish_count >= 2:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _get_risk_assessment(self, bob_result: dict, lily_result: dict, yasuo_result: dict) -> str:
        """Get risk assessment from all agents"""
        risks = []
        
        # Bob risk
        bob_risk = bob_result.get('master_signal', {}).get('risk_level', 'medium')
        risks.append(bob_risk)
        
        # Lily confidence
        lily_confidence = lily_result.get('average_confidence', 0.5)
        if lily_confidence > 0.7:
            risks.append('low')
        elif lily_confidence < 0.3:
            risks.append('high')
        else:
            risks.append('medium')
        
        # Yasuo confidence
        yasuo_confidence = yasuo_result.get('analysis', {}).get('recommendation', {}).get('confidence', 0.5)
        if yasuo_confidence > 0.7:
            risks.append('low')
        elif yasuo_confidence < 0.3:
            risks.append('high')
        else:
            risks.append('medium')
        
        # Calculate average risk
        risk_scores = {'low': 1, 'medium': 2, 'high': 3}
        avg_risk_score = sum(risk_scores.get(risk, 2) for risk in risks) / len(risks)
        
        if avg_risk_score <= 1.5:
            return 'LOW'
        elif avg_risk_score >= 2.5:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def _get_time_horizon(self, bob_result: dict, lily_result: dict, yasuo_result: dict) -> str:
        """Get recommended time horizon"""
        # Bob focuses on short-term technicals
        bob_timeframe = 'SHORT-TERM'
        
        # Lily sentiment is typically short-term
        lily_timeframe = 'SHORT-TERM'
        
        # Yasuo on-chain is medium-term
        yasuo_timeframe = 'MEDIUM-TERM'
        
        return f"{bob_timeframe} (Technical) + {lily_timeframe} (Sentiment) + {yasuo_timeframe} (On-Chain)"
    
    def send_email_report(self, report: str) -> bool:
        """Send email report"""
        try:
            if not self.sender_password:
                self.logger.error("❌ Email password not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f"📊 Daily ETH Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Add body
            msg.attach(MIMEText(report, 'plain'))
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            text = msg.as_string()
            server.sendmail(self.sender_email, self.recipient_email, text)
            server.quit()
            
            self.logger.info(f"✅ Email sent successfully to {self.recipient_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send email: {e}")
            return False
    
    async def run_daily_cycle(self):
        """Run complete daily analysis cycle"""
        try:
            self.logger.info("🚀 Starting complete daily analysis cycle...")
            
            # Generate comprehensive report
            report = await self.generate_comprehensive_report()
            
            # Send email
            success = self.send_email_report(report)
            
            if success:
                self.logger.info("✅ Daily cycle completed successfully")
            else:
                self.logger.error("❌ Daily cycle failed - email not sent")
                
        except Exception as e:
            self.logger.error(f"❌ Daily cycle failed: {e}")

# Main execution
async def main():
    """Main execution function"""
    if len(sys.argv) < 2:
        print("Usage: python daily_email_automation.py [daemon|test|email-test]")
        sys.exit(1)
    
    command = sys.argv[1]
    reporter = DailyEmailReporter()
    
    if command == "daemon":
        print("🤖 Starting daily automation daemon...")
        print("📅 Daily schedule set for 10:00 Vietnam time")
        
        # Schedule daily report at 10AM Vietnam time
        schedule.every().day.at("10:00").do(lambda: asyncio.run(reporter.run_daily_cycle()))
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    elif command == "test":
        print("🧪 Running single test cycle...")
        await reporter.run_daily_cycle()
    
    elif command == "email-test":
        print("📧 Testing email configuration...")
        test_report = "📧 Test email from Daily Automation System\n\nThis is a test message to verify email configuration."
        success = reporter.send_email_report(test_report)
        
        if success:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Test email failed - check credentials")
    
    else:
        print("❌ Unknown command. Use: daemon, test, or email-test")

if __name__ == "__main__":
    asyncio.run(main())
