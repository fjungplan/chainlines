from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, date


class EditMetadataRequest(BaseModel):
    era_id: str
    registered_name: Optional[str] = None
    uci_code: Optional[str] = None
    country_code: Optional[str] = None
    tier_level: Optional[int] = None
    valid_from: Optional[date] = None
    founding_year: Optional[int] = None
    dissolution_year: Optional[int] = None
    reason: Optional[str] = None  # Why this edit is being made
    
    @field_validator('uci_code')
    @classmethod
    def validate_uci_code(cls, v):
        if v and (len(v) != 3 or not v.isalnum() or v != v.upper()):
            raise ValueError('UCI code must be 3 uppercase alphanumeric')
        return v
    
    @field_validator('tier_level')
    @classmethod
    def validate_tier(cls, v):
        if v and v not in [1, 2, 3]:
            raise ValueError('Tier must be 1, 2, or 3')
        return v
    
    @field_validator('founding_year')
    @classmethod
    def validate_founding_year(cls, v):
        if v and (v < 1900 or v > 2100):
            raise ValueError('Founding year must be between 1900 and 2100')
        return v
    
    @field_validator('dissolution_year')
    @classmethod
    def validate_dissolution_year(cls, v):
        if v and (v < 1900 or v > 2100):
            raise ValueError('Dissolution year must be between 1900 and 2100')
        return v
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()


