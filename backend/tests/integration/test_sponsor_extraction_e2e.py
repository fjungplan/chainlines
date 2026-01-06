
import pytest
from app.scraper.orchestration.phase1 import DiscoveryService
from app.scraper.orchestration.phase2 import TeamAssemblyService
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from app.scraper.llm.prompts import ScraperPrompts
from app.scraper.llm.models import SponsorInfo
from app.models.team import TeamEra
from app.models.sponsor import SponsorBrand, SponsorMaster, TeamSponsorLink
from app.services.audit_log_service import AuditLogService
from app.scraper.checkpoint import CheckpointManager
from sqlalchemy import select
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from datetime import date

@pytest.fixture
def real_html_fixture():
    # Content of backend/tests/scraper/fixtures/cyclingflash/team_detail_2024.html
    return """<!-- Simplified fixture representing CyclingFlash team detail -->
<html>

<body>
    <div class="team-header">
        <h1>Team Visma | Lease a Bike (2024)</h1>
    </div>

    <!-- Metadata Table -->
    <table>
        <tr>
            <td>Name</td>
            <td>Team Visma | Lease a Bike</td>
        </tr>
        <tr>
            <td>UCI Code</td>
            <td>TJV</td>
        </tr>
        <tr>
            <td>Category</td>
            <td>WorldTour</td>
        </tr>
        <tr>
            <td>Country</td>
            <td>Netherlands</td> <!-- Using full name to test mapper -->
        </tr>
    </table>

    <div class="container">
        <h3>Sponsors</h3>
        <ul>
            <li><a href="/brands/visma">Visma</a></li>
            <li><a href="/brands/lease-a-bike">Lease a Bike</a></li>
            <li><a href="/brands/cervelo">Cervelo</a></li>
        </ul>
    </div>

    <div class="history">
        <a href="/team/team-jumbo-visma-2023">Previous Season</a>
    </div>
</body>

</html>
"""

@pytest.fixture
def llm_service():
    service = MagicMock()
    # Mock extract_sponsors_from_name to return high confidence result
    # It needs to return a Coroutine that resolves to the result
    async def side_effect(*args, **kwargs):
        return  MagicMock(
            sponsors=[
                SponsorInfo(brand_name="Visma", parent_company="Visma Group"),
                SponsorInfo(brand_name="Lease a Bike", parent_company="Pon Holdings")
            ],
            confidence=0.95
        )
    service.extract_sponsors_from_name = AsyncMock(side_effect=side_effect)
    
    # Mock the internal call method usually used by prompts
    service.call = AsyncMock() 
    return service

