from pydantic import BaseModel, Field
from typing import List, Optional

class SponsorInfo(BaseModel):
    """Detailed sponsor/brand information."""
    brand_name: str = Field(description="Brand name (e.g., 'Ineos Grenadier')")
    parent_company: Optional[str] = Field(
        default=None,
        description="Parent company (e.g., 'INEOS Group')"
    )
    type: str = Field(
        default="TITLE",
        description="Sponsor type: 'TITLE' or 'EQUIPMENT'"
    )
    brand_color: Optional[str] = Field(
        default=None,
        description="Primary brand color as hex code (e.g., '#FF0000' for red). Extract from well-known brand colors."
    )
    industry_sector: Optional[str] = Field(
        default=None,
        description="Business sector (e.g., 'Financial Services', 'Healthcare', 'Technology')"
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Official website or Wikipedia URL for verification"
    )

class SponsorExtractionResult(BaseModel):
    """LLM response for sponsor extraction."""
    sponsors: List[SponsorInfo]
    team_descriptors: List[str] = Field(default_factory=list)
    filler_words: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class BrandMatchResult(BaseModel):
    """Brand matching analysis result."""
    known_brands: List[str]
    unmatched_words: List[str]
    needs_llm: bool
