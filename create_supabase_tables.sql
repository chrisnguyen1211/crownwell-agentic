    -- Create missing Supabase tables for TradingAgents system
    -- Run this SQL in your Supabase SQL Editor

    -- 1. Bob Technical Analysis Table
    CREATE TABLE IF NOT EXISTS bob_technical_analysis (
        id SERIAL PRIMARY KEY,
        analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        timeframe VARCHAR(10) NOT NULL, -- '1H', '4H', '1D'
        
        -- Price data
        current_price DECIMAL(20,8),
        price_change_24h DECIMAL(10,4),
        volume_24h DECIMAL(20,2),
        
        -- Technical indicators
        rsi_14 DECIMAL(5,2),
        macd_line DECIMAL(10,6),
        macd_signal DECIMAL(10,6),
        macd_histogram DECIMAL(10,6),
        bb_upper DECIMAL(20,8),
        bb_middle DECIMAL(20,8),
        bb_lower DECIMAL(20,8),
        bb_position DECIMAL(5,2), -- Position within Bollinger Bands
        
        -- Moving averages
        sma_20 DECIMAL(20,8),
        sma_50 DECIMAL(20,8),
        sma_200 DECIMAL(20,8),
        ema_12 DECIMAL(20,8),
        ema_26 DECIMAL(20,8),
        
        -- Pattern recognition
        patterns JSONB, -- Detected patterns
        support_levels JSONB, -- Support levels
        resistance_levels JSONB, -- Resistance levels
        
        -- Trading signals
        signal_direction VARCHAR(10), -- 'BULLISH', 'BEARISH', 'NEUTRAL'
        signal_strength DECIMAL(5,3), -- 0.000 to 1.000
        confidence_score DECIMAL(5,3), -- 0.000 to 1.000
        risk_level VARCHAR(20), -- 'LOW', 'MEDIUM', 'HIGH'
        
        -- Analysis metadata
        analysis_summary TEXT,
        key_insights JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- 2. Alpha Team Debate Sessions Table
    CREATE TABLE IF NOT EXISTS alpha_debate_sessions (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(50) UNIQUE NOT NULL,
        session_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        
        -- Debate participants
        bullish_agent_name VARCHAR(50) DEFAULT 'Bullish Agent',
        bearish_agent_name VARCHAR(50) DEFAULT 'Bearish Agent',
        
        -- Data sources used
        crawl_data_sources JSONB, -- References to crawl team data
        
        -- Debate rounds
        round_1_bullish_evidence JSONB,
        round_1_bearish_evidence JSONB,
        round_1_bullish_rebuttal JSONB,
        round_1_bearish_rebuttal JSONB,
        
        round_2_bullish_evidence JSONB,
        round_2_bearish_evidence JSONB,
        round_2_bullish_rebuttal JSONB,
        round_2_bearish_rebuttal JSONB,
        
        -- Debate outcomes
        final_bullish_score DECIMAL(5,3),
        final_bearish_score DECIMAL(5,3),
        debate_winner VARCHAR(20), -- 'BULLISH', 'BEARISH', 'TIE'
        confidence_level DECIMAL(5,3),
        
        -- Data sufficiency
        data_sufficient BOOLEAN DEFAULT true,
        missing_data_types JSONB, -- Types of data requested if insufficient
        dispatcher_activated BOOLEAN DEFAULT false,
        
        -- Analysis metadata
        debate_summary TEXT,
        key_arguments JSONB,
        market_implications JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- 3. Justin + Risk Team Analysis Table
    CREATE TABLE IF NOT EXISTS justin_risk_analysis (
        id SERIAL PRIMARY KEY,
        analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        
        -- Input data references
        crawl_data_session_id VARCHAR(50),
        alpha_debate_session_id VARCHAR(50),
        
        -- Justin's analysis
        justin_experience_years INTEGER DEFAULT 15,
        justin_verdict VARCHAR(10), -- 'BUY', 'SELL', 'HOLD'
        justin_confidence DECIMAL(5,3),
        justin_analysis_style VARCHAR(50) DEFAULT 'Skeptical Veteran',
        
        -- Trading proposals
        long_term_proposal JSONB, -- {action: 'BUY/SELL/DCA/PARTIAL', reasoning: '', confidence: 0.0}
        short_term_proposal JSONB, -- {action: 'LONG/SHORT', entry: 0.0, tp: 0.0, sl: 0.0, reasoning: ''}
        
        -- Risk assessment
        risk_profile VARCHAR(20) DEFAULT 'NEUTRAL', -- 'AGGRESSIVE', 'NEUTRAL', 'CONSERVATIVE'
        risk_adjusted_proposals JSONB,
        
        -- Final decisions
        final_holding_decision JSONB, -- Refined holding portfolio decision
        final_trading_decision JSONB, -- Refined trading decision
        
        -- Analysis metadata
        justin_notes TEXT,
        risk_assessment_notes TEXT,
        market_outlook TEXT,
        key_risks JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_bob_analysis_timestamp ON bob_technical_analysis(analysis_timestamp);
    CREATE INDEX IF NOT EXISTS idx_bob_timeframe ON bob_technical_analysis(timeframe);
    CREATE INDEX IF NOT EXISTS idx_bob_signal_direction ON bob_technical_analysis(signal_direction);

    CREATE INDEX IF NOT EXISTS idx_alpha_session_id ON alpha_debate_sessions(session_id);
    CREATE INDEX IF NOT EXISTS idx_alpha_timestamp ON alpha_debate_sessions(session_timestamp);
    CREATE INDEX IF NOT EXISTS idx_alpha_winner ON alpha_debate_sessions(debate_winner);

    CREATE INDEX IF NOT EXISTS idx_justin_timestamp ON justin_risk_analysis(analysis_timestamp);
    CREATE INDEX IF NOT EXISTS idx_justin_verdict ON justin_risk_analysis(justin_verdict);
    CREATE INDEX IF NOT EXISTS idx_justin_risk_profile ON justin_risk_analysis(risk_profile);

    -- Enable Row Level Security (RLS)
    ALTER TABLE bob_technical_analysis ENABLE ROW LEVEL SECURITY;
    ALTER TABLE alpha_debate_sessions ENABLE ROW LEVEL SECURITY;
    ALTER TABLE justin_risk_analysis ENABLE ROW LEVEL SECURITY;

    -- Create policies for public access (adjust as needed)
    CREATE POLICY "Allow public read access" ON bob_technical_analysis FOR SELECT USING (true);
    CREATE POLICY "Allow public read access" ON alpha_debate_sessions FOR SELECT USING (true);
    CREATE POLICY "Allow public read access" ON justin_risk_analysis FOR SELECT USING (true);

    CREATE POLICY "Allow public insert access" ON bob_technical_analysis FOR INSERT WITH CHECK (true);
    CREATE POLICY "Allow public insert access" ON alpha_debate_sessions FOR INSERT WITH CHECK (true);
    CREATE POLICY "Allow public insert access" ON justin_risk_analysis FOR INSERT WITH CHECK (true);

    -- Comments for documentation
    COMMENT ON TABLE bob_technical_analysis IS 'Technical analysis data from Bob agent using TA-Lib indicators';
    COMMENT ON TABLE alpha_debate_sessions IS 'Alpha team debate sessions between bullish and bearish agents';
    COMMENT ON TABLE justin_risk_analysis IS 'Justin trading manager analysis combined with risk team assessment';
