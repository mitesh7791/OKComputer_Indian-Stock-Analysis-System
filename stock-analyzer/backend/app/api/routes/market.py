"""
Market status and overview API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, date

from app.db.database import get_db
from app.models.stock import MarketStatus, Stock, DailyAnalysis
from app.services.market_data import market_data_service
from app.api.schemas import market_schemas

router = APIRouter()

@router.get("/status", response_model=market_schemas.MarketStatusResponse)
async def get_market_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get current market status and overview
    """
    from sqlalchemy import select, desc
    
    # Get latest market status
    result = await db.execute(
        select(MarketStatus)
        .order_by(desc(MarketStatus.trading_date))
        .limit(1)
    )
    
    market_status = result.scalar_one_or_none()
    
    if not market_status:
        # Create default market status if not exists
        market_status = MarketStatus(
            trading_date=date.today(),
            market_open=True,
            overall_sentiment="NEUTRAL",
            total_stocks_analyzed=0,
            bullish_stocks=0,
            bearish_stocks=0
        )
    
    # Get today's analysis summary
    today = date.today()
    result = await db.execute(
        select(DailyAnalysis)
        .where(DailyAnalysis.analysis_date == today)
    )
    
    analyses = result.scalars().all()
    
    if analyses:
        # Update market status with latest data
        market_status.total_stocks_analyzed = len(analyses)
        market_status.bullish_stocks = sum(1 for a in analyses if a.is_bullish)
        market_status.bearish_stocks = sum(1 for a in analyses if a.is_bearish)
        
        avg_score = sum(a.total_score for a in analyses) / len(analyses)
        if avg_score >= 60:
            market_status.overall_sentiment = "BULLISH"
        elif avg_score <= 40:
            market_status.overall_sentiment = "BEARISH"
        else:
            market_status.overall_sentiment = "NEUTRAL"
    
    return market_schemas.MarketStatusResponse(
        trading_date=market_status.trading_date,
        market_open=market_status.market_open,
        overall_sentiment=market_status.overall_sentiment,
        total_stocks_analyzed=market_status.total_stocks_analyzed,
        bullish_stocks=market_status.bullish_stocks,
        bearish_stocks=market_status.bearish_stocks,
        neutral_stocks=market_status.total_stocks_analyzed - market_status.bullish_stocks - market_status.bearish_stocks,
        bullish_percentage=round((market_status.bullish_stocks / max(market_status.total_stocks_analyzed, 1)) * 100, 2),
        bearish_percentage=round((market_status.bearish_stocks / max(market_status.total_stocks_analyzed, 1)) * 100, 2)
    )

