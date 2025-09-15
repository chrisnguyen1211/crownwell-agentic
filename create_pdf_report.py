#!/usr/bin/env python3
"""
Tạo PDF report từ HTML file
"""

import os
import subprocess
import sys
from datetime import datetime

def create_pdf_from_html():
    """Tạo PDF từ HTML file"""
    
    html_file = "Reports/trading_agents_execution_report_20250915.html"
    pdf_file = "Reports/trading_agents_execution_report_20250915.pdf"
    
    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        return False
    
    print(f"📄 Creating PDF from: {html_file}")
    print(f"📄 Output file: {pdf_file}")
    
    # Thử sử dụng wkhtmltopdf nếu có
    try:
        result = subprocess.run([
            'wkhtmltopdf', 
            '--page-size', 'A4',
            '--margin-top', '20mm',
            '--margin-right', '20mm', 
            '--margin-bottom', '20mm',
            '--margin-left', '20mm',
            '--encoding', 'UTF-8',
            '--enable-local-file-access',
            html_file, 
            pdf_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ PDF created successfully with wkhtmltopdf!")
            return True
        else:
            print(f"❌ wkhtmltopdf failed: {result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ wkhtmltopdf not available")
    
    # Thử sử dụng Chrome/Chromium headless
    try:
        result = subprocess.run([
            'google-chrome', 
            '--headless',
            '--disable-gpu',
            '--print-to-pdf=' + pdf_file,
            '--print-to-pdf-no-header',
            '--run-all-compositor-stages-before-draw',
            '--virtual-time-budget=5000',
            html_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ PDF created successfully with Chrome!")
            return True
        else:
            print(f"❌ Chrome failed: {result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ Chrome not available")
    
    # Thử sử dụng Safari (macOS)
    try:
        result = subprocess.run([
            'osascript', '-e', f'''
            tell application "Safari"
                activate
                open POSIX file "{os.path.abspath(html_file)}"
                delay 3
                tell application "System Events"
                    keystroke "p" using command down
                    delay 2
                    keystroke "s" using command down
                    delay 1
                    keystroke "{os.path.basename(pdf_file)}"
                    delay 1
                    keystroke return
                    delay 2
                end tell
                quit
            end tell
            '''
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ PDF creation initiated with Safari!")
            return True
        else:
            print(f"❌ Safari failed: {result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ Safari automation not available")
    
    print("❌ Could not create PDF automatically")
    print("💡 Manual options:")
    print(f"   1. Open {os.path.abspath(html_file)} in your browser")
    print("   2. Press Ctrl+P (Cmd+P on Mac) to print")
    print("   3. Select 'Save as PDF' as destination")
    print("   4. Save the file")
    
    return False

def main():
    print("🔄 Creating PDF report...")
    print("=" * 50)
    
    success = create_pdf_from_html()
    
    if success:
        pdf_file = "Reports/trading_agents_execution_report_20250915.pdf"
        if os.path.exists(pdf_file):
            size = os.path.getsize(pdf_file)
            print(f"📊 PDF file size: {size:,} bytes")
            print(f"📁 Full path: {os.path.abspath(pdf_file)}")
        else:
            print("⚠️ PDF file not found after creation")
    else:
        print("📄 HTML report is available at:")
        print(f"   {os.path.abspath('Reports/trading_agents_execution_report_20250915.html')}")

if __name__ == "__main__":
    main()
