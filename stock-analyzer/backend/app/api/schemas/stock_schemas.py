"""
Stock-related API schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal

class StockResponse(BaseModel):
    """Basic stock information response"""
    id: str
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    in_universe: bool

class StockDetailResponse(BaseModel):
    """Detailed stock information response"""
    id: str
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    current_price: Optional[float] = None
    indicators: Optional[Dict[str, Any]] = None
    latest_analysis: Optional['AnalysisResponse'] = None

class PriceResponse(BaseModel):
    """Stock price data response"""
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    adj_close: Optional[Decimal] = None

class IndicatorResponse(BaseModel):
    """Technical indicator response"""
    date: date
    sma_20: Optional[Decimal] = None
    sma_50: Optional[Decimal] = None
    sma_100: Optional[Decimal] = None
    ema_20: Optional[Decimal] = None
    ema_50: Optional[Decimal] = None
    supertrend_value: Optional[Decimal] = None
    supertrend_direction: Optional[str] = None
    rsi_14: Optional[Decimal] = None
    volume_ratio: Optional[Decimal] = None
    atr_14: Optional[Decimal] = None

class SignalResponse(BaseModel):
    """Trading signal response"""
    id: str
    symbol: str
    signal_date: date
    signal_type: str
    signal_strength: str
    entry_price: Decimal
    target_1: Optional[Decimal] = None
    target_2: Optional[Decimal] = None
    stop_loss: Decimal
    risk_amount: Optional[Decimal] = None
    reward_ratio_1: Optional[Decimal] = None
    reward_ratio_2: Optional[Decimal] = None
    status: str
    rationale: Optional[Dict[str, Any]] = None

class ComponentScores(BaseModel):
    """Individual component scores"""
    ma_alignment: float
    supertrend: float
    rsi_strength: float
    volume_expansion: float
    news_sentiment: float

class AnalysisResponse(BaseModel):
    """Stock analysis response"""
    date: date
    total_score: float
    signal_type: Optional[str] = None
    signal_strength: Optional[str] = None
    component_scores: Optional[ComponentScores] = None

# Forward references
StockDetailResponse.model_rebuild()