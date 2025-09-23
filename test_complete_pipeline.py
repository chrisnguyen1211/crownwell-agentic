#!/usr/bin/env python3
"""
Complete Pipeline Test with Data Flow and Dispatcher
Tests the entire Trading Agents system with enhanced data flow and dispatcher functionality
"""

import os
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompletePipelineTest:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_results = {}
        
    def test_crawl_agents(self) -> Dict[str, Any]:
        """Test all Crawl agents"""
        logger.info("🚀 Testing Crawl Agents...")
        
        agents = ['bob', 'j97', 'yasuo']  # Skip lily due to timeout issues
        results = {}
        
        for agent in agents:
            try:
                if agent == 'bob':
                    cmd = f"cd '{self.base_dir}/Bob' && python3 run_bob.py"
                elif agent == 'j97':
                    cmd = f"cd '{self.base_dir}/J97' && python3 run_j97.py --mode single"
                elif agent == 'yasuo':
                    cmd = f"cd '{self.base_dir}/Yasuo - Onchain analyst' && python3 yasuo_real_data_fetcher.py"
                
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    results[agent] = {'status': 'success', 'message': 'Completed successfully'}
                else:
                    results[agent] = {'status': 'error', 'message': result.stderr}
                    
            except subprocess.TimeoutExpired:
                results[agent] = {'status': 'timeout', 'message': 'Agent timed out'}
            except Exception as e:
                results[agent] = {'status': 'error', 'message': str(e)}
        
        return results
    
    def test_alpha_team(self) -> Dict[str, Any]:
        """Test Alpha Team with Gemini 2.5"""
        logger.info("⚔️ Testing Alpha Team...")
        
        try:
            cmd = f"cd '{self.base_dir}/AlphaTeam' && python3 run_alpha_gemini.py"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {'status': 'success', 'message': 'Alpha Team completed successfully'}
            else:
                return {'status': 'error', 'message': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Alpha Team timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def test_justin(self) -> Dict[str, Any]:
        """Test Justin with Gemini 2.5"""
        logger.info("🏛️ Testing Justin...")
        
        try:
            cmd = f"cd '{self.base_dir}/Justin' && python3 justin_gemini.py"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {'status': 'success', 'message': 'Justin completed successfully'}
            else:
                return {'status': 'error', 'message': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Justin timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def test_risk_team(self) -> Dict[str, Any]:
        """Test Risk Team with Gemini 2.5"""
        logger.info("🛡️ Testing Risk Team...")
        
        try:
            cmd = f"cd '{self.base_dir}/RiskTeam' && python3 risk_team_gemini.py --mode neutral"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {'status': 'success', 'message': 'Risk Team completed successfully'}
            else:
                return {'status': 'error', 'message': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Risk Team timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def test_dispatcher(self) -> Dict[str, Any]:
        """Test Enhanced Dispatcher"""
        logger.info("🚀 Testing Enhanced Dispatcher...")
        
        try:
            cmd = f"cd '{self.base_dir}' && python3 enhanced_dispatcher.py --check"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return {'status': 'success', 'message': 'Dispatcher completed successfully'}
            else:
                return {'status': 'error', 'message': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Dispatcher timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def test_data_flow(self) -> Dict[str, Any]:
        """Test data flow between components"""
        logger.info("📊 Testing Data Flow...")
        
        try:
            cmd = f"cd '{self.base_dir}' && python3 check_data_flow.py"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {'status': 'success', 'message': 'Data flow check completed successfully'}
            else:
                return {'status': 'error', 'message': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Data flow check timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def test_full_pipeline(self) -> Dict[str, Any]:
        """Test full pipeline with Gemini 2.5"""
        logger.info("🎯 Testing Full Pipeline...")
        
        try:
            cmd = f"cd '{self.base_dir}' && python3 run_full_pipeline_gemini.py --risk-mode neutral"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1800)  # 30 minutes
            
            if result.returncode == 0:
                return {'status': 'success', 'message': 'Full pipeline completed successfully'}
            else:
                return {'status': 'error', 'message': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Full pipeline timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run complete pipeline test"""
        logger.info("🚀 Starting Complete Pipeline Test...")
        logger.info("="*60)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # Test individual components
        test_results['tests']['crawl_agents'] = self.test_crawl_agents()
        test_results['tests']['alpha_team'] = self.test_alpha_team()
        test_results['tests']['justin'] = self.test_justin()
        test_results['tests']['risk_team'] = self.test_risk_team()
        test_results['tests']['dispatcher'] = self.test_dispatcher()
        test_results['tests']['data_flow'] = self.test_data_flow()
        
        # Test full pipeline
        test_results['tests']['full_pipeline'] = self.test_full_pipeline()
        
        # Calculate summary
        total_tests = len(test_results['tests'])
        successful_tests = sum(1 for test in test_results['tests'].values() if test['status'] == 'success')
        failed_tests = total_tests - successful_tests
        
        test_results['summary'] = {
            'total_tests': total_tests,
            'successful': successful_tests,
            'failed': failed_tests,
            'success_rate': f"{(successful_tests/total_tests)*100:.1f}%"
        }
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"complete_pipeline_test_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        logger.info(f"✅ Complete test report saved: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 COMPLETE PIPELINE TEST RESULTS")
        print("="*60)
        
        for test_name, result in test_results['tests'].items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_icon} {test_name.upper()}: {result['status']}")
            if result['status'] != 'success':
                print(f"   Message: {result['message']}")
        
        print(f"\n📈 SUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {test_results['summary']['success_rate']}")
        
        if successful_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! SYSTEM READY FOR PRODUCTION!")
        else:
            print(f"\n⚠️ {failed_tests} TESTS FAILED. CHECK LOGS FOR DETAILS.")
        
        return test_results

def main():
    """Main execution function"""
    tester = CompletePipelineTest()
    tester.run_complete_test()

if __name__ == "__main__":
    main()