@pytest.fixture
def failing_llm_service():
    service = MagicMock()
    # Simulate failure
    service.extract_sponsors_from_name = AsyncMock(side_effect=Exception("LLM API Error"))
    # Also fail generic calls
    service.call = AsyncMock(side_effect=Exception("LLM API Error"))
    return service

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_sponsor_extraction_pipeline(
    db_session,
    llm_service,
    real_html_fixture
):
    """Test complete flow: scrape → extract → assemble → verify DB."""
    # Setup: Initialize services
    scraper = CyclingFlashScraper()
    
    # Mock LLM Prompts that relies on the llm_service
    llm_prompts = ScraperPrompts(llm_service=llm_service)
    # We need to mock the extract_sponsors_from_name method on llm_prompts directly
    # because DiscoveryService calls it.
    # Actually, ScraperPrompts.extract_sponsors_from_name calls llm.something.
    # But for easier testing, let's mock the method on llm_prompts if possible,
    # OR rely on llm_service mock if ScraperPrompts delegates to it.
    # Looking at phase1.py, it calls: await self._llm_prompts.extract_sponsors_from_name(...)
    # So we should mock that method on the instance.
    
    # However, ScraperPrompts init takes llm. Let's assume ScraperPrompts is a real object
    # and we mock its dependencies, or mock ScraperPrompts entirely.
    # The prompt passes `llm_prompts=ScraperPrompts(llm=llm_service)`.
    # Let's mock the method on the real object to control return value easily.
    
    llm_prompts.extract_sponsors_from_name = AsyncMock(return_value=MagicMock(
        sponsors=[
            SponsorInfo(brand_name="Visma", parent_company="Visma Group"),
            SponsorInfo(brand_name="Lease a Bike", parent_company="Pon Holdings")
        ],
        confidence=0.95
    ))

    discovery = DiscoveryService(
        scraper=scraper,
        checkpoint_manager=MagicMock(spec=CheckpointManager),
        session=db_session,
        llm_prompts=llm_prompts,
    )
    
    audit_service = MagicMock(spec=AuditLogService)
    assembly = TeamAssemblyService(
        audit_service=audit_service,
        session=db_session,
        system_user_id=uuid4()
    )
    
    # Phase 1: Scrape and extract
    # Use _parser directly as per findings
    team_data = scraper._parser.parse_team_detail(real_html_fixture, season_year=2024)
    
    sponsors, confidence = await discovery._extract_sponsors(
        team_name=team_data.name,
        country_code=team_data.country_code,
        season_year=2024
    )
    
    # Update team data with extracted sponsors
    team_data = team_data.model_copy(update={"sponsors": sponsors})
    
    # Phase 2: Assemble and store
    team_era = await assembly.assemble_team(team_data)
    await db_session.commit()
    
    # Verify: Check database state
    stmt = select(TeamEra).where(TeamEra.registered_name == team_data.name)
    result = await db_session.execute(stmt)
    stored_era = result.scalar_one()
    
    # Needs refresh to load relationships if not eager loaded
    await db_session.refresh(stored_era, attribute_names=["sponsor_links"])
    
    assert stored_era is not None
    assert len(stored_era.sponsor_links) > 0
    
    # Verify sponsors were created
    sponsor_names = [s.brand_name for s in sponsors]
    stored_brands = []
    
    for link in stored_era.sponsor_links:
        await db_session.refresh(link, attribute_names=["brand"])
        assert link.brand is not None
        stored_brands.append(link.brand.brand_name)
        assert link.brand.brand_name in sponsor_names
        
        # Verify parent companies if provided (Visma Group case)
        if link.brand.brand_name == "Visma":
            await db_session.refresh(link.brand, attribute_names=["master"])
            assert link.brand.master is not None
            assert link.brand.master.legal_name == "Visma Group"

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sponsor_extraction_with_cache_hit(db_session, llm_service):
    """Test extraction uses cached sponsors from previous run."""
    # Setup: Create team with sponsors in DB using ORM models
    master = SponsorMaster(legal_name="Test Master")
    brand = SponsorBrand(master=master, brand_name="Test Brand", default_hex_color="#000000")
    
    # Need to create node first for era
    from app.models.team import TeamNode
    node = TeamNode(legal_name="Test Brand Team", founding_year=2020)
    db_session.add(node)
    
    db_session.add_all([master, brand])
    await db_session.commit()
    await db_session.refresh(node)
    
    # No need for full Era setup for brand matching cache, just the BrandMatcher needs to find it.
    # BrandMatcher.check_team_name uses TeamEra query.
    team_era = TeamEra(
        node_id=node.node_id,
        registered_name="Test Brand Team",
        season_year=2024,
        valid_from=date(2024, 1, 1),
        uci_code="TST",
        tier_level=1
    )
    db_session.add(team_era)
    await db_session.commit()
    
    link = TeamSponsorLink(era=team_era, brand=brand, prominence_percent=100, rank_order=1)
    db_session.add(link)
    await db_session.commit()
    
    # Run extraction
    llm_prompts = ScraperPrompts(llm_service=llm_service)
    # Ensure LLM is NOT called
    llm_prompts.extract_sponsors_from_name = AsyncMock() 

    discovery = DiscoveryService(
        scraper=CyclingFlashScraper(),
        checkpoint_manager=MagicMock(spec=CheckpointManager),
        session=db_session,
        llm_prompts=llm_prompts
    )
    
    sponsors, confidence = await discovery._extract_sponsors(
        team_name="Test Brand Team",
        country_code="USA",
        season_year=2025
    )
    
    # Verify cache was used
    assert confidence == 1.0
    assert len(sponsors) == 1
    assert sponsors[0].brand_name == "Test Brand"
    # Note: BrandMatcher currently returns SponsorInfo(brand_name=..., parent_company=None) usually,
    # unless it fetches parent company too. 
    # Let's check BrandMatcher implementation if it fetches parent.
    # Assuming it does or we check what is returned.
    # If the prompts imply it returns parent company, verify it.
    
    # Verify LLM was NOT called (cache hit)
    assert llm_prompts.extract_sponsors_from_name.call_count == 0

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sponsor_extraction_llm_fallback_creates_low_confidence(
    db_session,
    failing_llm_service
):
    """Test fallback to pattern extraction creates low confidence record."""
    # Setup failing prompts
    llm_prompts = ScraperPrompts(llm_service=failing_llm_service)
    llm_prompts.extract_sponsors_from_name = AsyncMock(side_effect=Exception("LLM Fail"))

    discovery = DiscoveryService(
        scraper=CyclingFlashScraper(),
        checkpoint_manager=MagicMock(spec=CheckpointManager),
        session=db_session,
        llm_prompts=llm_prompts
    )
    
    sponsors, confidence = await discovery._extract_sponsors(
        team_name="Unknown New Sponsor Team",
        country_code="USA",
        season_year=2024
    )
    
    # Verify fallback was used
    assert sponsors is not None
    # "Unknown New Sponsor Team" -> expects extraction to find something or at least safe fallback
    # The utils.sponsor_extractor should extract something.
    assert len(sponsors) > 0
    assert confidence < 0.5  # Low confidence from pattern fallback
