"""Conflict Arbiter for multi-source resolution.

Uses Deepseek Reasoner to decide if conflicting data from multiple sources
represents a MERGE (same entity), SPLIT (different entities), or PENDING
(requires human review).
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from app.scraper.llm.model_config import PromptType

if TYPE_CHECKING:
    from app.scraper.llm.service import LLMService
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    from app.scraper.orchestration.workers import SourceData


class ArbitrationDecision(Enum):
    """Possible outcomes from conflict arbitration."""
    MERGE = "merge"
    SPLIT = "split"
    PENDING = "pending"


class ArbitrationResult(BaseModel):
    """Result of conflict arbitration between sources."""
    decision: ArbitrationDecision
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    suggested_lineage_type: Optional[str] = Field(
        default=None,
        description="If SPLIT, the suggested lineage type (e.g., SPIRITUAL_SUCCESSION)"
    )


# System prompt for conflict arbitration
CONFLICT_ARBITRATION_PROMPT = """You are an expert cycling team historian analyzing conflicting data from multiple sources.

CONTEXT:
We have data from CyclingFlash (CF) and CyclingRanking (CR) that may conflict.
Your job is to determine if these represent the SAME legal entity or a SPLIT.

CYCLINGFLASH DATA:
- Team Name: {cf_name}
- Season Year: {cf_year}
- UCI Code: {cf_uci_code}

CYCLINGRANKING DATA:
- Founded Year: {cr_founded}
- Dissolved Year: {cr_dissolved}

WIKIPEDIA HISTORY (if available):
{wp_history}

DECISION PRINCIPLES (Legal Supremacy):
1. **If the UCI license holder / paying agent changed** → SPLIT
2. **If riders/staff transferred but entity is new** → Suggest SPIRITUAL_SUCCESSION as lineage type
3. **If only sponsor names changed but same license** → MERGE
4. **If sources simply have different data quality** → MERGE with explanation

OUTPUT:
- decision: "merge", "split", or "pending"
- confidence: 0.0 to 1.0
- reasoning: Explain your decision
- suggested_lineage_type: If SPLIT, suggest "LEGAL_TRANSFER", "SPIRITUAL_SUCCESSION", or null
"""


class ConflictArbiter:
    """Arbitrates conflicts between multi-source team data using LLM.
    
    Uses Deepseek Reasoner for high-intelligence decisions about whether
    conflicting source data represents one entity or a legal split.
    """
    
    CONFIDENCE_THRESHOLD = 0.90
    
    def __init__(self, llm_service: "LLMService"):
        """Initialize with LLM service.
        
        Args:
            llm_service: The LLM service for structured generation.
        """
        self._llm = llm_service
    
    async def decide(
        self,
        cf_data: "ScrapedTeamData",
        cr_data: Optional["SourceData"],
        wp_history: Optional[str]
    ) -> ArbitrationResult:
        """Decide if CF and CR data represent the same entity or a split.
        
        Args:
            cf_data: Data scraped from CyclingFlash.
            cr_data: Data from CyclingRanking (may be None).
            wp_history: Wikipedia history section text (may be None).
            
        Returns:
            ArbitrationResult with decision, confidence, and reasoning.
        """
        # No conflict if CR data is missing or dates match
        if not self._has_conflict(cf_data, cr_data):
            return ArbitrationResult(
                decision=ArbitrationDecision.MERGE,
                confidence=1.0,
                reasoning="No conflict detected - sources agree or CR data unavailable."
            )
        
        # Build prompt and call LLM
        prompt = self._build_prompt(cf_data, cr_data, wp_history)
        llm_result = await self._llm.generate_structured(
            prompt=prompt,
            response_model=ArbitrationResult,
            prompt_type=PromptType.CONFLICT_ARBITRATION
        )
        
        # If confidence is below threshold, return PENDING
        if llm_result.confidence < self.CONFIDENCE_THRESHOLD:
            return ArbitrationResult(
                decision=ArbitrationDecision.PENDING,
                confidence=llm_result.confidence,
                reasoning=f"Low confidence ({llm_result.confidence:.2f}) - requires human review. Original reasoning: {llm_result.reasoning}",
                suggested_lineage_type=llm_result.suggested_lineage_type
            )
        
        return llm_result
    
    def _has_conflict(
        self,
        cf_data: "ScrapedTeamData",
        cr_data: Optional["SourceData"]
    ) -> bool:
        """Check if there's a conflict between CF and CR data.
        
        A conflict exists if dissolved years differ significantly.
        
        Args:
            cf_data: CyclingFlash data.
            cr_data: CyclingRanking data (may be None).
            
        Returns:
            True if conflict detected, False otherwise.
        """
        if cr_data is None:
            return False
        
        # If CR has a dissolved year and it differs from CF's implied year
        # CF's season_year is the last known active year
        if cr_data.dissolved_year is not None:
            # Conflict if dissolved year is more than 1 year different
            if abs(cf_data.season_year - cr_data.dissolved_year) > 1:
                return True
        
        return False
    
    def _build_prompt(
        self,
        cf_data: "ScrapedTeamData",
        cr_data: Optional["SourceData"],
        wp_history: Optional[str]
    ) -> str:
        """Build the prompt for conflict arbitration.
        
        Args:
            cf_data: CyclingFlash data.
            cr_data: CyclingRanking data.
            wp_history: Wikipedia history text.
            
        Returns:
            Formatted prompt string.
        """
        return CONFLICT_ARBITRATION_PROMPT.format(
            cf_name=cf_data.name,
            cf_year=cf_data.season_year,
            cf_uci_code=cf_data.uci_code or "Unknown",
            cr_founded=cr_data.founded_year if cr_data else "Unknown",
            cr_dissolved=cr_data.dissolved_year if cr_data else "Unknown",
            wp_history=wp_history or "Not available"
        )
