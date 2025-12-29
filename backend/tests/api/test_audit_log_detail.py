import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json
from app.models.edit import EditHistory, EditAction, EditStatus
from app.models.team import TeamNode, TeamEra
from app.models.user import User

@pytest.mark.asyncio
async def test_get_audit_log_detail_resolves_legacy_entity_type(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user_token: str,
    admin_user: User
):
    """
    Test that the detail encpoint correctly resolves entity names even if the 
    stored entity_type is in legacy format (e.g. 'TEAM_NODE' instead of 'team_node').
    """
    # 1. Create a TeamNode
    team = TeamNode(
        node_id=uuid.uuid4(),
        legal_name="Legacy Team",
        display_name="Legacy Team Display",
        founding_year=2000,
        is_active=True,
        created_by=admin_user.user_id,
        last_modified_by=admin_user.user_id
    )
    db_session.add(team)
    
    # 2. Create an EditHistory with legacy uppercase entity_type
    edit_id = uuid.uuid4()
    edit = EditHistory(
        edit_id=edit_id,
        entity_type="TEAM_NODE", # Legacy uppercase
        entity_id=team.node_id,
        user_id=admin_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={"legal_name": "Old Name"},
        snapshot_after={"legal_name": "Legacy Team"},
        created_at=None # auto
    )
    db_session.add(edit)
    await db_session.commit()

    # 3. Fetch detail
    response = await client.get(
        f"/api/v1/audit-log/{edit_id}",
        headers={"Authorization": f"Bearer {admin_user_token}"}
    )

    # 4. Verify
    assert response.status_code == 200
    data = response.json()
    assert data["entity_type"] == "TEAM_NODE"
    # This assertion checks if the service correctly normalized the type to find the team name
    assert data["entity_name"] == "Legacy Team Display"

@pytest.mark.asyncio
async def test_get_audit_log_detail_permissions(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user_token: str,
    admin_user: User,
    test_user: User
):
    """Test permission flags for an admin viewing a pending edit."""
    
    # 1. Create correct lowercase edit
    edit_id = uuid.uuid4()
    edit = EditHistory(
        edit_id=edit_id,
        entity_type="team_node",
        entity_id=uuid.uuid4(), # Random ID, name will be "Unknown" which is fine
        user_id=test_user.user_id, # Submitted by regular user
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        snapshot_after={"some": "data"}
    )
    db_session.add(edit)
    await db_session.commit()

    # 2. Fetch as Admin (who has moderation rights)
    response = await client.get(
        f"/api/v1/audit-log/{edit_id}",
        headers={"Authorization": f"Bearer {admin_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Admin should be able to approve/reject a pending edit from a regular user
    assert data["can_approve"] is True
    assert data["can_reject"] is True
    assert data["can_revert"] is False # Not approved yet
