from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class TeamNodeBase(BaseModel):
    founding_year: int
    dissolution_year: Optional[int] = None

    model_config = {
        "from_attributes": True,
    }


class TeamNodeResponse(TeamNodeBase):
    node_id: UUID
    created_at: datetime


class TeamEraBase(BaseModel):
    season_year: int
    registered_name: str
    uci_code: Optional[str] = None
    tier_level: Optional[int] = None
    source_origin: Optional[str] = None
    is_manual_override: bool = False

    model_config = {
        "from_attributes": True,
    }


class TeamEraResponse(TeamEraBase):
    era_id: UUID
    node_id: UUID


class TeamNodeWithEras(TeamNodeResponse):
    eras: List[TeamEraResponse] = Field(default_factory=list)


class TeamListResponse(BaseModel):
    items: List[TeamNodeResponse]
    total: int
    skip: int
    limit: int
