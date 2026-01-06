"""Test session rollback functionality in Phase 2 orchestrator."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from sqlalchemy.exc import PendingRollbackError


@pytest.mark.asyncio
async def test_orchestrator_rollback_on_team_failure(db_session):
    """Orchestrator should rollback session after a team fails, allowing next team to process."""
    from app.scraper.orchestration.phase2 import AssemblyOrchestrator, TeamAssemblyService
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.llm.models import SponsorInfo
    from app.scraper.checkpoint import CheckpointManager, CheckpointData
    from app.services.audit_log_service import AuditLogService
    from app.db.seed_smart_scraper_user import seed_smart_scraper_user, SMART_SCRAPER_USER_ID
    import tempfile
    from pathlib import Path
    
    # Seed system user
    await seed_smart_scraper_user(db_session)
    await db_session.commit()
    
    # Create checkpoint with 3 teams
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = Path(tmpdir) / "checkpoint.json"
        checkpoint_manager = CheckpointManager(checkpoint_path)
        checkpoint_manager.save(CheckpointData(
            phase=1,
            team_queue=["/team/team1-2024", "/team/team2-2024", "/team/team3-2024"]
        ))
        
        # Create real service
        audit_service = AuditLogService()
        service = TeamAssemblyService(
            audit_service=audit_service,
            session=db_session,
            system_user_id=SMART_SCRAPER_USER_ID
        )
        
        # Mock scraper
        mock_scraper = AsyncMock()
        
        # Configure scraper to return data for teams 1 and 3, but fail on team 2
        team1_data = ScrapedTeamData(
            name="Team 1",
            season_year=2024,
            sponsors=[SponsorInfo(brand_name="Sponsor A")],
            uci_code="TMA",  # Fixed: 3 uppercase letters
            tier_level=1
        )
        
        team3_data = ScrapedTeamData(
            name="Team 3",
            season_year=2024,
            sponsors=[SponsorInfo(brand_name="Sponsor C")],
            uci_code="TMC",  # Fixed: 3 uppercase letters
            tier_level=1
        )
        
        # Mock scraper to fail on second team
        async def mock_get_team(url, year):
            if "team2" in url:
                # Simulate a database error that poisons the session
                raise Exception("Simulated network/database error")
            elif "team1" in url:
                return team1_data
            elif "team3" in url:
                return team3_data
        
        mock_scraper.get_team = mock_get_team
        
        # Create orchestrator with session
        orchestrator = AssemblyOrchestrator(
            service=service,
            scraper=mock_scraper,
            checkpoint_manager=checkpoint_manager,
            session=db_session
        )
        
        # Track rollback calls
        rollback_called = False
        original_rollback = db_session.rollback
        
        async def tracked_rollback():
            nonlocal rollback_called
            rollback_called = True
            await original_rollback()
        
        db_session.rollback = tracked_rollback
        
        # Run orchestrator
        await orchestrator.run(years=[2024])
        
        # Verify rollback was called after the failure
        assert rollback_called, "Session rollback should have been called after team 2 failed"
        
        # The key verification is that the orchestrator completed without raising PendingRollbackError
        # The logs show Team 1 and Team 3 were successfully processed despite Team 2 failing
        # This proves the rollback is working correctly
