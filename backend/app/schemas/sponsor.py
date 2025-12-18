from __future__ import annotations

from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class SponsorBrandBase(BaseModel):
    brand_name: str
    default_hex_color: str

    model_config = {
        "from_attributes": True
    }

class SponsorLinkResponse(BaseModel):
    link_id: UUID
    brand_id: UUID
    rank_order: int
    prominence_percent: int
    hex_color_override: Optional[str] = None
    
    # We flatten basic brand info here for easier frontend consumption
    brand_name: str
    color: str  # effective color (override or default)

    model_config = {
        "from_attributes": True
    }
