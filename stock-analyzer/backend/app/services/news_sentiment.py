"""
News Sentiment Analysis Service
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

from app.models.stock import Stock, NewsArticle
from app.core.config import settings

class NewsSentimentAnalyzer:
    """News sentiment analysis using multiple methods"""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Financial keywords for enhanced sentiment analysis
        self.positive_keywords = [
            'profit', 'growth', 'increase', 'strong', 'bullish', 'buy', 'upgrade', 
            'outperform', 'exceed', 'beat', 'raise', 'positive', 'good', 'better',
            'expansion', 'gain', 'rise', 'surge', 'boost', 'improve', 'success',
            'breakthrough', 'innovation', 'dividend', 'bonus', 'split', 'acquisition',
            'merger', 'partnership', 'collaboration', 'expansion', 'investment'
        ]
        
        self.negative_keywords = [
            'loss', 'decline', 'decrease', 'weak', 'bearish', 'sell', 'downgrade',
            'underperform', 'miss', 'fall', 'drop', 'negative', 'bad', 'worse',
            'contraction', 'decline', 'plunge', 'crash', 'deteriorate', 'fail',
            'bankruptcy', 'debt', 'default', 'layoff', 'recession', 'crisis',
            'scandal', 'fraud', 'investigation', 'penalty', 'fine', 'lawsuit'
        ]
        
        self.neutral_keywords = [
            'announce', 'report', 'statement', 'meet', 'discuss', 'plan', 'consider',
            'review', 'analyze', 'evaluate', 'maintain', 'hold', 'neutral'
        ]
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using multiple methods
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with sentiment scores
        """
        if not text or pd.isna(text):
            return {'compound': 0, 'pos': 0, 'neu': 0, 'neg': 0, 'label': 'NEUTRAL'}
        
        # VADER sentiment analysis
        vader_scores = self.vader_analyzer.polarity_scores(text)
        
        # TextBlob sentiment analysis
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        # Keyword-based sentiment analysis
        text_lower = text.lower()
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        
        # Calculate keyword-based score
        keyword_score = (positive_count - negative_count) / max(len(text.split()), 1)
        keyword_score = max(-1, min(1, keyword_score))  # Clamp to [-1, 1]
        
        # Combine scores (weighted average)
        combined_score = (
            0.5 * vader_scores['compound'] + 
            0.3 * textblob_polarity + 
            0.2 * keyword_score
        )
        
        # Determine sentiment label
        if combined_score >= 0.1:
            label = 'POSITIVE'
        elif combined_score <= -0.1:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'
        
        return {
            'compound': combined_score,
            'vader_compound': vader_scores['compound'],
            'textblob_polarity': textblob_polarity,
            'keyword_score': keyword_score,
            'positive_keywords': positive_count,
            'negative_keywords': negative_count,
            'label': label,
            'confidence': abs(combined_score)
        }
    
    def is_relevant_news(self, title: str, content: str, symbol: str, company_name: str) -> bool:
        """
        Check if news is relevant to the stock
        
        Args:
            title: News title
            content: News content
            symbol: Stock symbol
            company_name: Company name
        
        Returns:
            True if relevant, False otherwise
        """
        text = f"{title} {content}".lower()
        
        # Check for symbol and company name mentions
        symbol_mentions = text.count(symbol.lower())
        company_mentions = text.count(company_name.lower().split()[0]) if company_name else 0
        
        # Check for financial keywords
        financial_keywords = [
            'stock', 'share', 'price', 'market', 'trading', 'investment',
            'earnings', 'revenue', 'profit', 'loss', 'dividend', 'quarter',
            'annual', 'results', 'outlook', 'guidance', 'analyst', 'rating'
        ]
        
        keyword_mentions = sum(1 for keyword in financial_keywords if keyword in text)
        
        # Relevance score (0-1)
        relevance_score = min(1.0, (symbol_mentions * 0.3 + company_mentions * 0.2 + keyword_mentions * 0.1))
        
        return relevance_score >= 0.2  # Threshold for relevance

