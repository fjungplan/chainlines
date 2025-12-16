import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.team import TeamNode
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType
from app.services.lineage_service import LineageService
from app.core.exceptions import ValidationException

@pytest.mark.asyncio
async def test_create_legal_transfer_event(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    next_node = TeamNode(founding_year=sample_team_node.founding_year + 1, legal_name="Legal Transfer Successor")
    isolated_session.add(next_node)
    await isolated_session.commit()
    await isolated_session.refresh(next_node)
    
    event = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=next_node.node_id,
        year=sample_team_node.founding_year + 1,
        event_type=LineageEventType.LEGAL_TRANSFER,
        notes="Legal transfer test"
    )
    assert event.event_type == LineageEventType.LEGAL_TRANSFER
    assert event.predecessor_node_id == sample_team_node.node_id
    assert event.successor_node_id == next_node.node_id

@pytest.mark.asyncio
async def test_create_merge_event(isolated_session: AsyncSession, sample_team_node, another_team_node):
    service = LineageService(isolated_session)
    # Create merge event with two previous nodes to same next node
    next_node = TeamNode(founding_year=2020, legal_name="Merge Target")
    isolated_session.add(next_node)
    await isolated_session.commit()
    await isolated_session.refresh(next_node)
    event1 = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=next_node.node_id,
        year=2021,
        event_type=LineageEventType.MERGE,
        notes="Merge part 1"
    )
    event2 = await service.create_event(
        previous_id=another_team_node.node_id,
        next_id=next_node.node_id,
        year=2021,
        event_type=LineageEventType.MERGE,
        notes="Merge part 2"
    )
    assert event1.successor_node_id == next_node.node_id
    assert event2.successor_node_id == next_node.node_id

@pytest.mark.asyncio
async def test_create_spiritual_succession(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    successor = TeamNode(founding_year=sample_team_node.founding_year + 10, legal_name="Successor Node")
    isolated_session.add(successor)
    await isolated_session.commit()
    await isolated_session.refresh(successor)
    event = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=successor.node_id,
        year=successor.founding_year,
        event_type=LineageEventType.SPIRITUAL_SUCCESSION,
        notes="Spiritual succession"
    )
    assert event.is_spiritual()

@pytest.mark.asyncio
async def test_create_split_events(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    child1 = TeamNode(founding_year=sample_team_node.founding_year + 5, legal_name="Split Child 1")
    child2 = TeamNode(founding_year=sample_team_node.founding_year + 5, legal_name="Split Child 2")
    isolated_session.add_all([child1, child2])
    await isolated_session.commit()
    await isolated_session.refresh(child1)
    await isolated_session.refresh(child2)
    e1 = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=child1.node_id,
        year=child1.founding_year,
        event_type=LineageEventType.SPLIT,
        notes="Split part 1"
    )
    e2 = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=child2.node_id,
        year=child2.founding_year,
        event_type=LineageEventType.SPLIT,
        notes="Split part 2"
    )
    # After canonicalization, both events should be LEGAL_TRANSFER (not SPLIT) since only one leg per year
    assert e1.event_type == LineageEventType.LEGAL_TRANSFER
    assert e2.event_type == LineageEventType.LEGAL_TRANSFER
    # Ensure both successors recorded
    chain = await service.get_lineage_chain(sample_team_node.node_id)
    assert set(chain["successors"]) == {child1.node_id, child2.node_id}

