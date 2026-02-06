import pytest
from sqlalchemy import select
from app.models.team import TeamNode, TeamEra
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType
from app.models.precomputed_layout import PrecomputedLayout
from app.services.family_discovery import FamilyDiscoveryService

@pytest.mark.asyncio
async def test_family_merger_leaves_ghost_records(isolated_session):
    """
    Reproduction: Family merger should not leave old 'ghost' fragments in the DB.
    Currently, adding a link that merges two families results in 3 records:
    [Old Family A (stale), Old Family B (stale), New Merged Family (active)]
    
    Expected: Only 1 record (the active merger).
    """
    # 1. Setup: Create two separate families
    # Family A: Node 1 -> Node 2
    n1 = TeamNode(founding_year=2000, legal_name="Team A1")
    n2 = TeamNode(founding_year=2005, legal_name="Team A2")
    isolated_session.add_all([n1, n2])
    await isolated_session.flush()
    l1 = LineageEvent(
        predecessor_node_id=n1.node_id, 
        successor_node_id=n2.node_id, 
        event_year=2005, 
        event_type=LineageEventType.MERGE
    )
    isolated_session.add(l1)
    
    # Family B: Node 3 -> Node 4
    n3 = TeamNode(founding_year=2010, legal_name="Team B1")
    n4 = TeamNode(founding_year=2015, legal_name="Team B2")
    isolated_session.add_all([n3, n4])
    await isolated_session.flush()
    l2 = LineageEvent(
        predecessor_node_id=n3.node_id, 
        successor_node_id=n4.node_id, 
        event_year=2015, 
        event_type=LineageEventType.MERGE
    )
    isolated_session.add(l2)
    await isolated_session.commit()
    
    # 2. Initial Discovery
    service = FamilyDiscoveryService(isolated_session)
    await service.discover_all_families()
    
    stmt = select(PrecomputedLayout)
    layouts = (await isolated_session.execute(stmt)).scalars().all()
    assert len(layouts) == 2, "Initially there should be 2 separate families"
    
    # 3. Merge: Connect A2 to B1
    l_merge = LineageEvent(
        predecessor_node_id=n2.node_id,
        successor_node_id=n3.node_id,
        event_year=2010,
        event_type=LineageEventType.MERGE
    )
    isolated_session.add(l_merge)
    await isolated_session.commit()
    
    # 4. Re-Discovery
    await service.discover_all_families()
    
    # Check layouts
    result = await isolated_session.execute(select(PrecomputedLayout))
    all_layouts = result.scalars().all()
    
    # THIS ASSERTION IS EXPECTED TO FAIL CURRENTLY
    # It will likely be 3 (2 old + 1 new)
    assert len(all_layouts) == 1, f"Expected 1 merged family, found {len(all_layouts)}"

@pytest.mark.asyncio
async def test_internal_family_change_leaves_ghost_record(isolated_session):
    """
    Reproduction: Adding a link within an existing family should prune the previous structural hash.
    Expected: Only 1 record (the updated one).
    """
    # 1. Setup: Family with 3 nodes and 1 link
    n1 = TeamNode(founding_year=2000, legal_name="Node 1")
    n2 = TeamNode(founding_year=2000, legal_name="Node 2")
    n3 = TeamNode(founding_year=2010, legal_name="Node 3")
    isolated_session.add_all([n1, n2, n3])
    await isolated_session.flush()
    
    l1 = LineageEvent(
        predecessor_node_id=n1.node_id,
        successor_node_id=n3.node_id,
        event_year=2010,
        event_type=LineageEventType.MERGE
    )
    isolated_session.add(l1)
    await isolated_session.commit()
    
    # 2. Initial Discovery
    service = FamilyDiscoveryService(isolated_session)
    await service.discover_all_families()
    
    stmt = select(PrecomputedLayout)
    layouts = (await isolated_session.execute(stmt)).scalars().all()
    assert len(layouts) == 1
    
    # 3. Structural Change: Link n2 to n3 as well
    l2 = LineageEvent(
        predecessor_node_id=n2.node_id,
        successor_node_id=n3.node_id,
        event_year=2010,
        event_type=LineageEventType.MERGE
    )
    isolated_session.add(l2)
    await isolated_session.commit()
    
    # 4. Re-Discovery
    await service.discover_all_families()
    
    # Check layouts
    result = await isolated_session.execute(select(PrecomputedLayout))
    all_layouts = result.scalars().all()
    
    # THIS ASSERTION IS EXPECTED TO FAIL CURRENTLY
    # It will likely be 2 (1 stale + 1 new)
    assert len(all_layouts) == 1, f"Expected 1 updated family, found {len(all_layouts)}"
    
def test_node_to_family_pruning_logic():
    # Helper to test the core logic of identifying superseded layouts
    from sqlalchemy import String
    from app.models.precomputed_layout import PrecomputedLayout
    
    # Mock node IDs in fingerprint
    f1 = {"node_ids": ["A", "B"]}
    f2 = {"node_ids": ["B", "C"]}
    
    # If a new component has nodes ["A", "B", "C"], it should prune both f1 and f2
    pass
