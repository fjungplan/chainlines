"""Tests for split event functionality."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models.edit import EditHistory
from app.models.enums import LineageEventType, EditAction, EditStatus
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_create_split_basic(async_session, test_user_trusted, sample_teams):
    """Test basic split with 2 resulting teams."""
    from app.services.edit_service import EditService
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    from app.models.team import TeamNode
    from app.models.lineage import LineageEvent
    
    # Get source team
    source_team = sample_teams[0]
    
    request = SplitEventRequest(
        source_node_id=str(source_team.node_id),
        split_year=2020,
        new_teams=[
            NewTeamInfo(name="Team A", tier=1),
            NewTeamInfo(name="Team B", tier=2)
        ],
        reason="The team split into two separate entities due to management disagreement"
    )
    
    result = await EditService.create_split_edit(
        async_session,
        test_user_trusted,
        request
    )
    
    # Check result
    assert result.status == "APPROVED"
    assert "successfully" in result.message.lower()
    
    # Verify source node is dissolved
    await async_session.refresh(source_team)
    assert source_team.dissolution_year == 2020
    
    # Verify new nodes were created
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    stmt = select(TeamNode).where(TeamNode.founding_year == 2020).options(selectinload(TeamNode.eras))
    result_nodes = await async_session.execute(stmt)
    new_nodes = result_nodes.scalars().all()
    
    assert len(new_nodes) >= 2
    
    # Verify lineage events were created
    stmt = select(LineageEvent).where(LineageEvent.predecessor_node_id == source_team.node_id)
    result_events = await async_session.execute(stmt)
    events = result_events.scalars().all()
    
    assert len(events) == 2
    assert all(e.event_type == LineageEventType.SPLIT for e in events)
    assert all(e.event_year == 2020 for e in events)


@pytest.mark.asyncio
async def test_create_split_five_teams_maximum(async_session, test_user_admin):
    """Test split with maximum 5 resulting teams."""
    from app.services.edit_service import EditService
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    from app.models.team import TeamNode, TeamEra
    from app.models.lineage import LineageEvent
    from sqlalchemy import select
    
    # Create source team
    from datetime import date
    source_node = TeamNode(founding_year=2010, legal_name="Split Source Team 2010")
    async_session.add(source_node)
    await async_session.flush()
    
    source_era = TeamEra(
        node_id=source_node.node_id,
        season_year=2018,
        valid_from=date(2018, 1, 1),
        registered_name="Large Team",
        tier_level=1
    )
    async_session.add(source_era)
    await async_session.commit()
    
    # Create request for 5 teams
    new_teams = [
        NewTeamInfo(name=f"Split Team {i+1}", tier=(i % 3) + 1)
        for i in range(5)
    ]
    
    request = SplitEventRequest(
        source_node_id=str(source_node.node_id),
        split_year=2018,
        new_teams=new_teams,
        reason="Large team split into 5 separate organizations"
    )
    
    result = await EditService.create_split_edit(
        async_session,
        test_user_admin,
        request
    )
    
    # Check result
    assert result.status == "APPROVED"
    
    # Verify source node is dissolved
    await async_session.refresh(source_node)
    assert source_node.dissolution_year == 2018
    
    # Verify lineage events were created (should be 5)
    stmt = select(LineageEvent).where(LineageEvent.predecessor_node_id == source_node.node_id)
    result_events = await async_session.execute(stmt)
    events = result_events.scalars().all()
    
    assert len(events) == 5


@pytest.mark.asyncio
async def test_split_validation_minimum_two_teams(async_session, test_user_trusted):
    """Test that split requires at least 2 resulting teams."""
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    from pydantic_core import ValidationError
    
    # Should fail validation when creating request
    try:
        request = SplitEventRequest(
            source_node_id=str(uuid4()),
            split_year=2020,
            new_teams=[
                NewTeamInfo(name="Only Team", tier=1)
            ],
            reason="This should fail - only one team"
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "at least 2" in str(e).lower()


@pytest.mark.asyncio
async def test_split_validation_maximum_five_teams(async_session, test_user_trusted):
    """Test that split cannot have more than 5 resulting teams."""
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    from pydantic_core import ValidationError
    
    # Try to create 6 teams
    new_teams = [
        NewTeamInfo(name=f"Team {i+1}", tier=1)
        for i in range(6)
    ]
    
    try:
        request = SplitEventRequest(
            source_node_id=str(uuid4()),
            split_year=2020,
            new_teams=new_teams,
            reason="This should fail - too many teams"
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "more than 5" in str(e).lower()


@pytest.mark.asyncio
async def test_split_source_node_not_found(async_session, test_user_trusted):
    """Test split with non-existent source node."""
    from app.services.edit_service import EditService
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    
    request = SplitEventRequest(
        source_node_id=str(uuid4()),
        split_year=2020,
        new_teams=[
            NewTeamInfo(name="Team A", tier=1),
            NewTeamInfo(name="Team B", tier=1)
        ],
        reason="Source team does not exist"
    )
    
    with pytest.raises(ValueError, match="Source team not found"):
        await EditService.create_split_edit(async_session, test_user_trusted, request)


@pytest.mark.asyncio
async def test_split_team_success_in_era_year(async_session, test_user_trusted):
    """Test split succeeds when source team has an era."""
    from app.services.edit_service import EditService
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    from app.models.team import TeamNode, TeamEra
    
    # Create team active in 2000
    from datetime import date
    source_node = TeamNode(founding_year=2000, legal_name="Old Team 2000")
    async_session.add(source_node)
    await async_session.flush()
    
    era = TeamEra(
        node_id=source_node.node_id,
        season_year=2000,
        valid_from=date(2000, 1, 1),
        registered_name="Old Team",
        tier_level=1
    )
    async_session.add(era)
    await async_session.commit()
    
    # Split in the same year where team has era
    request = SplitEventRequest(
        source_node_id=str(source_node.node_id),
        split_year=2000,  # Team active in 2000
        new_teams=[
            NewTeamInfo(name="Team A", tier=1),
            NewTeamInfo(name="Team B", tier=1)
        ],
        reason="Team splitting in year it was active"
    )
    
    result = await EditService.create_split_edit(async_session, test_user_trusted, request)
    
    # Should succeed
    assert result.status == "APPROVED"
    assert "successfully" in result.message.lower()


@pytest.mark.asyncio
async def test_split_year_validation_before_1900(async_session, test_user_trusted):
    """Test that split year must be >= 1900."""
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    from pydantic_core import ValidationError
    
    try:
        request = SplitEventRequest(
            source_node_id=str(uuid4()),
            split_year=1850,
            new_teams=[
                NewTeamInfo(name="Team A", tier=1),
                NewTeamInfo(name="Team B", tier=1)
            ],
            reason="Year too old"
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "1900" in str(e)


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_split_as_new_user_creates_pending_edit(async_session, test_user_new, sample_teams):
    """Test that new users' splits go to moderation queue."""
    from app.services.edit_service import EditService
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    
    source_team = sample_teams[0]  # Has era in 2020 from fixture
    
    request = SplitEventRequest(
        source_node_id=str(source_team.node_id),
        split_year=2020,
        new_teams=[
            NewTeamInfo(name="Split A", tier=1),
            NewTeamInfo(name="Split B", tier=1)
        ],
        reason="New user submitting a split for moderation"
    )
    
    result = await EditService.create_split_edit(
        async_session,
        test_user_new,
        request
    )
    
    # Check result indicates pending status
    assert result.status == "PENDING"
    assert "moderation" in result.message.lower()
    
    # Verify source node NOT dissolved (only happens on approval)
    await async_session.refresh(source_team)
    assert source_team.dissolution_year is None

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_split_as_trusted_user_auto_approved(async_session, test_user_trusted, sample_teams):
    """Test that trusted users' splits are auto-approved."""
    from app.services.edit_service import EditService
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    
    source_team = sample_teams[0]  # Has era in 2020 from fixture
    
    initial_approved_count = test_user_trusted.approved_edits_count
    
    request = SplitEventRequest(
        source_node_id=str(source_team.node_id),
        split_year=2020,
        new_teams=[
            NewTeamInfo(name="Split A", tier=1),
            NewTeamInfo(name="Split B", tier=1)
        ],
        reason="Trusted user creating a split"
    )
    
    result = await EditService.create_split_edit(
        async_session,
        test_user_trusted,
        request
    )
    
    # Check result
    assert result.status == "APPROVED"
    
    # Verify source node IS dissolved (immediately applied)
    await async_session.refresh(source_team)
    assert source_team.dissolution_year == request.split_year
    
    # Verify approved_edits_count incremented
    await async_session.refresh(test_user_trusted)
    assert test_user_trusted.approved_edits_count == initial_approved_count + 1

