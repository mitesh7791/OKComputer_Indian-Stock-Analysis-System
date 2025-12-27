"""
Technical Indicators Calculation Engine
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import talib

from app.models.stock import Stock, StockPrice, TechnicalIndicator
from app.core.config import settings

class TechnicalIndicators:
    """Technical indicator calculation engine"""
    
    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return talib.SMA(data, timeperiod=period)
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return talib.EMA(data, timeperiod=period)
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        return talib.RSI(data, timeperiod=period)
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        return talib.ATR(high, low, close, timeperiod=period)
    
    @staticmethod
    def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """
        Calculate SuperTrend indicator
        
        Args:
            df: DataFrame with OHLCV data
            period: ATR period (default: 10)
            multiplier: ATR multiplier (default: 3.0)
        
        Returns:
            DataFrame with SuperTrend values
        """
        # Calculate ATR
        df['atr'] = TechnicalIndicators.calculate_atr(df['High'], df['Low'], df['Close'], period)
        
        # Calculate basic upper and lower bands
        df['basic_upper'] = (df['High'] + df['Low']) / 2 + multiplier * df['atr']
        df['basic_lower'] = (df['High'] + df['Low']) / 2 - multiplier * df['atr']
        
        # Initialize final bands
        df['final_upper'] = 0.0
        df['final_lower'] = 0.0
        df['supertrend'] = 0.0
        df['supertrend_direction'] = ''
        
        # Calculate final bands with smoothing
        for i in range(1, len(df)):
            # Final upper band logic
            if df['basic_upper'].iloc[i] < df['final_upper'].iloc[i-1] or df['Close'].iloc[i-1] > df['final_upper'].iloc[i-1]:
                df.loc[df.index[i], 'final_upper'] = df['basic_upper'].iloc[i]
            else:
                df.loc[df.index[i], 'final_upper'] = df['final_upper'].iloc[i-1]
            
            # Final lower band logic
            if df['basic_lower'].iloc[i] > df['final_lower'].iloc[i-1] or df['Close'].iloc[i-1] < df['final_lower'].iloc[i-1]:
                df.loc[df.index[i], 'final_lower'] = df['basic_lower'].iloc[i]
            else:
                df.loc[df.index[i], 'final_lower'] = df['final_lower'].iloc[i-1]
        
        # Calculate SuperTrend
        for i in range(1, len(df)):
            if df['supertrend'].iloc[i-1] == df['final_upper'].iloc[i-1]:
                if df['Close'].iloc[i] <= df['final_upper'].iloc[i]:
                    df.loc[df.index[i], 'supertrend'] = df['final_upper'].iloc[i]
                    df.loc[df.index[i], 'supertrend_direction'] = 'SELL'
                else:
                    df.loc[df.index[i], 'supertrend'] = df['final_lower'].iloc[i]
                    df.loc[df.index[i], 'supertrend_direction'] = 'BUY'
            else:
                if df['Close'].iloc[i] >= df['final_lower'].iloc[i]:
                    df.loc[df.index[i], 'supertrend'] = df['final_lower'].iloc[i]
                    df.loc[df.index[i], 'supertrend_direction'] = 'BUY'
                else:
                    df.loc[df.index[i], 'supertrend'] = df['final_upper'].iloc[i]
                    df.loc[df.index[i], 'supertrend_direction'] = 'SELL'
        
        # Set initial values
        df.loc[df.index[0], 'final_upper'] = df['basic_upper'].iloc[0]
        df.loc[df.index[0], 'final_lower'] = df['basic_lower'].iloc[0]
        df.loc[df.index[0], 'supertrend'] = df['final_upper'].iloc[0]
        df.loc[df.index[0], 'supertrend_direction'] = 'SELL'
        
        # Clean up temporary columns
        df['supertrend_upper'] = df['final_upper']
        df['supertrend_lower'] = df['final_lower']
        
        return df
    
    @staticmethod
    def calculate_volume_average(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Calculate volume moving average and ratio"""
        df['volume_avg'] = TechnicalIndicators.calculate_sma(df['Volume'], period)
        df['volume_ratio'] = df['Volume'] / df['volume_avg']
        return df
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators for a stock
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with all indicators
        """
        # Ensure data is sorted by date
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Moving Averages
        df['sma_20'] = TechnicalIndicators.calculate_sma(df['Close'], 20)
        df['sma_50'] = TechnicalIndicators.calculate_sma(df['Close'], 50)
        df['sma_100'] = TechnicalIndicators.calculate_sma(df['Close'], 100)
        df['ema_20'] = TechnicalIndicators.calculate_ema(df['Close'], 20)
        df['ema_50'] = TechnicalIndicators.calculate_ema(df['Close'], 50)
        
        # RSI
        df['rsi_14'] = TechnicalIndicators.calculate_rsi(df['Close'], 14)
        
        # ATR
        df['atr_14'] = TechnicalIndicators.calculate_atr(df['High'], df['Low'], df['Close'], 14)
        
        # SuperTrend
        df = TechnicalIndicators.calculate_supertrend(df, period=10, multiplier=3.0)
        
        # Volume indicators
        df = TechnicalIndicators.calculate_volume_average(df, 20)
        
        return df

class IndicatorService:
    """Service for calculating and storing technical indicators"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    async def calculate_indicators_for_stock(self, db: AsyncSession, symbol: str) -> bool:
        """
        Calculate all technical indicators for a stock and save to database
        
        Args:
            db: Database session
            symbol: Stock symbol
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get stock ID
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            
            if not stock:
                print(f"Stock {symbol} not found")
                return False
            
            # Get price data from database
            result = await db.execute(
                select(StockPrice)
                .where(StockPrice.stock_id == stock.id)
                .order_by(StockPrice.date)
            )
            prices = result.scalars().all()
            
            if len(prices) < 100:  # Need minimum data for indicators
                print(f"Insufficient data for {symbol}: {len(prices)} records")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'Date': p.date,
                    'Open': float(p.open),
                    'High': float(p.high),
                    'Low': float(p.low),
                    'Close': float(p.close),
                    'Volume': int(p.volume)
                }
                for p in prices
            ])
            
            # Calculate indicators
            df = self.indicators.calculate_all_indicators(df)
            
            # Save indicators to database
            for _, row in df.iterrows():
                if pd.isna(row['sma_20']) or pd.isna(row['supertrend']):
                    continue  # Skip rows with NaN values
                
                # Check if indicator already exists
                existing = await db.execute(
                    select(TechnicalIndicator).where(
                        and_(
                            TechnicalIndicator.stock_id == stock.id,
                            TechnicalIndicator.date == row['Date']
                        )
                    )
                )
                
                if existing.scalar_one_or_none():
                    continue  # Skip existing records
                
                # Create new indicator record
                indicator = TechnicalIndicator(
                    stock_id=stock.id,
                    date=row['Date'],
                    sma_20=float(row['sma_20']) if not pd.isna(row['sma_20']) else None,
                    sma_50=float(row['sma_50']) if not pd.isna(row['sma_50']) else None,
                    sma_100=float(row['sma_100']) if not pd.isna(row['sma_100']) else None,
                    ema_20=float(row['ema_20']) if not pd.isna(row['ema_20']) else None,
                    ema_50=float(row['ema_50']) if not pd.isna(row['ema_50']) else None,
                    supertrend_value=float(row['supertrend']) if not pd.isna(row['supertrend']) else None,
                    supertrend_direction=row['supertrend_direction'] if not pd.isna(row['supertrend_direction']) else None,
                    supertrend_upper=float(row['supertrend_upper']) if not pd.isna(row['supertrend_upper']) else None,
                    supertrend_lower=float(row['supertrend_lower']) if not pd.isna(row['supertrend_lower']) else None,
                    rsi_14=float(row['rsi_14']) if not pd.isna(row['rsi_14']) else None,
                    volume_avg_20=float(row['volume_avg']) if not pd.isna(row['volume_avg']) else None,
                    volume_ratio=float(row['volume_ratio']) if not pd.isna(row['volume_ratio']) else None,
                    atr_14=float(row['atr_14']) if not pd.isna(row['atr_14']) else None
                )
                
                db.add(indicator)
            
            await db.commit()
            print(f"Calculated and saved indicators for {symbol}")
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"Error calculating indicators for {symbol}: {str(e)}")
            return False
    
    async def get_latest_indicators(self, db: AsyncSession, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest technical indicators for a stock
        
        Args:
            db: Database session
            symbol: Stock symbol
        
        Returns:
            Dictionary with latest indicators or None if not found
        """
        try:
            # Get stock ID
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            
            if not stock:
                return None
            
            # Get latest indicators
            result = await db.execute(
                select(TechnicalIndicator)
                .where(TechnicalIndicator.stock_id == stock.id)
                .order_by(TechnicalIndicator.date.desc())
                .limit(1)
            )
            
            indicator = result.scalar_one_or_none()
            
            if not indicator:
                return None
            
            # Convert to dictionary
            return {
                'symbol': symbol,
                'date': indicator.date,
                'sma_20': indicator.sma_20,
                'sma_50': indicator.sma_50,
                'sma_100': indicator.sma_100,
                'ema_20': indicator.ema_20,
                'ema_50': indicator.ema_50,
                'supertrend_value': indicator.supertrend_value,
                'supertrend_direction': indicator.supertrend_direction,
                'supertrend_upper': indicator.supertrend_upper,
                'supertrend_lower': indicator.supertrend_lower,
                'rsi_14': indicator.rsi_14,
                'volume_avg_20': indicator.volume_avg_20,
                'volume_ratio': indicator.volume_ratio,
                'atr_14': indicator.atr_14
            }
            
        except Exception as e:
            print(f"Error getting latest indicators for {symbol}: {str(e)}")
            return None
    
    async def calculate_indicators_for_all_stocks(self, db: AsyncSession) -> Dict[str, int]:
        """
        Calculate indicators for all stocks in the universe
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with calculation statistics
        """
        # Get all active stocks in universe
        result = await db.execute(
            select(Stock).where(Stock.is_active == True)
        )
        stocks = result.scalars().all()
        
        stats = {
            'total_stocks': len(stocks),
            'successful': 0,
            'failed': 0
        }
        
        for stock in stocks:
            if await self.calculate_indicators_for_stock(db, stock.symbol):
                stats['successful'] += 1
            else:
                stats['failed'] += 1
        
        print(f"Indicator calculation completed: {stats['successful']} successful, {stats['failed']} failed")
        return stats

# Global instance
indicator_service = IndicatorService()