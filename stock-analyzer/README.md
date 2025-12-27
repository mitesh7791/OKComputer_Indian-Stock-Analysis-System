# Indian Stock Analysis System

A production-ready web application for daily technical analysis of Indian stocks (NSE) providing actionable trading signals with entry, target, and stop-loss levels.

## Features

- **Daily Stock Analysis**: Analyzes NIFTY 50 + NIFTY NEXT 50 stocks
- **Technical Indicators**: SMA, EMA, SuperTrend, RSI, Volume analysis
- **News Sentiment**: Fetches and analyzes news sentiment for stocks
- **Scoring Engine**: Multi-factor scoring system (0-100 scale)
- **Trading Signals**: BUY/SELL signals with entry, targets, and stop-loss
- **Real-time Dashboard**: Interactive charts and market overview
- **Daily Scheduler**: Automated daily analysis at configurable time

## System Architecture

```
┌─────────────┐
│   Frontend  │  React + Material-UI + Charts
├─────────────┤
│     API     │  FastAPI + Async Endpoints
├─────────────┤
│   Services  │  Market Data + Indicators + News + Scoring
├─────────────┤
│  Database   │  PostgreSQL + SQLAlchemy
└─────────────┘
```

## Technical Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Market Data**: Yahoo Finance API
- **News**: NewsAPI with sentiment analysis
- **Scheduler**: Python schedule library

### Frontend
- **Framework**: React 18
- **UI Library**: Material-UI (MUI)
- **Charts**: Recharts + Lightweight Charts
- **HTTP Client**: Axios
- **Routing**: React Router DOM

## Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Quick Start (Docker)

1. Clone the repository:
```bash
git clone <repository-url>
cd stock-analyzer
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Edit `.env` file with your API keys:
```bash
NEWS_API_KEY=your_news_api_key_here
```

4. Start with Docker Compose:
```bash
docker-compose up -d
```

5. Access the application:
- Frontend: http://localhost
- Backend API: http://localhost/api
- PostgreSQL: localhost:5432

### Manual Installation

#### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements/requirements.txt
```

3. Install TA-Lib:
```bash
# Linux
pip install TA-Lib

# Windows (download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)
pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
python -m alembic upgrade head
```

6. Run the backend:
```bash
uvicorn app.main:app --reload
```

#### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment:
```bash
# Create .env file
REACT_APP_API_URL=http://localhost:8000
```

3. Start the frontend:
```bash
npm start
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `NEWS_API_KEY` | NewsAPI key (required) | - |
| `DAILY_ANALYSIS_TIME` | Time for daily analysis | `09:00` |
| `MIN_PRICE_THRESHOLD` | Minimum stock price | `20` |
| `SCORE_THRESHOLD_BUY` | Buy signal threshold | `70` |
| `SCORE_THRESHOLD_SELL` | Sell signal threshold | `30` |

### Stock Universe

The system analyzes NIFTY 50 + NIFTY NEXT 50 stocks by default. You can modify the stock list in:
- `backend/app/services/market_data.py`

## API Endpoints

### Core Endpoints

- `GET /api/stocks` - List all stocks
- `GET /api/stocks/{symbol}` - Get stock details
- `GET /api/stocks/{symbol}/prices` - Get price history
- `GET /api/stocks/{symbol}/indicators` - Get technical indicators
- `GET /api/stocks/{symbol}/signals` - Get trading signals

### Analysis Endpoints

- `GET /api/analysis/top-stocks` - Get top 5 stock picks
- `GET /api/analysis/market-sentiment` - Get market sentiment
- `GET /api/analysis/daily-ranking` - Get daily stock ranking
- `POST /api/analysis/run-analysis` - Run daily analysis manually

### News Endpoints

- `GET /api/news/{symbol}` - Get news for a stock
- `GET /api/news/trending` - Get trending news
- `GET /api/news/sources` - Get news source statistics
- `GET /api/news/sentiment/{symbol}` - Get sentiment analysis

### Market Endpoints

- `GET /api/market/status` - Get market status
- `GET /api/market/overview` - Get market overview
- `GET /api/market/heatmap` - Get market heatmap
- `GET /api/market/sectors` - Get sector analysis

## Scoring System

The system uses a multi-factor scoring approach with the following weights:

| Factor | Weight | Description |
|--------|--------|-------------|
| Moving Average Alignment | 30% | SMA/EMA crossover analysis |
| SuperTrend Direction | 25% | SuperTrend indicator signals |
| RSI Strength | 15% | RSI momentum analysis |
| Volume Expansion | 10% | Volume vs average analysis |
| News Sentiment | 20% | News sentiment scoring |

### Signal Generation

- **BUY Signal**: Score ≥ 70
- **SELL Signal**: Score ≤ 30
- **Signal Strength**: STRONG (≥85), MODERATE (≥75), WEAK (≥70)

### Entry/Exit Logic

- **Entry**: Breakout above previous high or EMA 20
- **Target 1**: 1.5 × Risk
- **Target 2**: ATR-based or nearest resistance
- **Stop Loss**: Below SuperTrend line or recent swing low

## Database Schema

### Key Tables

- `stocks`: Master stock information
- `stock_prices`: OHLCV price data
- `technical_indicators`: Calculated indicators
- `news_articles`: News with sentiment analysis
- `daily_analysis`: Daily scoring results
- `trading_signals`: Generated trading signals
- `market_status`: Market overview data

## Daily Workflow

1. **Market Data Update** (9:00 AM): Fetch latest OHLCV data
2. **Indicator Calculation**: Calculate all technical indicators
3. **News Analysis**: Fetch and analyze news sentiment
4. **Scoring & Ranking**: Generate scores and rank stocks
5. **Signal Generation**: Create trading signals for top stocks
6. **Market Status Update**: Update overall market sentiment

## Development

### Running Tests
```bash
cd backend
pytest
```

### Code Formatting
```bash
black app/
flake8 app/
```

### Database Migrations
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Deployment

### Production Deployment

1. Build Docker images:
```bash
docker-compose build
```

2. Start in production mode:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

3. Configure reverse proxy (Nginx/Apache)
4. Set up SSL certificates (Let's Encrypt)
5. Configure monitoring and logging

### Environment-Specific Configurations

- **Development**: Debug mode, hot reload, local database
- **Staging**: Production-like setup, test data
- **Production**: Optimized settings, SSL, monitoring

## Monitoring

### Application Metrics
- API response times
- Database query performance
- Error rates
- System resource usage

### Business Metrics
- Number of stocks analyzed
- Signal generation rate
- News sentiment trends
- Market sentiment distribution

## Security Considerations

- Rate limiting on API endpoints
- Input validation and sanitization
- CORS configuration
- API key management
- Database connection security

## Disclaimer

**Not SEBI registered. For educational purposes only. Not financial advice.**

This system is designed for analysis and educational purposes. Users should:
- Conduct their own research before making investment decisions
- Understand that all investments carry risk
- Not rely solely on automated signals for trading
- Consult with qualified financial advisors

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API schema at `/docs` when running

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Roadmap

- [ ] Options analysis integration
- [ ] Portfolio tracking features
- [ ] Advanced charting tools
- [ ] Mobile application
- [ ] Real-time data feeds
- [ ] Backtesting framework
- [ ] Machine learning models
- [ ] Social sentiment analysis