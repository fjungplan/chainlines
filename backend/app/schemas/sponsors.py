from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# --- Shared Base Schemas ---

class SponsorBase(BaseModel):
    source_url: Optional[str] = Field(None, max_length=500)
    source_notes: Optional[str] = None

class SponsorMasterBase(SponsorBase):
    legal_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    industry_sector: Optional[str] = Field(None, max_length=100)
    is_protected: bool = False

class SponsorBrandBase(SponsorBase):
    brand_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    default_hex_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")

# --- Creation Schemas ---

class SponsorBrandCreate(SponsorBrandBase):
    pass

class SponsorMasterCreate(SponsorMasterBase):
    pass

class SponsorBrandCreateWithMaster(SponsorBrandCreate):
    master_id: UUID

# --- Update Schemas ---

class SponsorMasterUpdate(BaseModel):
    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    industry_sector: Optional[str] = Field(None, max_length=100)
    is_protected: Optional[bool] = None
    source_url: Optional[str] = Field(None, max_length=500)
    source_notes: Optional[str] = None

class SponsorBrandUpdate(BaseModel):
    master_id: Optional[UUID] = None  # For brand transfers
    brand_name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    default_hex_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    source_url: Optional[str] = Field(None, max_length=500)
    source_notes: Optional[str] = None

# --- Response Schemas ---

class SponsorBrandResponse(SponsorBrandBase):
    brand_id: UUID
    master_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SponsorMasterResponse(SponsorMasterBase):
    master_id: UUID
    created_at: datetime
    updated_at: datetime
    brands: List[SponsorBrandResponse] = []

    model_config = ConfigDict(from_attributes=True)

class SponsorMasterListResponse(SponsorMasterBase):
    """Lighter version for lists (omitting brands if needed, or keeping them light)"""
    master_id: UUID
    brand_count: int = 0  # Calculated field
    
    model_config = ConfigDict(from_attributes=True)

class TeamSponsorLinkCreate(BaseModel):
    brand_id: UUID
    rank_order: int
    prominence_percent: int
    hex_color_override: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

class TeamSponsorLinkResponse(BaseModel):
    link_id: UUID
    era_id: UUID
    brand_id: UUID
    rank_order: int
    prominence_percent: int
    hex_color_override: Optional[str] = None
    brand: Optional[SponsorBrandResponse] = None # Include brand details
    
    model_config = ConfigDict(from_attributes=True)
