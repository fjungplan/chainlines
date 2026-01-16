
import pytest
import uuid
from datetime import datetime
from app.models.edit import EditHistory
from app.models.enums import EditAction, EditStatus
from app.models.user import User

@pytest.mark.asyncio
async def test_audit_log_resolves_team_name(
    client,
    admin_user_token,  # Use admin token from conftest (ADMIN implies MODERATOR access)
    isolated_session,
    admin_user         # Use admin user from conftest
):
    """Test that TeamNode entity_name is resolved from snapshot data."""
    
    edit_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    
    edit = EditHistory(
        edit_id=edit_id,
        entity_type="TeamNode",
        entity_id=entity_id,
        user_id=admin_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={},
        snapshot_after={
            "legal_name": "Test Team Name",
            "display_name": "Test Team"
        },
        created_at=datetime.utcnow()
    )
    isolated_session.add(edit)
    await isolated_session.commit()
    
    response = await client.get(
        "/api/v1/audit-log",
        headers={"Authorization": f"Bearer {admin_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    item = data["items"][0]
    
    # Should be the name from snapshot, NOT the UUID
    # Currently fails (returns UUID) because "TeamNode" != "TEAM_NODE"
    assert item["entity_name"] == "Test Team"
    assert item["entity_name"] != str(entity_id)

@pytest.mark.asyncio
async def test_audit_log_resolves_team_era_name(
    client,
    admin_user_token,
    isolated_session,
    admin_user
):
    # Clear previous edits
    await isolated_session.execute(EditHistory.__table__.delete())

    edit = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="TeamEra",
        entity_id=uuid.uuid4(),
        user_id=admin_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={},
        snapshot_after={
            "registered_name": "Test Era Name",
            "season_year": 2024
        },
        created_at=datetime.utcnow()
    )
    isolated_session.add(edit)
    await isolated_session.commit()
    
    response = await client.get(
        "/api/v1/audit-log",
        headers={"Authorization": f"Bearer {admin_user_token}"}
    )
    
    item = response.json()["items"][0]
    # Service returns "Name (Year)"
    assert item["entity_name"] == "Test Era Name (2024)"

@pytest.mark.asyncio
async def test_audit_log_detail_resolves_name(
    client,
    admin_user_token,
    isolated_session,
    admin_user
):
    """Test that Detail endpoint resolves entity name using AuditLogService."""
    
    # Create a TeamNode to resolve (DB fetch)
    # We need an actual TeamNode in DB because Service fetches it if snapshot checks fail (or always?)
    # AuditLogService.resolve_entity_name ALWAYS fetches from DB according to code (lines 78+)!
    # It does NOT use snapshot.
    
    from app.models.team import TeamNode
    import uuid
    
    node_id = uuid.uuid4()
    node = TeamNode(
        node_id=node_id,
        legal_name="DB Team Name",
        founding_year=2020
    )
    isolated_session.add(node)
    
    edit_id = uuid.uuid4()
    edit = EditHistory(
        edit_id=edit_id,
        entity_type="TeamNode",
        entity_id=node_id,
        user_id=admin_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.APPROVED,
        snapshot_before={},
        snapshot_after={"updated": "true"},
        created_at=datetime.utcnow(),
        reviewed_at=datetime.utcnow()
    )
    isolated_session.add(edit)
    await isolated_session.commit()
    
    response = await client.get(
        f"/api/v1/audit-log/{edit_id}",
        headers={"Authorization": f"Bearer {admin_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Needs to match "DB Team Name"
    assert data["entity_name"] == "DB Team Name"
    assert data["entity_name"] != str(node_id)
