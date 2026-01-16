import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
import uuid

from app.models.user import User, UserRole
from app.models.team import TeamEra, TeamNode
from app.models.edit import EditHistory, EditStatus, EditAction
from app.models.enums import EditType
from app.services.moderation_service import ModerationService
from app.schemas.moderation import ReviewEditRequest

@pytest.fixture
async def moderator_user(async_session: AsyncSession):
    user = User(
        user_id=uuid.uuid4(),
        email="mod@example.com",
        google_id="mod_sub",
        role=UserRole.MODERATOR,
        display_name="Mod User"
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user

@pytest.fixture
async def editor_user(async_session: AsyncSession):
    user = User(
        user_id=uuid.uuid4(),
        email="editor@example.com",
        google_id="editor_sub",
        role=UserRole.EDITOR,
        display_name="Editor User"
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user

@pytest.mark.asyncio
async def test_format_pending_metadata_edit(async_session: AsyncSession, editor_user, moderator_user):
    # Setup: Create Era and Node
    node = TeamNode(
        legal_name="Test Node", 
        founding_year=2020, 
        created_by=editor_user.user_id
    )
    async_session.add(node)
    await async_session.flush()
    
    era = TeamEra(
        node_id=node.node_id,
        season_year=2020,
        valid_from=date(2020, 1, 1),
        registered_name="Test Team 2020",
        created_by=editor_user.user_id
    )
    async_session.add(era)
    await async_session.flush()
    
    # Create EditHistory (Metadata Update)
    edit = EditHistory(
        entity_type="team_era",
        entity_id=era.era_id,
        user_id=editor_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={"era": {"registered_name": "Test Team 2020"}},
        snapshot_after={"era": {"registered_name": "Test Team 2020 Updated"}},
        source_notes="Fixing name"
    )
    async_session.add(edit)
    await async_session.commit()
    
    # Test Format
    formatted = await ModerationService.format_edit_for_review(async_session, edit)
    assert formatted.edit_type == "METADATA"
    assert formatted.changes == {"registered_name": "Test Team 2020 Updated"}
    assert formatted.target_info['type'] == 'era'
    assert formatted.target_info['team_name'] == "Test Team 2020 Updated" # From Era in DB (snapshot_after)

    # Test Stats - Removed as get_stats is not in ModerationService
    # stats = await ModerationService.get_stats(async_session)
    # assert stats.pending_count >= 1
    # assert stats.pending_by_type["METADATA"] >= 1

@pytest.mark.asyncio
async def test_review_approve_metadata(async_session: AsyncSession, editor_user, moderator_user):
    # Setup
    node = TeamNode(legal_name="Old Name", founding_year=2000, created_by=editor_user.user_id)
    async_session.add(node)
    await async_session.flush()
    
    edit = EditHistory(
        entity_type="team_node",
        entity_id=node.node_id,
        user_id=editor_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={"node": {"legal_name": "Old Name"}},
        snapshot_after={"node": {"legal_name": "New Name"}},
        source_notes="Legal name change"
    )
    async_session.add(edit)
    await async_session.commit()
    
    # Review Approve
    resp = await ModerationService.review_edit(
        async_session, edit, moderator_user, approved=True, notes="Looks good"
    )
    
    assert resp.status == "APPROVED"
    assert edit.status == EditStatus.APPROVED
    
    # Verify DB update
    await async_session.refresh(node)
    assert node.legal_name == "New Name"

@pytest.mark.asyncio
async def test_review_reject(async_session: AsyncSession, editor_user, moderator_user):
    edit = EditHistory(
        entity_type="team_node",
        entity_id=uuid.uuid4(),
        user_id=editor_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        snapshot_after={"proposal": "junk"},
        source_notes="Spam"
    )
    async_session.add(edit)
    await async_session.commit()
    
    resp = await ModerationService.review_edit(
        async_session, edit, moderator_user, approved=False, notes="No spam"
    )
    
    assert resp.status == "REJECTED"
    assert edit.status == EditStatus.REJECTED
    assert edit.review_notes == "No spam"

@pytest.mark.asyncio
async def test_derive_changes_create_team(async_session: AsyncSession, editor_user):
    snap = {
        "proposed_team": {
            "legal_name": "New Team",
            "registered_name": "New Team Display",
            "founding_year": 2024,
            "tier_level": 2
        }
    }
    edit = EditHistory(
        entity_type="team_node",
        entity_id=uuid.uuid4(),
        user_id=editor_user.user_id,
        action=EditAction.CREATE, # Implies CREATE type
        status=EditStatus.PENDING,
        snapshot_after=snap
    )
    
    changes = ModerationService._derive_changes(edit)
    assert "create_team" in changes
    assert changes["create_team"]["legal_name"] == "New Team"
    
    # Check Type
    etype = ModerationService._get_edit_type(edit)
    assert etype == EditType.CREATE
