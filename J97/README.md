# J97 News Analyst - 24/7 Ethereum News Analysis Agent

🕵️ **J97** is a specialized AI agent that continuously monitors and analyzes Ethereum-related news from multiple sources 24/7. J97 provides real-time sentiment analysis, impact assessment, and trading signals based on news coverage.

## 🌟 Features

- **24/7 News Monitoring**: Continuous crawling of multiple news sources
- **Multi-Source Integration**: GNews, NewsAPI, Mediastack, NewsData.io
- **Advanced Sentiment Analysis**: VADER + TextBlob + Pattern-based analysis
- **Impact Scoring**: Intelligent impact assessment based on keywords
- **Trading Signals**: Generate BUY/SELL/HOLD signals based on news sentiment
- **Supabase Integration**: Store all data and analysis results
- **Rate Limiting**: Respects API rate limits to avoid blocking
- **Categorization**: Automatically categorizes news by type (protocol, DeFi, regulation, etc.)

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv j97_venv
source j97_venv/bin/activate  # On Windows: j97_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `env_example.txt` to `.env` and add your API keys:

```bash
cp env_example.txt .env
```

Get free API keys from:
- **GNews**: https://gnews.io/ (100 requests/day)
- **NewsAPI**: https://newsapi.org/ (1000 requests/month)
- **Mediastack**: https://mediastack.com/ (100 requests/month)
- **NewsData.io**: https://newsdata.io/ (200 requests/day)

### 3. Setup Supabase Tables

Create these tables in your Supabase database:

```sql
-- News articles table
CREATE TABLE j97_news_articles (
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
CREATE TABLE j97_daily_reports (
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
```

### 4. Run J97

```bash
# Single analysis
python run_j97.py --mode single

# Continuous monitoring (every hour)
python run_j97.py --mode continuous --interval 1

# Continuous monitoring (every 6 hours)
python run_j97.py --mode continuous --interval 6
```

## 📊 Analysis Output

J97 provides comprehensive analysis including:

### Trading Signals
- **BUY**: Bullish sentiment + high impact news
- **SELL**: Bearish sentiment + high impact news  
- **HOLD**: Neutral sentiment or low impact

### Sentiment Analysis
- Compound sentiment score (-1 to +1)
- Positive/Neutral/Negative breakdown
- Pattern-based sentiment detection

### Impact Scoring
- High impact: Protocol upgrades, major partnerships
- Medium impact: Market analysis, price predictions
- Technical: DeFi, smart contracts, technical developments

### News Categories
- `protocol_upgrade`: Hard forks, EIPs, consensus changes
- `staking`: Validator updates, staking rewards
- `defi`: DeFi protocols, smart contracts
- `nft`: NFT market, ERC standards
- `scaling`: Layer 2, rollups, optimization
- `regulation`: Legal, compliance, SEC updates
- `market`: Price analysis, trading signals
- `partnership`: Collaborations, integrations

## 🔧 Configuration

### Environment Variables

```bash
# API Keys
GNEWS_API_KEY=your_gnews_key
NEWSAPI_KEY=your_newsapi_key
MEDIASTACK_API_KEY=your_mediastack_key
NEWSDATA_API_KEY=your_newsdata_key

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# J97 Settings
J97_SLEEP_INTERVAL=3600  # Seconds between crawls
J97_MAX_ARTICLES_PER_SOURCE=50
J97_KEYWORDS=ethereum,eth,ethereum 2.0,eth2,defi,smart contracts,gas fees
```

### Rate Limits

J97 respects API rate limits:
- **GNews**: 100 requests/day, 1 request/second
- **NewsAPI**: 1000 requests/month
- **Mediastack**: 100 requests/month
- **NewsData.io**: 200 requests/day

## 📁 File Structure

```
J97/
├── run_j97.py              # Main runner script
├── news_crawler.py         # News crawling engine
├── news_analyzer.py        # Sentiment & impact analysis
├── supabase_integration.py # Database integration
├── requirements.txt        # Python dependencies
├── env_example.txt         # Environment variables template
└── README.md              # This file
```

## 🎯 Usage Examples

### Single Analysis
```bash
python run_j97.py --mode single
```

### Continuous Monitoring
```bash
# Monitor every hour
python run_j97.py --mode continuous --interval 1

# Monitor every 6 hours
python run_j97.py --mode continuous --interval 6
```

### Programmatic Usage
```python
from run_j97 import J97NewsAnalyst
import asyncio

async def main():
    j97 = J97NewsAnalyst()
    summary = await j97.run_single_analysis()
    print(f"Trading Signal: {summary['trading_signal']}")

asyncio.run(main())
```

## 📈 Output Files

- `j97_news_analyst.log`: Detailed logging
- `j97_articles_YYYYMMDD_HHMMSS.json`: Raw articles data
- `j97_analysis_summary_YYYYMMDD_HHMMSS.json`: Analysis summary

## 🔍 Monitoring

J97 provides detailed logging and monitoring:
- Real-time crawl status
- API rate limit tracking
- Error handling and retry logic
- Supabase storage confirmation

## 🛠️ Troubleshooting

### Common Issues

1. **API Rate Limits**: J97 automatically handles rate limits, but you may need to wait for reset periods
2. **Supabase Connection**: Ensure your Supabase credentials are correct
3. **Missing Dependencies**: Run `pip install -r requirements.txt`
4. **No Articles Found**: Check if API keys are valid and sources have recent ETH news

### Logs

Check `j97_news_analyst.log` for detailed error messages and debugging information.

## 🤝 Contributing

J97 is part of the TradingAgents ecosystem. Contributions are welcome!

## 📄 License

Part of the TradingAgents project. See main project license.

---

**J97 - Your 24/7 Ethereum News Intelligence Agent** 🕵️📰



