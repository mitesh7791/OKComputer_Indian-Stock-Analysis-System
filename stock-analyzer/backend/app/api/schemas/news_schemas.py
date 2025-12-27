"""
News and sentiment API schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class NewsResponse(BaseModel):
    """News article response"""
    id: str
    title: str
    content: Optional[str] = None
    source: Optional[str] = None
    published_at: datetime
    url: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    relevance_score: Optional[float] = None

class SentimentResponse(BaseModel):
    """Sentiment analysis response"""
    symbol: str
    overall_sentiment: float
    sentiment_label: str
    total_articles: int
    positive_articles: int
    negative_articles: int
    neutral_articles: int
    recent_news: List[NewsResponse]

class TrendingNewsResponse(BaseModel):
    """Trending news response"""
    symbol: str
    name: str
    title: str
    source: Optional[str] = None
    published_at: datetime
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    relevance_score: Optional[float] = None

class NewsSourceResponse(BaseModel):
    """News source statistics response"""
    source: str
    article_count: int
    average_sentiment: float