@router.get("/overview", response_model=market_schemas.MarketOverviewResponse)
async def get_market_overview(
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive market overview
    """
    from sqlalchemy import select, func, and_
    
    # Get market status
    market_status = await get_market_status(db)
    
    # Get sector performance
    result = await db.execute(
        select(
            Stock.sector,
            func.count(Stock.id).label('stock_count'),
            func.avg(DailyAnalysis.total_score).label('avg_score')
        )
        .join(DailyAnalysis)
        .where(DailyAnalysis.analysis_date == date.today())
        .group_by(Stock.sector)
        .order_by(func.avg(DailyAnalysis.total_score).desc())
    )
    
    sector_performance = [
        market_schemas.SectorPerformance(
            sector=sector,
            stock_count=count,
            average_score=round(avg_score or 0, 2)
        )
        for sector, count, avg_score in result.all()
    ]
    
    # Get signal statistics
    result = await db.execute(
        select(
            TradingSignal.signal_type,
            func.count(TradingSignal.id).label('signal_count')
        )
        .where(TradingSignal.signal_date == date.today())
        .group_by(TradingSignal.signal_type)
    )
    
    signal_stats = result.all()
    buy_signals = sum(count for signal_type, count in signal_stats if signal_type == 'BUY')
    sell_signals = sum(count for signal_type, count in signal_stats if signal_type == 'SELL')
    
    # Get top gainers and losers (would need price history)
    # For now, return top and bottom by score
    result = await db.execute(
        select(Stock, DailyAnalysis)
        .join(DailyAnalysis)
        .where(DailyAnalysis.analysis_date == date.today())
        .order_by(DailyAnalysis.total_score.desc())
        .limit(5)
    )
    
    top_stocks = [
        market_schemas.StockPerformance(
            symbol=stock.symbol,
            name=stock.name,
            score=analysis.total_score,
            signal=analysis.signal_type
        )
        for stock, analysis in result.all()
    ]
    
    result = await db.execute(
        select(Stock, DailyAnalysis)
        .join(DailyAnalysis)
        .where(DailyAnalysis.analysis_date == date.today())
        .order_by(DailyAnalysis.total_score.asc())
        .limit(5)
    )
    
    bottom_stocks = [
        market_schemas.StockPerformance(
            symbol=stock.symbol,
            name=stock.name,
            score=analysis.total_score,
            signal=analysis.signal_type
        )
        for stock, analysis in result.all()
    ]
    
    return market_schemas.MarketOverviewResponse(
        market_status=market_status,
        sector_performance=sector_performance,
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        top_performers=top_stocks,
        bottom_performers=bottom_stocks
    )

@router.get("/sectors", response_model=List[market_schemas.SectorResponse])
async def get_sectors(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all available sectors
    """
    from sqlalchemy import select, distinct
    
    result = await db.execute(
        select(distinct(Stock.sector))
        .where(Stock.sector.isnot(None))
        .order_by(Stock.sector)
    )
    
    sectors = result.scalars().all()
    
    return [market_schemas.SectorResponse(name=sector) for sector in sectors if sector]

@router.get("/sector/{sector_name}", response_model=market_schemas.SectorDetailResponse)
async def get_sector_detail(
    sector_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific sector
    """
    from sqlalchemy import select, and_, func
    
    # Get stocks in sector
    result = await db.execute(
        select(Stock).where(Stock.sector == sector_name)
    )
    
    stocks = result.scalars().all()
    
    if not stocks:
        raise HTTPException(status_code=404, detail="Sector not found")
    
    # Get today's analysis for sector stocks
    today = date.today()
    stock_ids = [stock.id for stock in stocks]
    
    result = await db.execute(
        select(DailyAnalysis)
        .where(
            and_(
                DailyAnalysis.stock_id.in_(stock_ids),
                DailyAnalysis.analysis_date == today
            )
        )
    )
    
    analyses = result.scalars().all()
    
    if not analyses:
        return market_schemas.SectorDetailResponse(
            sector_name=sector_name,
            stock_count=len(stocks),
            average_score=0,
            top_stocks=[],
            sector_sentiment="NEUTRAL"
        )
    
    # Calculate sector metrics
    avg_score = sum(a.total_score for a in analyses) / len(analyses)
    
    # Determine sector sentiment
    if avg_score >= 60:
        sector_sentiment = "BULLISH"
    elif avg_score <= 40:
        sector_sentiment = "BEARISH"
    else:
        sector_sentiment = "NEUTRAL"
    
    # Get top stocks in sector
    analyses.sort(key=lambda x: x.total_score, reverse=True)
    
    top_stocks = []
    for analysis in analyses[:5]:
        stock = next(s for s in stocks if s.id == analysis.stock_id)
        top_stocks.append(market_schemas.StockPerformance(
            symbol=stock.symbol,
            name=stock.name,
            score=analysis.total_score,
            signal=analysis.signal_type
        ))
    
    return market_schemas.SectorDetailResponse(
        sector_name=sector_name,
        stock_count=len(stocks),
        average_score=round(avg_score, 2),
        top_stocks=top_stocks,
        sector_sentiment=sector_sentiment,
        bullish_stocks=sum(1 for a in analyses if a.is_bullish),
        bearish_stocks=sum(1 for a in analyses if a.is_bearish)
    )

@router.get("/heatmap", response_model=market_schemas.MarketHeatmapResponse)
async def get_market_heatmap(
    db: AsyncSession = Depends(get_db)
):
    """
    Get market heatmap data
    """
    from sqlalchemy import select, and_
    
    # Get today's analyses
    today = date.today()
    
    result = await db.execute(
        select(Stock, DailyAnalysis)
        .join(DailyAnalysis)
        .where(DailyAnalysis.analysis_date == today)
        .order_by(DailyAnalysis.total_score.desc())
    )
    
    analyses = result.all()
    
    # Group by sector
    sector_data = {}
    for stock, analysis in analyses:
        if stock.sector not in sector_data:
            sector_data[stock.sector] = []
        
        sector_data[stock.sector].append({
            'symbol': stock.symbol,
            'name': stock.name,
            'score': analysis.total_score,
            'signal': analysis.signal_type
        })
    
    # Format heatmap data
    heatmap_data = []
    for sector, stocks in sector_data.items():
        if not stocks:
            continue
        
        avg_score = sum(s['score'] for s in stocks) / len(stocks)
        
        heatmap_data.append(market_schemas.HeatmapSector(
            sector=sector,
            average_score=round(avg_score, 2),
            stock_count=len(stocks),
            stocks=[
                market_schemas.HeatmapStock(
                    symbol=s['symbol'],
                    name=s['name'],
                    score=s['score'],
                    intensity=self._get_score_intensity(s['score'])
                )
                for s in stocks
            ]
        ))
    
    # Sort by average score
    heatmap_data.sort(key=lambda x: x.average_score, reverse=True)
    
    return market_schemas.MarketHeatmapResponse(
        date=today,
        sectors=heatmap_data
    )

def _get_score_intensity(self, score: float) -> str:
    """Get color intensity based on score"""
    if score >= 80:
        return "very_strong"
    elif score >= 65:
        return "strong"
    elif score >= 50:
        return "moderate"
    elif score >= 35:
        return "weak"
    else:
        return "very_weak"

@router.get("/nifty50", response_model=market_schemas.IndexResponse)
async def get_nifty50_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get NIFTY 50 index status and composition
    """
    # This would integrate with actual NIFTY 50 data
    # For now, return placeholder data
    
    return market_schemas.IndexResponse(
        index_name="NIFTY 50",
        current_value=17500.00,  # Placeholder
        change=125.50,
        change_percent=0.72,
        last_updated=datetime.now()
    )

@router.get("/nifty-next50", response_model=market_schemas.IndexResponse)
async def get_nifty_next50_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get NIFTY NEXT 50 index status and composition
    """
    # This would integrate with actual NIFTY NEXT 50 data
    # For now, return placeholder data
    
    return market_schemas.IndexResponse(
        index_name="NIFTY NEXT 50",
        current_value=45000.00,  # Placeholder
        change=-85.25,
        change_percent=-0.19,
        last_updated=datetime.now()
    )