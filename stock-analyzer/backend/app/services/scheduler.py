"""
Daily analysis scheduler
"""

import asyncio
import schedule
import time
from datetime import datetime, time as dt_time
from typing import Optional
import threading

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import async_session_maker
from app.services.market_data import market_data_service
from app.services.indicators import indicator_service
from app.services.news_sentiment import news_service
from app.services.scoring import ranking_service
from app.core.config import settings

class DailyScheduler:
    """Scheduler for running daily analysis"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.analysis_time = dt_time(9, 0)  # 9:00 AM by default
        
        # Parse configured time
        if hasattr(settings, 'DAILY_ANALYSIS_TIME'):
            try:
                hour, minute = map(int, settings.DAILY_ANALYSIS_TIME.split(':'))
                self.analysis_time = dt_time(hour, minute)
            except:
                pass  # Use default time
    
    async def run_daily_analysis(self) -> dict:
        """
        Run complete daily analysis pipeline
        
        Returns:
            Dictionary with analysis results
        """
        print(f"Starting daily analysis at {datetime.now()}")
        
        async with async_session_maker() as db:
            try:
                results = {
                    'timestamp': datetime.now().isoformat(),
                    'steps': {}
                }
                
                # Step 1: Update market data
                print("Step 1: Updating market data...")
                market_results = await market_data_service.update_all_stocks(db, period="6mo")
                results['steps']['market_data'] = market_results
                print(f"Market data updated: {market_results}")
                
                # Step 2: Calculate technical indicators
                print("Step 2: Calculating technical indicators...")
                indicator_results = await indicator_service.calculate_indicators_for_all_stocks(db)
                results['steps']['indicators'] = indicator_results
                print(f"Indicators calculated: {indicator_results}")
                
                # Step 3: Fetch and analyze news
                print("Step 3: Fetching and analyzing news...")
                news_results = await news_service.fetch_and_analyze_all_stocks(db)
                results['steps']['news'] = news_results
                print(f"News analysis completed: {news_results}")
                
                # Step 4: Run scoring and ranking
                print("Step 4: Running scoring and ranking...")
                ranking_results = await ranking_service.rank_all_stocks(db)
                results['steps']['ranking'] = {
                    'total_analyzed': ranking_results['total_analyzed'],
                    'buy_signals': len(ranking_results['buy_signals']),
                    'sell_signals': len(ranking_results['sell_signals'])
                }
                print(f"Ranking completed: {ranking_results['total_analyzed']} stocks analyzed")
                
                # Step 5: Update market status
                print("Step 5: Updating market status...")
                await self.update_market_status(db, ranking_results)
                
                print("Daily analysis completed successfully")
                return results
                
            except Exception as e:
                print(f"Error in daily analysis: {str(e)}")
                await db.rollback()
                raise
    
    async def update_market_status(self, db: AsyncSession, ranking_results: dict) -> None:
        """
        Update market status based on analysis results
        
        Args:
            db: Database session
            ranking_results: Results from ranking analysis
        """
        from app.models.stock import MarketStatus
        from sqlalchemy import select
        
        try:
            # Get today's date
            from datetime import date
            today = date.today()
            
            # Check if market status already exists
            result = await db.execute(
                select(MarketStatus).where(MarketStatus.trading_date == today)
            )
            market_status = result.scalar_one_or_none()
            
            # Calculate metrics
            total_stocks = ranking_results['total_analyzed']
            buy_signals = len(ranking_results['buy_signals'])
            sell_signals = len(ranking_results['sell_signals'])
            
            # Determine overall sentiment
            if total_stocks > 0:
                buy_ratio = buy_signals / total_stocks
                sell_ratio = sell_signals / total_stocks
                
                if buy_ratio > 0.3:
                    overall_sentiment = "BULLISH"
                elif sell_ratio > 0.3:
                    overall_sentiment = "BEARISH"
                else:
                    overall_sentiment = "NEUTRAL"
            else:
                overall_sentiment = "NEUTRAL"
            
            if market_status:
                # Update existing record
                market_status.total_stocks_analyzed = total_stocks
                market_status.bullish_stocks = buy_signals
                market_status.bearish_stocks = sell_signals
                market_status.overall_sentiment = overall_sentiment
            else:
                # Create new record
                market_status = MarketStatus(
                    trading_date=today,
                    market_open=True,
                    overall_sentiment=overall_sentiment,
                    total_stocks_analyzed=total_stocks,
                    bullish_stocks=buy_signals,
                    bearish_stocks=sell_signals
                )
                db.add(market_status)
            
            await db.commit()
            print(f"Market status updated: {overall_sentiment}")
            
        except Exception as e:
            print(f"Error updating market status: {str(e)}")
            await db.rollback()
    
    def schedule_daily_job(self):
        """Schedule the daily analysis job"""
        # Clear any existing jobs
        schedule.clear()
        
        # Schedule daily analysis
        schedule.every().day.at(f"{self.analysis_time.hour:02d}:{self.analysis_time.minute:02d}").do(
            self.run_scheduled_analysis
        )
        
        print(f"Daily analysis scheduled for {self.analysis_time}")
    
    def run_scheduled_analysis(self):
        """Wrapper to run analysis in async context"""
        def run_analysis():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(self.run_daily_analysis())
                print(f"Scheduled analysis completed: {results}")
            except Exception as e:
                print(f"Scheduled analysis failed: {str(e)}")
            finally:
                loop.close()
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=run_analysis)
        thread.start()
    
    def start_scheduler(self):
        """Start the scheduler in a separate thread"""
        if self.is_running:
            print("Scheduler is already running")
            return
        
        self.schedule_daily_job()
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("Daily scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        print("Daily scheduler stopped")
    
    def run_analysis_now(self) -> dict:
        """
        Manually trigger analysis immediately
        
        Returns:
            Analysis results
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(self.run_daily_analysis())
            return results
        finally:
            loop.close()

# Global scheduler instance
daily_scheduler = DailyScheduler()

def start_scheduler():
    """Start the global scheduler"""
    daily_scheduler.start_scheduler()

def stop_scheduler():
    """Stop the global scheduler"""
    daily_scheduler.stop_scheduler()

def run_analysis_now():
    """Run analysis immediately"""
    return daily_scheduler.run_analysis_now()