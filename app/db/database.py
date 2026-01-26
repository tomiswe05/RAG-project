"""
Database connection configuration for PostgreSQL.

This module sets up:
1. Async database engine - manages connection pool to PostgreSQL
2. Session factory - creates database sessions for each request
3. Base class - all our models will inherit from this
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment
# Format: postgresql+asyncpg://username:password@host:port/database_name
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create async engine
# - echo=True prints SQL queries to console (helpful for debugging, disable in production)
# - pool_size=5 means up to 5 connections can be open at once
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=5,
    max_overflow=10  # Allow 10 extra connections during high load
)

# Create session factory
# - expire_on_commit=False means objects stay usable after commit
# - class_=AsyncSession tells it to create async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all models
# All our database models (Conversation, Message) will inherit from this
Base = declarative_base()


async def get_db():
    """
    Dependency function that provides a database session.

    FastAPI will call this for each request that needs database access.
    The 'yield' makes this a generator - it gives the session to the route,
    waits for the route to finish, then closes the session.

    Usage in a route:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # use db here
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Create all tables in the database.

    This is called once when the app starts to ensure tables exist.
    In production, you'd use migrations (like Alembic) instead.
    """
    async with engine.begin() as conn:
        # Import models here to ensure they're registered with Base
        from . import models  # noqa
        await conn.run_sync(Base.metadata.create_all)
