"""Test Phase 1 Discovery orchestration."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.scraper.llm.models import SponsorInfo, SponsorExtractionResult, BrandMatchResult

@pytest.fixture
def mock_llm():
    return AsyncMock()

@pytest.fixture
def discovery_service_with_llm(mock_llm):
    from app.scraper.orchestration.phase1 import DiscoveryService
    
    mock_scraper = AsyncMock()
    mock_checkpoint = MagicMock()
    mock_session = AsyncMock()
    
    service = DiscoveryService(
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint,
        session=mock_session,
        llm_prompts=mock_llm
    )
    # Mock the brand matcher since it's created internally
    service._brand_matcher = AsyncMock()
    return service

@pytest.fixture
def discovery_service_no_llm():
    from app.scraper.orchestration.phase1 import DiscoveryService
    
    mock_scraper = AsyncMock()
    mock_checkpoint = MagicMock()
    
    return DiscoveryService(
        scraper=mock_scraper,
        checkpoint_manager=mock_checkpoint
    )

@pytest.fixture
def db_session():
    return AsyncMock()

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

# -- New Tests for Slice 4.2 --

@pytest.mark.asyncio
async def test_extract_sponsors_cache_hit(discovery_service_with_llm, db_session):
    """Test extraction uses cached sponsors when team name found."""
    # Setup: Mock cache hit (exact team name match)
    cached_sponsors = [SponsorInfo(brand_name="Lotto"), SponsorInfo(brand_name="Jumbo")]
    discovery_service_with_llm._brand_matcher.check_team_name.return_value = cached_sponsors
    
    sponsors, confidence = await discovery_service_with_llm._extract_sponsors(
        team_name="Lotto Jumbo Team",
        country_code="NED",
        season_year=2024
    )
    
    assert len(sponsors) == 2
    assert confidence == 1.0  # Cache hit = full confidence
    discovery_service_with_llm._brand_matcher.check_team_name.assert_called_once_with("Lotto Jumbo Team")

@pytest.mark.asyncio
async def test_extract_sponsors_all_known_brands(discovery_service_with_llm, db_session):
    """Test extraction skips LLM when all words are known brands."""
    # Setup: Mock cache miss but full brand coverage
    discovery_service_with_llm._brand_matcher.check_team_name.return_value = None
    discovery_service_with_llm._brand_matcher.analyze_words.return_value = BrandMatchResult(
        known_brands=["Lotto", "Jumbo"],
        unmatched_words=[],
        needs_llm=False
    )
    
    sponsors, confidence = await discovery_service_with_llm._extract_sponsors(
        team_name="Lotto Jumbo",
        country_code="NED",
        season_year=2024
    )
    
    assert len(sponsors) == 2
    assert confidence == 1.0  # All known = full confidence
    # Verify LLM was NOT called
    discovery_service_with_llm._llm_prompts.extract_sponsors_from_name.assert_not_called()

@pytest.mark.asyncio
async def test_extract_sponsors_llm_call(discovery_service_with_llm, mock_llm):
    """Test extraction calls LLM for unknown words."""
    # Setup: Mock cache miss and partial coverage
    discovery_service_with_llm._brand_matcher.check_team_name.return_value = None
    discovery_service_with_llm._brand_matcher.analyze_words.return_value = BrandMatchResult(
        known_brands=["Lotto"],
        unmatched_words=["Jumbo"],
        needs_llm=True
    )
    
    # Mock LLM response
    mock_llm.extract_sponsors_from_name.return_value = SponsorExtractionResult(
        sponsors=[SponsorInfo(brand_name="Lotto"), SponsorInfo(brand_name="Jumbo")],
        confidence=0.95,
        reasoning="Extracted both brands"
    )
    
    sponsors, confidence = await discovery_service_with_llm._extract_sponsors(
        team_name="Lotto Jumbo",
        country_code="NED",
        season_year=2016
    )
    
    assert len(sponsors) == 2
    assert sponsors[0].brand_name == "Lotto"
    assert confidence == 0.95
    # Verify LLM WAS called
    mock_llm.extract_sponsors_from_name.assert_called_once()

@pytest.mark.asyncio
async def test_extract_sponsors_fallback(discovery_service_no_llm):
    """Test extraction falls back to pattern matching without LLM."""
    # Service without LLM initialized
    sponsors, confidence = await discovery_service_no_llm._extract_sponsors(
        team_name="Lotto Jumbo Team",
        country_code="NED",
        season_year=2024
    )
    
    # Should use simple pattern extraction
    assert len(sponsors) > 0
    assert confidence < 1.0  # Fallback has lower confidence

@pytest.mark.asyncio
async def test_discover_teams_extracts_sponsors(discovery_service_with_llm, mock_llm, db_session):
    """Test discovery loop extracts sponsors via LLM."""
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    # Setup: Mock scraper to return team data
    mock_team_data = ScrapedTeamData(
        name="Lotto Jumbo Team",
        uci_code="LOT",
        tier_level=1,
        country_code="NED",
        sponsors=[SponsorInfo(brand_name="Shimano")],  # Equipment sponsor from parser
        season_year=2024,
        previous_season_url=None
    )
    
    # Configure mock scraper on the fixture
    discovery_service_with_llm._scraper.get_team_list_by_tier.return_value = ["/team/lotto-jumbo"]
    discovery_service_with_llm._scraper.get_team.return_value = mock_team_data
    
    # Setup brand matcher mock (part of discovery_service_with_llm fixture)
    discovery_service_with_llm._brand_matcher.check_team_name.return_value = None
    discovery_service_with_llm._brand_matcher.analyze_words.return_value.needs_llm = True
    
    # Mock LLM to add title sponsors
    mock_llm.extract_sponsors_from_name.return_value = SponsorExtractionResult(
        sponsors=[
            SponsorInfo(brand_name="Lotto"),
            SponsorInfo(brand_name="Jumbo")
        ],
        confidence=0.95,
        reasoning="..."
    )
    
    # Run discovery
    await discovery_service_with_llm.discover_teams(start_year=2024, end_year=2024, tier_level=1)
    
    # Verify sponsors were extracted from team name
    mock_llm.extract_sponsors_from_name.assert_called()
    
    # Verify collector has merged sponsors (Lotto, Jumbo, Shimano)
    collected_names = discovery_service_with_llm._collector.get_all()
    assert "Lotto" in collected_names
    assert "Jumbo" in collected_names
    assert "Shimano" in collected_names

# -- New Tests for Slice 6.1 --

@pytest.mark.asyncio
async def test_retry_queue_adds_failed_teams(discovery_service_with_llm, mock_llm):
    """Test failed LLM extractions are added to retry queue."""
    # Mock cache and brand matcher to pass through to LLM
    discovery_service_with_llm._brand_matcher.check_team_name.return_value = None
    discovery_service_with_llm._brand_matcher.analyze_words.return_value = BrandMatchResult(
        known_brands=[],
        unmatched_words=["Test", "Team"],
        needs_llm=True
    )
    
    # Mock LLM to fail
    mock_llm.extract_sponsors_from_name.side_effect = Exception("LLM service unavailable")
    
    sponsors, confidence = await discovery_service_with_llm._extract_sponsors(
        team_name="Test Team",
        country_code="USA",
        season_year=2024
    )
    
    # Should fallback to pattern extraction
    assert len(sponsors) > 0
    assert confidence < 1.0
    
    # Should be in retry queue
    assert len(discovery_service_with_llm._retry_queue) == 1
    assert discovery_service_with_llm._retry_queue[0][0] == "Test Team"

@pytest.mark.asyncio
async def test_process_retry_queue(discovery_service_with_llm, mock_llm):
    """Test retry queue is processed at end of year."""
    # Add items to retry queue
    discovery_service_with_llm._retry_queue.append(("Team 1", {
        "country_code": "USA",
        "season_year": 2024,
        "partial_matches": []
    }))
    discovery_service_with_llm._retry_queue.append(("Team 2", {
        "country_code": "GBR",
        "season_year": 2024,
        "partial_matches": []
    }))
    
    # Mock brand matcher for retries
    discovery_service_with_llm._brand_matcher.check_team_name.return_value = None
    discovery_service_with_llm._brand_matcher.analyze_words.return_value = BrandMatchResult(
        known_brands=[],
        unmatched_words=["Team"],
        needs_llm=True
    )
    
    # Mock LLM to succeed on retry
    mock_llm.extract_sponsors_from_name.return_value = SponsorExtractionResult(
        sponsors=[SponsorInfo(brand_name="Test Sponsor")],
        confidence=0.95,
        reasoning="Extracted successfully on retry"
    )
    
    # Process retry queue
    await discovery_service_with_llm._process_retry_queue()
    
    # Verify LLM was called for each queued item
    assert mock_llm.extract_sponsors_from_name.call_count == 2
    
    # Verify queue is cleared
    assert len(discovery_service_with_llm._retry_queue) == 0

