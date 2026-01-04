"""Test that Smart Scraper system user exists after seeding."""
import pytest
from uuid import UUID
from sqlalchemy import select
from app.models.user import User

SMART_SCRAPER_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest.mark.asyncio
async def test_smart_scraper_user_exists(isolated_session):
    """After seeding, the Smart Scraper user should exist."""
    from app.db.seed_smart_scraper_user import seed_smart_scraper_user
    
    await seed_smart_scraper_user(isolated_session)
    await isolated_session.commit()
    
    result = await isolated_session.execute(
        select(User).where(User.user_id == SMART_SCRAPER_USER_ID)
    )
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.display_name == "smart_scraper"
    assert user.google_id == "system_smart_scraper"
    assert user.email == "system@chainlines.local"
