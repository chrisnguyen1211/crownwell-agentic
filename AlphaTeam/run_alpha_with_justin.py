#!/usr/bin/env python3
"""
Complete Alpha Team Workflow with Justin Skeptical Judge
1. Run Alpha debate
2. Dispatch to crawl agents
3. Run Justin's skeptical analysis
4. Generate final comprehensive report
"""

import os
import json
import subprocess
import sys
from datetime import datetime

BASE = "/Users/nguyenhuycuong/Crownwell agentic/TradingAgents"
ALPHA_DIR = os.path.join(BASE, 'AlphaTeam')
JUSTIN_DIR = os.path.join(BASE, 'JustinLy')
REPORTS_DIR = os.path.join(BASE, 'Reports')

def run_alpha_debate():
    """Run Alpha team to generate debate"""
    print("🏛️ Running Alpha Team Debate...")
    alpha_script = os.path.join(ALPHA_DIR, 'run_alpha.py')
    res = subprocess.run([sys.executable, alpha_script], cwd=ALPHA_DIR, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("Alpha stderr:", res.stderr)
    return res.returncode == 0

def run_dispatch():
    """Run dispatcher to execute crawl agents"""
    print("📡 Dispatching to Crawl Agents...")
    dispatch_script = os.path.join(ALPHA_DIR, 'dispatch_requests.py')
    res = subprocess.run([dispatch_script], cwd=ALPHA_DIR, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("Dispatch stderr:", res.stderr)
    return res.returncode == 0

def run_justin_judge():
    """Run Justin's skeptical analysis"""
    print("⚖️ Running Justin's Skeptical Analysis...")
    justin_script = os.path.join(JUSTIN_DIR, 'run_justin.py')
    res = subprocess.run([sys.executable, justin_script], cwd=JUSTIN_DIR, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("Justin stderr:", res.stderr)
    return res.returncode == 0

def get_latest_files():
    """Get the latest generated files"""
    files = {}
    
    # Alpha debate file
    alpha_files = sorted([f for f in os.listdir(ALPHA_DIR) if f.startswith('alpha_debate_') and f.endswith('.json')])
    if alpha_files:
        files['alpha_debate'] = os.path.join(ALPHA_DIR, alpha_files[-1])
    
    # Dispatch report
    if os.path.exists(REPORTS_DIR):
        dispatch_files = sorted([f for f in os.listdir(REPORTS_DIR) if f.startswith('alpha_dispatch_') and f.endswith('.json')])
        if dispatch_files:
            files['dispatch_report'] = os.path.join(REPORTS_DIR, dispatch_files[-1])
    
    # Justin verdict
    justin_files = sorted([f for f in os.listdir(JUSTIN_DIR) if f.startswith('justin_verdict_') and f.endswith('.json')])
    if justin_files:
        files['justin_verdict'] = os.path.join(JUSTIN_DIR, justin_files[-1])
    
    return files

def generate_comprehensive_report(files):
    """Generate comprehensive report combining all results"""
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "workflow": "Alpha Team + Justin Skeptical Judge",
        "status": "completed",
        "components": {}
    }
    
    # Load Alpha debate
    if 'alpha_debate' in files:
        with open(files['alpha_debate'], 'r') as f:
            alpha_data = json.load(f)
        report['components']['alpha_debate'] = {
            "file": files['alpha_debate'],
            "bullish_thesis": alpha_data.get('bullish', {}).get('thesis', ''),
            "bearish_thesis": alpha_data.get('bearish', {}).get('thesis', ''),
            "debate_rounds": alpha_data.get('debate_rounds', [])
        }
    
    # Load dispatch results
    if 'dispatch_report' in files:
        with open(files['dispatch_report'], 'r') as f:
            dispatch_data = json.load(f)
        report['components']['dispatch_results'] = {
            "file": files['dispatch_report'],
            "agents_run": dispatch_data.get('targets', []),
            "successful_runs": [k for k, v in dispatch_data.get('runs', {}).items() if v.get('ok', False)],
            "failed_runs": [k for k, v in dispatch_data.get('runs', {}).items() if not v.get('ok', False)]
        }
    
    # Load Justin verdict
    if 'justin_verdict' in files:
        with open(files['justin_verdict'], 'r') as f:
            justin_data = json.load(f)
        report['components']['justin_verdict'] = {
            "file": files['justin_verdict'],
            "judge": justin_data.get('judge', ''),
            "experience_years": justin_data.get('experience_years', 0),
            "verdict": justin_data.get('verdict', ''),
            "confidence": justin_data.get('confidence', 0),
            "scores": justin_data.get('scores', {}),
            "recommendation": justin_data.get('recommendation', {}),
            "justin_notes": justin_data.get('justin_notes', [])
        }
    
    # Generate summary
    if 'justin_verdict' in files:
        justin_verdict = report['components']['justin_verdict']
        report['summary'] = {
            "final_verdict": justin_verdict['verdict'],
            "confidence_level": justin_verdict['confidence'],
            "judge_experience": f"{justin_verdict['experience_years']}+ years",
            "analysis_style": "Skeptical veteran approach",
            "key_insights": justin_verdict['justin_notes'][:3]  # Top 3 insights
        }
    
    return report

def main():
    """Main workflow execution"""
    print("🚀 STARTING COMPLETE ALPHA TEAM + JUSTIN WORKFLOW")
    print("=" * 70)
    
    success_count = 0
    total_steps = 3
    
    # Step 1: Run Alpha debate
    if run_alpha_debate():
        success_count += 1
        print("✅ Alpha debate completed")
    else:
        print("❌ Alpha debate failed")
        return
    
    # Step 2: Run dispatch
    if run_dispatch():
        success_count += 1
        print("✅ Dispatch completed")
    else:
        print("❌ Dispatch failed")
        return
    
    # Step 3: Run Justin judge
    if run_justin_judge():
        success_count += 1
        print("✅ Justin analysis completed")
    else:
        print("❌ Justin analysis failed")
        return
    
    print(f"\n📊 WORKFLOW SUMMARY: {success_count}/{total_steps} steps completed")
    
    # Generate comprehensive report
    print("\n📋 Generating comprehensive report...")
    files = get_latest_files()
    report = generate_comprehensive_report(files)
    
    # Save comprehensive report
    report_file = os.path.join(REPORTS_DIR, f"comprehensive_alpha_justin_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Comprehensive report saved to: {report_file}")
    
    # Print final summary
    if 'summary' in report:
        summary = report['summary']
        print("\n🏆 FINAL SUMMARY:")
        print(f"🎯 Verdict: {summary['final_verdict']}")
        print(f"🎲 Confidence: {summary['confidence_level']:.2f}")
        print(f"👨‍💼 Judge: {summary['judge_experience']} experience")
        print(f"🔍 Style: {summary['analysis_style']}")
        print("\n💭 Key Insights:")
        for insight in summary['key_insights']:
            print(f"   • {insight}")
    
    print("\n🎉 Complete workflow finished successfully!")

if __name__ == '__main__':
    main()
