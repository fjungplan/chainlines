import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.services.brand_matcher import BrandMatcherService
from app.models.team import TeamNode, TeamEra
from app.models.sponsor import SponsorBrand, SponsorMaster, TeamSponsorLink
from app.scraper.llm.models import SponsorInfo

@pytest.mark.asyncio
async def test_team_name_cache_hit(db_session: AsyncSession):
    """Test team name cache returns existing sponsors when found."""
    # Setup: Create team era with sponsors in DB
    master = SponsorMaster(legal_name="Test Master")
    brand1 = SponsorBrand(master=master, brand_name="Lotto", default_hex_color="#FF0000")
    brand2 = SponsorBrand(master=master, brand_name="Jumbo", default_hex_color="#FFFF00")
    
    node = TeamNode(legal_name="Lotto Jumbo Team node", founding_year=2020)
    team_era = TeamEra(
        node=node,
        season_year=2024,
        valid_from=date(2024, 1, 1),
        registered_name="Lotto Jumbo Team"
    )
    
    link1 = TeamSponsorLink(era=team_era, brand=brand1, rank_order=1, prominence_percent=50)
    link2 = TeamSponsorLink(era=team_era, brand=brand2, rank_order=2, prominence_percent=50)
    
    db_session.add_all([master, brand1, brand2, node, team_era, link1, link2])
    await db_session.commit()
    
    # Test
    matcher = BrandMatcherService(db_session)
    result = await matcher.check_team_name("Lotto Jumbo Team")
    
    # Assert
    assert result is not None
    assert len(result) == 2
    # Sponsors from DB might be in any order unless we explicitly sort, 
    # but the service just loops over era.sponsor_links.
    # In TeamEra.sponsors_ordered property it's sorted by rank_order.
    # The service implementation uses team_era.sponsor_links.
    
    brand_names = {s.brand_name for s in result}
    assert "Lotto" in brand_names
    assert "Jumbo" in brand_names
    assert all(s.parent_company == "Test Master" for s in result)

@pytest.mark.asyncio
async def test_team_name_cache_miss(db_session: AsyncSession):
    """Test returns None when team name not found."""
    matcher = BrandMatcherService(db_session)
    result = await matcher.check_team_name("Unknown Team")
    assert result is None

@pytest.mark.asyncio
async def test_team_name_cache_in_memory(db_session: AsyncSession):
    """Test in-memory cache works across multiple calls."""
    # Setup: Create team era with sponsors in DB
    master = SponsorMaster(legal_name="Test Master")
    brand = SponsorBrand(master=master, brand_name="Lotto", default_hex_color="#FF0000")
    node = TeamNode(legal_name="Lotto node", founding_year=2020)
    team_era = TeamEra(
        node=node,
        season_year=2024,
        valid_from=date(2024, 1, 1),
        registered_name="Lotto Team"
    )
    link = TeamSponsorLink(era=team_era, brand=brand, rank_order=1, prominence_percent=100)
    
    db_session.add_all([master, brand, node, team_era, link])
    await db_session.commit()
    
    matcher = BrandMatcherService(db_session)
    
    # First call: DB query (should populate in-memory cache)
    result1 = await matcher.check_team_name("Lotto Team")
    assert result1 is not None
    
    # Second call: Should hit in-memory cache
    # We can verify this by checking if result1 and result2 are the same object 
    # (if the implementation returns the cached list directly)
    result2 = await matcher.check_team_name("Lotto Team")
    
    assert result1 == result2
    assert result1 is result2 # Identity check for in-memory cache
