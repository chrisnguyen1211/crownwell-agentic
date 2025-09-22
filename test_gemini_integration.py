#!/usr/bin/env python3
"""
Test script for Gemini integration
"""

import os
import sys

def test_gemini_setup():
    """Test if Gemini is properly configured"""
    print("🧪 Testing Gemini Integration Setup...")
    print("="*50)
    
    # Test 1: Check environment variable
    print("1. Checking GEMINI_API_KEY...")
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"   ✅ GEMINI_API_KEY found: {api_key[:10]}...")
    else:
        print("   ❌ GEMINI_API_KEY not found")
        print("   Please set: export GEMINI_API_KEY='your_api_key_here'")
        return False
    
    # Test 2: Check imports
    print("2. Testing imports...")
    try:
        import google.generativeai as genai
        print("   ✅ google.generativeai imported successfully")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   Please install: pip install google-generativeai")
        return False
    
    # Test 3: Test Gemini connection
    print("3. Testing Gemini connection...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Hello, this is a test. Please respond with 'Test successful'.")
        print(f"   ✅ Gemini connection successful: {response.text[:50]}...")
    except Exception as e:
        print(f"   ❌ Gemini connection failed: {e}")
        return False
    
    # Test 4: Check file structure
    print("4. Checking file structure...")
    required_files = [
        'gemini_config.py',
        'AlphaTeam/run_alpha_gemini.py',
        'Justin/justin_gemini.py',
        'RiskTeam/risk_team_gemini.py',
        'run_full_pipeline_gemini.py'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} not found")
            all_files_exist = False
    
    if not all_files_exist:
        return False
    
    # Test 5: Test gemini_config import
    print("5. Testing gemini_config import...")
    try:
        sys.path.append('.')
        from gemini_config import get_gemini_llm, PERSONAS
        print("   ✅ gemini_config imported successfully")
        print(f"   ✅ Found {len(PERSONAS)} personas")
    except Exception as e:
        print(f"   ❌ gemini_config import failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Gemini integration is ready.")
    return True

def test_individual_components():
    """Test individual components"""
    print("\n🔧 Testing Individual Components...")
    print("="*50)
    
    # Test Alpha Team
    print("1. Testing Alpha Team...")
    try:
        from AlphaTeam.run_alpha_gemini import AlphaTeamGemini
        alpha = AlphaTeamGemini()
        print("   ✅ Alpha Team Gemini initialized")
    except Exception as e:
        print(f"   ❌ Alpha Team test failed: {e}")
    
    # Test Justin
    print("2. Testing Justin...")
    try:
        from Justin.justin_gemini import JustinGemini
        justin = JustinGemini()
        print("   ✅ Justin Gemini initialized")
    except Exception as e:
        print(f"   ❌ Justin test failed: {e}")
    
    # Test Risk Team
    print("3. Testing Risk Team...")
    try:
        from RiskTeam.risk_team_gemini import RiskTeamGemini
        risk = RiskTeamGemini()
        print("   ✅ Risk Team Gemini initialized")
    except Exception as e:
        print(f"   ❌ Risk Team test failed: {e}")

def main():
    """Main test function"""
    print("🚀 Trading Agents Gemini Integration Test")
    print("="*60)
    
    # Basic setup test
    if not test_gemini_setup():
        print("\n❌ Setup test failed. Please fix the issues above.")
        return False
    
    # Component test
    test_individual_components()
    
    print("\n" + "="*60)
    print("✅ Gemini integration test completed!")
    print("\nNext steps:")
    print("1. Run full pipeline: python3 run_full_pipeline_gemini.py")
    print("2. Or run individual components as needed")
    print("3. Check GEMINI_SETUP.md for detailed instructions")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
