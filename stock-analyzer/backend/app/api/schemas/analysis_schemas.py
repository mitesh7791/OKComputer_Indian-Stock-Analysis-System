"""
Analysis and ranking API schemas
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal

class ComponentScores(BaseModel):
    """Individual component scores"""
    ma_alignment: float
    supertrend: float
    rsi_strength: float
    volume_expansion: float
    news_sentiment: float

class RankingEntry(BaseModel):
    """Stock ranking entry"""
    symbol: str
    name: str
    sector: Optional[str] = None
    total_score: float
    signal_type: Optional[str] = None
    signal_strength: Optional[str] = None
    component_scores: ComponentScores

class TopStockResponse(BaseModel):
    """Top stock response with trading signal"""
    symbol: str
    name: str
    sector: Optional[str] = None
    current_price: Optional[float] = None
    signal_type: str
    signal_strength: str
    entry_price: Decimal
    target_1: Optional[Decimal] = None
    target_2: Optional[Decimal] = None
    stop_loss: Decimal
    risk_amount: Optional[Decimal] = None
    reward_ratio_1: Optional[Decimal] = None
    reward_ratio_2: Optional[Decimal] = None
    score: float
    rationale: Optional[Dict[str, Any]] = None

class DailyRankingResponse(BaseModel):
    """Daily ranking response"""
    date: date
    total_stocks: int
    rankings: List[RankingEntry]

class StockPerformance(BaseModel):
    """Stock performance entry"""
    symbol: str
    name: str
    score: float
    signal: Optional[str] = None

class MarketSentimentResponse(BaseModel):
    """Market sentiment response"""
    date: date
    overall_sentiment: str
    average_score: float
    total_stocks_analyzed: int
    bullish_stocks: int
    bearish_stocks: int
    neutral_stocks: int
    buy_signals: int
    sell_signals: int
    bullish_percentage: float
    bearish_percentage: float

class TopPerformersResponse(BaseModel):
    """Top performers response"""
    period: str
    top_stocks: List[TopStockResponse]