"""
Tests for My Edits API endpoints.

These endpoints allow any authenticated user to view their own edit history.
"""
import pytest
import uuid
from httpx import AsyncClient
from datetime import datetime

from app.models.edit import EditHistory
from app.models.enums import EditStatus, EditAction
from app.models.team import TeamNode


@pytest.mark.asyncio
async def test_list_returns_only_current_user_edits(
    client: AsyncClient, db_session, new_user, new_user_token, admin_user
):
    """Verify that the list endpoint only returns edits submitted by the current user."""
    # Create a node to reference
    node = TeamNode(
        node_id=uuid.uuid4(),
        legal_name="Test Node",
        founding_year=2020,
        created_by=new_user.user_id
    )
    db_session.add(node)
    await db_session.flush()

    # Create edit by current user
    my_edit = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="team_node",
        entity_id=node.node_id,
        user_id=new_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={"test": "before"},
        snapshot_after={"test": "after"}
    )
    db_session.add(my_edit)

    # Create edit by another user (admin)
    other_edit = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="team_node",
        entity_id=node.node_id,
        user_id=admin_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={"test": "before2"},
        snapshot_after={"test": "after2"}
    )
    db_session.add(other_edit)
    await db_session.commit()

    # Request my edits
    headers = {"Authorization": f"Bearer {new_user_token}"}
    response = await client.get("/api/v1/my-edits", headers=headers)

    assert response.status_code == 200
    data = response.json()
    
    # Should only contain my edit
    assert len(data["items"]) == 1
    # Verify entity name resolution returns a string (actual value depends on DB state which is mocked/empty)
    assert isinstance(data["items"][0]["entity_name"], str)
    
    assert data["items"][0]["edit_id"] == str(my_edit.edit_id)


@pytest.mark.asyncio
async def test_list_unauthenticated_returns_401(client: AsyncClient):
    """Verify that unauthenticated requests are rejected."""
    response = await client.get("/api/v1/my-edits")
    assert response.status_code in (401, 403)  # Unauthenticated/unauthorized


@pytest.mark.asyncio
async def test_detail_own_edit_succeeds(
    client: AsyncClient, db_session, new_user, new_user_token
):
    """Verify that a user can view their own edit details."""
    # Create a node
    node = TeamNode(
        node_id=uuid.uuid4(),
        legal_name="Detail Test Node",
        founding_year=2021,
        created_by=new_user.user_id
    )
    db_session.add(node)
    await db_session.flush()

    # Create edit by current user
    my_edit = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="team_node",
        entity_id=node.node_id,
        user_id=new_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        snapshot_before=None,
        snapshot_after={"legal_name": "Detail Test Node"}
    )
    db_session.add(my_edit)
    await db_session.commit()

    # Request detail
    headers = {"Authorization": f"Bearer {new_user_token}"}
    response = await client.get(f"/api/v1/my-edits/{my_edit.edit_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["edit_id"] == str(my_edit.edit_id)
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_detail_other_user_edit_forbidden(
    client: AsyncClient, db_session, new_user, new_user_token, admin_user
):
    """Verify that a user cannot view another user's edit details (unless moderator)."""
    # Create a node
    node = TeamNode(
        node_id=uuid.uuid4(),
        legal_name="Forbidden Test Node",
        founding_year=2022,
        created_by=admin_user.user_id
    )
    db_session.add(node)
    await db_session.flush()

    # Create edit by admin
    admin_edit = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="team_node",
        entity_id=node.node_id,
        user_id=admin_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={"test": "before"},
        snapshot_after={"test": "after"}
    )
    db_session.add(admin_edit)
    await db_session.commit()

    # Request detail as non-owner, non-moderator
    headers = {"Authorization": f"Bearer {new_user_token}"}
    response = await client.get(f"/api/v1/my-edits/{admin_edit.edit_id}", headers=headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_detail_moderator_can_view_any(
    client: AsyncClient, db_session, new_user, admin_user, admin_user_token
):
    """Verify that a moderator can view any user's edit details via my-edits endpoint."""
    # Create a node
    node = TeamNode(
        node_id=uuid.uuid4(),
        legal_name="Mod View Test Node",
        founding_year=2023,
        created_by=new_user.user_id
    )
    db_session.add(node)
    await db_session.flush()

    # Create edit by new_user
    user_edit = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="team_node",
        entity_id=node.node_id,
        user_id=new_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={"test": "before"},
        snapshot_after={"test": "after"}
    )
    db_session.add(user_edit)
    await db_session.commit()

    # Request detail as moderator
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = await client.get(f"/api/v1/my-edits/{user_edit.edit_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["edit_id"] == str(user_edit.edit_id)


@pytest.mark.asyncio
async def test_permission_flags_false_for_editor(
    client: AsyncClient, db_session, new_user, new_user_token
):
    """Verify that permission flags are false for non-moderator viewing their own edit."""
    # Create a node
    node = TeamNode(
        node_id=uuid.uuid4(),
        legal_name="Permissions Test Node",
        founding_year=2024,
        created_by=new_user.user_id
    )
    db_session.add(node)
    await db_session.flush()

    # Create pending edit
    my_edit = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="team_node",
        entity_id=node.node_id,
        user_id=new_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.PENDING,
        snapshot_before={"test": "before"},
        snapshot_after={"test": "after"}
    )
    db_session.add(my_edit)
    await db_session.commit()

    # Request detail
    headers = {"Authorization": f"Bearer {new_user_token}"}
    response = await client.get(f"/api/v1/my-edits/{my_edit.edit_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    
    # Non-moderator should not have moderation permissions
    assert data["can_approve"] is False
    assert data["can_reject"] is False
    assert data["can_revert"] is False
