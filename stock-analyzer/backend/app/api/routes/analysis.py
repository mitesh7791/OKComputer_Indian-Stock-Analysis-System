"""
Analysis and ranking API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, date

from app.db.database import get_db
from app.models.stock import DailyAnalysis, TradingSignal, Stock
from app.services.scoring import ranking_service
from app.api.schemas import analysis_schemas

router = APIRouter()

@router.get("/top-stocks", response_model=List[analysis_schemas.TopStockResponse])
async def get_top_stocks(
    limit: int = Query(5, description="Number of top stocks to return"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type (BUY/SELL)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top stocks with trading signals
    """
    from sqlalchemy import select, and_, desc
    from sqlalchemy.orm import joinedload
    
    # Get today's date
    today = date.today()
    
    # Query for top stocks
    query = (
        select(TradingSignal)
        .join(Stock)
        .where(
            and_(
                TradingSignal.signal_date == today,
                TradingSignal.status == 'ACTIVE'
            )
        )
        .options(joinedload(TradingSignal.stock))
        .order_by(desc(TradingSignal.signal_strength))
    )
    
    if signal_type:
        query = query.where(TradingSignal.signal_type == signal_type)
    
    result = await db.execute(query.limit(limit))
    signals = result.scalars().all()
    
    # Format response
    top_stocks = []
    for signal in signals:
        stock = signal.stock
        
        # Get latest analysis
        analysis_result = await db.execute(
            select(DailyAnalysis)
            .where(
                and_(
                    DailyAnalysis.stock_id == stock.id,
                    DailyAnalysis.analysis_date == today
                )
            )
        )
        analysis = analysis_result.scalar_one_or_none()
        
        # Get current price (placeholder - in real implementation would fetch live price)
        current_price = signal.entry_price
        
        top_stocks.append(analysis_schemas.TopStockResponse(
            symbol=stock.symbol,
            name=stock.name,
            sector=stock.sector,
            current_price=current_price,
            signal_type=signal.signal_type,
            signal_strength=signal.signal_strength,
            entry_price=signal.entry_price,
            target_1=signal.target_1,
            target_2=signal.target_2,
            stop_loss=signal.stop_loss,
            risk_amount=signal.risk_amount,
            reward_ratio_1=signal.reward_ratio_1,
            reward_ratio_2=signal.reward_ratio_2,
            score=analysis.total_score if analysis else 0,
            rationale=signal.rationale
        ))
    
    return top_stocks

