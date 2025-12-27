"""
Market status and overview API schemas
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class MarketStatusResponse(BaseModel):
    """Market status response"""
    trading_date: date
    market_open: bool
    overall_sentiment: str
    total_stocks_analyzed: int
    bullish_stocks: int
    bearish_stocks: int
    neutral_stocks: int
    buy_signals: int
    sell_signals: int
    bullish_percentage: float
    bearish_percentage: float

class SectorPerformance(BaseModel):
    """Sector performance"""
    sector: str
    stock_count: int
    average_score: float

class StockPerformance(BaseModel):
    """Stock performance"""
    symbol: str
    name: str
    score: float
    signal: Optional[str] = None

class MarketOverviewResponse(BaseModel):
    """Market overview response"""
    market_status: MarketStatusResponse
    sector_performance: List[SectorPerformance]
    buy_signals: int
    sell_signals: int
    top_performers: List[StockPerformance]
    bottom_performers: List[StockPerformance]

class SectorResponse(BaseModel):
    """Sector response"""
    name: str

class SectorDetailResponse(BaseModel):
    """Detailed sector information"""
    sector_name: str
    stock_count: int
    average_score: float
    top_stocks: List[StockPerformance]
    sector_sentiment: str
    bullish_stocks: int
    bearish_stocks: int

class HeatmapStock(BaseModel):
    """Heatmap stock entry"""
    symbol: str
    name: str
    score: float
    intensity: str

class HeatmapSector(BaseModel):
    """Heatmap sector"""
    sector: str
    average_score: float
    stock_count: int
    stocks: List[HeatmapStock]

class MarketHeatmapResponse(BaseModel):
    """Market heatmap response"""
    date: date
    sectors: List[HeatmapSector]

class IndexResponse(BaseModel):
    """Index response"""
    index_name: str
    current_value: float
    change: float
    change_percent: float
    last_updated: datetime