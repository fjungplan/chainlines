from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.lineage import LineageEvent
from app.models.team import TeamNode
from app.models.enums import LineageEventType
from app.core.exceptions import ValidationException
import uuid
from app.services.timeline_service import TimelineService

class LineageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(
        self,
        previous_id: Optional[uuid.UUID],
        next_id: Optional[uuid.UUID],
        year: int,
        event_type: LineageEventType,
        notes: Optional[str] = None,
    ) -> LineageEvent:
        # Validation: at least one node
        if not previous_id and not next_id:
            raise ValidationException("At least one of previous_id or next_id must be set.")
        # Fetch nodes
        previous_node = None
        next_node = None
        if previous_id:
            previous_node = await self.db.get(TeamNode, previous_id)
            if not previous_node:
                raise ValidationException("Previous node not found.")
        if next_id:
            next_node = await self.db.get(TeamNode, next_id)
            if not next_node:
                raise ValidationException("Next node not found.")
        # Year validation
        if previous_node and year < previous_node.founding_year:
            raise ValidationException("event_year cannot be before previous node's founding_year.")
        if next_node and next_node.dissolution_year and year > next_node.dissolution_year:
            raise ValidationException("event_year cannot be after next node's dissolution_year.")
        # Pre-create checks for MERGE/SPLIT semantics (we allow first event but enforce on second)
        if event_type == LineageEventType.MERGE and not next_id:
            raise ValidationException("MERGE events require a successor (next_id).")
        if event_type == LineageEventType.SPLIT and not previous_id:
            raise ValidationException("SPLIT events require an origin (previous_id).")
        # Prevent circular references
        if previous_id and next_id and previous_id == next_id:
            raise ValidationException("Cannot create circular lineage event.")
        event = LineageEvent(
            predecessor_node_id=previous_id,
            successor_node_id=next_id,
            event_year=year,
            event_type=event_type,
            notes=notes,
        )
        # Model-level validation (timeline bounds etc.)
        # event.validate() 

        self.db.add(event)
        await self.db.commit()
        # Invalidate timeline cache after data change
        TimelineService.invalidate_cache()
        await self.db.refresh(event)

        # Canonicalization: auto-downgrade single-leg MERGE/SPLIT to succession
        if event_type in (LineageEventType.MERGE, LineageEventType.SPLIT):
            if event_type == LineageEventType.MERGE:
                q = await self.db.execute(
                    select(LineageEvent).where(
                        LineageEvent.successor_node_id == next_id,
                        LineageEvent.event_year == year,
                        LineageEvent.event_type == LineageEventType.MERGE,
                    )
                )
                related_events = q.scalars().all()
                if len(related_events) == 1:
                    # Only one leg: auto-downgrade to LEGAL_TRANSFER
                    event.event_type = LineageEventType.LEGAL_TRANSFER
                    # Remove any incomplete warning
                    if event.notes and "INCOMPLETE MERGE" in event.notes:
                        parts = [p.strip() for p in event.notes.split("|") if p.strip() and not p.strip().startswith("INCOMPLETE MERGE")]
                        event.notes = " | ".join(parts) if parts else None
                    self.db.add(event)
                    await self.db.commit()
                    await self.db.refresh(event)
                elif len(related_events) >= 2:
                    # Remove incomplete warnings from all related events
                    incomplete_phrase = "INCOMPLETE MERGE: add another predecessor"
                    changed = False
                    for ev in related_events:
                        if ev.notes and incomplete_phrase in ev.notes:
                            parts = [p.strip() for p in ev.notes.split("|") if p.strip() and p.strip() != incomplete_phrase]
                            ev.notes = " | ".join(parts) if parts else None
                            self.db.add(ev)
                            changed = True
                    if changed:
                        await self.db.commit()
                        await self.db.refresh(event)
            else:  # SPLIT
                q = await self.db.execute(
                    select(LineageEvent).where(
                        LineageEvent.predecessor_node_id == previous_id,
                        LineageEvent.event_year == year,
                        LineageEvent.event_type == LineageEventType.SPLIT,
                    )
                )
                related_events = q.scalars().all()
                if len(related_events) == 1:
                    # Only one leg: auto-downgrade to LEGAL_TRANSFER
                    event.event_type = LineageEventType.LEGAL_TRANSFER
                    if event.notes and "INCOMPLETE SPLIT" in event.notes:
                        parts = [p.strip() for p in event.notes.split("|") if p.strip() and not p.strip().startswith("INCOMPLETE SPLIT")]
                        event.notes = " | ".join(parts) if parts else None
                    self.db.add(event)
                    await self.db.commit()
                    await self.db.refresh(event)
                elif len(related_events) >= 2:
                    incomplete_phrase = "INCOMPLETE SPLIT: add another successor"
                    changed = False
                    for ev in related_events:
                        if ev.notes and incomplete_phrase in ev.notes:
                            parts = [p.strip() for p in ev.notes.split("|") if p.strip() and p.strip() != incomplete_phrase]
                            ev.notes = " | ".join(parts) if parts else None
                            self.db.add(ev)
                            changed = True
                    if changed:
                        await self.db.commit()
                        await self.db.refresh(event)
        return event

    async def get_lineage_chain(self, node_id: uuid.UUID) -> Dict:
        # Return full ancestry/descendants for a node
        result = await self.db.execute(
            select(TeamNode)
            .options(
                # Eager-load lineage relations and eras with sponsors to avoid async lazy-loads
                selectinload(TeamNode.outgoing_events)
                .selectinload(LineageEvent.successor_node)
                .selectinload(TeamNode.eras),
                selectinload(TeamNode.incoming_events)
                .selectinload(LineageEvent.predecessor_node)
                .selectinload(TeamNode.eras),
                selectinload(TeamNode.eras),
            )
            .where(TeamNode.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        if not node:
            raise ValidationException("Node not found.")
        return {
            "node_id": node.node_id,
            "predecessors": [e.predecessor_node_id for e in node.incoming_events if e.predecessor_node_id],
            "successors": [e.successor_node_id for e in node.outgoing_events if e.successor_node_id],
            "era_years": [era.season_year for era in node.eras],
        }

    async def validate_event_timeline(self, event: LineageEvent):
        # Ensure event_year makes sense for connected nodes
        if event.predecessor_node and event.event_year < event.predecessor_node.founding_year:
            raise ValidationException("event_year before previous node's founding_year.")
        if event.successor_node and event.successor_node.dissolution_year and event.event_year > event.successor_node.dissolution_year:
            raise ValidationException("event_year after next node's dissolution_year.")
        # Add more timeline validation as needed

