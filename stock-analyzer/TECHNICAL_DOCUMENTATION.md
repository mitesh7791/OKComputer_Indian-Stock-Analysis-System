# Technical Documentation

## System Overview

The Indian Stock Analysis System is a production-ready web application built with modern technologies for analyzing Indian stock market data and generating actionable trading signals.

## Architecture Components

### 1. Backend Services (FastAPI)

#### Core Services

**Market Data Service** (`app/services/market_data.py`)
- Fetches OHLCV data from Yahoo Finance
- Manages stock universe (NIFTY 50 + NIFTY NEXT 50)
- Handles data persistence to PostgreSQL
- Provides live price fetching

**Technical Indicators Service** (`app/services/indicators.py`)
- Calculates SMA, EMA, RSI, ATR, SuperTrend
- Uses TA-Lib for indicator calculations
- Stores results in technical_indicators table
- Supports multiple timeframes

**News Sentiment Service** (`app/services/news_sentiment.py`)
- Fetches news from NewsAPI
- Performs sentiment analysis using VADER + TextBlob
- Keyword-based sentiment enhancement
- Relevance scoring for news articles

**Scoring Engine** (`app/services/scoring.py`)
- Multi-factor scoring system (0-100 scale)
- Component weights: MA (30%), SuperTrend (25%), News (20%), RSI (15%), Volume (10%)
- Signal generation with entry/exit logic
- Risk/reward calculations

#### Database Models

**Stock** (`app/models/stock.py`)
```python
- id (UUID)
- symbol (str) - NSE symbol
- name (str) - Company name
- sector (str) - Industry sector
- is_active (bool) - Active in analysis
- in_universe (bool) - Part of analysis universe
```

**TechnicalIndicator**
```python
- stock_id (ForeignKey)
- date (Date)
- sma_20, sma_50, sma_100 (Decimal)
- ema_20, ema_50 (Decimal)
- supertrend_value, supertrend_direction
- rsi_14 (Decimal)
- atr_14 (Decimal)
- volume_avg_20, volume_ratio
```

**DailyAnalysis**
```python
- stock_id (ForeignKey)
- analysis_date (Date)
- Component scores (Decimal)
- total_score (Decimal)
- signal_type, signal_strength
- is_bullish, is_bearish (Boolean)
```

### 2. Frontend (React)

#### Components Structure

```
src/
├── components/
│   ├── Header.js           # Navigation header
│   └── [Other components]
├── pages/
│   ├── Dashboard.js        # Main dashboard
│   ├── StockDetail.js      # Individual stock view
│   ├── MarketOverview.js   # Market analysis
│   └── News.js             # News and sentiment
├── utils/
│   └── api.js              # API client
└── App.js                  # Main app component
```

#### Key Features

**Dashboard** (`pages/Dashboard.js`)
- Top 5 stock picks with signals
- Market sentiment overview
- Quick statistics cards
- Interactive data tables

**Stock Detail** (`pages/StockDetail.js`)
- Price charts with indicators
- Technical indicator tables
- Signal history
- News feed
- Tabbed interface

**Market Overview** (`pages/MarketOverview.js`)
- Sector performance charts
- Market sentiment distribution
- Top/bottom performers
- Market heatmap visualization

### 3. Database (PostgreSQL)

#### Schema Design

**Tables Overview**

| Table | Purpose | Key Indexes |
|-------|---------|-------------|
| stocks | Master stock data | symbol (unique) |
| stock_prices | OHLCV data | (stock_id, date) |
| technical_indicators | Calculated indicators | (stock_id, date) |
| news_articles | News with sentiment | (stock_id, published_at) |
| daily_analysis | Daily scores | (analysis_date, total_score) |
| trading_signals | Generated signals | (signal_date, status) |
| market_status | Market overview | trading_date (unique) |

#### Performance Optimizations

1. **Composite Indexes**: For common query patterns
2. **Partitioning**: Consider date-based partitioning for large tables
3. **Caching**: Redis for frequently accessed data
4. **Connection Pooling**: Async connection management

### 4. Scheduler System

#### Daily Analysis Pipeline

```
1. Market Data Update (9:00 AM)
   └─ Fetch OHLCV for all stocks
   └─ Store in stock_prices table

2. Technical Analysis
   └─ Calculate all indicators
   └─ Store in technical_indicators table

3. News Analysis
   └─ Fetch latest news (72 hours)
   └─ Analyze sentiment
   └─ Store in news_articles table

4. Scoring & Ranking
   └─ Calculate component scores
   └─ Generate total score
   └─ Create trading signals

5. Market Status Update
   └─ Calculate market sentiment
   └─ Update market_status table
```

## API Design

### RESTful Endpoints

**Stock Endpoints**
```
GET    /api/stocks                    # List stocks
GET    /api/stocks/{symbol}           # Stock details
GET    /api/stocks/{symbol}/prices    # Price history
GET    /api/stocks/{symbol}/indicators # Technical indicators
GET    /api/stocks/{symbol}/signals   # Trading signals
POST   /api/stocks/{symbol}/analyze   # Manual analysis
```

**Analysis Endpoints**
```
GET    /api/analysis/top-stocks       # Top 5 picks
GET    /api/analysis/market-sentiment # Market overview
GET    /api/analysis/daily-ranking    # Ranked stocks
POST   /api/analysis/run-analysis     # Trigger analysis
```

### Response Schemas