@pytest.mark.asyncio
async def test_split_creates_new_eras_with_manual_override(async_session, test_user_admin, sample_teams):
    """Test that split creates new eras with manual_override=True."""
    from app.services.edit_service import EditService
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    from app.models.team import TeamNode
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    source_team = sample_teams[0]
    
    request = SplitEventRequest(
        source_node_id=str(source_team.node_id),
        split_year=2020,
        new_teams=[
            NewTeamInfo(name="Split A", tier=1),
            NewTeamInfo(name="Split B", tier=2)
        ],
        reason="Check manual override flag"
    )
    
    result = await EditService.create_split_edit(
        async_session,
        test_user_admin,
        request
    )
    
    # Get nodes created from this split via lineage events
    from app.models.lineage import LineageEvent

    stmt_events = select(LineageEvent.successor_node_id).where(
        LineageEvent.predecessor_node_id == source_team.node_id,
        LineageEvent.event_type == LineageEventType.SPLIT
    )
    event_results = await async_session.execute(stmt_events)
    next_node_ids = [row[0] for row in event_results.all()]

    stmt_nodes = select(TeamNode).where(TeamNode.node_id.in_(next_node_ids)).options(selectinload(TeamNode.eras))
    result_nodes = await async_session.execute(stmt_nodes)
    new_nodes = result_nodes.scalars().all()
    assert len(new_nodes) == len(request.new_teams)
    
    # Verify new eras have manual_override=True
    for node in new_nodes:
        for era in node.eras:
            assert era.is_manual_override is True
            assert f"user_{test_user_admin.user_id}" in era.source_origin


@pytest.mark.asyncio
async def test_split_team_names_validation(async_session, test_user_trusted):
    """Test validation of new team names."""
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    
    # Test empty name
    with pytest.raises(ValueError):
        NewTeamInfo(name="", tier=1)
    
    # Test name too short
    with pytest.raises(ValueError):
        NewTeamInfo(name="AB", tier=1)
    
    # Test name too long (>200 chars)
    long_name = "A" * 201
    with pytest.raises(ValueError):
        NewTeamInfo(name=long_name, tier=1)


@pytest.mark.asyncio
async def test_split_tier_validation(async_session, test_user_trusted):
    """Test validation of tier levels."""
    from app.schemas.edits import NewTeamInfo
    
    # Valid tiers
    NewTeamInfo(name="Team", tier=1)
    NewTeamInfo(name="Team", tier=2)
    NewTeamInfo(name="Team", tier=3)
    
    # Invalid tier
    with pytest.raises(ValueError):
        NewTeamInfo(name="Team", tier=4)
    
    with pytest.raises(ValueError):
        NewTeamInfo(name="Team", tier=0)


@pytest.mark.asyncio
async def test_split_reason_validation(async_session, test_user_trusted):
    """Test that split reason must be at least 10 characters."""
    from app.schemas.edits import SplitEventRequest, NewTeamInfo
    from pydantic_core import ValidationError
    
    try:
        request = SplitEventRequest(
            source_node_id=str(uuid4()),
            split_year=2020,
            new_teams=[
                NewTeamInfo(name="Team A", tier=1),
                NewTeamInfo(name="Team B", tier=1)
            ],
            reason="Too short"  # Only 9 characters
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "at least 10" in str(e).lower()

