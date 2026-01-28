"""
Tests for FamilyDiscoveryService.

Tests the service that discovers and registers complex families for optimization.
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.services.family_discovery import FamilyDiscoveryService
from app.models.team import TeamNode
from app.models.lineage import LineageEvent
from app.models.precomputed_layout import PrecomputedLayout
from app.models.enums import LineageEventType
from sqlalchemy import select


@pytest.mark.asyncio
async def test_find_connected_component_single_node(db_session):
    """Test finding component for isolated node."""
    node = TeamNode(
        node_id=uuid4(),
        legal_name="Isolated Team",
        founding_year=2000
    )
    db_session.add(node)
    await db_session.commit()
    
    service = FamilyDiscoveryService(db_session)
    component = await service.find_connected_component(node.node_id)
    
    assert len(component) == 1
    assert component[0].node_id == node.node_id


@pytest.mark.asyncio
async def test_find_connected_component_linear_chain(db_session):
    """Test finding component for linear chain A -> B -> C."""
    node_a = TeamNode(node_id=uuid4(), legal_name="Team A", founding_year=2000)
    node_b = TeamNode(node_id=uuid4(), legal_name="Team B", founding_year=2005)
    node_c = TeamNode(node_id=uuid4(), legal_name="Team C", founding_year=2010)
    
    db_session.add_all([node_a, node_b, node_c])
    await db_session.flush()
    
    link_ab = LineageEvent(
        predecessor_node_id=node_a.node_id,
        successor_node_id=node_b.node_id,
        event_year=2005,
        event_type=LineageEventType.LEGAL_TRANSFER
    )
    link_bc = LineageEvent(
        predecessor_node_id=node_b.node_id,
        successor_node_id=node_c.node_id,
        event_year=2010,
        event_type=LineageEventType.LEGAL_TRANSFER
    )
    
    db_session.add_all([link_ab, link_bc])
    await db_session.commit()
    
    service = FamilyDiscoveryService(db_session)
    component = await service.find_connected_component(node_b.node_id)
    
    assert len(component) == 3
    node_ids = {n.node_id for n in component}
    assert node_a.node_id in node_ids
    assert node_b.node_id in node_ids
    assert node_c.node_id in node_ids


@pytest.mark.asyncio
async def test_find_connected_component_complex_family(db_session):
    """Test finding component for complex family with splits and merges."""
    # Create diamond pattern: A -> (B, C) -> D
    node_a = TeamNode(node_id=uuid4(), legal_name="Team A", founding_year=2000)
    node_b = TeamNode(node_id=uuid4(), legal_name="Team B", founding_year=2005)
    node_c = TeamNode(node_id=uuid4(), legal_name="Team C", founding_year=2005)
    node_d = TeamNode(node_id=uuid4(), legal_name="Team D", founding_year=2010)
    
    db_session.add_all([node_a, node_b, node_c, node_d])
    await db_session.flush()
    
    links = [
        LineageEvent(
            predecessor_node_id=node_a.node_id,
            successor_node_id=node_b.node_id,
            event_year=2005,
            event_type=LineageEventType.SPLIT
        ),
        LineageEvent(
            predecessor_node_id=node_a.node_id,
            successor_node_id=node_c.node_id,
            event_year=2005,
            event_type=LineageEventType.SPLIT
        ),
        LineageEvent(
            predecessor_node_id=node_b.node_id,
            successor_node_id=node_d.node_id,
            event_year=2010,
            event_type=LineageEventType.MERGE
        ),
        LineageEvent(
            predecessor_node_id=node_c.node_id,
            successor_node_id=node_d.node_id,
            event_year=2010,
            event_type=LineageEventType.MERGE
        ),
    ]
    
    db_session.add_all(links)
    await db_session.commit()
    
    service = FamilyDiscoveryService(db_session)
    component = await service.find_connected_component(node_d.node_id)
    
    assert len(component) == 4


@pytest.mark.asyncio
async def test_assess_family_below_threshold(db_session):
    """Test that small families are not registered."""
    # Create small family (3 nodes < 20 threshold)
    nodes = [
        TeamNode(node_id=uuid4(), legal_name=f"Team {i}", founding_year=2000 + i*5)
        for i in range(3)
    ]
    db_session.add_all(nodes)
    await db_session.flush()
    
    link = LineageEvent(
        predecessor_node_id=nodes[0].node_id,
        successor_node_id=nodes[1].node_id,
        event_year=2005,
        event_type=LineageEventType.LEGAL_TRANSFER
    )
    db_session.add(link)
    await db_session.commit()
    
    service = FamilyDiscoveryService(db_session, complexity_threshold=20)
    result = await service.assess_family(nodes[0].node_id)
    
    assert result is None  # Should not register small family
    
    # Verify no PrecomputedLayout was created
    stmt = select(PrecomputedLayout)
    layouts = (await db_session.execute(stmt)).scalars().all()
    assert len(layouts) == 0


@pytest.mark.asyncio
async def test_assess_family_above_threshold_creates_record(db_session):
    """Test that complex families are registered."""
    # Create large family (25 nodes > 20 threshold)
    nodes = [
        TeamNode(node_id=uuid4(), legal_name=f"Team {i}", founding_year=2000)
        for i in range(25)
    ]
    db_session.add_all(nodes)
    await db_session.flush()
    
    # Create linear chain to connect all nodes
    links = [
        LineageEvent(
            predecessor_node_id=nodes[i].node_id,
            successor_node_id=nodes[i+1].node_id,
            event_year=2000,
            event_type=LineageEventType.LEGAL_TRANSFER
        )
        for i in range(24)
    ]
    db_session.add_all(links)
    await db_session.commit()
    
    service = FamilyDiscoveryService(db_session, complexity_threshold=20)
    result = await service.assess_family(nodes[0].node_id)
    
    assert result is not None
    assert "family_hash" in result
    assert result["node_count"] == 25
    assert result["link_count"] == 24
    
    # Verify PrecomputedLayout was created
    stmt = select(PrecomputedLayout).where(
        PrecomputedLayout.family_hash == result["family_hash"]
    )
    layout = (await db_session.execute(stmt)).scalar_one_or_none()
    
    assert layout is not None
    assert layout.family_hash == result["family_hash"]
    assert layout.score == 0.0  # Initial placeholder score


@pytest.mark.asyncio
async def test_assess_family_idempotent(db_session):
    """Test that assessing the same family twice doesn't create duplicates."""
    # Create large family
    nodes = [
        TeamNode(node_id=uuid4(), legal_name=f"Team {i}", founding_year=2000)
        for i in range(25)
    ]
    db_session.add_all(nodes)
    await db_session.flush()
    
    links = [
        LineageEvent(
            predecessor_node_id=nodes[i].node_id,
            successor_node_id=nodes[i+1].node_id,
            event_year=2000,
            event_type=LineageEventType.LEGAL_TRANSFER
        )
        for i in range(24)
    ]
    db_session.add_all(links)
    await db_session.commit()
    
    service = FamilyDiscoveryService(db_session, complexity_threshold=20)
    
    # First assessment
    result1 = await service.assess_family(nodes[0].node_id)
    
    # Second assessment
    result2 = await service.assess_family(nodes[10].node_id)
    
    # Should return same hash
    assert result1["family_hash"] == result2["family_hash"]
    
    # Should only have one record
    stmt = select(PrecomputedLayout)
    layouts = (await db_session.execute(stmt)).scalars().all()
    assert len(layouts) == 1


