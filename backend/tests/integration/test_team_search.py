
from datetime import date
import pytest
from uuid import uuid4
from app.services.team_service import TeamService
from app.schemas.team import TeamNodeCreate, TeamEraCreate
from app.models.team import TeamNode
from sqlalchemy import select

@pytest.mark.asyncio
async def test_search_teams_includes_eras_and_fuzzy(isolated_session, admin_user):
    # 1. Create a TeamNode "Visma"
    node_data = TeamNodeCreate(
        legal_name="Visma Lease a Bike",
        display_name="Visma",
        founding_year=2024,
        dissolution_year=None,
        country="NED"
    )
    node = await TeamService.create_node(isolated_session, node_data, admin_user.user_id)
    
    # 2. Add an Era with a historical name "Jumbo-Visma"
    era_data = TeamEraCreate(
        season_year=2023,
        registered_name="Jumbo-Visma",
        uci_code="TJV",
        country="NED",
        tier_level=1,
        valid_from=date(2023, 1, 1)
    )
    await TeamService.create_era(isolated_session, node.node_id, era_data, admin_user.user_id)

    # 3. Add an Era with accents "Cervélo TestTeam"
    # Create another node for this
    node2_data = TeamNodeCreate(
        legal_name="Cervélo TestTeam",
        display_name="Cervélo",
        founding_year=2009,
        country="SUI"
    )
    node2 = await TeamService.create_node(isolated_session, node2_data, admin_user.user_id)

    # 4. Test Search (Historical Name)
    # Search for "Jumbo" should find "Visma" node
    nodes, count = await TeamService.list_nodes(isolated_session, search="Jumbo")
    assert count >= 1
    assert any(n.node_id == node.node_id for n in nodes)

    # 5. Test Search (Accent Insensitive)
    # Search for "Cervelo" should find "Cervélo" node
    nodes_accent, count_accent = await TeamService.list_nodes(isolated_session, search="Cervelo")
    assert count_accent >= 1
    assert any(n.node_id == node2.node_id for n in nodes_accent)