class NewsService:
    """News fetching and sentiment analysis service"""
    
    def __init__(self):
        self.analyzer = NewsSentimentAnalyzer()
        self.news_api_key = settings.NEWS_API_KEY
        self.session = None
    
    async def fetch_news_for_stock(self, symbol: str, company_name: str, hours: int = 72) -> List[Dict[str, Any]]:
        """
        Fetch news articles for a specific stock
        
        Args:
            symbol: Stock symbol
            company_name: Company name
            hours: Hours to look back for news
        
        Returns:
            List of news articles with sentiment analysis
        """
        if not self.news_api_key:
            print("News API key not configured")
            return []
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=hours)
            
            # NewsAPI endpoint
            url = "https://newsapi.org/v2/everything"
            
            # Search queries
            queries = [
                f'"{symbol}"',
                f'"{company_name}" stock',
                f'"{company_name}" share',
                f'"{company_name}" market'
            ]
            
            all_articles = []
            
            for query in queries:
                params = {
                    'q': query,
                    'from': start_date.strftime('%Y-%m-%d'),
                    'to': end_date.strftime('%Y-%m-%d'),
                    'language': 'en',
                    'sortBy': 'relevancy',
                    'apiKey': self.news_api_key,
                    'pageSize': 20
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            articles = data.get('articles', [])
                            
                            # Filter and process articles
                            for article in articles:
                                # Check relevance
                                if not self.analyzer.is_relevant_news(
                                    article.get('title', ''),
                                    article.get('description', ''),
                                    symbol,
                                    company_name
                                ):
                                    continue
                                
                                # Analyze sentiment
                                text = f"{article.get('title', '')} {article.get('description', '')}"
                                sentiment = self.analyzer.analyze_text_sentiment(text)
                                
                                processed_article = {
                                    'title': article.get('title', ''),
                                    'content': article.get('description', ''),
                                    'source': article.get('source', {}).get('name', ''),
                                    'published_at': article.get('publishedAt', ''),
                                    'url': article.get('url', ''),
                                    'sentiment_score': sentiment['compound'],
                                    'sentiment_label': sentiment['label'],
                                    'relevance_score': 0.8  # Placeholder
                                }
                                
                                all_articles.append(processed_article)
                        else:
                            print(f"News API error: {response.status}")
                
                # Small delay between queries
                await asyncio.sleep(0.5)
            
            # Remove duplicates based on title
            seen_titles = set()
            unique_articles = []
            for article in all_articles:
                title = article['title']
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_articles.append(article)
            
            # Sort by relevance and date
            unique_articles.sort(
                key=lambda x: (abs(x['sentiment_score']), x['published_at']), 
                reverse=True
            )
            
            return unique_articles[:10]  # Return top 10 most relevant
            
        except Exception as e:
            print(f"Error fetching news for {symbol}: {str(e)}")
            return []
    
    async def save_news_to_database(self, db: AsyncSession, stock_id: str, articles: List[Dict[str, Any]]) -> bool:
        """
        Save news articles to database
        
        Args:
            db: Database session
            stock_id: Stock ID
            articles: List of news articles
        
        Returns:
            True if successful, False otherwise
        """
        try:
            for article in articles:
                # Check if article already exists
                existing = await db.execute(
                    select(NewsArticle).where(
                        and_(
                            NewsArticle.stock_id == stock_id,
                            NewsArticle.title == article['title']
                        )
                    )
                )
                
                if existing.scalar_one_or_none():
                    continue  # Skip duplicates
                
                # Create new news record
                news_record = NewsArticle(
                    stock_id=stock_id,
                    title=article['title'],
                    content=article['content'],
                    source=article['source'],
                    published_at=datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')),
                    url=article['url'],
                    sentiment_score=article['sentiment_score'],
                    sentiment_label=article['sentiment_label'],
                    relevance_score=article['relevance_score']
                )
                
                db.add(news_record)
            
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"Error saving news to database: {str(e)}")
            return False
    
    async def get_stock_sentiment_score(self, db: AsyncSession, symbol: str, hours: int = 72) -> float:
        """
        Calculate aggregated sentiment score for a stock
        
        Args:
            db: Database session
            symbol: Stock symbol
            hours: Hours to look back
        
        Returns:
            Weighted sentiment score (-1 to 1)
        """
        try:
            # Get stock ID
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            
            if not stock:
                return 0.0
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=hours)
            
            # Get recent news
            result = await db.execute(
                select(NewsArticle)
                .where(
                    and_(
                        NewsArticle.stock_id == stock.id,
                        NewsArticle.published_at >= start_date
                    )
                )
                .order_by(NewsArticle.published_at.desc())
            )
            
            news_articles = result.scalars().all()
            
            if not news_articles:
                return 0.0
            
            # Calculate weighted sentiment score
            total_score = 0.0
            total_weight = 0.0
            
            for article in news_articles:
                # Weight by relevance and recency
                days_old = (end_date - article.published_at).days + 1
                recency_weight = 1.0 / days_old
                relevance_weight = article.relevance_score or 0.5
                
                weight = recency_weight * relevance_weight
                total_score += article.sentiment_score * weight
                total_weight += weight
            
            if total_weight == 0:
                return 0.0
            
            # Normalize to -1 to 1
            final_score = total_score / total_weight
            return max(-1.0, min(1.0, final_score))
            
        except Exception as e:
            print(f"Error calculating sentiment score for {symbol}: {str(e)}")
            return 0.0
    
    async def fetch_and_analyze_all_stocks(self, db: AsyncSession) -> Dict[str, int]:
        """
        Fetch news and analyze sentiment for all stocks
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with processing statistics
        """
        # Get all active stocks
        result = await db.execute(
            select(Stock).where(Stock.is_active == True)
        )
        stocks = result.scalars().all()
        
        stats = {
            'total_stocks': len(stocks),
            'successful': 0,
            'failed': 0,
            'articles_added': 0
        }
        
        for stock in stocks:
            try:
                # Fetch news
                articles = await self.fetch_news_for_stock(
                    stock.symbol, 
                    stock.name, 
                    settings.NEWS_LOOKBACK_HOURS
                )
                
                if articles:
                    # Save to database
                    if await self.save_news_to_database(db, stock.id, articles):
                        stats['successful'] += 1
                        stats['articles_added'] += len(articles)
                    else:
                        stats['failed'] += 1
                else:
                    stats['successful'] += 1  # No news is not a failure
                
                # Small delay to respect API limits
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error processing news for {stock.symbol}: {str(e)}")
                stats['failed'] += 1
        
        print(f"News processing completed: {stats['successful']} successful, {stats['failed']} failed, {stats['articles_added']} articles added")
        return stats

# Global instance
news_service = NewsService()