"""
Stock-related API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.stock import Stock, StockPrice, TechnicalIndicator, DailyAnalysis, TradingSignal
from app.services.market_data import market_data_service
from app.services.indicators import indicator_service
from app.services.scoring import ranking_service
from app.api.schemas import stock_schemas

router = APIRouter()

@router.get("/", response_model=List[stock_schemas.StockResponse])
async def get_stocks(
    in_universe: bool = Query(True, description="Filter stocks in analysis universe"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of stocks with optional filtering
    """
    from sqlalchemy import select, and_
    
    query = select(Stock).where(Stock.is_active == True)
    
    if in_universe:
        query = query.where(Stock.in_universe == True)
    
    if sector:
        query = query.where(Stock.sector == sector)
    
    result = await db.execute(query)
    stocks = result.scalars().all()
    
    return [stock_schemas.StockResponse(
        id=str(stock.id),
        symbol=stock.symbol,
        name=stock.name,
        sector=stock.sector,
        industry=stock.industry,
        market_cap=stock.market_cap,
        in_universe=stock.in_universe
    ) for stock in stocks]

@router.get("/{symbol}", response_model=stock_schemas.StockDetailResponse)
async def get_stock_detail(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific stock
    """
    from sqlalchemy import select
    
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get current price
    current_price = await market_data_service.get_live_price(f"{symbol}.NS")
    
    # Get latest indicators
    indicators = await indicator_service.get_latest_indicators(db, symbol)
    
    # Get latest analysis
    result = await db.execute(
        select(DailyAnalysis)
        .where(DailyAnalysis.stock_id == stock.id)
        .order_by(DailyAnalysis.analysis_date.desc())
        .limit(1)
    )
    latest_analysis = result.scalar_one_or_none()
    
    return stock_schemas.StockDetailResponse(
        id=str(stock.id),
        symbol=stock.symbol,
        name=stock.name,
        sector=stock.sector,
        industry=stock.industry,
        market_cap=stock.market_cap,
        current_price=current_price,
        indicators=indicators,
        latest_analysis=stock_schemas.AnalysisResponse(
            date=latest_analysis.analysis_date,
            total_score=latest_analysis.total_score,
            signal_type=latest_analysis.signal_type,
            signal_strength=latest_analysis.signal_strength
        ) if latest_analysis else None
    )

@router.get("/{symbol}/prices", response_model=List[stock_schemas.PriceResponse])
async def get_stock_prices(
    symbol: str,
    days: int = Query(30, description="Number of days to fetch"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical price data for a stock
    """
    from sqlalchemy import select, and_
    
    # Get stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get price data
    result = await db.execute(
        select(StockPrice)
        .where(StockPrice.stock_id == stock.id)
        .order_by(StockPrice.date.desc())
        .limit(days)
    )
    
    prices = result.scalars().all()
    
    return [stock_schemas.PriceResponse(
        date=price.date,
        open=price.open,
        high=price.high,
        low=price.low,
        close=price.close,
        volume=price.volume,
        adj_close=price.adj_close
    ) for price in reversed(prices)]  # Reverse to get chronological order

@router.get("/{symbol}/indicators", response_model=List[stock_schemas.IndicatorResponse])
async def get_stock_indicators(
    symbol: str,
    days: int = Query(30, description="Number of days to fetch"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get technical indicators for a stock
    """
    from sqlalchemy import select, and_
    
    # Get stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get indicators
    result = await db.execute(
        select(TechnicalIndicator)
        .where(TechnicalIndicator.stock_id == stock.id)
        .order_by(TechnicalIndicator.date.desc())
        .limit(days)
    )
    
    indicators = result.scalars().all()
    
    return [stock_schemas.IndicatorResponse(
        date=indicator.date,
        sma_20=indicator.sma_20,
        sma_50=indicator.sma_50,
        sma_100=indicator.sma_100,
        ema_20=indicator.ema_20,
        ema_50=indicator.ema_50,
        supertrend_value=indicator.supertrend_value,
        supertrend_direction=indicator.supertrend_direction,
        rsi_14=indicator.rsi_14,
        volume_ratio=indicator.volume_ratio,
        atr_14=indicator.atr_14
    ) for indicator in reversed(indicators)]

@router.get("/{symbol}/signals", response_model=List[stock_schemas.SignalResponse])
async def get_stock_signals(
    symbol: str,
    active_only: bool = Query(True, description="Only return active signals"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trading signals for a stock
    """
    from sqlalchemy import select, and_
    
    # Get stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get signals
    query = select(TradingSignal).where(TradingSignal.stock_id == stock.id)
    
    if active_only:
        query = query.where(TradingSignal.status == 'ACTIVE')
    
    query = query.order_by(TradingSignal.signal_date.desc())
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    return [stock_schemas.SignalResponse(
        id=str(signal.id),
        symbol=stock.symbol,
        signal_date=signal.signal_date,
        signal_type=signal.signal_type,
        signal_strength=signal.signal_strength,
        entry_price=signal.entry_price,
        target_1=signal.target_1,
        target_2=signal.target_2,
        stop_loss=signal.stop_loss,
        risk_amount=signal.risk_amount,
        reward_ratio_1=signal.reward_ratio_1,
        reward_ratio_2=signal.reward_ratio_2,
        status=signal.status,
        rationale=json.loads(signal.rationale) if signal.rationale else {}
    ) for signal in signals]

@router.post("/{symbol}/analyze", response_model=stock_schemas.AnalysisResponse)
async def analyze_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform technical analysis on a stock
    """
    from sqlalchemy import select
    
    # Get stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Perform analysis
    analysis = await ranking_service.analyze_stock(db, stock)
    
    if not analysis:
        raise HTTPException(status_code=500, detail="Analysis failed")
    
    # Save to database
    db.add(analysis)
    await db.commit()
    
    return stock_schemas.AnalysisResponse(
        date=analysis.analysis_date,
        total_score=analysis.total_score,
        signal_type=analysis.signal_type,
        signal_strength=analysis.signal_strength,
        component_scores={
            'ma_alignment': analysis.ma_alignment_score,
            'supertrend': analysis.supertrend_score,
            'rsi_strength': analysis.rsi_score,
            'volume_expansion': analysis.volume_score,
            'news_sentiment': analysis.sentiment_score
        }
    )

@router.post("/update-data")
async def update_stock_data(
    symbols: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Update market data for stocks
    """
    if symbols:
        # Update specific stocks
        stats = {'successful': 0, 'failed': 0}
        for symbol in symbols:
            # Fetch data
            df = await market_data_service.fetch_stock_data(f"{symbol}.NS", period="6mo")
            if df is not None:
                if await market_data_service.save_stock_data(db, symbol, df):
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
            else:
                stats['failed'] += 1
    else:
        # Update all stocks
        stats = await market_data_service.update_all_stocks(db, period="6mo")
    
    return {
        "message": "Data update completed",
        "statistics": stats
    }