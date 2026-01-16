"""Schemas for mobile-optimized team detail/history responses."""
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.sponsor import SponsorLinkResponse


class TransitionInfo(BaseModel):
    """Represents a lineage transition (predecessor or successor)."""
    year: int = Field(..., description="Year of the transition event")
    name: Optional[str] = Field(None, description="Name of the related team")
    event_type: str = Field(..., description="Classified transition type (MERGED_INTO, ACQUISITION, REVIVAL, SPLIT)")


class TeamHistoryEra(BaseModel):
    """Single era in the team's chronological history."""
    era_id: UUID = Field(..., description="Unique identifier for the era")
    year: int = Field(..., description="Season year")
    name: str = Field(..., description="Registered team name")
    tier: Optional[int] = Field(None, description="UCI tier level (1, 2, 3)")
    uci_code: Optional[str] = Field(None, description="3-letter UCI code")
    country_code: Optional[str] = Field(None, description="Alpha-3 Country Code (e.g. FRA, ITA)")
    status: str = Field(..., description="Era status: active, historical, dissolved")
    predecessor: Optional[TransitionInfo] = Field(None, description="Incoming lineage transition")
    successor: Optional[TransitionInfo] = Field(None, description="Outgoing lineage transition")
    sponsors: List[SponsorLinkResponse] = Field(default_factory=list, description="List of sponsors for this era")


class LineageSummary(BaseModel):
    """High-level lineage flags for quick UI decisions."""
    has_predecessors: bool = Field(..., description="True if team has any incoming lineage")
    has_successors: bool = Field(..., description="True if team has any outgoing lineage")
    spiritual_succession: bool = Field(..., description="True if any spiritual succession events exist")


class TeamHistoryEvent(BaseModel):
    """Lineage event (Merge, Split, etc) for the history timeline."""
    event_id: UUID = Field(..., description="Unique identifier for the event")
    year: int = Field(..., description="Year of the event")
    event_type: str = Field(..., description="Type of event (MERGE, SPLIT, ACQUISITION, etc)")
    direction: str = Field(..., description="INCOMING (Predecessor) or OUTGOING (Successor)")
    related_team_id: Optional[UUID] = Field(None, description="ID of the other team involved")
    related_team_name: str = Field(..., description="Name of the other team involved")
    related_era_name: Optional[str] = Field(None, description="Specific era name of the other team (e.g. at year-1)")
    notes: Optional[str] = Field(None, description="Notes/Reason for the event")


class TeamHistoryResponse(BaseModel):
    """Mobile-optimized chronological history for a team node."""
    node_id: str = Field(..., description="UUID of the team node")
    current_name: Optional[str] = Field(None, description="Most recent known team name")
    legal_name: str = Field(..., description="Official legal name of the team entity")
    display_name: Optional[str] = Field(None, description="Common or abbreviated display name")
    founding_year: int = Field(..., description="Year the team was founded")
    dissolution_year: Optional[int] = Field(None, description="Year dissolved, if applicable")
    timeline: list[TeamHistoryEra] = Field(..., description="Chronological list of eras")
    events: list[TeamHistoryEvent] = Field(default_factory=list, description="List of lineage events")
    lineage_summary: LineageSummary = Field(..., description="Lineage overview")
