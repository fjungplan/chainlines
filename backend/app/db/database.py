"""Database configuration and session management for async SQLAlchemy."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.db.base import Base  # Unified Base import so metadata matches models

# Create async engine (single shared engine for application)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory bound to the unified Base metadata
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency yielding a database session."""
    async with async_session_maker() as session:
        yield session


async def create_tables():
    """Create tables from model metadata (only useful before migrations exist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> bool:
    """Return True if a simple query succeeds, else False."""
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
