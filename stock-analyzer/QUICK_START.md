# Quick Start Guide

Get the Indian Stock Analysis System running in under 10 minutes.

## Prerequisites Checklist

- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 1.27+)
- [ ] Git installed
- [ ] 4GB+ free RAM
- [ ] Internet connection

## Step 1: Get the Code

```bash
git clone <repository-url>
cd stock-analyzer
```

## Step 2: Get Required API Keys

1. **NewsAPI Key** (Free tier available):
   - Visit https://newsapi.org/
   - Sign up for free account
   - Get your API key from dashboard

2. **Optional**: Alpha Vantage API Key (for additional data):
   - Visit https://www.alphavantage.co/
   - Sign up for free account
   - Get your API key

## Step 3: Configure Environment

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` file and add your API keys:
```bash
# Required - Get from https://newsapi.org/
NEWS_API_KEY=your_actual_news_api_key_here

# Optional - Get from https://www.alphavantage.co/
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

3. Save the file.

## Step 4: Start the System

```bash
docker-compose up -d
```

This will:
- Pull required Docker images
- Start PostgreSQL database
- Start Redis cache
- Start backend API (Python/FastAPI)
- Start frontend (React)
- Start Nginx reverse proxy

## Step 5: Wait for Startup

Wait 2-3 minutes for all services to start:

```bash
# Check if all services are running
docker-compose ps

# View logs if needed
docker-compose logs -f
```

## Step 6: Access the Application

Open your browser and go to:
- **Main Application**: http://localhost
- **API Documentation**: http://localhost/api/docs
- **Alternative**: http://127.0.0.1

## Step 7: Verify Everything Works

1. **Check Dashboard**: You should see the main dashboard with disclaimer
2. **View Top Stocks**: Top 5 stock picks should be displayed
3. **Check Market Overview**: Navigate to Market tab for overview
4. **Search News**: Go to News tab and search for any stock symbol

## Step 8: Run Initial Analysis (Optional)

To populate data immediately instead of waiting for scheduled analysis:

```bash
# Trigger manual analysis
curl -X POST http://localhost/api/analysis/run-analysis

# Or use the API endpoint in the docs
```

## Troubleshooting

### Issue: "Connection refused" when accessing localhost

1. Check if all containers are running:
```bash
docker-compose ps
```

2. Check container logs:
```bash
docker-compose logs backend
docker-compose logs frontend
```

3. Restart services:
```bash
docker-compose restart
```

### Issue: "News API key required"

1. Make sure you added the NEWS_API_KEY to .env file
2. Restart the backend:
```bash
docker-compose restart backend
```

### Issue: Database connection failed

1. Wait a bit longer for database to initialize
2. Check database logs:
```bash
docker-compose logs db
```

3. Restart all services:
```bash
docker-compose down
docker-compose up -d
```

### Issue: Frontend shows "Failed to fetch"

1. Check if backend is accessible:
```bash
curl http://localhost/api/health
```

2. Check backend logs:
```bash
docker-compose logs backend
```

## What's Next?

1. **Explore the Dashboard**: View top stock picks and market sentiment
2. **Analyze Stocks**: Click on any stock symbol to see detailed analysis
3. **Check Market Overview**: See sector performance and market heatmap
4. **Read News**: Search for stock-specific news and sentiment
5. **Review API Docs**: Visit http://localhost/api/docs for API reference

## System Defaults

- **Analysis Time**: 9:00 AM daily (configurable in .env)
- **Stock Universe**: NIFTY 50 + NIFTY NEXT 50
- **Data Retention**: 6 months of price data
- **News Lookback**: 72 hours
- **Signal Expiry**: 5 days

## Performance Notes

- First analysis may take 5-10 minutes to complete
- Subsequent analyses are faster due to cached data
- System uses ~2GB RAM when running
- Database grows ~100MB per month

## Security Reminder

- Default PostgreSQL password is 'postgres' - change in production
- API keys are stored in .env file - keep it secure
- System is for educational purposes only

## Getting Help

1. Check logs: `docker-compose logs [service]`
2. Review README.md for detailed documentation
3. Check API docs: http://localhost/api/docs
4. Create an issue if problems persist

## Stopping the System

```bash
docker-compose down
```

To also remove volumes (database data):

```bash
docker-compose down -v
```