
import pytest
from uuid import uuid4
from datetime import date
from app.models.team import TeamNode, TeamEra
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType

@pytest.mark.asyncio
async def test_team_history_includes_events(
    client, isolated_session, sample_team_node
):
    # 1. Setup: Node A (Predecessor) -> Event -> Node B (Successor)
    
    # Predecessor (Node A)
    node_a = TeamNode(legal_name="Team A", founding_year=2000)
    isolated_session.add(node_a)
    await isolated_session.flush()
    
    era_a = TeamEra(
        node_id=node_a.node_id,
        season_year=2000,
        registered_name="Team A 2000",
        valid_from=date(2000,1,1)
    )
    isolated_session.add(era_a)
    
    # Successor (Node B)
    node_b = TeamNode(legal_name="Team B", founding_year=2001)
    isolated_session.add(node_b)
    await isolated_session.flush()
    
    era_b = TeamEra(
        node_id=node_b.node_id,
        season_year=2001,
        registered_name="Team B 2001",
        valid_from=date(2001,1,1)
    )
    isolated_session.add(era_b)
    
    # Event: Merge in 2001
    event = LineageEvent(
        event_year=2001,
        event_type=LineageEventType.MERGE,
        predecessor_node_id=node_a.node_id,
        successor_node_id=node_b.node_id,
        notes="Big merger"
    )
    isolated_session.add(event)
    await isolated_session.commit()
    
    # 2. Test Node B (Should have INCOMING event from A)
    # Actually wait, my test setup: 
    # Event: A -> B. 
    # Querying B (Successor). Should see INCOMING event from A.
    
    resp = await client.get(f"/api/v1/teams/{node_b.node_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    
    assert "events" in data
    assert len(data["events"]) == 1
    ev = data["events"][0]
    assert ev["direction"] == "INCOMING"
    assert ev["related_team_name"] == "Team A" # legal_name fallback
    assert ev["related_era_name"] == "Team A 2000" # year-1 logic (2001-1 = 2000)
    assert ev["event_type"] == "MERGE"
    assert ev["notes"] == "Big merger"
    
    # 3. Test Node A (Should have OUTGOING event to B)
    resp_a = await client.get(f"/api/v1/teams/{node_a.node_id}/history")
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    
    assert len(data_a["events"]) == 1
    ev_a = data_a["events"][0]
    assert ev_a["direction"] == "OUTGOING"
    assert ev_a["related_team_name"] == "Team B"
    assert ev_a["related_era_name"] == "Team B 2001" # year logic (event year 2001)
