"""Test Phase 2 Team Assembly orchestration."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.scraper.llm.models import SponsorInfo


def test_prominence_calculator_one_sponsor():
    """One sponsor should get 100%."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["Visma"])
    assert result == [100]


def test_prominence_calculator_two_sponsors():
    """Two sponsors should get 60/40."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["Visma", "Lease a Bike"])
    assert result == [60, 40]


def test_prominence_calculator_three_sponsors():
    """Three sponsors should get 40/30/30."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["A", "B", "C"])
    assert result == [40, 30, 30]


def test_prominence_calculator_four_sponsors():
    """Four sponsors should get 40/20/20/20."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["A", "B", "C", "D"])
    assert result == [40, 20, 20, 20]


def test_prominence_calculator_five_sponsors():
    """Five+ sponsors: LLM pattern extension (sum=100)."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["A", "B", "C", "D", "E"])
    assert sum(result) == 100
    assert result[0] >= result[-1]  # First should be highest


@pytest.mark.asyncio
async def test_team_assembly_creates_edit():
    """TeamAssemblyService should create edits via AuditLog."""
    from app.scraper.orchestration.phase2 import TeamAssemblyService
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    mock_audit = AsyncMock()
    mock_audit.create_edit = AsyncMock(return_value=MagicMock(edit_id=uuid4()))
    
    mock_session = AsyncMock()
    
    service = TeamAssemblyService(
        audit_service=mock_audit,
        session=mock_session,
        system_user_id=uuid4()
    )
    
    team_data = ScrapedTeamData(
        name="Team Visma",
        season_year=2024,
        sponsors=[
            SponsorInfo(brand_name="Visma"),
            SponsorInfo(brand_name="Lease a Bike")
        ],
        uci_code="TJV",
        tier_level=1
    )
    
    await service.create_team_era(team_data, confidence=0.95)
    
    mock_audit.create_edit.assert_called_once()


@pytest.mark.asyncio
async def test_assembly_creates_sponsor_with_parent(db_session):
    """Test Phase 2 creates sponsor brand with parent company."""
    from unittest.mock import AsyncMock
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.orchestration.phase2 import TeamAssemblyService
    
    audit_service = AsyncMock()
    
    # Needs to match ScrapedTeamData structure
    team_data = ScrapedTeamData(
        name="Ineos Grenadiers",
        sponsors=[
            SponsorInfo(
                brand_name="Ineos Grenadier",
                parent_company="INEOS Group"
            )
        ],
        tier_level=1,
        uci_code="IGD", # Added required field
        country_code="GBR",
        season_year=2024
    )
    
    # We need a user ID for the service
    from app.db.seed_smart_scraper_user import SMART_SCRAPER_USER_ID
    
    assembly_service = TeamAssemblyService(session=db_session, audit_service=audit_service, system_user_id=SMART_SCRAPER_USER_ID)
    team_era = await assembly_service.assemble_team(team_data)
    
    # Re-fetch with eager loading to avoid MissingGreenlet error
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    from app.models.team import TeamEra
    from app.models.sponsor import TeamSponsorLink, SponsorBrand

    stmt = select(TeamEra).options(
        joinedload(TeamEra.sponsor_links).joinedload(TeamSponsorLink.brand).joinedload(SponsorBrand.master)
    ).where(TeamEra.era_id == team_era.era_id)
    result = await db_session.execute(stmt)
    team_era = result.unique().scalar_one()

    # Verify sponsor brand created
    assert len(team_era.sponsor_links) == 1
    assert team_era.sponsor_links[0].brand.brand_name == "Ineos Grenadier"
    
    # Verify parent company created/linked
    assert team_era.sponsor_links[0].brand.master is not None
    assert team_era.sponsor_links[0].brand.master.legal_name == "INEOS Group"

