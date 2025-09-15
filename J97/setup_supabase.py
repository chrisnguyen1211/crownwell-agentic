#!/usr/bin/env python3
"""
J97 Supabase Setup Script
Create tables for news articles and daily reports
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('api_keys.env')

def setup_supabase_tables():
    """Setup Supabase tables for J97"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in environment variables")
        print("Please add SUPABASE_URL and SUPABASE_KEY to api_keys.env")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # SQL for creating tables
        create_tables_sql = """
        -- News articles table
        CREATE TABLE IF NOT EXISTS j97_news_articles (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT UNIQUE NOT NULL,
            published_at TIMESTAMP WITH TIME ZONE,
            source TEXT,
            api_source TEXT,
            sentiment JSONB,
            impact_score FLOAT DEFAULT 0,
            key_phrases TEXT[],
            category TEXT DEFAULT 'general',
            analyzed_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Daily reports table
        CREATE TABLE IF NOT EXISTS j97_daily_reports (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            total_articles INTEGER DEFAULT 0,
            trading_signal JSONB,
            categories JSONB,
            sentiment_breakdown JSONB,
            top_key_phrases JSONB,
            high_impact_articles INTEGER DEFAULT 0,
            high_impact_titles TEXT[],
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_j97_articles_published_at ON j97_news_articles(published_at);
        CREATE INDEX IF NOT EXISTS idx_j97_articles_category ON j97_news_articles(category);
        CREATE INDEX IF NOT EXISTS idx_j97_articles_impact_score ON j97_news_articles(impact_score);
        CREATE INDEX IF NOT EXISTS idx_j97_articles_created_at ON j97_news_articles(created_at);
        CREATE INDEX IF NOT EXISTS idx_j97_reports_date ON j97_daily_reports(date);
        """
        
        print("📝 Creating Supabase tables...")
        
        # Execute SQL (Note: This might need to be done manually in Supabase dashboard)
        print("⚠️  Please run the following SQL in your Supabase SQL Editor:")
        print("-" * 60)
        print(create_tables_sql)
        print("-" * 60)
        
        print("\n📋 Manual Setup Steps:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the SQL above")
        print("4. Click 'Run' to create the tables")
        print("5. Update api_keys.env with your Supabase credentials")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Supabase: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test connection by trying to read from a table
        result = supabase.table('j97_news_articles').select('id').limit(1).execute()
        print("✅ Supabase connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🕵️ J97 Supabase Setup")
    print("=" * 40)
    
    # Test connection first
    if test_supabase_connection():
        print("✅ Supabase is ready!")
    else:
        print("❌ Supabase setup needed")
        setup_supabase_tables()



