"""
Indian Stock Analysis System - Main Application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.api.routes import stocks, analysis, news, market
from app.core.config import settings
from app.db.database import engine, Base
from app.services.scheduler import start_scheduler

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting Indian Stock Analysis System...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start scheduler
    start_scheduler()
    
    yield
    
    # Shutdown
    print("Shutting down system...")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready Indian stock analysis system with actionable trading signals",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(market.router, prefix="/api/market", tags=["Market"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Indian Stock Analysis System",
        "version": settings.APP_VERSION,
        "status": "running",
        "disclaimer": "Not SEBI registered. For educational purposes only. Not financial advice."
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )