"""Tests for TeamNode matching by team_identity_id."""
import pytest
from sqlalchemy import select
from app.models.team import TeamNode, TeamEra


@pytest.mark.asyncio
async def test_node_matching_by_identity_id(db_session):
    """Team with same identity_id should reuse node across years."""
    from app.scraper.orchestration.phase2 import TeamAssemblyService
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.llm.models import SponsorInfo
    from app.services.audit_log_service import AuditLogService
    from app.db.seed_smart_scraper_user import seed_smart_scraper_user, SMART_SCRAPER_USER_ID
    
    # Seed system user
    await seed_smart_scraper_user(db_session)
    await db_session.commit()
    
    service = TeamAssemblyService(
        audit_service=AuditLogService(),
        session=db_session,
        system_user_id=SMART_SCRAPER_USER_ID
    )
    
    # Year 1: Create "Alpecin - Deceuninck"
    data_2025 = ScrapedTeamData(
        name="Alpecin - Deceuninck",
        season_year=2025,
        team_identity_id="abc123",  # Same identity
        sponsors=[],
        uci_code="ADC",
        tier_level=1
    )
    era_2025 = await service.assemble_team(data_2025)
    await db_session.commit()
    
    # Year 2: Create "Alpecin - Premier Tech" (name change)
    data_2026 = ScrapedTeamData(
        name="Alpecin - Premier Tech",
        season_year=2026,
        team_identity_id="abc123",  # Same identity!
        sponsors=[],
        uci_code="APT",
        tier_level=1
    )
    era_2026 = await service.assemble_team(data_2026)
    await db_session.commit()
    
    # Verify: Should be 1 node with 2 eras
    result = await db_session.execute(select(TeamNode))
    nodes = result.scalars().all()
    
    assert len(nodes) == 1, f"Expected 1 node, got {len(nodes)}"
    assert nodes[0].external_ids is not None
    assert nodes[0].external_ids.get("cyclingflash_identity") == "abc123"
    
    # Verify 2 eras on the same node
    era_result = await db_session.execute(
        select(TeamEra).where(TeamEra.node_id == nodes[0].node_id)
    )
    eras = era_result.scalars().all()
    assert len(eras) == 2, f"Expected 2 eras, got {len(eras)}"


@pytest.mark.asyncio
async def test_node_matching_without_identity_falls_back_to_name(db_session):
    """Teams without identity_id should fall back to legal_name matching."""
    from app.scraper.orchestration.phase2 import TeamAssemblyService
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.services.audit_log_service import AuditLogService
    from app.db.seed_smart_scraper_user import seed_smart_scraper_user, SMART_SCRAPER_USER_ID
    
    # Seed system user
    await seed_smart_scraper_user(db_session)
    await db_session.commit()
    
    service = TeamAssemblyService(
        audit_service=AuditLogService(),
        session=db_session,
        system_user_id=SMART_SCRAPER_USER_ID
    )
    
    # Create team without identity
    data_2025 = ScrapedTeamData(
        name="Test Team",
        season_year=2025,
        team_identity_id=None,  # No identity
        sponsors=[],
        uci_code="TST",
        tier_level=1
    )
    await service.assemble_team(data_2025)
    await db_session.commit()
    
    # Create same-named team again
    data_2026 = ScrapedTeamData(
        name="Test Team",
        season_year=2026,
        team_identity_id=None,  # No identity
        sponsors=[],
        uci_code="TST",
        tier_level=1
    )
    await service.assemble_team(data_2026)
    await db_session.commit()
    
    # Verify: Should still be 1 node (matched by name)
    result = await db_session.execute(select(TeamNode))
    nodes = result.scalars().all()
    
    assert len(nodes) == 1, f"Expected 1 node, got {len(nodes)}"
