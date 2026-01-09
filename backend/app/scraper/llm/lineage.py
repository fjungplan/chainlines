"""Lineage decision models and prompts."""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import LineageEventType


class LineageDecision(BaseModel):
    """LLM decision about team lineage.
    
    Represents the relationship between predecessor and successor teams,
    supporting various lineage event types like transfers, merges, and splits.
    
    Attributes:
        event_type: The type of lineage event (LEGAL_TRANSFER, MERGE, SPLIT, etc.)
        confidence: Confidence score between 0.0 and 1.0
        reasoning: Explanation of why this decision was made
        predecessor_ids: UUIDs of predecessor team(s)
        successor_ids: UUIDs of successor team(s)
        notes: Optional additional notes
    """
    event_type: Optional[LineageEventType]
    confidence: float
    reasoning: str
    predecessor_ids: List[UUID]
    successor_ids: List[UUID]
    notes: Optional[str] = None


class LineageEventInfo(BaseModel):
    """A single lineage event extracted from Wikipedia content."""
    event_type: str = Field(
        description="Type: SUCCEEDED_BY, JOINED, SPLIT_INTO, MERGED_WITH, SUCCESSOR_OF, BREAKAWAY_FROM, MERGER_OF"
    )
    target_name: str = Field(
        description="Name of the other team involved in the lineage event"
    )
    year: Optional[int] = Field(
        default=None,
        description="Year the event occurred, if mentioned"
    )
    confidence: float = Field(
        description="Confidence 0.0-1.0 that this event actually happened"
    )
    reasoning: str = Field(
        description="Brief explanation citing the Wikipedia evidence"
    )


class LineageEventsExtraction(BaseModel):
    """Result of extracting lineage events from Wikipedia content."""
    events: List[LineageEventInfo] = Field(
        default_factory=list,
        description="List of lineage events found in the Wikipedia content"
    )
    no_events_reason: Optional[str] = Field(
        default=None,
        description="If no events found, explain why (e.g., 'Team still active', 'No successor mentioned')"
    )

