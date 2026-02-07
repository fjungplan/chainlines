import pytest
import uuid
from httpx import AsyncClient
from app.models.lineage import LineageEvent
from app.models.team import TeamNode
from app.models.enums import LineageEventType

@pytest.mark.asyncio
async def test_list_lineage_events_sort_by_predecessor_asc(test_client: AsyncClient, admin_user_token: str, isolated_session):
    # Setup: Create some teams and lineage events
    node_a = TeamNode(founding_year=1990, legal_name="Team A", display_name="Team A")
    node_b = TeamNode(founding_year=1990, legal_name="Team B", display_name="Team B")
    node_c = TeamNode(founding_year=1990, legal_name="Team C", display_name="Team C")
    isolated_session.add_all([node_a, node_b, node_c])
    await isolated_session.commit()
    await isolated_session.refresh(node_a)
    await isolated_session.refresh(node_b)
    await isolated_session.refresh(node_c)

    # Note: Event 1 (C -> B), Event 2 (A -> C), Event 3 (B -> A)
    event1 = LineageEvent(predecessor_node_id=node_c.node_id, successor_node_id=node_b.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    event2 = LineageEvent(predecessor_node_id=node_a.node_id, successor_node_id=node_c.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    event3 = LineageEvent(predecessor_node_id=node_b.node_id, successor_node_id=node_a.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    
    isolated_session.add_all([event1, event2, event3])
    await isolated_session.commit()

    # Test sorting by predecessor name ASC
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = await test_client.get("/api/v1/lineage?sort_by=predecessor&order=asc", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["predecessor_node"]["display_name"] == "Team A"
    assert items[1]["predecessor_node"]["display_name"] == "Team B"
    assert items[2]["predecessor_node"]["display_name"] == "Team C"

@pytest.mark.asyncio
async def test_list_lineage_events_sort_by_successor_desc(test_client: AsyncClient, admin_user_token: str, isolated_session):
    # Setup: Create some teams and lineage events
    node_a = TeamNode(founding_year=1990, legal_name="Team A", display_name="Team A")
    node_b = TeamNode(founding_year=1990, legal_name="Team B", display_name="Team B")
    node_c = TeamNode(founding_year=1990, legal_name="Team C", display_name="Team C")
    isolated_session.add_all([node_a, node_b, node_c])
    await isolated_session.commit()
    await isolated_session.refresh(node_a)
    await isolated_session.refresh(node_b)
    await isolated_session.refresh(node_c)

    event1 = LineageEvent(predecessor_node_id=node_a.node_id, successor_node_id=node_a.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    event2 = LineageEvent(predecessor_node_id=node_a.node_id, successor_node_id=node_b.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    event3 = LineageEvent(predecessor_node_id=node_a.node_id, successor_node_id=node_c.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    
    # Wait, the circular constraint might fail pred == succ. Let's fix.
    event1.successor_node_id = node_c.node_id # A -> C
    event2.successor_node_id = node_a.node_id # A -> A (FAILS)
    # Let's just use distinct targets
    event1.successor_node_id = node_a.node_id # FAILS
    
    # Let's recreate properly
    # A -> B, B -> C, C -> A (not circular as separate events)
    e1 = LineageEvent(predecessor_node_id=node_a.node_id, successor_node_id=node_b.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    e2 = LineageEvent(predecessor_node_id=node_b.node_id, successor_node_id=node_c.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    e3 = LineageEvent(predecessor_node_id=node_c.node_id, successor_node_id=node_a.node_id, event_year=2000, event_type=LineageEventType.LEGAL_TRANSFER)
    
    isolated_session.add_all([e1, e2, e3])
    await isolated_session.commit()

    # Test sorting by successor name DESC
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = await test_client.get("/api/v1/lineage?sort_by=successor&order=desc", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["successor_node"]["display_name"] == "Team C"
    assert items[1]["successor_node"]["display_name"] == "Team B"
    assert items[2]["successor_node"]["display_name"] == "Team A"
