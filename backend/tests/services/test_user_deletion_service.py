import pytest
from uuid import UUID
from sqlalchemy import select
from app.services.user_deletion_service import UserDeletionService
from app.models.user import User, UserRole
from app.models.team import TeamNode, TeamEra
from app.models.sponsor import SponsorMaster, SponsorBrand
from app.models.lineage import LineageEvent
from app.models.edit import EditHistory
from app.models.enums import LineageEventType, EditAction, EditStatus
import datetime

@pytest.fixture
async def deletion_target_user(isolated_session):
    user = User(
        email="target@example.com",
        google_id="target_google_id",
        display_name="Target User",
        role=UserRole.EDITOR
    )
    isolated_session.add(user)
    await isolated_session.commit()
    await isolated_session.refresh(user)
    return user

@pytest.fixture
async def other_user(isolated_session):
    user = User(
        email="other@example.com",
        google_id="other_google_id",
        display_name="Other User",
        role=UserRole.EDITOR
    )
    isolated_session.add(user)
    await isolated_session.commit()
    await isolated_session.refresh(user)
    return user

@pytest.mark.asyncio
async def test_cannot_delete_system_user(isolated_session, deletion_target_user):
    # Mock system user ID check
    system_id = UserDeletionService.SYSTEM_USER_ID
    
    with pytest.raises(ValueError, match="Cannot delete system user"):
        await UserDeletionService.delete_user_account(
            isolated_session,
            system_id,
            deletion_target_user # requesting user doesn't matter here as check is first
        )

@pytest.mark.asyncio
async def test_user_can_only_delete_own_account(isolated_session, deletion_target_user, other_user):
    with pytest.raises(PermissionError, match="Can only delete own account"):
        await UserDeletionService.delete_user_account(
            isolated_session,
            other_user.user_id, # target
            deletion_target_user # requester
        )

@pytest.mark.asyncio
async def test_delete_user_anonymizes_all_entities(isolated_session, deletion_target_user):
    user_id = deletion_target_user.user_id
    
    # 1. Create entities linked to user
    team = TeamNode(legal_name="User Created Team", founding_year=2020, created_by=user_id, last_modified_by=user_id)
    isolated_session.add(team)
    await isolated_session.flush() # Ensure node_id is generated
    
    era = TeamEra(
        node_id=team.node_id, season_year=2020, valid_from=datetime.date(2020,1,1), 
        registered_name="User Team", created_by=user_id, last_modified_by=user_id
    ) # Note: TeamEra uses last_modified_by
    isolated_session.add(era)
    
    sponsor = SponsorMaster(legal_name="User Sponsor", created_by=user_id, last_modified_by=user_id)
    isolated_session.add(sponsor)
    await isolated_session.flush() # Ensure master_id is generated
    
    brand = SponsorBrand(master_id=sponsor.master_id, brand_name="User Brand", default_hex_color="#FFFFFF", created_by=user_id, last_modified_by=user_id)
    isolated_session.add(brand)
    await isolated_session.flush() # Ensure brand_id is generated
    
    from app.models.sponsor import TeamSponsorLink
    link = TeamSponsorLink(
        era_id=era.era_id, brand_id=brand.brand_id, rank_order=1, prominence_percent=100,
        created_by=user_id, last_modified_by=user_id
    )
    isolated_session.add(link)
    
    # Need another node for lineage
    other_node = TeamNode(legal_name="Other Node", founding_year=2021)
    isolated_session.add(other_node)
    await isolated_session.flush() # Ensure node_id is generated
    
    event = LineageEvent(
        predecessor_node_id=team.node_id, successor_node_id=other_node.node_id, 
        event_year=2021, event_type=LineageEventType.LEGAL_TRANSFER,
        created_by=user_id, last_modified_by=user_id
    )
    isolated_session.add(event)
    
    edit = EditHistory(
        entity_type="TEAM", entity_id=team.node_id, action=EditAction.CREATE, 
        status=EditStatus.APPROVED, snapshot_after={}, 
        user_id=user_id, reviewed_by=user_id
    )
    isolated_session.add(edit)
    
    await isolated_session.commit()
    
    # 2. Perform Validation - Check user IDs are present
    assert team.created_by == user_id
    assert edit.user_id == user_id
    
    # 3. Execute Deletion
    await UserDeletionService.delete_user_account(
        isolated_session,
        user_id,
        deletion_target_user
    )
    
    # 4. Verify Anonymization
    # Refresh all entities
    # Note: We need to use new queries because objects might be expired/deleted
    
    # TeamNode
    t = await isolated_session.get(TeamNode, team.node_id)
    assert t.created_by is None
    assert t.last_modified_by is None
    
    # TeamEra
    e = await isolated_session.get(TeamEra, era.era_id)
    assert e.created_by is None
    assert e.last_modified_by is None
    
    # SponsorMaster
    s = await isolated_session.get(SponsorMaster, sponsor.master_id)
    assert s.created_by is None
    assert s.last_modified_by is None
    
    # SponsorBrand
    b = await isolated_session.get(SponsorBrand, brand.brand_id)
    assert b.created_by is None
    assert b.last_modified_by is None
    
    # TeamSponsorLink
    lnk = await isolated_session.get(TeamSponsorLink, link.link_id)
    assert lnk.created_by is None
    assert lnk.last_modified_by is None

    # LineageEvent
    l = await isolated_session.get(LineageEvent, event.event_id)
    assert l.created_by is None
    assert l.last_modified_by is None
    
    # EditHistory
    ed = await isolated_session.get(EditHistory, edit.edit_id)
    assert ed.user_id is None
    assert ed.reviewed_by is None
    
    # User
    u = await isolated_session.get(User, user_id)
    assert u is None

