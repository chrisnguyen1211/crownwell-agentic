#!/usr/bin/env python3
"""
🔧 SUPABASE TABLE CREATOR
Automatically create missing tables for TradingAgents system
"""

import os
import sys
from supabase import create_client

def create_tables():
    """Create missing Supabase tables"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print('❌ SUPABASE_URL and SUPABASE_KEY not set')
        print('Please set environment variables:')
        print('export SUPABASE_URL="your_url"')
        print('export SUPABASE_KEY="your_key"')
        return False
    
    try:
        supabase = create_client(url, key)
        print('✅ Connected to Supabase')
        
        # SQL commands to create tables
        sql_commands = [
            # Bob Technical Analysis Table
            """
            CREATE TABLE IF NOT EXISTS bob_technical_analysis (
                id SERIAL PRIMARY KEY,
                analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                timeframe VARCHAR(10) NOT NULL,
                current_price DECIMAL(20,8),
                price_change_24h DECIMAL(10,4),
                volume_24h DECIMAL(20,2),
                rsi_14 DECIMAL(5,2),
                macd_line DECIMAL(10,6),
                macd_signal DECIMAL(10,6),
                macd_histogram DECIMAL(10,6),
                bb_upper DECIMAL(20,8),
                bb_middle DECIMAL(20,8),
                bb_lower DECIMAL(20,8),
                bb_position DECIMAL(5,2),
                sma_20 DECIMAL(20,8),
                sma_50 DECIMAL(20,8),
                sma_200 DECIMAL(20,8),
                ema_12 DECIMAL(20,8),
                ema_26 DECIMAL(20,8),
                patterns JSONB,
                support_levels JSONB,
                resistance_levels JSONB,
                signal_direction VARCHAR(10),
                signal_strength DECIMAL(5,3),
                confidence_score DECIMAL(5,3),
                risk_level VARCHAR(20),
                analysis_summary TEXT,
                key_insights JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Alpha Team Debate Sessions Table
            """
            CREATE TABLE IF NOT EXISTS alpha_debate_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(50) UNIQUE NOT NULL,
                session_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                bullish_agent_name VARCHAR(50) DEFAULT 'Bullish Agent',
                bearish_agent_name VARCHAR(50) DEFAULT 'Bearish Agent',
                crawl_data_sources JSONB,
                round_1_bullish_evidence JSONB,
                round_1_bearish_evidence JSONB,
                round_1_bullish_rebuttal JSONB,
                round_1_bearish_rebuttal JSONB,
                round_2_bullish_evidence JSONB,
                round_2_bearish_evidence JSONB,
                round_2_bullish_rebuttal JSONB,
                round_2_bearish_rebuttal JSONB,
                final_bullish_score DECIMAL(5,3),
                final_bearish_score DECIMAL(5,3),
                debate_winner VARCHAR(20),
                confidence_level DECIMAL(5,3),
                data_sufficient BOOLEAN DEFAULT true,
                missing_data_types JSONB,
                dispatcher_activated BOOLEAN DEFAULT false,
                debate_summary TEXT,
                key_arguments JSONB,
                market_implications JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Justin + Risk Team Analysis Table
            """
            CREATE TABLE IF NOT EXISTS justin_risk_analysis (
                id SERIAL PRIMARY KEY,
                analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                crawl_data_session_id VARCHAR(50),
                alpha_debate_session_id VARCHAR(50),
                justin_experience_years INTEGER DEFAULT 15,
                justin_verdict VARCHAR(10),
                justin_confidence DECIMAL(5,3),
                justin_analysis_style VARCHAR(50) DEFAULT 'Skeptical Veteran',
                long_term_proposal JSONB,
                short_term_proposal JSONB,
                risk_profile VARCHAR(20) DEFAULT 'NEUTRAL',
                risk_adjusted_proposals JSONB,
                final_holding_decision JSONB,
                final_trading_decision JSONB,
                justin_notes TEXT,
                risk_assessment_notes TEXT,
                market_outlook TEXT,
                key_risks JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
        ]
        
        # Execute SQL commands
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f'📝 Creating table {i}/3...')
                # Note: Supabase Python client doesn't support direct SQL execution
                # We need to use the REST API or run SQL manually
                print(f'⚠️  Please run this SQL manually in Supabase SQL Editor:')
                print('-' * 60)
                print(sql.strip())
                print('-' * 60)
                
            except Exception as e:
                print(f'❌ Error creating table {i}: {e}')
        
        print('\n✅ Table creation instructions generated!')
        print('📋 Next steps:')
        print('1. Go to your Supabase dashboard')
        print('2. Navigate to SQL Editor')
        print('3. Run the SQL commands above')
        print('4. Verify tables are created')
        
        return True
        
    except Exception as e:
        print(f'❌ Error connecting to Supabase: {e}')
        return False

def verify_tables():
    """Verify that tables exist"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print('❌ SUPABASE_URL and SUPABASE_KEY not set')
        return False
    
    try:
        supabase = create_client(url, key)
        
        tables_to_check = [
            'bob_technical_analysis',
            'alpha_debate_sessions', 
            'justin_risk_analysis'
        ]
        
        print('🔍 Verifying tables...')
        
        for table in tables_to_check:
            try:
                # Try to select from table (this will fail if table doesn't exist)
                result = supabase.table(table).select('id').limit(1).execute()
                print(f'✅ Table {table} exists')
            except Exception as e:
                if 'relation' in str(e).lower() and 'does not exist' in str(e).lower():
                    print(f'❌ Table {table} does not exist')
                else:
                    print(f'⚠️  Table {table} exists but has issues: {e}')
        
        return True
        
    except Exception as e:
        print(f'❌ Error verifying tables: {e}')
        return False

def main():
    """Main function"""
    print('🔧' * 50)
    print('🔧 SUPABASE TABLE CREATOR 🔧')
    print('🔧' * 50)
    print('')
    
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        verify_tables()
    else:
        create_tables()
    
    print('')
    print('🔧' * 50)
    print('🔧 TABLE CREATOR COMPLETE! 🔧')
    print('🔧' * 50)

if __name__ == "__main__":
    main()