class CreateTeamRequest(BaseModel):
    legal_name: str # Unique internal identifier (for TeamNode)
    registered_name: str  # Team name for the first era
    founding_year: int
    dissolution_year: Optional[int] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None
    uci_code: Optional[str] = None
    tier_level: int  # Initial tier
    reason: Optional[str] = None  # Optional for admins
    
    @field_validator('legal_name')
    @classmethod
    def validate_legal_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Legal name must be at least 3 characters')
        return v.strip()

    @field_validator('registered_name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Team name is required')
        return v
    
    @field_validator('founding_year')
    @classmethod
    def validate_founding_year(cls, v):
        if v < 1900 or v > 2100:
            raise ValueError('Founding year must be between 1900 and 2100')
        return v
    
    @field_validator('dissolution_year')
    @classmethod
    def validate_dissolution_year(cls, v):
        if v and (v < 1900 or v > 2100):
            raise ValueError('Dissolution year must be between 1900 and 2100')
        return v
    
    @field_validator('dissolution_year')
    @classmethod
    def validate_dissolution_year(cls, v):
        if v and (v < 1900 or v > 2100):
            raise ValueError('Dissolution year must be between 1900 and 2100')
        return v
    
    @field_validator('uci_code')
    @classmethod
    def validate_uci_code(cls, v):
        if v and (len(v) != 3 or not v.isalnum() or v != v.upper()):
            raise ValueError('UCI code must be 3 uppercase alphanumeric')
        return v
    
    @field_validator('tier_level')
    @classmethod
    def validate_tier(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError('Tier must be 1, 2, or 3')
        return v
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()

class EditMetadataResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    edit_id: str
    entity_id: Optional[str] = None  # ID of the created/modified entity
    status: str  # 'PENDING' or 'APPROVED'
    message: str


class MergeEventRequest(BaseModel):
    source_node_ids: list[str]  # Team IDs being merged
    merge_year: int
    new_team_name: str
    new_team_tier: int
    reason: Optional[str] = None
    
    @field_validator('source_node_ids')
    @classmethod
    def validate_sources(cls, v):
        if len(v) < 2:
            raise ValueError('Merge requires at least 2 source teams')
        if len(v) > 5:
            raise ValueError('Cannot merge more than 5 teams at once')
        return v
    
    @field_validator('merge_year')
    @classmethod
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v < 1900 or v > current_year + 1:
            raise ValueError(f'Year must be between 1900 and {current_year + 1}')
        return v
    
    @field_validator('new_team_name')
    @classmethod
    def validate_team_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Team name must be at least 3 characters')
        if len(v) > 200:
            raise ValueError('Team name cannot exceed 200 characters')
        return v.strip()
    
    @field_validator('new_team_tier')
    @classmethod
    def validate_tier(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError('Tier must be 1, 2, or 3')
        return v
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()


class NewTeamInfo(BaseModel):
    name: str
    tier: int
    
    @field_validator('tier')
    @classmethod
    def validate_tier(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError('Tier must be 1, 2, or 3')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Team name must be at least 3 characters')
        if len(v) > 200:
            raise ValueError('Team name cannot exceed 200 characters')
        return v.strip()


class SplitEventRequest(BaseModel):
    source_node_id: str  # Team being split
    split_year: int
    new_teams: list[NewTeamInfo]  # 2-5 new teams
    reason: Optional[str] = None
    
    @field_validator('new_teams')
    @classmethod
    def validate_new_teams(cls, v):
        if len(v) < 2:
            raise ValueError('Split requires at least 2 resulting teams')
        if len(v) > 5:
            raise ValueError('Cannot split into more than 5 teams')
        return v
    
    @field_validator('split_year')
    @classmethod
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v < 1900 or v > current_year + 1:
            raise ValueError(f'Year must be between 1900 and {current_year + 1}')
        return v
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()


class CreateEraEditRequest(BaseModel):
    season_year: int
    node_id: str
    registered_name: str
    uci_code: Optional[str] = None
    country_code: Optional[str] = None
    tier_level: Optional[int] = None
    reason: Optional[str] = None
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()


class UpdateEraEditRequest(BaseModel):
    """Request to update an existing TeamEra. Supports node_id change for transfers."""
    era_id: Optional[str] = None  # Set by path param if not in body
    node_id: Optional[str] = None  # New owner node for transfers
    registered_name: Optional[str] = None
    uci_code: Optional[str] = None
    country_code: Optional[str] = None
    tier_level: Optional[int] = None
    valid_from: Optional[date] = None
    reason: Optional[str] = None
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()


class UpdateNodeRequest(BaseModel):
    node_id: str
    legal_name: Optional[str] = None
    display_name: Optional[str] = None
    founding_year: Optional[int] = None
    dissolution_year: Optional[int] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None
    is_protected: Optional[bool] = None # Only modifiable if user has rights, checked in service
    reason: Optional[str] = None

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()

    @field_validator('founding_year')
    @classmethod
    def validate_founding_year(cls, v):
        if v and (v < 1900 or v > 2100):
            raise ValueError('Founding year must be between 1900 and 2100')
        return v



from app.models.enums import LineageEventType

class LineageEditRequest(BaseModel):
    event_id: Optional[str] = None # If present, treat as UPDATE
    event_type: LineageEventType
    event_year: int
    event_date: Optional[date] = None
    predecessor_node_id: str
    successor_node_id: str
    notes: Optional[str] = None
    source_url: Optional[str] = None
    is_protected: Optional[bool] = None
    reason: Optional[str] = None

    @field_validator('event_year')
    @classmethod
    def validate_year(cls, v):
        if v < 1900 or v > 2100:
            raise ValueError('Year must be between 1900 and 2100')
        return v

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()


class SponsorMasterEditRequest(BaseModel):
    master_id: Optional[str] = None  # If present, treat as UPDATE
    legal_name: str
    display_name: Optional[str] = None
    industry_sector: Optional[str] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None
    is_protected: Optional[bool] = None
    reason: Optional[str] = None

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()

    @field_validator('legal_name')
    @classmethod
    def validate_legal_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Legal name must be at least 2 characters')
        return v.strip()


class SponsorBrandEditRequest(BaseModel):
    brand_id: Optional[str] = None  # If present, treat as UPDATE
    master_id: Optional[str] = None  # Required to link to master
    brand_name: Optional[str] = None
    display_name: Optional[str] = None
    default_hex_color: Optional[str] = None
    source_url: Optional[str] = None
    source_notes: Optional[str] = None
    is_protected: Optional[bool] = None
    reason: Optional[str] = None

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if not v or not v.strip():
            return v
        if len(v.strip()) < 10:
            raise ValueError('Reason must be at least 10 characters')
        return v.strip()

    @field_validator('default_hex_color')
    @classmethod
    def validate_hex_color(cls, v):
        import re
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError(f"Invalid hex color format: {v}")
        return v