**Stock Response**
```json
{
  "id": "uuid",
  "symbol": "RELIANCE",
  "name": "Reliance Industries",
  "sector": "Oil & Gas",
  "current_price": 2500.50,
  "latest_analysis": {
    "score": 78.5,
    "signal": "BUY",
    "strength": "MODERATE"
  }
}
```

**Signal Response**
```json
{
  "symbol": "RELIANCE",
  "signal_type": "BUY",
  "signal_strength": "MODERATE",
  "entry_price": 2520.00,
  "target_1": 2580.00,
  "target_2": 2650.00,
  "stop_loss": 2480.00,
  "risk_reward_ratio": 1.5,
  "rationale": {
    "reasons": ["Strong MA alignment", "Positive news"],
    "technical_factors": ["Bullish SuperTrend"],
    "risk_factors": ["Market volatility"]
  }
}
```

## Configuration Management

### Environment Variables

**Database Configuration**
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
REDIS_URL=redis://localhost:6379/0
```

**API Keys**
```bash
NEWS_API_KEY=your_news_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

**Analysis Parameters**
```bash
MIN_PRICE_THRESHOLD=20
SCORE_THRESHOLD_BUY=70
SCORE_THRESHOLD_SELL=30
DAILY_ANALYSIS_TIME=09:00
```

### System Config Table

Stores runtime configuration in the database:
- min_price_threshold
- min_volume_threshold
- score_threshold_buy/sell
- news_lookback_hours
- signal_expiry_days

## Security Implementation

### Authentication & Authorization
- No user authentication (analysis only)
- API key validation for external services
- Rate limiting on endpoints

### Data Protection
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (React escapes content)
- CORS configuration

### Infrastructure Security
- Environment variables for secrets
- Docker secrets management
- Network isolation in containers
- Regular security updates

## Performance Optimization

### Database Optimization
1. **Indexing Strategy**
   - Primary keys: UUID with default indexing
   - Foreign keys: Automatic indexing
   - Composite indexes: For common queries
   - Partial indexes: For filtered queries

2. **Query Optimization**
   - Async queries with connection pooling
   - Batch operations where possible
   - Lazy loading for relationships
   - Query result caching

### Caching Strategy
1. **Redis Caching**
   - Market data (1 hour TTL)
   - Indicator calculations (24 hour TTL)
   - News sentiment (6 hour TTL)
   - Top stocks list (1 hour TTL)

2. **Application Caching**
   - Function result caching
   - Database query caching
   - Static asset caching

### Scaling Considerations
1. **Horizontal Scaling**
   - Multiple API server instances
   - Load balancer configuration
   - Database read replicas

2. **Vertical Scaling**
   - Increase server resources
   - Optimize database configuration
   - Tune application parameters

## Monitoring & Logging

### Application Monitoring
- **Metrics Collection**: Prometheus/Grafana
- **Health Checks**: `/health` endpoint
- **Performance Monitoring**: Response times, throughput
- **Error Tracking**: Sentry integration

### Logging Strategy
- **Structured Logging**: JSON format
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Log Rotation**: Prevent disk space issues
- **Centralized Logging**: ELK stack integration

### Business Metrics
- Number of stocks analyzed daily
- Signal generation rates
- News sentiment trends
- Market sentiment distribution
- User engagement metrics

## Testing Strategy

### Unit Tests
- Service layer testing
- Indicator calculation verification
- Scoring algorithm validation
- API endpoint testing

### Integration Tests
- Database operation testing
- External API integration
- End-to-end workflow testing
- Performance benchmarking

### Test Data
- Sample stock data
- Mock news articles
- Predefined indicator values
- Expected scoring results

## Deployment Architecture

### Development Environment
- Local Docker Compose setup
- Hot reload for development
- Debug mode enabled
- Local database

### Staging Environment
- Production-like setup
- Test data isolation
- Performance testing
- Integration testing

### Production Environment
- Container orchestration (Kubernetes/Docker Swarm)
- Load balancing
- Auto-scaling
- SSL termination
- Database backups
- Monitoring and alerting

## Maintenance

### Regular Tasks
- Database maintenance (VACUUM, ANALYZE)
- Log rotation and cleanup
- Security updates
- Performance monitoring
- Data quality checks

### Backup Strategy
- Database daily backups
- Configuration backups
- Application state backups
- Disaster recovery plan

### Updates & Upgrades
- Dependency updates
- Security patches
- Feature updates
- Database schema migrations

## Troubleshooting

### Common Issues

**Database Connection Issues**
- Check PostgreSQL service status
- Verify connection parameters
- Check network connectivity
- Review connection pool settings

**Indicator Calculation Errors**
- Verify TA-Lib installation
- Check data quality
- Review calculation parameters
- Debug specific indicators

**News API Errors**
- Verify API key validity
- Check rate limits
- Review API response format
- Handle network timeouts

**Performance Issues**
- Monitor database queries
- Check memory usage
- Review caching effectiveness
- Analyze bottlenecks

### Debug Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service]

# Access container
docker-compose exec backend bash

# Database queries
docker-compose exec db psql -U postgres -d stock_analysis_db

# Redis commands
docker-compose exec redis redis-cli
```

## Future Enhancements

### Technical Improvements
- Real-time data feeds
- Advanced machine learning models
- Options analysis
- Portfolio optimization
- Risk management tools

### Scalability Features
- Microservices architecture
- Event-driven design
- Distributed caching
- Message queue integration

### User Experience
- Mobile application
- Advanced charting
- Customizable dashboards
- Alert notifications
- Social features

This technical documentation provides a comprehensive guide for understanding, developing, and maintaining the Indian Stock Analysis System.