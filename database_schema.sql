-- Indian Stock Analysis System - Database Schema

-- Create database
CREATE DATABASE stock_analysis_db;

-- Use the database
\c stock_analysis_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==================== STOCKS AND MARKET DATA ====================

-- Stock master table
CREATE TABLE stocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    exchange VARCHAR(10) DEFAULT 'NSE',
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    in_universe BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock price data (OHLCV)
CREATE TABLE stock_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open DECIMAL(10,2) NOT NULL,
    high DECIMAL(10,2) NOT NULL,
    low DECIMAL(10,2) NOT NULL,
    close DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    adj_close DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date)
);

-- Create index for fast date range queries
CREATE INDEX idx_stock_prices_stock_date ON stock_prices(stock_id, date);

-- ==================== TECHNICAL INDICATORS ====================

-- Technical indicators table
CREATE TABLE technical_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Moving Averages
    sma_20 DECIMAL(10,2),
    sma_50 DECIMAL(10,2),
    sma_100 DECIMAL(10,2),
    ema_20 DECIMAL(10,2),
    ema_50 DECIMAL(10,2),
    
    -- SuperTrend
    supertrend_value DECIMAL(10,2),
    supertrend_direction VARCHAR(10), -- 'BUY' or 'SELL'
    supertrend_upper DECIMAL(10,2),
    supertrend_lower DECIMAL(10,2),
    
    -- RSI
    rsi_14 DECIMAL(5,2),
    
    -- Volume
    volume_avg_20 DECIMAL(15,0),
    volume_ratio DECIMAL(5,2), -- current volume / avg volume
    
    -- ATR for targets
    atr_14 DECIMAL(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date)
);

-- Create index for indicator queries
CREATE INDEX idx_indicators_stock_date ON technical_indicators(stock_id, date);

-- ==================== NEWS AND SENTIMENT ====================

-- News articles table
CREATE TABLE news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source VARCHAR(100),
    published_at TIMESTAMP NOT NULL,
    url VARCHAR(500),
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
    sentiment_label VARCHAR(10), -- 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
    relevance_score DECIMAL(3,2), -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for news queries
CREATE INDEX idx_news_stock_date ON news_articles(stock_id, published_at);
CREATE INDEX idx_news_sentiment ON news_articles(sentiment_label);

-- ==================== ANALYSIS AND SIGNALS ====================

-- Daily analysis scores
CREATE TABLE daily_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    
    -- Scoring components (0-100)
    ma_alignment_score DECIMAL(5,2),
    supertrend_score DECIMAL(5,2),
    rsi_score DECIMAL(5,2),
    volume_score DECIMAL(5,2),
    sentiment_score DECIMAL(5,2),
    
    -- Overall score
    total_score DECIMAL(5,2),
    
    -- Technical conditions
    is_bullish BOOLEAN DEFAULT FALSE,
    is_bearish BOOLEAN DEFAULT FALSE,
    
    -- Signal generation
    signal_generated BOOLEAN DEFAULT FALSE,
    signal_type VARCHAR(10), -- 'BUY' or 'SELL'
    signal_strength VARCHAR(10), -- 'STRONG', 'MODERATE', 'WEAK'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, analysis_date)
);

-- Create index for analysis queries
CREATE INDEX idx_analysis_date_score ON daily_analysis(analysis_date, total_score DESC);
CREATE INDEX idx_analysis_signals ON daily_analysis(analysis_date, signal_type);

-- Trading signals table
CREATE TABLE trading_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    signal_date DATE NOT NULL,
    signal_type VARCHAR(10) NOT NULL, -- 'BUY' or 'SELL'
    signal_strength VARCHAR(10) NOT NULL,
    
    -- Price levels
    entry_price DECIMAL(10,2) NOT NULL,
    target_1 DECIMAL(10,2),
    target_2 DECIMAL(10,2),
    stop_loss DECIMAL(10,2) NOT NULL,
    
    -- Risk metrics
    risk_amount DECIMAL(10,2), -- entry - stop_loss
    reward_ratio_1 DECIMAL(5,2), -- target_1 / risk_amount
    reward_ratio_2 DECIMAL(5,2), -- target_2 / risk_amount
    
    -- Signal rationale
    rationale TEXT, -- JSON string of reasons
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'HIT_TARGET_1', 'HIT_TARGET_2', 'STOPPED_OUT', 'EXPIRED'
    expiry_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for signal queries
