"""
Stock data models
"""

from sqlalchemy import Column, String, DateTime, Date, Numeric, BigInteger, Boolean, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.database import Base

class Stock(Base):
    """Stock master table"""
    __tablename__ = "stocks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(10), default="NSE")
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(BigInteger)
    is_active = Column(Boolean, default=True)
    in_universe = Column(Boolean, default=False)
    created_at = Column(DateTime, default="now()")
    updated_at = Column(DateTime, default="now()", onupdate="now()")
    
    # Relationships
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("TechnicalIndicator", back_populates="stock", cascade="all, delete-orphan")
    news = relationship("NewsArticle", back_populates="stock", cascade="all, delete-orphan")
    analyses = relationship("DailyAnalysis", back_populates="stock", cascade="all, delete-orphan")
    signals = relationship("TradingSignal", back_populates="stock", cascade="all, delete-orphan")

class StockPrice(Base):
    """Stock price data (OHLCV)"""
    __tablename__ = "stock_prices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(10, 2), nullable=False)
    high = Column(Numeric(10, 2), nullable=False)
    low = Column(Numeric(10, 2), nullable=False)
    close = Column(Numeric(10, 2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    adj_close = Column(Numeric(10, 2))
    created_at = Column(DateTime, default="now()")
    
    # Relationships
    stock = relationship("Stock", back_populates="prices")
    
    # Composite index for efficient queries
    __table_args__ = (
        {"postgresql_indexes": [{"name": "idx_stock_prices_stock_date", "columns": ["stock_id", "date"]}]},
    )

class TechnicalIndicator(Base):
    """Technical indicators table"""
    __tablename__ = "technical_indicators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Moving Averages
    sma_20 = Column(Numeric(10, 2))
    sma_50 = Column(Numeric(10, 2))
    sma_100 = Column(Numeric(10, 2))
    ema_20 = Column(Numeric(10, 2))
    ema_50 = Column(Numeric(10, 2))
    
    # SuperTrend
    supertrend_value = Column(Numeric(10, 2))
    supertrend_direction = Column(String(10))  # 'BUY' or 'SELL'
    supertrend_upper = Column(Numeric(10, 2))
    supertrend_lower = Column(Numeric(10, 2))
    
    # RSI
    rsi_14 = Column(Numeric(5, 2))
    
    # Volume
    volume_avg_20 = Column(Numeric(15, 0))
    volume_ratio = Column(Numeric(5, 2))  # current volume / avg volume
    
    # ATR for targets
    atr_14 = Column(Numeric(10, 2))
    
    created_at = Column(DateTime, default="now()")
    
    # Relationships
    stock = relationship("Stock", back_populates="indicators")
    
    # Composite index
    __table_args__ = (
        {"postgresql_indexes": [{"name": "idx_indicators_stock_date", "columns": ["stock_id", "date"]}]},
    )

class NewsArticle(Base):
    """News articles table"""
    __tablename__ = "news_articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    source = Column(String(100))
    published_at = Column(DateTime, nullable=False)
    url = Column(String(500))
    sentiment_score = Column(Numeric(3, 2))  # -1.0 to 1.0
    sentiment_label = Column(String(10))  # 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
    relevance_score = Column(Numeric(3, 2))  # 0.0 to 1.0
    created_at = Column(DateTime, default="now()")
    
    # Relationships
    stock = relationship("Stock", back_populates="news")
    
    # Indexes
    __table_args__ = (
        {"postgresql_indexes": [
            {"name": "idx_news_stock_date", "columns": ["stock_id", "published_at"]},
            {"name": "idx_news_sentiment", "columns": ["sentiment_label"]}
        ]},
    )

class DailyAnalysis(Base):
    """Daily analysis scores"""
    __tablename__ = "daily_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    analysis_date = Column(Date, nullable=False)
    
    # Scoring components (0-100)
    ma_alignment_score = Column(Numeric(5, 2))
    supertrend_score = Column(Numeric(5, 2))
    rsi_score = Column(Numeric(5, 2))
    volume_score = Column(Numeric(5, 2))
    sentiment_score = Column(Numeric(5, 2))
    
    # Overall score
    total_score = Column(Numeric(5, 2))
    
    # Technical conditions
    is_bullish = Column(Boolean, default=False)
    is_bearish = Column(Boolean, default=False)
    
    # Signal generation
    signal_generated = Column(Boolean, default=False)
    signal_type = Column(String(10))  # 'BUY' or 'SELL'
    signal_strength = Column(String(10))  # 'STRONG', 'MODERATE', 'WEAK'
    
    created_at = Column(DateTime, default="now()")
    
    # Relationships
    stock = relationship("Stock", back_populates="analyses")
    
    # Indexes
    __table_args__ = (
        {"postgresql_indexes": [
            {"name": "idx_analysis_date_score", "columns": ["analysis_date", "total_score"]},
            {"name": "idx_analysis_signals", "columns": ["analysis_date", "signal_type"]}
        ]},
    )

class TradingSignal(Base):
    """Trading signals table"""
    __tablename__ = "trading_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    signal_date = Column(Date, nullable=False)
    signal_type = Column(String(10), nullable=False)  # 'BUY' or 'SELL'
    signal_strength = Column(String(10), nullable=False)  # 'STRONG', 'MODERATE', 'WEAK'
    
    # Price levels
    entry_price = Column(Numeric(10, 2), nullable=False)
    target_1 = Column(Numeric(10, 2))
    target_2 = Column(Numeric(10, 2))
    stop_loss = Column(Numeric(10, 2), nullable=False)
    
    # Risk metrics
    risk_amount = Column(Numeric(10, 2))
    reward_ratio_1 = Column(Numeric(5, 2))
    reward_ratio_2 = Column(Numeric(5, 2))
    
    # Signal rationale
    rationale = Column(Text)
    
    # Status tracking
    status = Column(String(20), default="ACTIVE")  # 'ACTIVE', 'HIT_TARGET_1', 'HIT_TARGET_2', 'STOPPED_OUT', 'EXPIRED'
    expiry_date = Column(Date)
    
    created_at = Column(DateTime, default="now()")
    updated_at = Column(DateTime, default="now()", onupdate="now()")
    
    # Relationships
    stock = relationship("Stock", back_populates="signals")
    
    # Indexes
    __table_args__ = (
        {"postgresql_indexes": [
            {"name": "idx_signals_date", "columns": ["signal_date"]},
            {"name": "idx_signals_status", "columns": ["status"]}
        ]},
    )

class MarketStatus(Base):
    """Market status tracking"""
    __tablename__ = "market_status"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trading_date = Column(Date, nullable=False, unique=True)
    market_open = Column(Boolean, default=True)
    nifty_50_change = Column(Numeric(5, 2))
    nifty_next_50_change = Column(Numeric(5, 2))
    overall_sentiment = Column(String(20))  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    total_stocks_analyzed = Column(Integer, default=0)
    bullish_stocks = Column(Integer, default=0)
    bearish_stocks = Column(Integer, default=0)
    created_at = Column(DateTime, default="now()")

class SystemConfig(Base):
    """System configuration"""
    __tablename__ = "system_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default="now()", onupdate="now()")