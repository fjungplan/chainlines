"""
SQLAlchemy event hooks for automatic layout invalidation.

Listens for changes to TeamNode and LineageEvent that affect layout structure
and marks affected families as needing recomputation.
"""
import uuid
from typing import Set
from sqlalchemy import event, String
from sqlalchemy.orm import Session
from app.models.team import TeamNode
from app.models.lineage import LineageEvent


class InvalidationTracker:
    """
    Singleton tracker for invalidation events during testing.
    In production, this would trigger actual database updates.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.invalidated_nodes: Set[uuid.UUID] = set()
        return cls._instance
    
    def clear(self):
        """Clear tracked invalidations"""
        self.invalidated_nodes.clear()
    
    def mark_node_invalidated(self, node_id: uuid.UUID):
        """Mark a node as needing layout recomputation"""
        self.invalidated_nodes.add(node_id)


# Global tracker instance
_tracker = InvalidationTracker()


def _should_invalidate_node_update(target: TeamNode, old_values: dict) -> bool:
    """
    Determine if a TeamNode update requires invalidation.
    
    Only structural changes (founding_year, dissolution_year) trigger invalidation.
    Metadata changes (names, etc.) do not.
    """
    # Check if founding_year changed
    if hasattr(target, 'founding_year'):
        old_founding = old_values.get('founding_year')
        if old_founding is not None and old_founding != target.founding_year:
            return True
    
    # Check if dissolution_year changed
    if hasattr(target, 'dissolution_year'):
        old_dissolution = old_values.get('dissolution_year')
        if old_dissolution != target.dissolution_year:
            return True
    
    return False


@event.listens_for(TeamNode, 'after_update')
def invalidate_on_node_update(mapper, connection, target):
    """
    Invalidate layouts when TeamNode structural data changes.
    
    Triggers on:
    - founding_year changes
    - dissolution_year changes
    
    Does NOT trigger on:
    - name changes
    - metadata changes
    """
    # Get old values from history
    from sqlalchemy import inspect
    insp = inspect(target)
    
    old_values = {}
    for attr in insp.attrs:
        hist = attr.load_history()
        if hist.has_changes():
            old_values[attr.key] = hist.deleted[0] if hist.deleted else None
    
    if _should_invalidate_node_update(target, old_values):
        _tracker.mark_node_invalidated(target.node_id)
        
        # Mark affected families as stale in DB
        from app.models.precomputed_layout import PrecomputedLayout
        from sqlalchemy import update
        
        node_id_str = str(target.node_id)
        # We use a LIKE search for the node_id string within the JSON/JSONB field
        # to remain relatively cross-db compatible for tests vs production.
        stmt = (
            update(PrecomputedLayout)
            .where(PrecomputedLayout.data_fingerprint.cast(String).like(f'%{node_id_str}%'))
            .values(is_stale=True)
        )
        connection.execute(stmt)


@event.listens_for(LineageEvent, 'after_insert')
def invalidate_on_link_insert(mapper, connection, target):
    """
    Invalidate layouts when a new lineage event is created.
    
    This handles the case where a new link connects to existing nodes,
    potentially merging families or creating new family structures.
    
    IMPORTANT: This is also the trigger for "Continuous Discovery".
    When a new link is added, it may cause a small family to grow beyond
    the complexity threshold, requiring registration for optimization.
    
    In production, this should enqueue a background task:
        assess_family_complexity(target.predecessor_node_id)
    
    The task will:
    1. Find the connected component containing this node
    2. Check if size > threshold (e.g., 20 nodes)
    3. If yes, ensure a PrecomputedLayout record exists
    4. If record exists, mark it as stale (hash will differ)
    """
    _tracker.mark_node_invalidated(target.predecessor_node_id)
    _tracker.mark_node_invalidated(target.successor_node_id)
    
    # Mark affected families as stale in DB
    from app.models.precomputed_layout import PrecomputedLayout
    from sqlalchemy import update
    
    pred_str = str(target.predecessor_node_id)
    succ_str = str(target.successor_node_id)
    
    stmt = (
        update(PrecomputedLayout)
        .where(
            (PrecomputedLayout.data_fingerprint.cast(String).like(f'%{pred_str}%')) |
            (PrecomputedLayout.data_fingerprint.cast(String).like(f'%{succ_str}%'))
        )
        .values(is_stale=True)
    )
    connection.execute(stmt)
    
    # TODO: In production, enqueue background task:
    # from app.tasks import assess_family_complexity
    # assess_family_complexity.delay(target.predecessor_node_id)
    #
    # For now, this is handled by periodic discovery sweeps or manual triggers


@event.listens_for(LineageEvent, 'after_update')
def invalidate_on_link_update(mapper, connection, target):
    """
    Invalidate layouts when a lineage event changes.
    
    Triggers on event_year changes or event_type changes.
    """
    _tracker.mark_node_invalidated(target.predecessor_node_id)
    _tracker.mark_node_invalidated(target.successor_node_id)
    
    from app.models.precomputed_layout import PrecomputedLayout
    from sqlalchemy import update
    
    pred_str = str(target.predecessor_node_id)
    succ_str = str(target.successor_node_id)
    
    stmt = (
        update(PrecomputedLayout)
        .where(
            (PrecomputedLayout.data_fingerprint.cast(String).like(f'%{pred_str}%')) |
            (PrecomputedLayout.data_fingerprint.cast(String).like(f'%{succ_str}%'))
        )
        .values(is_stale=True)
    )
    connection.execute(stmt)


@event.listens_for(LineageEvent, 'after_delete')
def invalidate_on_link_delete(mapper, connection, target):
    """
    Invalidate layouts when a lineage event is deleted.
    
    This may split a family into multiple families.
    """
    _tracker.mark_node_invalidated(target.predecessor_node_id)
    _tracker.mark_node_invalidated(target.successor_node_id)
    # In production: invalidate families containing either node