CREATE INDEX idx_signals_date ON trading_signals(signal_date);
CREATE INDEX idx_signals_status ON trading_signals(status);

-- ==================== MARKET STATUS ====================

-- Market status tracking
CREATE TABLE market_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trading_date DATE NOT NULL UNIQUE,
    market_open BOOLEAN DEFAULT TRUE,
    nifty_50_change DECIMAL(5,2),
    nifty_next_50_change DECIMAL(5,2),
    overall_sentiment VARCHAR(20), -- 'BULLISH', 'BEARISH', 'NEUTRAL'
    total_stocks_analyzed INTEGER DEFAULT 0,
    bullish_stocks INTEGER DEFAULT 0,
    bearish_stocks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== CONFIGURATION ====================

-- System configuration
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO system_config (config_key, config_value, description) VALUES 
('min_price_threshold', '20', 'Minimum stock price to consider'),
('min_volume_threshold', '100000', 'Minimum average volume (20-day)'),
('score_threshold_buy', '70', 'Minimum score for BUY signal'),
('score_threshold_sell', '30', 'Maximum score for SELL signal'),
('news_lookback_hours', '72', 'Hours to look back for news'),
('signal_expiry_days', '5', 'Days until signal expires'),
('risk_reward_ratio_min', '1.5', 'Minimum risk:reward ratio'),
('atr_multiplier_target', '2.0', 'ATR multiplier for target calculation'),
('atr_multiplier_sl', '1.5', 'ATR multiplier for stop loss');

-- ==================== UTILITY FUNCTIONS ====================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON stocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trading_signals_updated_at BEFORE UPDATE ON trading_signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== INITIAL DATA ====================

-- Insert NIFTY 50 stocks (sample)
INSERT INTO stocks (symbol, name, sector) VALUES 
('RELIANCE', 'Reliance Industries Limited', 'Oil & Gas'),
('TCS', 'Tata Consultancy Services', 'IT'),
('HDFCBANK', 'HDFC Bank Limited', 'Banking'),
('INFY', 'Infosys Limited', 'IT'),
('HINDUNILVR', 'Hindustan Unilever Limited', 'FMCG'),
('ICICIBANK', 'ICICI Bank Limited', 'Banking'),
('SBIN', 'State Bank of India', 'Banking'),
('BHARTIARTL', 'Bharti Airtel Limited', 'Telecom'),
('ITC', 'ITC Limited', 'FMCG'),
('KOTAKBANK', 'Kotak Mahindra Bank', 'Banking');

-- Insert NIFTY NEXT 50 stocks (sample)
INSERT INTO stocks (symbol, name, sector) VALUES 
('ADANIPORTS', 'Adani Ports and SEZ', 'Infrastructure'),
('ASIANPAINT', 'Asian Paints Limited', 'Paints'),
('AXISBANK', 'Axis Bank Limited', 'Banking'),
('BAJAJFINSV', 'Bajaj Finserv Limited', 'Financial Services'),
('DRREDDY', 'Dr. Reddy''s Laboratories', 'Pharmaceuticals'),
('HCLTECH', 'HCL Technologies', 'IT'),
('HDFC', 'Housing Development Finance Corporation', 'Financial Services'),
('LT', 'Larsen & Toubro Limited', 'Infrastructure'),
('MARUTI', 'Maruti Suzuki India Limited', 'Automobile'),
('ONGC', 'Oil and Natural Gas Corporation', 'Oil & Gas');

-- Set universe flags
UPDATE stocks SET in_universe = TRUE WHERE symbol IN (
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 
    'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
    'ADANIPORTS', 'ASIANPAINT', 'AXISBANK', 'BAJAJFINSV', 
    'DRREDDY', 'HCLTECH', 'HDFC', 'LT', 'MARUTI', 'ONGC'
);