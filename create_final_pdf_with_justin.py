#!/usr/bin/env python3
"""
Tạo báo cáo PDF cuối cùng với phân tích của Justin Skeptical Judge
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, blue, green, red, orange
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
import json
from datetime import datetime

def create_final_pdf_with_justin():
    """Tạo PDF báo cáo cuối cùng với Justin analysis"""
    
    # Load comprehensive report
    report_file = "/Users/nguyenhuycuong/Crownwell agentic/TradingAgents/Reports/comprehensive_alpha_justin_report_20250915_050436.json"
    
    try:
        with open(report_file, 'r') as f:
            report_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Report file not found: {report_file}")
        return None
    
    pdf_file = "Reports/final_trading_agents_report_with_justin_20250915.pdf"
    
    # Tạo document
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, 
                          rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#2c3e50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=HexColor('#34495e')
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
        textColor=HexColor('#7f8c8d')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leading=14
    )
    
    # Content
    story = []
    
    # Title
    story.append(Paragraph("🏛️ TRADING AGENTS COMPREHENSIVE REPORT", title_style))
    story.append(Paragraph("With Justin Skeptical Judge Analysis", normal_style))
    story.append(Paragraph("Ngày: 15 tháng 9, 2025", normal_style))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("📋 EXECUTIVE SUMMARY", heading_style))
    
    summary = report_data.get('summary', {})
    exec_summary_data = [
        ['Final Verdict', summary.get('final_verdict', 'Unknown')],
        ['Confidence Level', f"{summary.get('confidence_level', 0):.2f}"],
        ['Judge Experience', summary.get('judge_experience', 'Unknown')],
        ['Analysis Style', summary.get('analysis_style', 'Unknown')],
        ['Workflow Status', report_data.get('status', 'Unknown')]
    ]
    
    exec_table = Table(exec_summary_data, colWidths=[2*inch, 4*inch])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e3f2fd')),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    
    story.append(exec_table)
    story.append(Spacer(1, 20))
    
    # Alpha Team Debate
    story.append(Paragraph("🏛️ ALPHA TEAM DEBATE", heading_style))
    
    alpha_data = report_data.get('components', {}).get('alpha_debate', {})
    if alpha_data:
        story.append(Paragraph("Bullish Thesis:", subheading_style))
        story.append(Paragraph(f"\"{alpha_data.get('bullish_thesis', 'N/A')}\"", normal_style))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("Bearish Thesis:", subheading_style))
        story.append(Paragraph(f"\"{alpha_data.get('bearish_thesis', 'N/A')}\"", normal_style))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("Debate Rounds:", subheading_style))
        debate_rounds = alpha_data.get('debate_rounds', [])
        for i, round_data in enumerate(debate_rounds, 1):
            story.append(Paragraph(f"Round {i}:", normal_style))
            story.append(Paragraph(f"• Bullish: {round_data.get('bullish', 'N/A')}", normal_style))
            story.append(Paragraph(f"• Bearish: {round_data.get('bearish', 'N/A')}", normal_style))
            story.append(Spacer(1, 5))
    
    story.append(Spacer(1, 20))
    
    # Dispatch Results
    story.append(Paragraph("📡 CRAWL AGENTS EXECUTION", heading_style))
    
    dispatch_data = report_data.get('components', {}).get('dispatch_results', {})
    if dispatch_data:
        agents_data = [
            ['Agent', 'Status'],
            ['Bob (Technical)', '✅ SUCCESS' if 'bob' in dispatch_data.get('successful_runs', []) else '❌ FAILED'],
            ['J97 (News)', '✅ SUCCESS' if 'j97' in dispatch_data.get('successful_runs', []) else '❌ FAILED'],
            ['Lily (Social)', '✅ SUCCESS' if 'lily' in dispatch_data.get('successful_runs', []) else '❌ FAILED'],
            ['Yasuo (Onchain)', '✅ SUCCESS' if 'yasuo' in dispatch_data.get('successful_runs', []) else '❌ FAILED']
        ]
        
        agents_table = Table(agents_data, colWidths=[2*inch, 4*inch])
        agents_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#fff3e0')),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(agents_table)
    
    story.append(Spacer(1, 20))
    
    # Justin's Analysis
    story.append(Paragraph("⚖️ JUSTIN'S SKEPTICAL ANALYSIS", heading_style))
    
    justin_data = report_data.get('components', {}).get('justin_verdict', {})
    if justin_data:
        # Justin's profile
        story.append(Paragraph("Judge Profile:", subheading_style))
        justin_profile_data = [
            ['Name', justin_data.get('judge', 'N/A')],
            ['Experience', f"{justin_data.get('experience_years', 0)}+ years"],
            ['Specialty', 'Market Manipulation Detection & ETH Value Analysis'],
            ['Risk Profile', 'Neutral - Neither fearful nor greedy'],
            ['Analysis Style', 'Deep, methodical, and skeptical']
        ]
        
        justin_profile_table = Table(justin_profile_data, colWidths=[2*inch, 4*inch])
        justin_profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#e8f5e8')),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(justin_profile_table)
        story.append(Spacer(1, 15))
        
        # Justin's verdict
        story.append(Paragraph("Verdict & Scores:", subheading_style))
        verdict_data = [
            ['Final Verdict', justin_data.get('verdict', 'N/A')],
            ['Confidence', f"{justin_data.get('confidence', 0):.2f}"],
            ['Bullish Score', str(justin_data.get('scores', {}).get('bullish', 0))],
            ['Bearish Score', str(justin_data.get('scores', {}).get('bearish', 0))],
            ['Neutral Score', str(justin_data.get('scores', {}).get('neutral', 0))]
        ]
        
        verdict_table = Table(verdict_data, colWidths=[2*inch, 4*inch])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#fce4ec')),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(verdict_table)
        story.append(Spacer(1, 15))
        
        # Justin's recommendation
        story.append(Paragraph("Trading Recommendation:", subheading_style))
        recommendation = justin_data.get('recommendation', {})
        rec_data = [
            ['Action', recommendation.get('action', 'N/A')],
            ['Position Sizing', recommendation.get('position_sizing', 'N/A')],
            ['Risk Management', recommendation.get('risk_management', 'N/A')],
            ['Time Horizon', recommendation.get('time_horizon', 'N/A')],
            ['Entry Strategy', recommendation.get('entry_strategy', 'N/A')],
            ['Exit Strategy', recommendation.get('exit_strategy', 'N/A')],
            ['Risk Factors', recommendation.get('risk_factors', 'N/A')]
        ]
        
        rec_table = Table(rec_data, colWidths=[2*inch, 4*inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#fff8e1')),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(rec_table)
        story.append(Spacer(1, 15))
        
        # Justin's notes
        story.append(Paragraph("Justin's Expert Notes:", subheading_style))
        justin_notes = justin_data.get('justin_notes', [])
        for note in justin_notes:
            story.append(Paragraph(f"• {note}", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Key Insights
    story.append(Paragraph("💡 KEY INSIGHTS", heading_style))
    key_insights = summary.get('key_insights', [])
    for insight in key_insights:
        story.append(Paragraph(f"• {insight}", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Conclusion
    story.append(Paragraph("✅ CONCLUSION", heading_style))
    story.append(Paragraph("The TradingAgents system has successfully executed a comprehensive analysis using:", normal_style))
    story.append(Paragraph("• 4 specialized crawl agents (Bob, Lily, J97, Yasuo)", normal_style))
    story.append(Paragraph("• Alpha team debate framework", normal_style))
    story.append(Paragraph("• Justin's skeptical veteran analysis", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Justin's 15+ years of market experience provides a crucial skeptical lens to evaluate all data sources for potential manipulation and assess ETH's true fundamental value beyond price speculation.", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Final recommendation: HOLD with conservative position sizing and high risk management, waiting for clearer signals before making significant moves.", normal_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Báo cáo được tạo tự động bởi TradingAgents System với Justin Skeptical Judge", normal_style))
    story.append(Paragraph(f"Thời gian tạo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} UTC+7", normal_style))
    
    # Build PDF
    doc.build(story)
    
    return pdf_file

def main():
    print("🔄 Creating final PDF report with Justin analysis...")
    print("=" * 60)
    
    try:
        pdf_file = create_final_pdf_with_justin()
        if pdf_file and os.path.exists(pdf_file):
            size = os.path.getsize(pdf_file)
            print(f"✅ Final PDF report created successfully!")
            print(f"📄 File: {pdf_file}")
            print(f"📊 File size: {size:,} bytes")
            print(f"📁 Full path: {os.path.abspath(pdf_file)}")
        else:
            print("❌ PDF file not created")
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")

if __name__ == "__main__":
    main()
