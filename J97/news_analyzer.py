#!/usr/bin/env python3
"""
J97 News Analyzer - Sentiment and Impact Analysis
Analyzes news articles for sentiment, impact, and trading signals
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """J97 News Analyzer - Sentiment and Impact Analysis"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Keywords for different impact levels
        self.high_impact_keywords = [
            'upgrade', 'hard fork', 'merge', 'staking', 'sharding', 'eip-1559',
            'gas fee', 'scalability', 'layer 2', 'rollup', 'optimism', 'arbitrum',
            'polygon', 'consensus', 'proof of stake', 'pos', 'pow', 'mining',
            'regulation', 'sec', 'sec approval', 'etf', 'institutional', 'adoption',
            'partnership', 'integration', 'mainnet', 'testnet', 'launch'
        ]
        
        self.medium_impact_keywords = [
            'price', 'market', 'trading', 'volume', 'bullish', 'bearish',
            'support', 'resistance', 'breakout', 'breakdown', 'trend',
            'analysis', 'prediction', 'forecast', 'target', 'resistance'
        ]
        
        self.technical_keywords = [
            'smart contract', 'dapp', 'defi', 'nft', 'dao', 'governance',
            'token', 'erc-20', 'erc-721', 'erc-1155', 'metamask', 'wallet',
            'transaction', 'block', 'blockchain', 'node', 'validator'
        ]
        
        # Sentiment patterns
        self.bullish_patterns = [
            r'\b(?:bullish|positive|optimistic|upward|growth|increase|rise|surge|rally)\b',
            r'\b(?:breakthrough|milestone|achievement|success|adoption|adoption)\b',
            r'\b(?:partnership|collaboration|integration|launch|release)\b'
        ]
        
        self.bearish_patterns = [
            r'\b(?:bearish|negative|pessimistic|downward|decline|decrease|fall|crash|dump)\b',
            r'\b(?:concern|risk|warning|caution|volatility|uncertainty)\b',
            r'\b(?:hack|exploit|vulnerability|bug|issue|problem)\b'
        ]
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using multiple methods"""
        if not text or len(text.strip()) < 10:
            return {'compound': 0.0, 'positive': 0.0, 'neutral': 1.0, 'negative': 0.0}
        
        # VADER sentiment
        vader_scores = self.sentiment_analyzer.polarity_scores(text)
        
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        # Pattern-based sentiment
        bullish_score = sum(len(re.findall(pattern, text.lower())) for pattern in self.bullish_patterns)
        bearish_score = sum(len(re.findall(pattern, text.lower())) for pattern in self.bearish_patterns)
        
        # Combine scores
        pattern_sentiment = (bullish_score - bearish_score) / max(bullish_score + bearish_score, 1)
        
        # Weighted combination
        final_sentiment = {
            'compound': (vader_scores['compound'] * 0.6 + textblob_polarity * 0.3 + pattern_sentiment * 0.1),
            'positive': vader_scores['pos'],
            'neutral': vader_scores['neu'],
            'negative': vader_scores['neg'],
            'subjectivity': textblob_subjectivity,
            'pattern_bullish': bullish_score,
            'pattern_bearish': bearish_score
        }
        
        return final_sentiment
    
    def calculate_impact_score(self, title: str, description: str, content: str = "") -> float:
        """Calculate impact score based on keywords and content"""
        text = f"{title} {description} {content}".lower()
        
        high_impact_count = sum(1 for keyword in self.high_impact_keywords if keyword in text)
        medium_impact_count = sum(1 for keyword in self.medium_impact_keywords if keyword in text)
        technical_count = sum(1 for keyword in self.technical_keywords if keyword in text)
        
        # Weighted impact score
        impact_score = (
            high_impact_count * 3.0 +
            medium_impact_count * 1.5 +
            technical_count * 1.0
        ) / max(len(text.split()), 1) * 100
        
        return min(impact_score, 10.0)  # Cap at 10
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        if not text:
            return []
        
        # Simple key phrase extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter for relevant terms
        relevant_terms = []
        all_keywords = self.high_impact_keywords + self.medium_impact_keywords + self.technical_keywords
        
        for word in words:
            if any(keyword in word or word in keyword for keyword in all_keywords):
                relevant_terms.append(word)
        
        # Return unique terms
        return list(set(relevant_terms))
    
    def categorize_news(self, title: str, description: str, content: str = "") -> str:
        """Categorize news into different types"""
        text = f"{title} {description} {content}".lower()
        
        if any(keyword in text for keyword in ['upgrade', 'hard fork', 'merge', 'eip']):
            return 'protocol_upgrade'
        elif any(keyword in text for keyword in ['staking', 'validator', 'consensus']):
            return 'staking'
        elif any(keyword in text for keyword in ['defi', 'dapp', 'smart contract']):
            return 'defi'
        elif any(keyword in text for keyword in ['nft', 'erc-721', 'erc-1155']):
            return 'nft'
        elif any(keyword in text for keyword in ['layer 2', 'rollup', 'optimism', 'arbitrum']):
            return 'scaling'
        elif any(keyword in text for keyword in ['regulation', 'sec', 'legal', 'compliance']):
            return 'regulation'
        elif any(keyword in text for keyword in ['price', 'market', 'trading', 'bullish', 'bearish']):
            return 'market'
        elif any(keyword in text for keyword in ['partnership', 'collaboration', 'integration']):
            return 'partnership'
        else:
            return 'general'
    
    def generate_trading_signal(self, articles: List[Dict]) -> Dict[str, any]:
        """Generate trading signal based on analyzed articles"""
        if not articles:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'No articles to analyze',
                'sentiment': 'neutral'
            }
        
        # Calculate weighted sentiment
        total_sentiment = 0
        total_impact = 0
        total_weight = 0
        
        for article in articles:
            sentiment = article.get('sentiment', {})
            impact = article.get('impact_score', 0)
            
            # Weight by impact and recency
            weight = impact + 1  # Base weight of 1
            if article.get('publishedAt'):
                try:
                    pub_date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                    hours_ago = (datetime.now() - pub_date).total_seconds() / 3600
                    weight *= max(0.1, 1 - (hours_ago / 24))  # Decay over 24 hours
                except:
                    pass
            
            total_sentiment += sentiment.get('compound', 0) * weight
            total_impact += impact * weight
            total_weight += weight
        
        if total_weight == 0:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'No valid articles to analyze',
                'sentiment': 'neutral'
            }
        
        avg_sentiment = total_sentiment / total_weight
        avg_impact = total_impact / total_weight
        
        # Generate signal
        if avg_sentiment > 0.3 and avg_impact > 3:
            signal = 'BUY'
            confidence = min(0.9, (avg_sentiment + avg_impact / 10) / 2)
        elif avg_sentiment < -0.3 and avg_impact > 3:
            signal = 'SELL'
            confidence = min(0.9, (abs(avg_sentiment) + avg_impact / 10) / 2)
        else:
            signal = 'HOLD'
            confidence = 0.5
        
        # Determine sentiment label
        if avg_sentiment > 0.1:
            sentiment_label = 'bullish'
        elif avg_sentiment < -0.1:
            sentiment_label = 'bearish'
        else:
            sentiment_label = 'neutral'
        
        return {
            'signal': signal,
            'confidence': confidence,
            'sentiment': sentiment_label,
            'avg_sentiment': avg_sentiment,
            'avg_impact': avg_impact,
            'article_count': len(articles),
            'reasoning': f"Based on {len(articles)} articles with {sentiment_label} sentiment and {avg_impact:.1f} impact"
        }
    
    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """Analyze a list of articles"""
        analyzed_articles = []
        
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            
            # Analyze sentiment
            sentiment = self.analyze_sentiment(f"{title} {description}")
            
            # Calculate impact score
            impact_score = self.calculate_impact_score(title, description)
            
            # Extract key phrases
            key_phrases = self.extract_key_phrases(f"{title} {description}")
            
            # Categorize news
            category = self.categorize_news(title, description)
            
            # Add analysis to article
            analyzed_article = article.copy()
            analyzed_article.update({
                'sentiment': sentiment,
                'impact_score': impact_score,
                'key_phrases': key_phrases,
                'category': category,
                'analyzed_at': datetime.now().isoformat()
            })
            
            analyzed_articles.append(analyzed_article)
        
        return analyzed_articles
    
    def generate_daily_report(self, articles: List[Dict]) -> Dict[str, any]:
        """Generate daily news analysis report"""
        if not articles:
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_articles': 0,
                'message': 'No articles analyzed today'
            }
        
        # Analyze articles
        analyzed_articles = self.analyze_articles(articles)
        
        # Generate trading signal
        trading_signal = self.generate_trading_signal(analyzed_articles)
        
        # Category breakdown
        categories = {}
        for article in analyzed_articles:
            category = article.get('category', 'general')
            categories[category] = categories.get(category, 0) + 1
        
        # Sentiment breakdown
        sentiment_counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        for article in analyzed_articles:
            sentiment = article.get('sentiment', {})
            compound = sentiment.get('compound', 0)
            if compound > 0.1:
                sentiment_counts['bullish'] += 1
            elif compound < -0.1:
                sentiment_counts['bearish'] += 1
            else:
                sentiment_counts['neutral'] += 1
        
        # Top key phrases
        all_phrases = []
        for article in analyzed_articles:
            all_phrases.extend(article.get('key_phrases', []))
        
        phrase_counts = {}
        for phrase in all_phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        top_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # High impact articles
        high_impact_articles = [
            article for article in analyzed_articles 
            if article.get('impact_score', 0) > 5
        ]
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_articles': len(analyzed_articles),
            'trading_signal': trading_signal,
            'categories': categories,
            'sentiment_breakdown': sentiment_counts,
            'top_key_phrases': top_phrases,
            'high_impact_articles': len(high_impact_articles),
            'high_impact_titles': [article['title'] for article in high_impact_articles[:5]],
            'analyzed_articles': analyzed_articles
        }

if __name__ == "__main__":
    # Test the analyzer
    analyzer = NewsAnalyzer()
    
    # Sample articles for testing
    sample_articles = [
        {
            'title': 'Ethereum 2.0 Merge Successfully Completed',
            'description': 'The long-awaited Ethereum merge has been completed successfully, transitioning from Proof of Work to Proof of Stake.',
            'url': 'https://example.com/eth-merge',
            'publishedAt': datetime.now().isoformat(),
            'source': 'Test Source'
        }
    ]
    
    report = analyzer.generate_daily_report(sample_articles)
    print(json.dumps(report, indent=2))