@router.get("/daily-ranking", response_model=analysis_schemas.DailyRankingResponse)
async def get_daily_ranking(
    date: Optional[date] = Query(None, description="Date for ranking (defaults to today)"),
    limit: int = Query(20, description="Number of stocks to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily stock ranking by score
    """
    from sqlalchemy import select, and_, desc
    
    if not date:
        date = date.today()
    
    # Get daily analyses
    result = await db.execute(
        select(DailyAnalysis)
        .where(DailyAnalysis.analysis_date == date)
        .order_by(desc(DailyAnalysis.total_score))
        .limit(limit)
        .options(joinedload(DailyAnalysis.stock))
    )
    
    analyses = result.scalars().all()
    
    # Format response
    rankings = []
    for analysis in analyses:
        stock = analysis.stock
        
        # Check if there's an active signal
        signal_result = await db.execute(
            select(TradingSignal)
            .where(
                and_(
                    TradingSignal.stock_id == stock.id,
                    TradingSignal.signal_date == date,
                    TradingSignal.status == 'ACTIVE'
                )
            )
        )
        signal = signal_result.scalar_one_or_none()
        
        rankings.append(analysis_schemas.RankingEntry(
            symbol=stock.symbol,
            name=stock.name,
            sector=stock.sector,
            total_score=analysis.total_score,
            signal_type=signal.signal_type if signal else None,
            signal_strength=signal.signal_strength if signal else None,
            component_scores=analysis_schemas.ComponentScores(
                ma_alignment=analysis.ma_alignment_score,
                supertrend=analysis.supertrend_score,
                rsi_strength=analysis.rsi_score,
                volume_expansion=analysis.volume_score,
                news_sentiment=analysis.sentiment_score
            )
        ))
    
    return analysis_schemas.DailyRankingResponse(
        date=date,
        total_stocks=len(rankings),
        rankings=rankings
    )

@router.post("/run-analysis")
async def run_daily_analysis(
    symbols: Optional[List[str]] = Query(None, description="Specific symbols to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Run daily analysis for all or specific stocks
    """
    from sqlalchemy import select
    
    if symbols:
        # Analyze specific stocks
        stocks_to_analyze = []
        for symbol in symbols:
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            if stock:
                stocks_to_analyze.append(stock)
    else:
        # Analyze all active stocks in universe
        result = await db.execute(
            select(Stock).where(Stock.is_active == True)
        )
        stocks_to_analyze = result.scalars().all()
    
    # Run analysis
    results = await ranking_service.rank_all_stocks(db)
    
    return {
        "message": "Daily analysis completed",
        "statistics": {
            "total_stocks_analyzed": results['total_analyzed'],
            "buy_signals_generated": len(results['buy_signals']),
            "sell_signals_generated": len(results['sell_signals']),
            "top_performers": len(results['top_stocks'])
        },
        "top_stocks": [
            {
                "symbol": stock.symbol,
                "name": stock.name,
                "score": analysis.total_score,
                "signal": analysis.signal_type
            }
            for stock, analysis in [(s.stock, s) for s in results['top_stocks'][:5]]
        ]
    }

@router.get("/market-sentiment", response_model=analysis_schemas.MarketSentimentResponse)
async def get_market_sentiment(
    date: Optional[date] = Query(None, description="Date for sentiment analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall market sentiment
    """
    from sqlalchemy import select, func, and_
    
    if not date:
        date = date.today()
    
    # Get all analyses for the date
    result = await db.execute(
        select(DailyAnalysis)
        .where(DailyAnalysis.analysis_date == date)
    )
    
    analyses = result.scalars().all()
    
    if not analyses:
        raise HTTPException(status_code=404, detail="No analysis data found for the specified date")
    
    # Calculate sentiment metrics
    total_stocks = len(analyses)
    bullish_stocks = sum(1 for a in analyses if a.is_bullish)
    bearish_stocks = sum(1 for a in analyses if a.is_bearish)
    neutral_stocks = total_stocks - bullish_stocks - bearish_stocks
    
    avg_score = sum(a.total_score for a in analyses) / total_stocks
    
    # Determine overall sentiment
    if avg_score >= 60:
        overall_sentiment = "BULLISH"
    elif avg_score <= 40:
        overall_sentiment = "BEARISH"
    else:
        overall_sentiment = "NEUTRAL"
    
    # Get signal counts
    buy_signals = sum(1 for a in analyses if a.signal_type == 'BUY')
    sell_signals = sum(1 for a in analyses if a.signal_type == 'SELL')
    
    return analysis_schemas.MarketSentimentResponse(
        date=date,
        overall_sentiment=overall_sentiment,
        average_score=round(avg_score, 2),
        total_stocks_analyzed=total_stocks,
        bullish_stocks=bullish_stocks,
        bearish_stocks=bearish_stocks,
        neutral_stocks=neutral_stocks,
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        bullish_percentage=round((bullish_stocks / total_stocks) * 100, 2),
        bearish_percentage=round((bearish_stocks / total_stocks) * 100, 2)
    )

@router.get("/top-performers", response_model=analysis_schemas.TopPerformersResponse)
async def get_top_performers(
    period: str = Query("1w", description="Time period (1w, 1m, 3m)"),
    limit: int = Query(10, description="Number of performers to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top performing stocks based on historical signals
    """
    # This would require historical performance tracking
    # For now, return top stocks by score
    
    result = await ranking_service.get_top_stocks(db, limit)
    
    return analysis_schemas.TopPerformersResponse(
        period=period,
        top_stocks=result
    )