@pytest.mark.asyncio
async def test_assembly_handles_sponsor_without_parent(db_session):
    """Test Phase 2 handles sponsors without parent company."""
    from unittest.mock import AsyncMock
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.orchestration.phase2 import TeamAssemblyService

    audit_service = AsyncMock()

    team_data = ScrapedTeamData(
        name="Bahrain Victorious",
        sponsors=[
            SponsorInfo(brand_name="Bahrain", parent_company=None)
        ],
        tier_level=1,
        uci_code="TBV", # Added required field
        country_code="BHR",
        season_year=2024
    )
    
    
    from app.db.seed_smart_scraper_user import SMART_SCRAPER_USER_ID
    
    assembly_service = TeamAssemblyService(session=db_session, audit_service=audit_service, system_user_id=SMART_SCRAPER_USER_ID)
    team_era = await assembly_service.assemble_team(team_data)
    
    # Re-fetch with eager loading
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    from app.models.team import TeamEra
    from app.models.sponsor import TeamSponsorLink, SponsorBrand

    stmt = select(TeamEra).options(
        joinedload(TeamEra.sponsor_links).joinedload(TeamSponsorLink.brand).joinedload(SponsorBrand.master)
    ).where(TeamEra.era_id == team_era.era_id)
    result = await db_session.execute(stmt)
    team_era = result.unique().scalar_one()

    # Verify sponsor created without parent
    assert len(team_era.sponsor_links) == 1
    assert team_era.sponsor_links[0].brand.brand_name == "Bahrain"
    # Logic Update: Since master_id is NOT NULL, we create a self-master for brands without parents
    assert team_era.sponsor_links[0].brand.master is not None
    assert team_era.sponsor_links[0].brand.master.legal_name == "Bahrain"


# -- New Tests for Slice C2.1 (Workers Integration) --

@pytest.mark.asyncio
async def test_orchestrator_calls_wikidata_resolver():
    """AssemblyOrchestrator should call WikidataResolver with team name."""
    from app.scraper.orchestration.phase2 import AssemblyOrchestrator
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.services.wikidata import WikidataResult
    
    # Mock dependencies
    mock_service = AsyncMock()
    mock_scraper = AsyncMock()
    mock_checkpoint = MagicMock()
    mock_resolver = AsyncMock()
    
    # Mock resolver to return a WikidataResult
    mock_resolver.resolve.return_value = WikidataResult(
        qid="Q12345",
        label="Test Team",
        sitelinks={"en": "https://en.wikipedia.org/wiki/Test_Team"}
    )
    
    orchestrator = AssemblyOrchestrator(
        service=mock_service,
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint,
        wikidata_resolver=mock_resolver,
        workers=[]
    )
    
    base_data = ScrapedTeamData(
        name="Test Team",
        season_year=2024,
        sponsors=[],
        tier_level=1,
        uci_code="TST"
    )
    
    # Call the enrichment method
    enriched = await orchestrator._enrich_team(base_data)
    
    # Verify resolver was called with team name
    mock_resolver.resolve.assert_called_once_with("Test Team")
    assert enriched.wikidata_result is not None
    assert enriched.wikidata_result.qid == "Q12345"


