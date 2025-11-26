"""
Pytest configuration and fixtures.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import AsyncGenerator
from main import app
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async test HTTP client for the FastAPI app (starts lifespan)."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def isolated_engine():
    """Provide a fresh async engine per test to avoid connection contention."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def isolated_session(isolated_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated session bound to a fresh engine for DB tests."""
    maker = async_sessionmaker(isolated_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session
