import pytest
import uuid
from httpx import AsyncClient
from app.models.enums import EditStatus
from app.models.team import TeamNode

@pytest.mark.asyncio
async def test_create_era_edit_endpoint_as_editor(client: AsyncClient, db_session, new_user_token, new_user):
    """Test creating an era edit via API as an EDITOR (Pending)."""
    # Create Node
    node = TeamNode(
        node_id=uuid.uuid4(),
        legal_name="API Node",
        founding_year=2000,
        created_by=new_user.user_id # Assign UUID, not object
    )
    db_session.add(node)
    await db_session.commit()
    
    payload = {
        "season_year": 2025,
        "node_id": str(node.node_id),
        "registered_name": "API Era Pending",
        "uci_code": "PEN",
        "country_code": "USA",
        "tier_level": 2,
        "reason": "Testing pending flow via API"
    }
    
    headers = {"Authorization": f"Bearer {new_user_token}"}
    response = await client.post("/api/v1/edits/era", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == EditStatus.PENDING.value
    assert "submitted for moderation" in data["message"].lower()

@pytest.mark.asyncio
async def test_create_era_edit_endpoint_as_trusted(client: AsyncClient, db_session, trusted_user_token, trusted_user):
    """Test creating an era edit via API as TRUSTED (Approved)."""
    node = TeamNode(
        node_id=uuid.uuid4(),
        legal_name="API Node Trusted",
        founding_year=2000,
        created_by=trusted_user.user_id
    )
    db_session.add(node)
    await db_session.commit()

    payload = {
        "season_year": 2026,
        "node_id": str(node.node_id),
        "registered_name": "API Era Approved",
        "uci_code": "APP",
        "country_code": "FRA",
        "tier_level": 1,
        "reason": "Testing approved flow via API"
    }
    
    headers = {"Authorization": f"Bearer {trusted_user_token}"}
    response = await client.post("/api/v1/edits/era", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == EditStatus.APPROVED.value
    assert "created" in data["message"].lower()
