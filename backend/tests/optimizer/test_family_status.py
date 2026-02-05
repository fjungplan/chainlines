import pytest
from datetime import datetime
from sqlalchemy import select
from app.models.precomputed_layout import PrecomputedLayout
from app.models.team import TeamNode
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType
from app.optimizer.runner import run_optimization, _optimization_status
from app.services.family_discovery import FamilyDiscoveryService

@pytest.mark.asyncio
async def test_family_status_lifecycle(isolated_session):
    """
    Test the full lifecycle of family statuses:
    pending -> optimizing -> cached -> stale -> optimizing -> cached
    """
    # 1. Setup: Create a simple family (2 nodes, 1 link)
    node1 = TeamNode(founding_year=2000, legal_name="Status Test Team A")
    node2 = TeamNode(founding_year=2005, legal_name="Status Test Team B")
    isolated_session.add_all([node1, node2])
    await isolated_session.flush()
    
    link = LineageEvent(
        predecessor_node_id=node1.node_id,
        successor_node_id=node2.node_id,
        event_year=2005,
        event_type=LineageEventType.MERGE
    )
    isolated_session.add(link)
    await isolated_session.commit()
    
    # 2. Discovery: Should be 'pending' initially
    service = FamilyDiscoveryService(isolated_session, complexity_threshold=1)
    await service.discover_all_families()
    
    stmt = select(PrecomputedLayout)
    layout = (await isolated_session.execute(stmt)).scalar_one()
    
    # helper to get status from API logic (mocked here)
    def determine_status(l, active_hashes):
        if l.family_hash in active_hashes:
            return "optimizing"
        if getattr(l, 'is_stale', False):
            return "stale"
        if l.optimized_at is None:
            return "pending"
        return "cached"

    assert determine_status(layout, set()) == "pending"

    # 3. Optimizing: Trigger optimization and check status
    family_hash = layout.family_hash
    _optimization_status["active_hashes"] = {family_hash} # Manual inject for test
    assert determine_status(layout, _optimization_status["active_hashes"]) == "optimizing"
    
    # 4. Cached: Run optimization (actual run)
    _optimization_status["active_hashes"].clear()
    await run_optimization([family_hash], isolated_session)
    await isolated_session.refresh(layout)
    
    assert layout.score >= 0
    assert determine_status(layout, set()) == "cached"
    assert layout.is_stale is False

    # 5. Stale: Update node structure
    node1.founding_year = 2005
    await isolated_session.commit()
    await isolated_session.refresh(layout)
    
    # Verify hooks correctly marked it as stale
    assert layout.is_stale is True
    assert determine_status(layout, set()) == "stale"

    # 6. Back to Optimizing
    _optimization_status["active_hashes"] = {family_hash}
    assert determine_status(layout, _optimization_status["active_hashes"]) == "optimizing"
    
    # 7. Final Cached
    _optimization_status["active_hashes"].clear()
    await run_optimization([family_hash], isolated_session)
    await isolated_session.refresh(layout)
    assert layout.is_stale is False
    assert determine_status(layout, set()) == "cached"
