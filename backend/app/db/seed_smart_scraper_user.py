"""Seed script for Smart Scraper system user."""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.enums import UserRole

# Fixed UUID for reproducibility across environments
SMART_SCRAPER_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

async def seed_smart_scraper_user(session: AsyncSession) -> User:
    """Create or retrieve the Smart Scraper system user."""
    result = await session.execute(
        select(User).where(User.user_id == SMART_SCRAPER_USER_ID)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return existing
    
    user = User(
        user_id=SMART_SCRAPER_USER_ID,
        google_id="system_smart_scraper",
        display_name="smart_scraper",
        email="system@chainlines.local",
        role=UserRole.ADMIN,  # Needs admin to create edits
    )
    session.add(user)
    return user
