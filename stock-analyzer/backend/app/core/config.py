"""
Application Configuration Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "Indian Stock Analyzer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Debug mode")
    SECRET_KEY: str = Field(default="your-secret-key", description="Secret key for encryption")
    
    # API Keys
    NEWS_API_KEY: str = Field(default="", description="News API key")
    ALPHA_VANTAGE_API_KEY: str = Field(default="", description="Alpha Vantage API key")
    
    # Database
    DATABASE_URL: str = Field(default="", description="Database connection URL")
    DATABASE_URL_SYNC: str = Field(default="", description="Synchronous database URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )
    
    # Market Configuration
    MIN_PRICE_THRESHOLD: float = Field(default=20.0, description="Minimum stock price")
    MIN_VOLUME_THRESHOLD: int = Field(default=100000, description="Minimum average volume")
    SCORE_THRESHOLD_BUY: float = Field(default=70.0, description="Minimum score for BUY signal")
    SCORE_THRESHOLD_SELL: float = Field(default=30.0, description="Maximum score for SELL signal")
    NEWS_LOOKBACK_HOURS: int = Field(default=72, description="News lookback period in hours")
    SIGNAL_EXPIRY_DAYS: int = Field(default=5, description="Signal expiry in days")
    
    # Technical Analysis
    RISK_REWARD_RATIO_MIN: float = Field(default=1.5, description="Minimum risk:reward ratio")
    ATR_MULTIPLIER_TARGET: float = Field(default=2.0, description="ATR multiplier for targets")
    ATR_MULTIPLIER_SL: float = Field(default=1.5, description="ATR multiplier for stop loss")
    
    # Scheduler
    DAILY_ANALYSIS_TIME: str = Field(default="09:00", description="Daily analysis time")
    TIMEZONE: str = Field(default="Asia/Kolkata", description="Application timezone")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()