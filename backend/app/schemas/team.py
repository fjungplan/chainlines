from __future__ import annotations

from typing import List, Optional
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.sponsor import SponsorLinkResponse

class TeamNodeBase(BaseModel):
    legal_name: str
    display_name: Optional[str] = None
    founding_year: int
    dissolution_year: Optional[int] = None
    is_protected: bool = False
    source_url: Optional[str] = None
    source_notes: Optional[str] = None

    model_config = {
        "from_attributes": True,
    }


class TeamNodeCreate(TeamNodeBase):
    pass


class TeamNodeUpdate(BaseModel):
    legal_name: Optional[str] = None
    display_name: Optional[str] = None
    founding_year: Optional[int] = None
    dissolution_year: Optional[int] = None
    is_protected: Optional[bool] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None


class TeamNodeResponse(TeamNodeBase):
    node_id: UUID
    latest_team_name: Optional[str] = None
    latest_uci_code: Optional[str] = None
    current_tier: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class TeamEraBase(BaseModel):
    season_year: int
    valid_from: date
    valid_until: Optional[date] = None
    registered_name: str
    uci_code: Optional[str] = None
    country_code: Optional[str] = None
    tier_level: Optional[int] = None
    is_name_auto_generated: bool = True
    is_manual_override: bool = False
    is_auto_filled: bool = False
    has_license: bool = False
    source_origin: Optional[str] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None

    model_config = {
        "from_attributes": True,
    }


class TeamEraCreate(TeamEraBase):
    pass


class TeamEraUpdate(BaseModel):
    season_year: Optional[int] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    registered_name: Optional[str] = None
    uci_code: Optional[str] = None
    country_code: Optional[str] = None
    tier_level: Optional[int] = None
    is_name_auto_generated: Optional[bool] = None
    is_manual_override: Optional[bool] = None
    is_auto_filled: Optional[bool] = None
    has_license: Optional[bool] = None
    source_origin: Optional[str] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None


class TeamEraResponse(TeamEraBase):
    era_id: UUID
    node_id: UUID
    sponsors: List[SponsorLinkResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TeamNodeWithEras(TeamNodeResponse):
    eras: List[TeamEraResponse] = Field(default_factory=list)


class TeamListResponse(BaseModel):
    items: List[TeamNodeResponse]
    total: int
    skip: int
    limit: int
