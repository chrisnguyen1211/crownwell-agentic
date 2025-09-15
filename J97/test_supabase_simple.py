#!/usr/bin/env python3
"""
Simple Supabase Test
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('api_keys.env')

def test_supabase():
    """Test Supabase connection with simple approach"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    print("🕵️ J97 Supabase Test")
    print("=" * 30)
    
    if not supabase_url or supabase_key == 'your_supabase_url':
        print("❌ Supabase credentials not configured")
        print("\n📋 To setup Supabase:")
        print("1. Go to https://supabase.com")
        print("2. Create a new project")
        print("3. Get your URL and API key from Settings > API")
        print("4. Update api_keys.env with:")
        print("   SUPABASE_URL=your_actual_url")
        print("   SUPABASE_KEY=your_actual_key")
        return False
    
    print(f"✅ Supabase URL: {supabase_url[:30]}...")
    print(f"✅ Supabase Key: {supabase_key[:20]}...")
    
    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test a simple query
        result = client.table('j97_news_articles').select('id').limit(1).execute()
        print("✅ Supabase connection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if your Supabase project is active")
        print("2. Verify the URL and key are correct")
        print("3. Make sure the tables exist (run setup_supabase.py first)")
        return False

if __name__ == "__main__":
    test_supabase()



