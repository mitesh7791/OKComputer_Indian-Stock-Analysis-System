"""
News and sentiment API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.stock import NewsArticle, Stock
from app.services.news_sentiment import news_service
from app.api.schemas import news_schemas

router = APIRouter()

@router.get("/{symbol}", response_model=List[news_schemas.NewsResponse])
async def get_stock_news(
    symbol: str,
    hours: int = Query(72, description="Hours to look back for news"),
    limit: int = Query(10, description="Maximum number of news articles"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get news articles for a specific stock
    """
    from sqlalchemy import select, and_
    from sqlalchemy.orm import joinedload
    
    # Get stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)
    
    # Get news articles
    result = await db.execute(
        select(NewsArticle)
        .where(
            and_(
                NewsArticle.stock_id == stock.id,
                NewsArticle.published_at >= start_date
            )
        )
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
    )
    
    articles = result.scalars().all()
    
    return [news_schemas.NewsResponse(
        id=str(article.id),
        title=article.title,
        content=article.content,
        source=article.source,
        published_at=article.published_at,
        url=article.url,
        sentiment_score=article.sentiment_score,
        sentiment_label=article.sentiment_label,
        relevance_score=article.relevance_score
    ) for article in articles]

@router.get("/sentiment/{symbol}", response_model=news_schemas.SentimentResponse)
async def get_stock_sentiment(
    symbol: str,
    hours: int = Query(72, description="Hours to look back for sentiment analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sentiment analysis for a stock
    """
    # Get sentiment score
    sentiment_score = await news_service.get_stock_sentiment_score(db, symbol, hours)
    
    # Get recent news for details
    news = await get_stock_news(symbol, hours, 10, db)
    
    # Calculate sentiment breakdown
    positive_count = sum(1 for article in news if article.sentiment_label == 'POSITIVE')
    negative_count = sum(1 for article in news if article.sentiment_label == 'NEGATIVE')
    neutral_count = len(news) - positive_count - negative_count
    
    return news_schemas.SentimentResponse(
        symbol=symbol,
        overall_sentiment=sentiment_score,
        sentiment_label='POSITIVE' if sentiment_score > 0.1 else 'NEGATIVE' if sentiment_score < -0.1 else 'NEUTRAL',
        total_articles=len(news),
        positive_articles=positive_count,
        negative_articles=negative_count,
        neutral_articles=neutral_count,
        recent_news=news
    )

@router.post("/fetch-news")
async def fetch_news_for_stock(
    symbol: str = Query(..., description="Stock symbol to fetch news for"),
    hours: int = Query(72, description="Hours to look back for news"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch latest news for a stock and analyze sentiment
    """
    from sqlalchemy import select
    
    # Get stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Fetch news
    articles = await news_service.fetch_news_for_stock(symbol, stock.name, hours)
    
    if not articles:
        return {
            "message": f"No news found for {symbol}",
            "articles_found": 0
        }
    
    # Save to database
    success = await news_service.save_news_to_database(db, stock.id, articles)
    
    return {
        "message": f"Fetched {len(articles)} articles for {symbol}",
        "articles_found": len(articles),
        "articles_saved": len(articles) if success else 0,
        "sample_articles": [
            {
                "title": article["title"],
                "sentiment": article["sentiment_label"],
                "score": article["sentiment_score"]
            }
            for article in articles[:3]
        ]
    }

@router.post("/fetch-all-news")
async def fetch_news_for_all_stocks(
    hours: int = Query(72, description="Hours to look back for news"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch news for all stocks in the universe
    """
    stats = await news_service.fetch_and_analyze_all_stocks(db)
    
    return {
        "message": "News fetching completed",
        "statistics": stats
    }

@router.get("/trending", response_model=List[news_schemas.TrendingNewsResponse])
async def get_trending_news(
    limit: int = Query(10, description="Number of trending news items"),
    hours: int = Query(24, description="Hours to consider for trending news"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trending news across all stocks
    """
    from sqlalchemy import select, and_, desc, func
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)
    
    # Get trending news (high sentiment scores or high relevance)
    result = await db.execute(
        select(NewsArticle, Stock)
        .join(Stock)
        .where(NewsArticle.published_at >= start_date)
        .order_by(desc(func.abs(NewsArticle.sentiment_score)))
        .limit(limit)
    )
    
    articles_with_stocks = result.all()
    
    trending_news = []
    for article, stock in articles_with_stocks:
        trending_news.append(news_schemas.TrendingNewsResponse(
            symbol=stock.symbol,
            name=stock.name,
            title=article.title,
            source=article.source,
            published_at=article.published_at,
            sentiment_score=article.sentiment_score,
            sentiment_label=article.sentiment_label,
            relevance_score=article.relevance_score
        ))
    
    return trending_news

@router.get("/sources", response_model=List[news_schemas.NewsSourceResponse])
async def get_news_sources(
    db: AsyncSession = Depends(get_db)
):
    """
    Get news source statistics
    """
    from sqlalchemy import select, func, desc
    
    # Get source statistics
    result = await db.execute(
        select(
            NewsArticle.source,
            func.count(NewsArticle.id).label('article_count'),
            func.avg(NewsArticle.sentiment_score).label('avg_sentiment')
        )
        .group_by(NewsArticle.source)
        .order_by(desc('article_count'))
    )
    
    sources = result.all()
    
    return [news_schemas.NewsSourceResponse(
        source=source,
        article_count=count,
        average_sentiment=round(avg_sentiment or 0, 3)
    ) for source, count, avg_sentiment in sources]