@pytest.mark.asyncio
async def test_discover_all_families(db_session):
    """Test discovering all families in the database."""
    # Create two separate families
    # Family 1: 25 nodes (complex)
    family1_nodes = [
        TeamNode(node_id=uuid4(), legal_name=f"F1-Team {i}", founding_year=2000)
        for i in range(25)
    ]
    db_session.add_all(family1_nodes)
    await db_session.flush()
    
    family1_links = [
        LineageEvent(
            predecessor_node_id=family1_nodes[i].node_id,
            successor_node_id=family1_nodes[i+1].node_id,
            event_year=2000,
            event_type=LineageEventType.LEGAL_TRANSFER
        )
        for i in range(24)
    ]
    db_session.add_all(family1_links)
    
    # Family 2: 5 nodes (simple, should be skipped)
    family2_nodes = [
        TeamNode(node_id=uuid4(), legal_name=f"F2-Team {i}", founding_year=2010)
        for i in range(5)
    ]
    db_session.add_all(family2_nodes)
    await db_session.flush()
    
    family2_links = [
        LineageEvent(
            predecessor_node_id=family2_nodes[i].node_id,
            successor_node_id=family2_nodes[i+1].node_id,
            event_year=2010,
            event_type=LineageEventType.LEGAL_TRANSFER
        )
        for i in range(4)
    ]
    db_session.add_all(family2_links)
    await db_session.commit()
    
    service = FamilyDiscoveryService(db_session, complexity_threshold=20)
    results = await service.discover_all_families()
    
    # Should only register the complex family
    assert len(results) == 1
    assert results[0]["node_count"] == 25
    
    # Verify database state
    stmt = select(PrecomputedLayout)
    layouts = (await db_session.execute(stmt)).scalars().all()
    assert len(layouts) == 1
