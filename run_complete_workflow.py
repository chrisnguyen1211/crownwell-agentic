#!/usr/bin/env python3
"""
🚀 TRADING AGENTS - MAIN ORCHESTRATOR
Complete flow: Crawl Team -> Alpha Team -> Justin + Risk Team
"""

import os
import sys
import json
import subprocess
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'AlphaTeam'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Justin'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Bob'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Lily'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Yasuo - Onchain analyst'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'J97'))

class TradingAgentsOrchestrator:
    """Main orchestrator for the complete trading agents workflow"""
    
    def __init__(self):
        self.setup_logging()
        # Load env (Supabase + Gemini) and capture a consistent subprocess env
        try:
            load_dotenv()
            # project root is this directory
            project_root = os.path.dirname(os.path.abspath(__file__))
            load_dotenv(os.path.join(project_root, '.env.supabase'))
            load_dotenv(os.path.join(project_root, 'gemini_config.env'))
        except Exception:
            pass
        self.subprocess_env = os.environ.copy()
        self.setup_paths()
        self.workflow_status = {
            'crawl_team': {'status': 'pending', 'data': {}},
            'alpha_team': {'status': 'pending', 'data': {}},
            'justin_risk': {'status': 'pending', 'data': {}},
            'overall': {'status': 'pending', 'start_time': None, 'end_time': None}
        }
        # Detailed steps for report (with ministeps)
        self.detailed_steps = {}
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_paths(self):
        """Setup project paths"""
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.project_root = self.base_path  # The script is already in the project root
        
        # Agent paths - USING REAL IMPLEMENTATIONS
        self.agent_paths = {
            'lily': os.path.join(self.project_root, 'Lily', 'standalone_sentiment_bot.py'),
            'bob': os.path.join(self.project_root, 'Bob', 'technical_analysis_engine.py'),
            'yasuo': os.path.join(self.project_root, 'Yasuo - Onchain analyst', 'yasuo_real_data_fetcher.py'),
            'j97': os.path.join(self.project_root, 'J97', 'run_j97.py'),
            'alpha': os.path.join(self.project_root, 'AlphaTeam', 'run_alpha_gemini_separate.py'),
            'justin_risk': os.path.join(self.project_root, 'Justin', 'run_justin_risk_gemini.py')
        }
        
        # Virtual environment paths
        self.venv_paths = {
            'lily': os.path.join(self.project_root, 'lily_venv', 'bin', 'python'),
            'bob': os.path.join(self.project_root, 'bob_venv', 'bin', 'python'),
            'yasuo': os.path.join(self.project_root, 'eth_venv', 'bin', 'python'),
            'j97': os.path.join(self.project_root, 'j97_venv', 'bin', 'python'),
            'alpha': 'python3',  # Use system Python for Alpha team
            'justin_risk': 'python3'  # Use system Python for Justin + Risk
        }
    
    def run_crawl_agent(self, agent_name: str) -> Tuple[bool, Dict]:
        """Run individual crawl agent"""
        self.logger.info(f"🕷️ Running {agent_name.upper()} crawl agent...")
        
        agent_path = self.agent_paths.get(agent_name)
        venv_path = self.venv_paths.get(agent_name)
        
        if not agent_path or not os.path.exists(agent_path):
            self.logger.error(f"❌ {agent_name} script not found: {agent_path}")
            return False, {}
        
        try:
            # Run agent with appropriate Python environment
            if venv_path and os.path.exists(venv_path):
                cmd = [venv_path, agent_path]
            else:
                cmd = ['python3', agent_path]
            
            self.logger.info(f"🚀 Executing: {' '.join(cmd)}")
            
            # Special timeout handling for Lily and Yasuo (15 minutes timeout)
            if agent_name in ['lily', 'yasuo']:
                # Use Popen to capture real-time output with proper timeout
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.path.dirname(agent_path),
                        env=self.subprocess_env,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Collect output in real-time
                    stdout_lines = []
                    stderr_lines = []
                    
                    import time
                    start_time = time.time()
                    timeout_seconds = 900  # 15 minutes
                    
                    # Read output with timeout
                    while time.time() - start_time < timeout_seconds:
                        # Check if process is still running
                        if process.poll() is not None:
                            # Process finished, get remaining output
                            remaining_stdout, remaining_stderr = process.communicate()
                            stdout_lines.append(remaining_stdout)
                            stderr_lines.append(remaining_stderr)
                            break
                        
                        # Try to read available output
                        try:
                            # Non-blocking read
                            import select
                            if hasattr(select, 'select'):
                                ready, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                                for stream in ready:
                                    if stream == process.stdout:
                                        line = process.stdout.readline()
                                        if line:
                                            stdout_lines.append(line)
                                    elif stream == process.stderr:
                                        line = process.stderr.readline()
                                        if line:
                                            stderr_lines.append(line)
                            else:
                                # Fallback for Windows
                                time.sleep(0.1)
                        except:
                            time.sleep(0.1)
                    
                    # Check if process is still running after timeout
                    if process.poll() is None:
                        self.logger.warning(f"⚠️ {agent_name.upper()} timed out after 15 minutes, but continuing with partial results...")
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        
                        return True, {
                            'partial_results': True, 
                            'timeout': True,
                            'stdout': ''.join(stdout_lines),
                            'stderr': ''.join(stderr_lines),
                            'returncode': -1
                        }
                    else:
                        # Process completed normally - get final output
                        final_stdout, final_stderr = process.communicate()
                        if final_stdout:
                            stdout_lines.append(final_stdout)
                        if final_stderr:
                            stderr_lines.append(final_stderr)
                        
                        self.logger.info(f"✅ {agent_name.upper()} completed successfully")
                        return True, {
                            'stdout': ''.join(stdout_lines),
                            'stderr': ''.join(stderr_lines),
                            'returncode': process.returncode
                        }
                        
                except Exception as e:
                    self.logger.error(f"❌ Error running {agent_name.upper()}: {e}")
                    return False, {
                        'stdout': '',
                        'stderr': str(e),
                        'returncode': -1
                    }
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout for other agents
                    cwd=os.path.dirname(agent_path),
                    env=self.subprocess_env
                )
            
            if result.returncode == 0:
                self.logger.info(f"✅ {agent_name.upper()} completed successfully")
                return True, {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
            else:
                self.logger.error(f"❌ {agent_name.upper()} failed with return code {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                return False, {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"❌ {agent_name.upper()} timed out after 5 minutes")
            return False, {'error': 'timeout'}
        except Exception as e:
            self.logger.error(f"❌ Error running {agent_name.upper()}: {e}")
            return False, {'error': str(e)}
    
    def run_crawl_team(self) -> bool:
        """Run all crawl team agents"""
        self.logger.info("🕷️" * 50)
        self.logger.info("🕷️ STARTING CRAWL TEAM 🕷️")
        self.logger.info("🕷️" * 50)
        
        crawl_agents = ['lily', 'bob', 'yasuo', 'j97']
        successful_agents = []
        failed_agents = []
        step_start = datetime.now(timezone.utc)
        ministeps = {}
        
        for agent in crawl_agents:
            agent_start = datetime.now(timezone.utc)
            success, data = self.run_crawl_agent(agent)
            agent_end = datetime.now(timezone.utc)
            duration = (agent_end - agent_start).total_seconds()
            
            if success:
                successful_agents.append(agent)
                self.workflow_status['crawl_team']['data'][agent] = data
                ministeps[f"{agent}_crawl"] = {
                    'agent': agent.capitalize(),
                    'task': 'Data collection',
                    'status': 'completed',
                    'start_time': agent_start.isoformat(),
                    'end_time': agent_end.isoformat(),
                    'duration_seconds': duration,
                    'partial_results': bool(data.get('partial_results')),
                    'stdout_full': data.get('stdout') or '',
                    'stderr_full': data.get('stderr') or ''
                }
            else:
                failed_agents.append(agent)
                self.workflow_status['crawl_team']['data'][agent] = data
                ministeps[f"{agent}_crawl"] = {
                    'agent': agent.capitalize(),
                    'task': 'Data collection',
                    'status': 'failed',
                    'start_time': agent_start.isoformat(),
                    'end_time': agent_end.isoformat(),
                    'duration_seconds': duration,
                    'error': data.get('error') or (data.get('stderr') or '')[-200:]
                }
        
        # Update crawl team status
        if len(successful_agents) >= 3:  # At least 3 out of 4 agents must succeed
            self.workflow_status['crawl_team']['status'] = 'completed'
            self.logger.info(f"✅ Crawl team completed: {len(successful_agents)}/4 agents successful")
            step_end = datetime.now(timezone.utc)
            self.detailed_steps['step_1_crawl_team'] = {
                'step_name': 'Crawl Team Data Collection',
                'status': 'completed',
                'start_time': step_start.isoformat(),
                'end_time': step_end.isoformat(),
                'duration_seconds': (step_end - step_start).total_seconds(),
                'ministeps': ministeps
            }
            return True
        else:
            self.workflow_status['crawl_team']['status'] = 'failed'
            self.logger.error(f"❌ Crawl team failed: {len(failed_agents)} agents failed")
            step_end = datetime.now(timezone.utc)
            self.detailed_steps['step_1_crawl_team'] = {
                'step_name': 'Crawl Team Data Collection',
                'status': 'failed',
                'start_time': step_start.isoformat(),
                'end_time': step_end.isoformat(),
                'duration_seconds': (step_end - step_start).total_seconds(),
                'ministeps': ministeps
            }
            return False
    
    def run_alpha_team(self) -> bool:
        """Run Alpha team debate"""
        self.logger.info("🏛️" * 50)
        self.logger.info("🏛️ STARTING ALPHA TEAM 🏛️")
        self.logger.info("🏛️" * 50)
        
        alpha_path = self.agent_paths.get('alpha')
        
        if not alpha_path or not os.path.exists(alpha_path):
            self.logger.error(f"❌ Alpha team script not found: {alpha_path}")
            self.workflow_status['alpha_team']['status'] = 'failed'
            return False
        
        try:
            step_start = datetime.now(timezone.utc)
            self.logger.info("🧠 Running Alpha team debate with Gemini...")
            
            cmd = ['python3', alpha_path]
            self.logger.info(f"🚀 Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for debate
                cwd=os.path.dirname(alpha_path),
                env=self.subprocess_env
            )
            
            if result.returncode == 0:
                self.logger.info("✅ Alpha team debate completed successfully")
                self.workflow_status['alpha_team']['status'] = 'completed'
                self.workflow_status['alpha_team']['data'] = {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
                step_end = datetime.now(timezone.utc)
                # Try to parse embedded full debate JSON from stdout
                embedded = None
                try:
                    marker_start = "=== ALPHA_DEBATE_SESSION_JSON_START ==="
                    marker_end = "=== ALPHA_DEBATE_SESSION_JSON_END ==="
                    if result.stdout and marker_start in result.stdout and marker_end in result.stdout:
                        start_idx = result.stdout.index(marker_start) + len(marker_start)
                        end_idx = result.stdout.index(marker_end, start_idx)
                        json_str = result.stdout[start_idx:end_idx].strip()
                        embedded = json.loads(json_str)
                except Exception:
                    embedded = None
                self.detailed_steps['step_2_alpha_team'] = {
                    'step_name': 'Alpha Team Debate',
                    'status': 'completed',
                    'start_time': step_start.isoformat(),
                    'end_time': step_end.isoformat(),
                    'duration_seconds': (step_end - step_start).total_seconds(),
                    'results': {
                        'stdout_full': result.stdout or '',
                        'stderr_full': result.stderr or '',
                        'alpha_debate_session': embedded or {}
                    }
                }
                return True
            else:
                self.logger.error(f"❌ Alpha team failed with return code {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                self.workflow_status['alpha_team']['status'] = 'failed'
                self.workflow_status['alpha_team']['data'] = {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
                step_end = datetime.now(timezone.utc)
                self.detailed_steps['step_2_alpha_team'] = {
                    'step_name': 'Alpha Team Debate',
                    'status': 'failed',
                    'start_time': step_start.isoformat(),
                    'end_time': step_end.isoformat(),
                    'duration_seconds': (step_end - step_start).total_seconds(),
                    'results': {
                        'stdout_full': result.stdout or '',
                        'stderr_full': result.stderr or ''
                    }
                }
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Alpha team timed out after 10 minutes")
            self.workflow_status['alpha_team']['status'] = 'failed'
            # Record step timeout
            step_end = datetime.now(timezone.utc)
            self.detailed_steps['step_2_alpha_team'] = {
                'step_name': 'Alpha Team Debate',
                'status': 'timeout',
                'end_time': step_end.isoformat()
            }
            return False
        except Exception as e:
            self.logger.error(f"❌ Error running Alpha team: {e}")
            self.workflow_status['alpha_team']['status'] = 'failed'
            step_end = datetime.now(timezone.utc)
            self.detailed_steps['step_2_alpha_team'] = {
                'step_name': 'Alpha Team Debate',
                'status': 'error',
                'end_time': step_end.isoformat(),
                'error': str(e)
            }
            return False
    
    def run_justin_risk_team(self, risk_profile: str = 'NEUTRAL') -> bool:
        """Run Justin + Risk team analysis"""
        self.logger.info("⚖️" * 50)
        self.logger.info("⚖️ STARTING JUSTIN + RISK TEAM ⚖️")
        self.logger.info("⚖️" * 50)
        
        justin_path = self.agent_paths.get('justin_risk')
        
        if not justin_path or not os.path.exists(justin_path):
            self.logger.error(f"❌ Justin + Risk script not found: {justin_path}")
            self.workflow_status['justin_risk']['status'] = 'failed'
            return False
        
        try:
            step_start = datetime.now(timezone.utc)
            self.logger.info(f"👨‍💼 Running Justin + Risk analysis (Profile: {risk_profile})...")
            
            # Set environment variable for risk profile
            env = self.subprocess_env.copy()
            env['RISK_PROFILE'] = risk_profile
            
            cmd = ['python3', justin_path]
            self.logger.info(f"🚀 Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=os.path.dirname(justin_path),
                env=env
            )
            
            if result.returncode == 0:
                self.logger.info("✅ Justin + Risk analysis completed successfully")
                self.workflow_status['justin_risk']['status'] = 'completed'
                self.workflow_status['justin_risk']['data'] = {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode,
                    'risk_profile': risk_profile
                }
                step_end = datetime.now(timezone.utc)
                self.detailed_steps['step_3_justin_risk'] = {
                    'step_name': 'Justin + Risk Analysis',
                    'status': 'completed',
                    'start_time': step_start.isoformat(),
                    'end_time': step_end.isoformat(),
                    'duration_seconds': (step_end - step_start).total_seconds(),
                    'results': {
                        'stdout_full': result.stdout or '',
                        'stderr_full': result.stderr or '',
                        'risk_profile': risk_profile
                    }
                }
                return True
            else:
                self.logger.error(f"❌ Justin + Risk failed with return code {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                self.workflow_status['justin_risk']['status'] = 'failed'
                self.workflow_status['justin_risk']['data'] = {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode,
                    'risk_profile': risk_profile
                }
                step_end = datetime.now(timezone.utc)
                self.detailed_steps['step_3_justin_risk'] = {
                    'step_name': 'Justin + Risk Analysis',
                    'status': 'failed',
                    'start_time': step_start.isoformat(),
                    'end_time': step_end.isoformat(),
                    'duration_seconds': (step_end - step_start).total_seconds(),
                    'results': {
                        'stdout_full': result.stdout or '',
                        'stderr_full': result.stderr or '',
                        'risk_profile': risk_profile
                    }
                }
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Justin + Risk timed out after 10 minutes")
            self.workflow_status['justin_risk']['status'] = 'failed'
            step_end = datetime.now(timezone.utc)
            self.detailed_steps['step_3_justin_risk'] = {
                'step_name': 'Justin + Risk Analysis',
                'status': 'timeout',
                'end_time': step_end.isoformat()
            }
            return False
        except Exception as e:
            self.logger.error(f"❌ Error running Justin + Risk: {e}")
            self.workflow_status['justin_risk']['status'] = 'failed'
            step_end = datetime.now(timezone.utc)
            self.detailed_steps['step_3_justin_risk'] = {
                'step_name': 'Justin + Risk Analysis',
                'status': 'error',
                'end_time': step_end.isoformat(),
                'error': str(e)
            }
            return False
    
    def generate_workflow_report(self) -> Dict:
        """Generate comprehensive workflow report"""
        report = {
            'workflow_id': f"trading_agents_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': self.workflow_status['overall']['status'],
            'start_time': self.workflow_status['overall']['start_time'],
            'end_time': self.workflow_status['overall']['end_time'],
            'detailed_steps': self.detailed_steps,
            'teams': {
                'crawl_team': {
                    'status': self.workflow_status['crawl_team']['status'],
                    'agents': list(self.workflow_status['crawl_team']['data'].keys()),
                    'success_count': len([k for k, v in self.workflow_status['crawl_team']['data'].items() if v.get('returncode') == 0])
                },
                'alpha_team': {
                    'status': self.workflow_status['alpha_team']['status'],
                    'data_available': bool(self.workflow_status['alpha_team']['data'])
                },
                'justin_risk': {
                    'status': self.workflow_status['justin_risk']['status'],
                    'risk_profile': self.workflow_status['justin_risk']['data'].get('risk_profile', 'N/A'),
                    'data_available': bool(self.workflow_status['justin_risk']['data'])
                }
            },
            'summary': self.generate_summary()
        }
        
        return report
    
    def generate_summary(self) -> str:
        """Generate workflow summary"""
        crawl_status = self.workflow_status['crawl_team']['status']
        alpha_status = self.workflow_status['alpha_team']['status']
        justin_status = self.workflow_status['justin_risk']['status']
        
        if all(status == 'completed' for status in [crawl_status, alpha_status, justin_status]):
            return "✅ Complete workflow executed successfully. All teams completed their analysis."
        elif any(status == 'failed' for status in [crawl_status, alpha_status, justin_status]):
            failed_teams = [team for team, status in [('Crawl', crawl_status), ('Alpha', alpha_status), ('Justin+Risk', justin_status)] if status == 'failed']
            return f"❌ Workflow partially failed. Failed teams: {', '.join(failed_teams)}"
        else:
            return "⚠️ Workflow in progress or incomplete."
    
    def save_report(self, report: Dict) -> str:
        """Save workflow report to file"""
        reports_dir = os.path.join(self.project_root, 'Reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"workflow_report_{report['workflow_id']}.json"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"📄 Workflow report saved: {filepath}")
        return filepath
    
    def run_complete_workflow(self, risk_profile: str = 'NEUTRAL') -> Dict:
        """Run the complete trading agents workflow"""
        self.logger.info("🚀" * 60)
        self.logger.info("🚀 STARTING COMPLETE TRADING AGENTS WORKFLOW 🚀")
        self.logger.info("🚀" * 60)
        self.logger.info("")
        self.logger.info("📋 Workflow Steps:")
        self.logger.info("   1. Crawl Team (Lily, Bob, Yasuo, J97)")
        self.logger.info("   2. Alpha Team (Bullish vs Bearish Debate)")
        self.logger.info("   3. Justin + Risk Team (Trading Analysis)")
        self.logger.info("")
        
        # Start timing
        self.workflow_status['overall']['start_time'] = datetime.now(timezone.utc).isoformat()
        
        # Step 1: Crawl Team
        self.logger.info("🕷️ STEP 1: CRAWL TEAM")
        self.logger.info("=" * 50)
        crawl_success = self.run_crawl_team()
        
        if not crawl_success:
            self.logger.error("❌ Crawl team failed. Stopping workflow.")
            self.workflow_status['overall']['status'] = 'failed'
            self.workflow_status['overall']['end_time'] = datetime.now(timezone.utc).isoformat()
            return self.generate_workflow_report()
        
        # Step 2: Alpha Team
        self.logger.info("🏛️ STEP 2: ALPHA TEAM")
        self.logger.info("=" * 50)
        alpha_success = self.run_alpha_team()
        
        if not alpha_success:
            self.logger.error("❌ Alpha team failed. Stopping workflow.")
            self.workflow_status['overall']['status'] = 'failed'
            self.workflow_status['overall']['end_time'] = datetime.now(timezone.utc).isoformat()
            return self.generate_workflow_report()
        
        # Step 3: Justin + Risk Team
        self.logger.info("⚖️ STEP 3: JUSTIN + RISK TEAM")
        self.logger.info("=" * 50)
        justin_success = self.run_justin_risk_team(risk_profile)
        
        # Complete workflow
        self.workflow_status['overall']['end_time'] = datetime.now(timezone.utc).isoformat()
        
        if justin_success:
            self.workflow_status['overall']['status'] = 'completed'
            self.logger.info("🎉 COMPLETE WORKFLOW SUCCESSFUL!")
        else:
            self.workflow_status['overall']['status'] = 'failed'
            self.logger.error("❌ Workflow failed at Justin + Risk team.")
        
        # Generate and save report
        report = self.generate_workflow_report()
        report_path = self.save_report(report)
        
        # Print final summary
        self.print_final_summary(report)
        
        return report
    
    def print_final_summary(self, report: Dict):
        """Print final workflow summary"""
        self.logger.info("")
        self.logger.info("📊" * 60)
        self.logger.info("📊 FINAL WORKFLOW SUMMARY 📊")
        self.logger.info("📊" * 60)
        
        self.logger.info(f"Workflow ID: {report['workflow_id']}")
        self.logger.info(f"Overall Status: {report['overall_status']}")
        self.logger.info(f"Start Time: {report['start_time']}")
        self.logger.info(f"End Time: {report['end_time']}")
        
        self.logger.info("")
        self.logger.info("Team Results:")
        for team, data in report['teams'].items():
            status_emoji = "✅" if data['status'] == 'completed' else "❌"
            self.logger.info(f"  {status_emoji} {team.replace('_', ' ').title()}: {data['status']}")
        
        self.logger.info("")
        self.logger.info(f"Summary: {report['summary']}")
        
        self.logger.info("")
        self.logger.info("🚀" * 60)
        self.logger.info("🚀 TRADING AGENTS WORKFLOW COMPLETE! 🚀")
        self.logger.info("🚀" * 60)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Trading Agents Workflow Orchestrator')
    parser.add_argument('--risk-profile', choices=['AGGRESSIVE', 'NEUTRAL', 'CONSERVATIVE'], 
                       default='NEUTRAL', help='Risk profile for analysis')
    parser.add_argument('--team', choices=['crawl', 'alpha', 'justin', 'all'], 
                       default='all', help='Which team(s) to run')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = TradingAgentsOrchestrator()
    
    if args.team == 'all':
        # Run complete workflow
        orchestrator.run_complete_workflow(args.risk_profile)
    elif args.team == 'crawl':
        orchestrator.run_crawl_team()
    elif args.team == 'alpha':
        orchestrator.run_alpha_team()
    elif args.team == 'justin':
        orchestrator.run_justin_risk_team(args.risk_profile)

if __name__ == "__main__":
    main()
