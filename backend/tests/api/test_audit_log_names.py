
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.edit import EditHistory
from app.models.enums import EditAction, EditStatus, LineageEventType as LineageType
from app.models.team import TeamNode, TeamEra
from app.models.sponsor import TeamSponsorLink, SponsorMaster
from app.models.lineage import LineageEvent
import uuid
import json

@pytest.mark.asyncio
async def test_audit_log_resolves_entity_names(
    client: AsyncClient,
    isolated_session: AsyncSession,
    admin_user: dict,
    admin_user_token: str
):
    """
    Test that the audit log list endpoint resolves human-readable names 
    for various entity types instead of UUIDs.
    """
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    
    # 1. Create a Team Edit
    team_id = uuid.uuid4()
    team_edit = EditHistory(
        entity_type="TEAM",
        entity_id=team_id,
        user_id=admin_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        snapshot_after={"legal_name": "QuickStep Floors", "display_name": "QuickStep"}
    )
    isolated_session.add(team_edit)

    # 2. Create a Sponsor Edit
    sponsor_id = uuid.uuid4()
    sponsor_edit = EditHistory(
        entity_type="SPONSOR",
        entity_id=sponsor_id,
        user_id=admin_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        snapshot_after={"legal_name": "Soudal Inc.", "industry": "Chemicals"}
    )
    isolated_session.add(sponsor_edit)
    
    await isolated_session.commit()
    
    # Verify via API
    response = await client.get("/api/v1/audit-log?status=PENDING", headers=headers)
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    
    # Find team edit
    team_item = next(i for i in items if i["entity_type"] == "TEAM")
    assert team_item["entity_name"] == "QuickStep", "Should use display_name"
    
    # Find sponsor edit
    sponsor_item = next(i for i in items if i["entity_type"] == "SPONSOR")
    assert sponsor_item["entity_name"] == "Soudal Inc.", "Should use legal_name"


@pytest.mark.asyncio
async def test_audit_log_resolves_lineage_names(
    client: AsyncClient,
    isolated_session: AsyncSession,
    admin_user: dict,
    admin_user_token: str
):
    """
    Test that lineage events resolve predecessor/successor names.
    This requires actual TeamNode records to exist for lookup.
    """
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    
    # Create actual teams
    pred_team = TeamNode(legal_name="Mapei", founding_year=1993)
    succ_team = TeamNode(legal_name="QuickStep", founding_year=2003)
    isolated_session.add(pred_team)
    isolated_session.add(succ_team)
    await isolated_session.flush()
    
    # Create Lineage Edit (referencing them by ID)
    lineage_id = uuid.uuid4()
    lineage_edit = EditHistory(
        entity_type="LINEAGE",
        entity_id=lineage_id,
        user_id=admin_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        snapshot_after={
            "predecessor_id": str(pred_team.node_id),
            "successor_id": str(succ_team.node_id),
            "type": "SPLIT"
        }
    )
    isolated_session.add(lineage_edit)
    await isolated_session.commit()
    
    # API Call
    response = await client.get("/api/v1/audit-log?status=PENDING", headers=headers)
    data = response.json()
    lineage_item = next(i for i in data["items"] if i["entity_type"] == "LINEAGE")
    
    # Expectation: "Mapei SPLIT QuickStep" (or similar format)
    expected_name = f"{pred_team.legal_name} SPLIT {succ_team.legal_name}"
    assert lineage_item["entity_name"] == expected_name


@pytest.mark.asyncio
async def test_audit_log_search_finds_by_name_in_snapshot(
    client: AsyncClient,
    isolated_session: AsyncSession,
    admin_user: dict,
    admin_user_token: str
):
    """
    Test that searching for 'QuickStep' finds the edit even though the name is inside the JSON snapshot.
    """
    headers = {"Authorization": f"Bearer {admin_user_token}"}

    team_id = uuid.uuid4()
    team_edit = EditHistory(
        entity_type="TEAM",
        entity_id=team_id,
        user_id=admin_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        # 'QuickStep' is inside the JSON
        snapshot_after={"legal_name": "QuickStep Team"}
    )
    isolated_session.add(team_edit)
    await isolated_session.commit()
    
    response = await client.get("/api/v1/audit-log?search=QuickStep", headers=headers)
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["entity_name"] == "QuickStep Team"