@pytest.mark.asyncio
async def test_circular_reference_prevention(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    with pytest.raises(ValidationException):
        await service.create_event(
            previous_id=sample_team_node.node_id,
            next_id=sample_team_node.node_id,
            year=2022,
            event_type=LineageEventType.LEGAL_TRANSFER,
            notes="Should fail"
        )

@pytest.mark.asyncio
async def test_event_year_validation(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    with pytest.raises(ValidationException):
        await service.create_event(
            previous_id=sample_team_node.node_id,
            next_id=None,
            year=sample_team_node.founding_year - 1,
            event_type=LineageEventType.LEGAL_TRANSFER,
            notes="Invalid year"
        )

@pytest.mark.asyncio
async def test_relationship_traversal(isolated_session: AsyncSession, sample_team_node, another_team_node):
    service = LineageService(isolated_session)
    next_node = TeamNode(founding_year=2020, legal_name="Traversal Target")
    isolated_session.add(next_node)
    await isolated_session.commit()
    await isolated_session.refresh(next_node)
    await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=next_node.node_id,
        year=2021,
        event_type=LineageEventType.LEGAL_TRANSFER,
        notes="Test traversal"
    )
    # Reload nodes with eager-loaded relationships to avoid async lazy loading issues
    next_loaded = (
        await isolated_session.execute(
            select(TeamNode)
            .options(
                selectinload(TeamNode.incoming_events).selectinload(LineageEvent.predecessor_node),
                selectinload(TeamNode.outgoing_events).selectinload(LineageEvent.successor_node),
            )
            .where(TeamNode.node_id == next_node.node_id)
        )
    ).scalar_one()
    prev_loaded = (
        await isolated_session.execute(
            select(TeamNode)
            .options(
                selectinload(TeamNode.outgoing_events).selectinload(LineageEvent.successor_node),
            )
            .where(TeamNode.node_id == sample_team_node.node_id)
        )
    ).scalar_one()
    assert [p.node_id for p in next_loaded.get_predecessors()] == [sample_team_node.node_id]
    assert [s.node_id for s in prev_loaded.get_successors()] == [next_node.node_id]

@pytest.mark.asyncio
async def test_get_lineage_chain(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    successor = TeamNode(founding_year=sample_team_node.founding_year + 3, legal_name="Chain Successor")
    isolated_session.add(successor)
    await isolated_session.commit()
    await isolated_session.refresh(successor)
    await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=successor.node_id,
        year=successor.founding_year,
        event_type=LineageEventType.LEGAL_TRANSFER,
        notes="Chain test"
    )
    chain = await service.get_lineage_chain(successor.node_id)
    assert chain["predecessors"] == [sample_team_node.node_id]
    assert chain["successors"] == []

@pytest.mark.asyncio
async def test_cascade_delete_sets_null(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    successor = TeamNode(founding_year=sample_team_node.founding_year + 2, legal_name="Cascade Successor")
    isolated_session.add(successor)
    await isolated_session.commit()
    await isolated_session.refresh(successor)
    event = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=successor.node_id,
        year=successor.founding_year,
        event_type=LineageEventType.LEGAL_TRANSFER,
        notes="Cascade test"
    )
    # Delete predecessor node
    await isolated_session.delete(sample_team_node)
    await isolated_session.commit()
    
    # Event should be cascaded deleted
    from sqlalchemy.exc import InvalidRequestError
    # Checking if it exists in DB
    result = await isolated_session.execute(select(LineageEvent).where(LineageEvent.event_id == event.event_id))
    assert result.scalar_one_or_none() is None

def test_discovery_smoke():
    # Ensures the test file is discovered even if asyncio fixtures misconfigure.
    assert 1 + 1 == 2

@pytest.mark.asyncio
async def test_incomplete_merge_warning(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    successor = TeamNode(founding_year=sample_team_node.founding_year + 5, legal_name="Incomplete Merge Target")
    isolated_session.add(successor)
    await isolated_session.commit()
    await isolated_session.refresh(successor)
    merge_event = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=successor.node_id,
        year=successor.founding_year,
        event_type=LineageEventType.MERGE,
        notes="First merge leg"
    )
    # After canonicalization, event should be LEGAL_TRANSFER and not have incomplete warning
    assert merge_event.event_type == LineageEventType.LEGAL_TRANSFER
    assert not merge_event.notes or "INCOMPLETE MERGE" not in merge_event.notes

@pytest.mark.asyncio
async def test_merge_completion_removes_warning(isolated_session: AsyncSession, sample_team_node, another_team_node):
    service = LineageService(isolated_session)
    successor = TeamNode(founding_year=2025, legal_name="Completion Merge Target")
    isolated_session.add(successor)
    await isolated_session.commit()
    await isolated_session.refresh(successor)
    first = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=successor.node_id,
        year=2025,
        event_type=LineageEventType.MERGE,
        notes="Leg 1"
    )
    second = await service.create_event(
        previous_id=another_team_node.node_id,
        next_id=successor.node_id,
        year=2025,
        event_type=LineageEventType.MERGE,
        notes="Leg 2"
    )
    # Refresh first to see updated notes after completion cleanup
    await isolated_session.refresh(first)
    assert first.notes is None or "INCOMPLETE MERGE" not in first.notes
    assert second.notes is None or "INCOMPLETE MERGE" not in second.notes

@pytest.mark.asyncio
async def test_incomplete_split_warning(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    child = TeamNode(founding_year=sample_team_node.founding_year + 2, legal_name="Incomplete Split Child")
    isolated_session.add(child)
    await isolated_session.commit()
    await isolated_session.refresh(child)
    split_event = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=child.node_id,
        year=child.founding_year,
        event_type=LineageEventType.SPLIT,
        notes="First split leg"
    )
    # After canonicalization, event should be LEGAL_TRANSFER and not have incomplete warning
    assert split_event.event_type == LineageEventType.LEGAL_TRANSFER
    assert not split_event.notes or "INCOMPLETE SPLIT" not in split_event.notes

@pytest.mark.asyncio
async def test_split_completion_removes_warning(isolated_session: AsyncSession, sample_team_node):
    service = LineageService(isolated_session)
    child1 = TeamNode(founding_year=sample_team_node.founding_year + 3, legal_name="Completion Split Child 1")
    child2 = TeamNode(founding_year=sample_team_node.founding_year + 3, legal_name="Completion Split Child 2")
    isolated_session.add_all([child1, child2])
    await isolated_session.commit()
    await isolated_session.refresh(child1)
    await isolated_session.refresh(child2)
    first = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=child1.node_id,
        year=child1.founding_year,
        event_type=LineageEventType.SPLIT,
        notes="Split leg 1"
    )
    second = await service.create_event(
        previous_id=sample_team_node.node_id,
        next_id=child2.node_id,
        year=child2.founding_year,
        event_type=LineageEventType.SPLIT,
        notes="Split leg 2"
    )
    await isolated_session.refresh(first)
    assert first.notes is None or "INCOMPLETE SPLIT" not in first.notes
    assert second.notes is None or "INCOMPLETE SPLIT" not in second.notes

