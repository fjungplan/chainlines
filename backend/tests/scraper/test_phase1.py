"""Test Phase 1 Discovery orchestration."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.scraper.llm.models import SponsorInfo

def test_sponsor_collector_extracts_unique():
    """SponsorCollector should collect unique sponsor names."""
    from app.scraper.orchestration.phase1 import SponsorCollector
    
    collector = SponsorCollector()
    
    collector.add(["Visma", "Lease a Bike"])
    collector.add(["Visma", "Jumbo"])  # Visma duplicate
    
    assert len(collector.get_all()) == 3
    assert "Visma" in collector.get_all()
    assert "Jumbo" in collector.get_all()

@pytest.mark.asyncio
async def test_discovery_service_collects_teams():
    """DiscoveryService should collect team URLs by spidering."""
    from app.scraper.orchestration.phase1 import DiscoveryService
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    mock_scraper = AsyncMock()
    mock_scraper.get_team_list = AsyncMock(return_value=["/team/a", "/team/b"])
    mock_scraper.get_team = AsyncMock(return_value=ScrapedTeamData(
        name="Team A",
        season_year=2024,
        sponsors=[SponsorInfo(brand_name="Sponsor1")],
        previous_season_url=None
    ))
    
    mock_checkpoint = MagicMock()
    mock_checkpoint.load.return_value = None
    
    service = DiscoveryService(
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint
    )
    
    result = await service.discover_teams(start_year=2024, end_year=2024)
    
    assert len(result.team_urls) >= 2
    assert "Sponsor1" in result.sponsor_names

def test_sponsor_resolution_model():
    """SponsorResolution should validate correctly."""
    from app.scraper.orchestration.phase1 import SponsorResolution
    
    resolution = SponsorResolution(
        raw_name="AG2R Prévoyance",
        master_name="AG2R Group",
        brand_name="AG2R Prévoyance",
        hex_color="#004A9C",
        confidence=0.95
    )
    
    assert resolution.master_name == "AG2R Group"
    assert resolution.confidence >= 0.9


@pytest.mark.asyncio
async def test_discovery_service_with_llm_dependencies():
    """DiscoveryService should accept session and llm_prompts parameters."""
    from app.scraper.orchestration.phase1 import DiscoveryService
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    mock_scraper = AsyncMock()
    mock_scraper.get_team_list = AsyncMock(return_value=["/team/a"])
    mock_scraper.get_team = AsyncMock(return_value=ScrapedTeamData(
        name="Lotto Jumbo",
        season_year=2024,
        sponsors=[SponsorInfo(brand_name="Shimano")],
        previous_season_url=None
    ))
    
    mock_checkpoint = MagicMock()
    mock_checkpoint.load.return_value = None
    
    mock_session = AsyncMock()
    mock_llm_prompts = AsyncMock()
    
    # Should not raise - new parameters are optional
    service = DiscoveryService(
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint,
        session=mock_session,
        llm_prompts=mock_llm_prompts
    )
    
    # Verify service has brand matcher if session provided
    assert service._session == mock_session
    assert service._llm_prompts == mock_llm_prompts
    # BrandMatcherService should be initialized when session is provided
    assert service._brand_matcher is not None


@pytest.mark.asyncio
async def test_discovery_service_logs_llm_availability():
    """DiscoveryService should log LLM and brand matcher availability."""
    from app.scraper.orchestration.phase1 import DiscoveryService
    
    mock_scraper = AsyncMock()
    mock_checkpoint = MagicMock()
    mock_checkpoint.load.return_value = None
    
    # Without LLM dependencies
    service_no_llm = DiscoveryService(
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint
    )
    assert service_no_llm._brand_matcher is None
    assert service_no_llm._llm_prompts is None
    
    # With LLM dependencies
    mock_session = AsyncMock()
    mock_llm_prompts = AsyncMock()
    
    service_with_llm = DiscoveryService(
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint,
        session=mock_session,
        llm_prompts=mock_llm_prompts
    )
    assert service_with_llm._brand_matcher is not None
    assert service_with_llm._llm_prompts == mock_llm_prompts

