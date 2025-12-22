from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app.models.enums import LineageEventType

class LineageNodeSummary(BaseModel):
    node_id: UUID
    legal_name: str
    display_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class LineageEventResponse(BaseModel):
    event_id: UUID
    event_year: int
    event_type: LineageEventType
    notes: Optional[str] = None
    predecessor_node: LineageNodeSummary
    successor_node: LineageNodeSummary
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LineageListResponse(BaseModel):
    items: list[LineageEventResponse]
    total: int
