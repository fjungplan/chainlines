import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.team import TeamNode, TeamEra
from app.models.user import User
from app.api.dependencies import require_admin

@pytest.mark.asyncio
async def test_create_team_node(test_client: AsyncClient, trusted_user_token: str, db_session: AsyncSession):
    # Test creating a team node
    payload = {
        "legal_name": "New Team 2024",
        "founding_year": 2024,
        "is_protected": False,
        "source_url": "http://example.com"
    }
    headers = {"Authorization": f"Bearer {trusted_user_token}"}
    response = await test_client.post("/api/v1/teams", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["legal_name"] == "New Team 2024"
    assert data["founding_year"] == 2024
    assert "node_id" in data
    
    # Verify DB
    node_id = data["node_id"]
    from uuid import UUID
    node = await db_session.get(TeamNode, UUID(node_id))
    assert node is not None
    assert node.legal_name == "New Team 2024"

@pytest.mark.asyncio
async def test_create_team_node_duplicate_name(test_client: AsyncClient, trusted_user_token: str):
    # Setup - handled by first test logic, but let's re-create
    payload = {
        "legal_name": "Duplicate Team",
        "founding_year": 2024
    }
    headers = {"Authorization": f"Bearer {trusted_user_token}"}
    response = await test_client.post("/api/v1/teams", json=payload, headers=headers)
    assert response.status_code == 201
    
    # Attempt duplicate create
    response = await test_client.post("/api/v1/teams", json=payload, headers=headers)
    # Should fail with 400 or 422 depending on error handling in TeamService.create_node
    # TeamService raises ValidationException, which maps to 400 usually? 
    # Need to check exception handlers, assuming standard FastAPI ValidationException handler or HTTP 500 if not caught.
    # Service raises app.core.exceptions.ValidationException.
    assert response.status_code in [400, 422] 

@pytest.mark.asyncio
async def test_update_team_node(test_client: AsyncClient, trusted_user_token: str, sample_team_node: TeamNode):
    payload = {
        "legal_name": "Updated Team Name",
        "is_protected": True
    }
    headers = {"Authorization": f"Bearer {trusted_user_token}"}
    response = await test_client.put(f"/api/v1/teams/{sample_team_node.node_id}", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["legal_name"] == "Updated Team Name"
    assert data["is_protected"] is True
    
    # Verify other fields untouched
    assert data["founding_year"] == sample_team_node.founding_year

@pytest.mark.asyncio
async def test_delete_team_node(test_client: AsyncClient, admin_user_token: str, sample_team_node: TeamNode, db_session: AsyncSession):
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = await test_client.delete(f"/api/v1/teams/{sample_team_node.node_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify deletion
    node = await db_session.get(TeamNode, sample_team_node.node_id)
    assert node is None

@pytest.mark.asyncio
async def test_create_team_era(test_client: AsyncClient, trusted_user_token: str, sample_team_node: TeamNode, db_session: AsyncSession):
    payload = {
        "season_year": 2025,
        "valid_from": "2025-01-01",
        "registered_name": "Era 2025",
        "uci_code": "ERA",
        "country_code": "FRA",
        "tier_level": 1
    }
    headers = {"Authorization": f"Bearer {trusted_user_token}"}
    response = await test_client.post(f"/api/v1/teams/{sample_team_node.node_id}/eras", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["season_year"] == 2025
    assert data["registered_name"] == "Era 2025"
    assert data["node_id"] == str(sample_team_node.node_id)

@pytest.mark.asyncio
async def test_update_team_era(test_client: AsyncClient, trusted_user_token: str, sample_team_era: TeamEra):
    payload = {
        "registered_name": "Updated Era Name",
        "tier_level": 2
    }
    headers = {"Authorization": f"Bearer {trusted_user_token}"}
    response = await test_client.put(f"/api/v1/teams/eras/{sample_team_era.era_id}", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["registered_name"] == "Updated Era Name"
    assert data["tier_level"] == 2

@pytest.mark.asyncio
async def test_delete_team_era(test_client: AsyncClient, admin_user_token: str, sample_team_era: TeamEra, db_session: AsyncSession):
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = await test_client.delete(f"/api/v1/teams/eras/{sample_team_era.era_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify deletion
    era = await db_session.get(TeamEra, sample_team_era.era_id)
    assert era is None
