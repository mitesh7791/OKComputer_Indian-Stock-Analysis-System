"""
Stock Scoring and Signal Generation Engine
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import joinedload

from app.models.stock import Stock, TechnicalIndicator, DailyAnalysis, TradingSignal, NewsArticle
from app.services.indicators import indicator_service
from app.services.news_sentiment import news_service
from app.core.config import settings

class ScoringEngine:
    """Stock scoring and ranking engine"""
    
    def __init__(self):
        # Scoring weights (must sum to 100)
        self.weights = {
            'ma_alignment': 0.30,      # 30% - Moving average alignment
            'supertrend': 0.25,        # 25% - SuperTrend direction
            'rsi_strength': 0.15,      # 15% - RSI strength
            'volume_expansion': 0.10,  # 10% - Volume expansion
            'news_sentiment': 0.20     # 20% - News sentiment
        }
        
        # Thresholds
        self.buy_threshold = settings.SCORE_THRESHOLD_BUY  # 70
        self.sell_threshold = settings.SCORE_THRESHOLD_SELL  # 30
        
    def calculate_ma_alignment_score(self, indicators: Dict[str, Any], current_price: float) -> float:
        """
        Calculate moving average alignment score (0-100)
        
        Bullish conditions:
        - Price > SMA 50
        - SMA 20 > SMA 50
        - EMA 20 > EMA 50
        
        Args:
            indicators: Technical indicators dictionary
            current_price: Current stock price
        
        Returns:
            Score from 0-100
        """
        score = 0.0
        conditions_met = 0
        total_conditions = 4
        
        # Check price above SMA 50
        if indicators.get('sma_50') and current_price > indicators['sma_50']:
            score += 25
            conditions_met += 1
        
        # Check SMA 20 > SMA 50
        if (indicators.get('sma_20') and indicators.get('sma_50') and 
            indicators['sma_20'] > indicators['sma_50']):
            score += 25
            conditions_met += 1
        
        # Check EMA 20 > EMA 50
        if (indicators.get('ema_20') and indicators.get('ema_50') and 
            indicators['ema_20'] > indicators['ema_50']):
            score += 25
            conditions_met += 1
        
        # Bonus for strong alignment (all MAs in order)
        if (indicators.get('sma_20') and indicators.get('sma_50') and 
            indicators.get('ema_20') and indicators.get('ema_50')):
            if (indicators['sma_20'] > indicators['sma_50'] and 
                indicators['ema_20'] > indicators['ema_50'] and
                current_price > indicators['sma_20']):
                score += 25
                conditions_met += 1
        
        return score
    
    def calculate_supertrend_score(self, indicators: Dict[str, Any]) -> float:
        """
        Calculate SuperTrend score (0-100)
        
        Args:
            indicators: Technical indicators dictionary
        
        Returns:
            Score from 0-100
        """
        direction = indicators.get('supertrend_direction')
        
        if direction == 'BUY':
            return 100.0  # Bullish
        elif direction == 'SELL':
            return 0.0    # Bearish
        else:
            return 50.0   # Neutral
    
    def calculate_rsi_score(self, indicators: Dict[str, Any]) -> float:
        """
        Calculate RSI strength score (0-100)
        
        Optimal RSI for bullish: 55-70
        Optimal RSI for bearish: 30-45
        
        Args:
            indicators: Technical indicators dictionary
        
        Returns:
            Score from 0-100
        """
        rsi = indicators.get('rsi_14')
        
        if rsi is None:
            return 50.0
        
        # Convert RSI to score
        # RSI 55-70 = bullish (high score)
        # RSI 30-45 = bearish (low score)
        # RSI 45-55 = neutral (medium score)
        
        if rsi >= 70:
            # Overbought - reduce score
            return max(0, 100 - (rsi - 70) * 2)
        elif rsi >= 55:
            # Strong bullish zone
            return 90 - (70 - rsi) * 2
        elif rsi >= 45:
            # Neutral zone
            return 50 + (rsi - 50) * 4
        elif rsi >= 30:
            # Weak/bearish zone
            return 50 - (45 - rsi) * 2
        else:
            # Oversold - potential bounce
            return min(100, (30 - rsi) * 2)
    
    def calculate_volume_score(self, indicators: Dict[str, Any]) -> float:
        """
        Calculate volume expansion score (0-100)
        
        Args:
            indicators: Technical indicators dictionary
        
        Returns:
            Score from 0-100
        """
        volume_ratio = indicators.get('volume_ratio')
        
        if volume_ratio is None:
            return 50.0
        
        # Volume ratio interpretation:
        # < 0.8 = Low volume (score 20-40)
        # 0.8-1.2 = Normal volume (score 40-60)
        # 1.2-2.0 = High volume (score 60-80)
        # > 2.0 = Very high volume (score 80-100)
        
        if volume_ratio >= 2.0:
            return min(100, 80 + (volume_ratio - 2.0) * 20)
        elif volume_ratio >= 1.2:
            return 60 + (volume_ratio - 1.2) * 25
        elif volume_ratio >= 0.8:
            return 40 + (volume_ratio - 0.8) * 50
        else:
            return max(20, volume_ratio * 50)
    
    def calculate_sentiment_score(self, sentiment_score: float) -> float:
        """
        Convert sentiment score to 0-100 scale
        
        Args:
            sentiment_score: Sentiment score from -1 to 1
        
        Returns:
            Score from 0-100
        """
        if sentiment_score is None:
            return 50.0
        
        # Convert -1 to 1 scale to 0 to 100
        return (sentiment_score + 1) * 50
    
    def calculate_total_score(self, component_scores: Dict[str, float]) -> float:
        """
        Calculate weighted total score
        
        Args:
            component_scores: Dictionary with individual scores
        
        Returns:
            Weighted total score from 0-100
        """
        total_score = 0.0
        
        for component, score in component_scores.items():
            weight = self.weights.get(component, 0)
            total_score += score * weight
        
        return min(100.0, max(0.0, total_score))
    
    def determine_signal(self, total_score: float) -> Tuple[str, str]:
        """
        Determine signal type and strength based on score
        
        Args:
            total_score: Total score from 0-100
        
        Returns:
            Tuple of (signal_type, signal_strength)
        """
        if total_score >= self.buy_threshold:
            signal_type = 'BUY'
            if total_score >= 85:
                signal_strength = 'STRONG'
            elif total_score >= 75:
                signal_strength = 'MODERATE'
            else:
                signal_strength = 'WEAK'
        elif total_score <= self.sell_threshold:
            signal_type = 'SELL'
            if total_score <= 15:
                signal_strength = 'STRONG'
            elif total_score <= 25:
                signal_strength = 'MODERATE'
            else:
                signal_strength = 'WEAK'
        else:
            signal_type = 'HOLD'
            signal_strength = 'NEUTRAL'
        
        return signal_type, signal_strength

class SignalGenerator:
    """Trading signal generation engine"""
    
    def __init__(self):
        self.scoring_engine = ScoringEngine()
    
    def generate_entry_exit_levels(self, 
                                 indicators: Dict[str, Any], 
                                 current_price: float,
                                 signal_type: str) -> Dict[str, float]:
        """
        Generate entry, target, and stop-loss levels
        
        Args:
            indicators: Technical indicators
            current_price: Current stock price
            signal_type: 'BUY' or 'SELL'
        
        Returns:
            Dictionary with price levels
        """
        levels = {}
        
        if signal_type == 'BUY':
            # Entry: Break above previous high or EMA 20
            entry_above = indicators.get('ema_20', current_price)
            levels['entry'] = max(current_price, entry_above)
            
            # Stop Loss: Below SuperTrend or recent swing low
            if indicators.get('supertrend_lower'):
                levels['stop_loss'] = indicators['supertrend_lower']
            else:
                # Fallback: 2% below entry
                levels['stop_loss'] = levels['entry'] * 0.98
            
            # Risk amount
            risk_amount = levels['entry'] - levels['stop_loss']
            
            # Target 1: 1.5x risk
            levels['target_1'] = levels['entry'] + risk_amount * 1.5
            
            # Target 2: ATR-based or nearest resistance
            if indicators.get('atr_14'):
                levels['target_2'] = levels['entry'] + indicators['atr_14'] * 2.0
            else:
                levels['target_2'] = levels['entry'] + risk_amount * 2.5
        
        elif signal_type == 'SELL':
            # Entry: Break below previous low or EMA 20
            entry_below = indicators.get('ema_20', current_price)
            levels['entry'] = min(current_price, entry_below)
            
            # Stop Loss: Above SuperTrend or recent swing high
            if indicators.get('supertrend_upper'):
                levels['stop_loss'] = indicators['supertrend_upper']
            else:
                # Fallback: 2% above entry
                levels['stop_loss'] = levels['entry'] * 1.02
            
            # Risk amount
            risk_amount = levels['stop_loss'] - levels['entry']
            
            # Target 1: 1.5x risk
            levels['target_1'] = levels['entry'] - risk_amount * 1.5
            
            # Target 2: ATR-based or nearest support
            if indicators.get('atr_14'):
                levels['target_2'] = levels['entry'] - indicators['atr_14'] * 2.0
            else:
                levels['target_2'] = levels['entry'] - risk_amount * 2.5
        
        # Ensure stop-loss is reasonable
        if signal_type == 'BUY':
            levels['stop_loss'] = min(levels['stop_loss'], levels['entry'] * 0.95)
        else:
            levels['stop_loss'] = max(levels['stop_loss'], levels['entry'] * 1.05)
        
        return levels
    
    def generate_rationale(self, 
                          component_scores: Dict[str, float],
                          indicators: Dict[str, Any]) -> str:
        """
        Generate signal rationale
        
        Args:
            component_scores: Individual component scores
            indicators: Technical indicators
        
        Returns:
            JSON string with rationale
        """
        rationale = {
            'reasons': [],
            'technical_factors': [],
            'risk_factors': []
        }
        
        # Analyze component scores
        if component_scores.get('ma_alignment', 0) > 70:
            rationale['reasons'].append("Strong moving average alignment")
            rationale['technical_factors'].append("Bullish MA crossover")
        
        if component_scores.get('supertrend', 0) > 80:
            rationale['reasons'].append("SuperTrend in bullish mode")
        elif component_scores.get('supertrend', 0) < 20:
            rationale['reasons'].append("SuperTrend in bearish mode")
        
        if component_scores.get('rsi_strength', 0) > 70:
            rationale['technical_factors'].append("Strong RSI momentum")
        
        if component_scores.get('volume_expansion', 0) > 70:
            rationale['technical_factors'].append("High volume confirmation")
        
        if component_scores.get('news_sentiment', 0) > 70:
            rationale['reasons'].append("Positive news sentiment")
        
        # Risk factors
        rsi = indicators.get('rsi_14', 50)
        if rsi > 75:
            rationale['risk_factors'].append("RSI overbought")
        elif rsi < 25:
            rationale['risk_factors'].append("RSI oversold")
        
        return json.dumps(rationale)

class RankingService:
    """Stock ranking and top picks service"""
    
    def __init__(self):
        self.signal_generator = SignalGenerator()
    
    async def analyze_stock(self, db: AsyncSession, stock: Stock) -> Optional[DailyAnalysis]:
        """
        Perform complete analysis for a single stock
        
        Args:
            db: Database session
            stock: Stock object
        
        Returns:
            DailyAnalysis object or None if failed
        """
        try:
            # Get latest indicators
            indicators = await indicator_service.get_latest_indicators(db, stock.symbol)
            
            if not indicators:
                return None
            
            # Get current price (use latest close)
            from app.services.market_data import market_data_service
            current_price = await market_data_service.get_live_price(f"{stock.symbol}.NS")
            
            if not current_price:
                # Fallback to latest close from indicators
                current_price = indicators.get('close', 0)
            
            # Calculate component scores
            component_scores = {
                'ma_alignment': self.signal_generator.scoring_engine.calculate_ma_alignment_score(
                    indicators, current_price
                ),
                'supertrend': self.signal_generator.scoring_engine.calculate_supertrend_score(indicators),
                'rsi_strength': self.signal_generator.scoring_engine.calculate_rsi_score(indicators),
                'volume_expansion': self.signal_generator.scoring_engine.calculate_volume_score(indicators)
            }
            
            # Get news sentiment score
            sentiment_score = await news_service.get_stock_sentiment_score(db, stock.symbol)
            component_scores['news_sentiment'] = self.signal_generator.scoring_engine.calculate_sentiment_score(
                sentiment_score
            )
            
            # Calculate total score
            total_score = self.signal_generator.scoring_engine.calculate_total_score(component_scores)
            
            # Determine signal
            signal_type, signal_strength = self.signal_generator.scoring_engine.determine_signal(total_score)
            
            # Determine market bias
            is_bullish = total_score >= 60
            is_bearish = total_score <= 40
            
            # Create analysis record
            analysis = DailyAnalysis(
                stock_id=stock.id,
                analysis_date=datetime.now().date(),
                ma_alignment_score=component_scores['ma_alignment'],
                supertrend_score=component_scores['supertrend'],
                rsi_score=component_scores['rsi_strength'],
                volume_score=component_scores['volume_expansion'],
                sentiment_score=component_scores['news_sentiment'],
                total_score=total_score,
                is_bullish=is_bullish,
                is_bearish=is_bearish,
                signal_generated=signal_type in ['BUY', 'SELL'],
                signal_type=signal_type if signal_type in ['BUY', 'SELL'] else None,
                signal_strength=signal_strength if signal_type in ['BUY', 'SELL'] else None
            )
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing stock {stock.symbol}: {str(e)}")
            return None
    
    async def generate_trading_signal(self, db: AsyncSession, analysis: DailyAnalysis) -> Optional[TradingSignal]:
        """
        Generate trading signal from analysis
        
        Args:
            db: Database session
            analysis: DailyAnalysis object
        
        Returns:
            TradingSignal object or None
        """
        if not analysis.signal_generated:
            return None
        
        try:
            # Get stock and indicators
            result = await db.execute(
                select(Stock).where(Stock.id == analysis.stock_id)
            )
            stock = result.scalar_one()
            
            indicators = await indicator_service.get_latest_indicators(db, stock.symbol)
            
            if not indicators:
                return None
            
            # Get current price
            from app.services.market_data import market_data_service
            current_price = await market_data_service.get_live_price(f"{stock.symbol}.NS")
            
            if not current_price:
                current_price = indicators.get('close', 0)
            
            # Generate price levels
            levels = self.signal_generator.generate_entry_exit_levels(
                indicators, current_price, analysis.signal_type
            )
            
            # Calculate risk metrics
            if analysis.signal_type == 'BUY':
                risk_amount = levels['entry'] - levels['stop_loss']
            else:
                risk_amount = levels['stop_loss'] - levels['entry']
            
            reward_ratio_1 = (levels['target_1'] - levels['entry']) / risk_amount if risk_amount > 0 else 0
            reward_ratio_2 = (levels['target_2'] - levels['entry']) / risk_amount if risk_amount > 0 else 0
            
            # Generate rationale
            component_scores = {
                'ma_alignment': analysis.ma_alignment_score,
                'supertrend': analysis.supertrend_score,
                'rsi_strength': analysis.rsi_score,
                'volume_expansion': analysis.volume_score,
                'news_sentiment': analysis.sentiment_score
            }
            
            rationale = self.signal_generator.generate_rationale(component_scores, indicators)
            
            # Create trading signal
            signal = TradingSignal(
                stock_id=stock.id,
                signal_date=datetime.now().date(),
                signal_type=analysis.signal_type,
                signal_strength=analysis.signal_strength,
                entry_price=levels['entry'],
                target_1=levels['target_1'],
                target_2=levels['target_2'],
                stop_loss=levels['stop_loss'],
                risk_amount=risk_amount,
                reward_ratio_1=reward_ratio_1,
                reward_ratio_2=reward_ratio_2,
                rationale=rationale,
                expiry_date=datetime.now().date() + timedelta(days=settings.SIGNAL_EXPIRY_DAYS)
            )
            
            return signal
            
        except Exception as e:
            print(f"Error generating signal for stock {analysis.stock_id}: {str(e)}")
            return None
    
    async def rank_all_stocks(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Analyze and rank all stocks
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with ranking results
        """
        # Get all active stocks
        result = await db.execute(
            select(Stock).where(Stock.is_active == True)
        )
        stocks = result.scalars().all()
        
        analyses = []
        signals = []
        
        for stock in stocks:
            # Analyze stock
            analysis = await self.analyze_stock(db, stock)
            
            if analysis:
                analyses.append(analysis)
                
                # Generate trading signal if applicable
                if analysis.signal_generated:
                    signal = await self.generate_trading_signal(db, analysis)
                    if signal:
                        signals.append(signal)
        
        # Sort analyses by total score (descending)
        analyses.sort(key=lambda x: x.total_score, reverse=True)
        
        # Sort signals by strength and score
        signals.sort(key=lambda x: (x.signal_strength, x.signal_date), reverse=True)
        
        # Save to database
        try:
            for analysis in analyses:
                db.add(analysis)
            
            for signal in signals:
                db.add(signal)
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            print(f"Error saving analyses: {str(e)}")
        
        return {
            'total_analyzed': len(analyses),
            'top_stocks': analyses[:10],  # Top 10 by score
            'buy_signals': [s for s in signals if s.signal_type == 'BUY'],
            'sell_signals': [s for s in signals if s.signal_type == 'SELL'],
            'all_analyses': analyses
        }
    
    async def get_top_stocks(self, db: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top N stocks with BUY signals
        
        Args:
            db: Database session
            limit: Number of top stocks to return
        
        Returns:
            List of top stocks with detailed information
        """
        # Get today's date
        today = datetime.now().date()
        
        # Get top stocks with BUY signals
        result = await db.execute(
            select(TradingSignal)
            .join(Stock)
            .where(
                and_(
                    TradingSignal.signal_type == 'BUY',
                    TradingSignal.signal_date == today,
                    TradingSignal.status == 'ACTIVE'
                )
            )
            .order_by(desc(TradingSignal.signal_strength))
            .limit(limit)
            .options(joinedload(TradingSignal.stock))
        )
        
        signals = result.scalars().all()
        
        # Format results
        top_stocks = []
        for signal in signals:
            stock = signal.stock
            
            # Get latest analysis
            analysis_result = await db.execute(
                select(DailyAnalysis)
                .where(
                    and_(
                        DailyAnalysis.stock_id == stock.id,
                        DailyAnalysis.analysis_date == today
                    )
                )
            )
            analysis = analysis_result.scalar_one_or_none()
            
            # Get current price
            from app.services.market_data import market_data_service
            current_price = await market_data_service.get_live_price(f"{stock.symbol}.NS")
            
            top_stocks.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'sector': stock.sector,
                'current_price': current_price,
                'signal_type': signal.signal_type,
                'signal_strength': signal.signal_strength,
                'entry_price': signal.entry_price,
                'target_1': signal.target_1,
                'target_2': signal.target_2,
                'stop_loss': signal.stop_loss,
                'risk_amount': signal.risk_amount,
                'reward_ratio_1': signal.reward_ratio_1,
                'reward_ratio_2': signal.reward_ratio_2,
                'score': analysis.total_score if analysis else 0,
                'rationale': json.loads(signal.rationale) if signal.rationale else {}
            })
        
        return top_stocks

# Global instances
scoring_engine = ScoringEngine()
signal_generator = SignalGenerator()
ranking_service = RankingService()