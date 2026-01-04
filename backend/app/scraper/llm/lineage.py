"""Lineage decision models and prompts."""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
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
    event_type: LineageEventType
    confidence: float
    reasoning: str
    predecessor_ids: List[UUID]
    successor_ids: List[UUID]
    notes: Optional[str] = None
