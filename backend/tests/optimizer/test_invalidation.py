"""
Tests for invalidation hooks.
Verifies that SQLAlchemy event hooks correctly detect when layouts need invalidation.
"""
import pytest
import uuid
from app.models.team import TeamNode
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType
from app.optimizer.invalidation_hooks import InvalidationTracker


@pytest.fixture
def invalidation_tracker():
    """Fixture to track invalidation events"""
    tracker = InvalidationTracker()
    tracker.clear()
    return tracker


@pytest.mark.asyncio
async def test_hook_fires_on_founding_year_change(isolated_session, invalidation_tracker):
    """Invalidation should fire when team founding_year changes"""
    # Create a team
    team = TeamNode(
        legal_name="Test Team",
        founding_year=2000,
        dissolution_year=None
    )
    isolated_session.add(team)
    await isolated_session.commit()
    
    # Clear tracker after initial creation
    invalidation_tracker.clear()
    
    # Update founding year
    team.founding_year = 2001
    await isolated_session.commit()
    
    # Should have triggered invalidation
    assert len(invalidation_tracker.invalidated_nodes) > 0
    assert team.node_id in invalidation_tracker.invalidated_nodes


@pytest.mark.asyncio
async def test_hook_fires_on_dissolution_year_change(isolated_session, invalidation_tracker):
    """Invalidation should fire when team dissolution_year changes"""
    # Create a team
    team = TeamNode(
        legal_name="Test Team 2",
        founding_year=2000,
        dissolution_year=2010
    )
    isolated_session.add(team)
    await isolated_session.commit()
    
    # Clear tracker
    invalidation_tracker.clear()
    
    # Update dissolution year
    team.dissolution_year = 2011
    await isolated_session.commit()
    
    # Should have triggered invalidation
    assert len(invalidation_tracker.invalidated_nodes) > 0
    assert team.node_id in invalidation_tracker.invalidated_nodes


@pytest.mark.asyncio
async def test_hook_does_not_fire_on_name_change(isolated_session, invalidation_tracker):
    """Invalidation should NOT fire when only team name changes"""
    # Create a team
    team = TeamNode(
        legal_name="Test Team 3",
        founding_year=2000,
        dissolution_year=None
    )
    isolated_session.add(team)
    await isolated_session.commit()
    
    # Clear tracker
    invalidation_tracker.clear()
    
    # Update only name (metadata)
    team.display_name = "New Display Name"
    await isolated_session.commit()
    
    # Should NOT have triggered invalidation
    assert len(invalidation_tracker.invalidated_nodes) == 0


@pytest.mark.asyncio
async def test_hook_fires_on_lineage_event_insert(isolated_session, invalidation_tracker):
    """Invalidation should fire when lineage event is added"""
    # Create two teams
    team1 = TeamNode(
        legal_name="Team A",
        founding_year=2000,
        dissolution_year=2010
    )
    team2 = TeamNode(
        legal_name="Team B",
        founding_year=2011,
        dissolution_year=None
    )
    isolated_session.add_all([team1, team2])
    await isolated_session.commit()
    
    # Clear tracker
    invalidation_tracker.clear()
    
    # Add lineage event
    event = LineageEvent(
        predecessor_node_id=team1.node_id,
        successor_node_id=team2.node_id,
        event_year=2010,
        event_type=LineageEventType.LEGAL_TRANSFER
    )
    isolated_session.add(event)
    await isolated_session.commit()
    
    # Should have triggered invalidation for both nodes
    assert len(invalidation_tracker.invalidated_nodes) > 0
    assert team1.node_id in invalidation_tracker.invalidated_nodes or team2.node_id in invalidation_tracker.invalidated_nodes


@pytest.mark.asyncio
async def test_hook_fires_on_lineage_event_update(isolated_session, invalidation_tracker):
    """Invalidation should fire when lineage event year changes"""
    # Create two teams and a lineage event
    team1 = TeamNode(
        legal_name="Team C",
        founding_year=2000,
        dissolution_year=2010
    )
    team2 = TeamNode(
        legal_name="Team D",
        founding_year=2011,
        dissolution_year=None
    )
    isolated_session.add_all([team1, team2])
    await isolated_session.commit()
    
    event = LineageEvent(
        predecessor_node_id=team1.node_id,
        successor_node_id=team2.node_id,
        event_year=2010,
        event_type=LineageEventType.LEGAL_TRANSFER
    )
    isolated_session.add(event)
    await isolated_session.commit()
    
    # Clear tracker
    invalidation_tracker.clear()
    
    # Update event year
    event.event_year = 2011
    await isolated_session.commit()
    
    # Should have triggered invalidation
    assert len(invalidation_tracker.invalidated_nodes) > 0


@pytest.mark.asyncio
async def test_hook_fires_on_lineage_event_delete(isolated_session, invalidation_tracker):
    """Invalidation should fire when lineage event is deleted"""
    # Create two teams and a lineage event
    team1 = TeamNode(
        legal_name="Team E",
        founding_year=2000,
        dissolution_year=2010
    )
    team2 = TeamNode(
        legal_name="Team F",
        founding_year=2011,
        dissolution_year=None
    )
    isolated_session.add_all([team1, team2])
    await isolated_session.commit()
    
    event = LineageEvent(
        predecessor_node_id=team1.node_id,
        successor_node_id=team2.node_id,
        event_year=2010,
        event_type=LineageEventType.LEGAL_TRANSFER
    )
    isolated_session.add(event)
    await isolated_session.commit()
    
    # Clear tracker
    invalidation_tracker.clear()
    
    # Delete event
    await isolated_session.delete(event)
    await isolated_session.commit()
    
    # Should have triggered invalidation
    assert len(invalidation_tracker.invalidated_nodes) > 0