@pytest.mark.asyncio
async def test_orchestrator_fans_out_to_workers():
    """AssemblyOrchestrator should call all workers in parallel."""
    from unittest.mock import patch
    from app.scraper.orchestration.phase2 import AssemblyOrchestrator
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.services.wikidata import WikidataResult
    from app.scraper.orchestration.workers import SourceData
    
    # Mock dependencies
    mock_service = AsyncMock()
    mock_scraper = AsyncMock()
    mock_checkpoint = MagicMock()
    mock_resolver = AsyncMock()
    
    # Mock resolver with sitelinks for all workers
    mock_resolver.resolve.return_value = WikidataResult(
        qid="Q12345",
        label="Test Team",
        sitelinks={
            "en": "https://en.wikipedia.org/wiki/Test_Team",
            "fr": "https://fr.wikipedia.org/wiki/Test_Team"
        }
    )
    
    # Create mock workers
    mock_wikipedia_worker = AsyncMock()
    mock_wikipedia_worker.source_name = "wikipedia"
    mock_wikipedia_worker.fetch.return_value = SourceData(
        source="wikipedia",
        history_text="Some history"
    )
    
    mock_memoire_worker = AsyncMock()
    mock_memoire_worker.source_name = "memoire"
    mock_memoire_worker.fetch.return_value = SourceData(
        source="memoire",
        raw_content="<html>...</html>"
    )
    
    workers = [mock_wikipedia_worker, mock_memoire_worker]
    
    orchestrator = AssemblyOrchestrator(
        service=mock_service,
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint,
        wikidata_resolver=mock_resolver,
        workers=workers
    )
    
    base_data = ScrapedTeamData(
        name="Test Team",
        season_year=2024,
        sponsors=[],
        tier_level=1,
        uci_code="TST"
    )
    
    # Patch asyncio.gather to verify parallel execution
    with patch('asyncio.gather', new_callable=AsyncMock) as mock_gather:
        # Configure gather to return worker results
        mock_gather.return_value = [
            SourceData(source="wikipedia", history_text="Some history"),
            SourceData(source="memoire", raw_content="<html>...</html>")
        ]
        
        await orchestrator._enrich_team(base_data)
        
        # Verify asyncio.gather was called (parallel execution)
        mock_gather.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_collects_enriched_data():
    """AssemblyOrchestrator should collect results into EnrichedTeamData."""
    from app.scraper.orchestration.phase2 import AssemblyOrchestrator
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.services.wikidata import WikidataResult
    from app.scraper.orchestration.workers import SourceData
    
    # Mock dependencies
    mock_service = AsyncMock()
    mock_scraper = AsyncMock()
    mock_checkpoint = MagicMock()
    mock_resolver = AsyncMock()
    
    # Mock resolver
    mock_resolver.resolve.return_value = WikidataResult(
        qid="Q12345",
        label="Test Team",
        sitelinks={
            "en": "https://en.wikipedia.org/wiki/Test_Team",
            "fr": "https://fr.wikipedia.org/wiki/Test_Team"
        }
    )
    
    # Create mock workers with specific return values
    # Note: CyclingRanking URL resolution not yet implemented, so test with Wikipedia and Memoire
    mock_wikipedia_worker = AsyncMock()
    mock_wikipedia_worker.source_name = "wikipedia"
    mock_wikipedia_worker.fetch.return_value = SourceData(
        source="wikipedia",
        history_text="Team was founded in 1980",
        founded_year=1980
    )
    
    mock_memoire_worker = AsyncMock()
    mock_memoire_worker.source_name = "memoire"
    mock_memoire_worker.fetch.return_value = SourceData(
        source="memoire",
        raw_content="<html>Archive content</html>"
    )
    
    workers = [mock_wikipedia_worker, mock_memoire_worker]
    
    orchestrator = AssemblyOrchestrator(
        service=mock_service,
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint,
        wikidata_resolver=mock_resolver,
        workers=workers
    )
    
    base_data = ScrapedTeamData(
        name="Test Team",
        season_year=2024,
        sponsors=[SponsorInfo(brand_name="TestSponsor")],
        tier_level=1,
        uci_code="TST"
    )
    
    # Call enrichment
    enriched = await orchestrator._enrich_team(base_data)
    
    # Verify EnrichedTeamData structure
    assert enriched.base_data.name == "Test Team"
    assert enriched.wikidata_result is not None
    assert enriched.wikidata_result.qid == "Q12345"
    assert enriched.wikipedia_data is not None
    assert enriched.wikipedia_data.history_text == "Team was founded in 1980"
    assert enriched.memoire_data is not None
    assert enriched.memoire_data.raw_content == "<html>Archive content</html>"
