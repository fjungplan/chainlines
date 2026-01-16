import pytest
from app.services.team_service import TeamService
from app.schemas.team import TeamNodeCreate

@pytest.mark.asyncio
async def test_list_teams_no_search(isolated_session, admin_user):
    # 1. Create a TeamNode
    node_data = TeamNodeCreate(
        legal_name="Regression Team",
        display_name="RegTeam",
        founding_year=2024,
        country="FRA"
    )
    await TeamService.create_node(isolated_session, node_data, admin_user.user_id)

    # 2. List nodes with defaults (no search, no filters)
    nodes, count = await TeamService.list_nodes(isolated_session)
    
    # 3. Verify results
    assert count >= 1
    assert any(n.legal_name == "Regression Team" for n in nodes)
