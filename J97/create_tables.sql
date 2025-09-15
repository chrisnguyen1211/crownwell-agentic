-- J97 News Analyst Supabase Tables
-- Run this SQL in your Supabase SQL Editor

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

-- Enable Row Level Security (RLS)
ALTER TABLE j97_news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE j97_daily_reports ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed)
CREATE POLICY "Allow public read access" ON j97_news_articles FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON j97_daily_reports FOR SELECT USING (true);
CREATE POLICY "Allow public insert access" ON j97_news_articles FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public insert access" ON j97_daily_reports FOR INSERT WITH CHECK (true);



