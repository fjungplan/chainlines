"""End-to-end scraper tests."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

@pytest.mark.asyncio
async def test_full_phase1_flow_mocked(isolated_session):
    """Full Phase 1 flow should discover teams and collect sponsors."""
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.orchestration.phase1 import DiscoveryService
    from app.scraper.checkpoint import CheckpointManager
    from pathlib import Path
    import tempfile
    
    # Mock scraper
    mock_scraper = AsyncMock()
    mock_scraper.get_team_list = AsyncMock(return_value=[
        "/team/team-a-2024",
        "/team/team-b-2024"
    ])
    mock_scraper.get_team = AsyncMock(side_effect=[
        ScrapedTeamData(
            name="Team A",
            season_year=2024,
            sponsors=["Sponsor1", "Sponsor2"],
            previous_season_url=None
        ),
        ScrapedTeamData(
            name="Team B",
            season_year=2024,
            sponsors=["Sponsor2", "Sponsor3"],
            previous_season_url=None
        )
    ])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint = CheckpointManager(Path(tmpdir) / "cp.json")
        
        service = DiscoveryService(
            scraper=mock_scraper,
            checkpoint_manager=checkpoint
        )
        
        result = await service.discover_teams(
            start_year=2024,
            end_year=2024
        )
        
        assert len(result.team_urls) == 2
        assert len(result.sponsor_names) == 3  # Unique sponsors
        assert "Sponsor1" in result.sponsor_names
        assert "Sponsor2" in result.sponsor_names
        assert "Sponsor3" in result.sponsor_names

@pytest.mark.asyncio
async def test_phase2_creates_audit_entries(isolated_session):
    """Phase 2 should create audit log entries."""
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.orchestration.phase2 import TeamAssemblyService
    
    mock_audit = AsyncMock()
    mock_audit.create_edit = AsyncMock(return_value=MagicMock(edit_id=uuid4()))
    
    service = TeamAssemblyService(
        audit_service=mock_audit,
        session=isolated_session,
        system_user_id=uuid4()
    )
    
    team_data = ScrapedTeamData(
        name="Test Team",
        season_year=2024,
        sponsors=["Main Sponsor", "Secondary"],
        tier_level=1
    )
    
    await service.create_team_era(team_data, confidence=0.95)
    
    mock_audit.create_edit.assert_called_once()
    call_args = mock_audit.create_edit.call_args
    assert call_args.kwargs["new_data"]["registered_name"] == "Test Team"
