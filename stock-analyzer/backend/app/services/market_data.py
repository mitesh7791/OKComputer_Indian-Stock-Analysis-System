"""
Market data fetching and management service
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import asyncio
import aiohttp

from app.models.stock import Stock, StockPrice
from app.core.config import settings

class MarketDataService:
    """Service for fetching and managing market data"""
    
    def __init__(self):
        self.stock_symbols = []
        self._load_stock_universe()
    
    def _load_stock_universe(self):
        """Load the stock universe (NIFTY 50 + NIFTY NEXT 50)"""
        # NIFTY 50 stocks
        nifty_50 = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
            'ICICIBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS',
            'LT.NS', 'HDFC.NS', 'BAJFINANCE.NS', 'AXISBANK.NS', 'HCLTECH.NS',
            'MARUTI.NS', 'TATASTEEL.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'SUNPHARMA.NS',
            'M&M.NS', 'WIPRO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ULTRACEMCO.NS',
            'NESTLEIND.NS', 'GRASIM.NS', 'ONGC.NS', 'JSWSTEEL.NS', 'INDUSINDBK.NS',
            'DRREDDY.NS', 'BAJAJFINSV.NS', 'CIPLA.NS', 'ADANIPORTS.NS', 'ASIANPAINT.NS',
            'HEROMOTOCO.NS', 'UPL.NS', 'SHREECEM.NS', 'BAJAJ-AUTO.NS', 'DIVISLAB.NS',
            'HINDALCO.NS', 'IOC.NS', 'COALINDIA.NS', 'BPCL.NS', 'BRITANNIA.NS',
            'SBILIFE.NS', 'EICHERMOT.NS', 'GAIL.NS', 'TITAN.NS', 'DABUR.NS'
        ]
        
        # NIFTY NEXT 50 stocks
        nifty_next_50 = [
            'ADANIGREEN.NS', 'ADANITRANS.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
            'AUBANK.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BERGEPAINT.NS', 'BOSCHLTD.NS',
            'CADILAHC.NS', 'COLPAL.NS', 'DLF.NS', 'GODREJCP.NS', 'GODREJPROP.NS',
            'HDFCAMC.NS', 'HDFCLIFE.NS', 'HAVELLS.NS', 'ICICIPRULI.NS', 'ICICIGI.NS',
            'IGL.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JUBLFOOD.NS', 'LUPIN.NS',
            'MARICO.NS', 'MUTHOOTFIN.NS', 'NMDC.NS', 'PIDILITIND.NS', 'PEL.NS',
            'PFIZER.NS', 'PGHH.NS', 'PNB.NS', 'SAIL.NS', 'SHRIRAMFIN.NS',
            'SIEMENS.NS', 'SRF.NS', 'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TVSMOTOR.NS',
            'UBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WHIRLPOOL.NS', 'ACC.NS',
            'AIRTEL.NS', 'BIOCON.NS', 'BHEL.NS', 'CUMMINSIND.NS', 'DMART.NS'
        ]
        
        self.stock_symbols = nifty_50 + nifty_next_50
        print(f"Loaded {len(self.stock_symbols)} stocks from NIFTY 50 and NIFTY NEXT 50")
    
    async def fetch_stock_data(self, symbol: str, period: str = "6mo") -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data for a symbol
        
        Args:
            symbol: Stock symbol with .NS suffix
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d", timeout=60)
            
            if hist.empty:
                print(f"No data found for {symbol}")
                return None
            
            # Reset index to make Date a column
            hist = hist.reset_index()
            hist['Date'] = hist['Date'].dt.date
            
            # Add symbol column
            hist['Symbol'] = symbol.replace('.NS', '')
            
            return hist
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    async def fetch_multiple_stocks(self, symbols: List[str], period: str = "6mo") -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks concurrently
        
        Args:
            symbols: List of stock symbols
            period: Time period for data
        
        Returns:
            Dictionary mapping symbols to their DataFrames
        """
        tasks = [self.fetch_stock_data(symbol, period) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data_dict = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, pd.DataFrame) and not result.empty:
                data_dict[symbol] = result
            else:
                print(f"Failed to fetch data for {symbol}")
        
        return data_dict
    
    async def get_live_price(self, symbol: str) -> Optional[float]:
        """
        Get current live price for a stock
        
        Args:
            symbol: Stock symbol with .NS suffix
        
        Returns:
            Current price or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price fields
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('lastPrice')
            
            return float(price) if price else None
            
        except Exception as e:
            print(f"Error getting live price for {symbol}: {str(e)}")
            return None
    
    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive stock information
        
        Args:
            symbol: Stock symbol with .NS suffix
        
        Returns:
            Dictionary with stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant information
            stock_info = {
                'symbol': symbol.replace('.NS', ''),
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
            }
            
            return stock_info
            
        except Exception as e:
            print(f"Error getting stock info for {symbol}: {str(e)}")
            return {}
    
    async def save_stock_data(self, db: AsyncSession, symbol: str, df: pd.DataFrame) -> bool:
        """
        Save stock data to database
        
        Args:
            db: Database session
            symbol: Stock symbol
            df: DataFrame with OHLCV data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get stock ID
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            
            if not stock:
                print(f"Stock {symbol} not found in database")
                return False
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Save each record
            for record in records:
                # Check if record already exists
                existing = await db.execute(
                    select(StockPrice).where(
                        and_(
                            StockPrice.stock_id == stock.id,
                            StockPrice.date == record['Date']
                        )
                    )
                )
                
                if existing.scalar_one_or_none():
                    continue  # Skip existing records
                
                # Create new price record
                price_record = StockPrice(
                    stock_id=stock.id,
                    date=record['Date'],
                    open=float(record['Open']),
                    high=float(record['High']),
                    low=float(record['Low']),
                    close=float(record['Close']),
                    volume=int(record['Volume']),
                    adj_close=float(record.get('Adj Close', record['Close']))
                )
                
                db.add(price_record)
            
            await db.commit()
            print(f"Saved {len(records)} records for {symbol}")
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"Error saving data for {symbol}: {str(e)}")
            return False
    
    async def update_all_stocks(self, db: AsyncSession, period: str = "6mo") -> Dict[str, int]:
        """
        Update data for all stocks in the universe
        
        Args:
            db: Database session
            period: Time period for data fetching
        
        Returns:
            Dictionary with update statistics
        """
        stats = {
            'total_stocks': len(self.stock_symbols),
            'successful': 0,
            'failed': 0,
            'records_added': 0
        }
        
        # Process in batches to avoid overwhelming the API
        batch_size = 10
        batches = [self.stock_symbols[i:i + batch_size] for i in range(0, len(self.stock_symbols), batch_size)]
        
        for batch in batches:
            # Fetch data for batch
            data_dict = await self.fetch_multiple_stocks(batch, period)
            
            # Save data for each stock
            for symbol, df in data_dict.items():
                if await self.save_stock_data(db, symbol.replace('.NS', ''), df):
                    stats['successful'] += 1
                    stats['records_added'] += len(df)
                else:
                    stats['failed'] += 1
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        print(f"Update completed: {stats['successful']} successful, {stats['failed']} failed")
        return stats
    
    async def get_stock_price_history(self, db: AsyncSession, symbol: str, days: int = 200) -> Optional[pd.DataFrame]:
        """
        Get stock price history from database
        
        Args:
            db: Database session
            symbol: Stock symbol
            days: Number of days to fetch
        
        Returns:
            DataFrame with price history or None if not found
        """
        try:
            # Get stock ID
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            
            if not stock:
                return None
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Fetch price data
            result = await db.execute(
                select(StockPrice)
                .where(
                    and_(
                        StockPrice.stock_id == stock.id,
                        StockPrice.date >= start_date,
                        StockPrice.date <= end_date
                    )
                )
                .order_by(StockPrice.date)
            )
            
            prices = result.scalars().all()
            
            if not prices:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'Date': p.date,
                    'Open': float(p.open),
                    'High': float(p.high),
                    'Low': float(p.low),
                    'Close': float(p.close),
                    'Volume': int(p.volume),
                    'Adj Close': float(p.adj_close)
                }
                for p in prices
            ])
            
            return df
            
        except Exception as e:
            print(f"Error fetching price history for {symbol}: {str(e)}")
            return None

# Global instance
market_data_service = MarketDataService()