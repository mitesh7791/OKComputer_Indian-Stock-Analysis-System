"""
Database configuration and connection management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
import asyncio
from app.core.config import settings

# Create async engine
if settings.DATABASE_URL:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool,
        future=True
    )
else:
    # Fallback for development
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost/stock_analysis_db",
        echo=True,
        poolclass=NullPool,
        future=True
    )

# Create session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

# Dependency for FastAPI
async def get_db():
    """Database dependency for FastAPI"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database
async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Close database connection
async def close_db():
    """Close database connection"""
    await engine.dispose()