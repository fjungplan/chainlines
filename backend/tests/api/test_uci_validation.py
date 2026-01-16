
import pytest
from app.models.team import TeamEra
from datetime import date
from uuid import uuid4

@pytest.mark.asyncio
async def test_edit_metadata_alphanumeric_uci(test_client, isolated_session, sample_team_node, admin_user_token):
    # Setup: Create an existing era to edit
    era = TeamEra(
        node_id=sample_team_node.node_id,
        season_year=2024,
        valid_from=date(2024, 1, 1),
        registered_name="Test Team",
        tier_level=1,
        uci_code="OLD"
    )
    isolated_session.add(era)
    await isolated_session.commit()
    await isolated_session.refresh(era)

    # Payload matching the frontend structure
    # Trying "1A3" which is alphanumeric mixed
    payload = {
        "era_id": str(era.era_id),
        "registered_name": "Test Team Updated",
        "uci_code": "1A3", 
        "country_code": "USA",
        "tier_level": 1,
        "valid_from": "2024-01-01",
        "reason": "Updating UCI code to alphanumeric"
    }

    # Attempt PUT/POST depending on actual endpoint. 
    # Frontend calls `editsApi.editMetadata` -> POST /api/v1/edits/metadata
    resp = await test_client.post(
        "/api/v1/edits/metadata", 
        json=payload,
        headers={"Authorization": f"Bearer {admin_user_token}"}
    )
    
    # If this fails with 422, we know it's validation.
    # If 500, it's a crash.
    # If 200, then the backend is fine and it's purely frontend.
    assert resp.status_code == 200, f"Response: {resp.text}"
    
    # Verify DB update
    await isolated_session.refresh(era)
    assert era.uci_code == "1A3"

@pytest.mark.asyncio
async def test_create_team_era_alphanumeric_uci(test_client, isolated_session, sample_team_node, admin_user_token):
    payload = {
        "season_year": 2025,
        "valid_from": "2025-01-01",
        "registered_name": "New Team 2025",
        "tier_level": 1,
        "uci_code": "Q36", # Alphanumeric mixed
        "country_code": "FRA",
        "is_name_auto_generated": True,
        "is_manual_override": True,
        "is_auto_filled": False,
        "has_license": True
    }
    
    resp = await test_client.post(
        f"/api/v1/teams/{sample_team_node.node_id}/eras",
        json=payload,
        headers={"Authorization": f"Bearer {admin_user_token}"}
    )
    
    assert resp.status_code == 201, f"Response: {resp.text}"
    data = resp.json()
    assert data["uci_code"] == "Q36"
