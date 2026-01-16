from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ConsolidationActionType(str, Enum):
    MERGE_MASTER = "merge_master"  # Merge Master A into Master B (brands move to B)
    MERGE_BRAND = "merge_brand"    # Merge Brand X into Brand Y (links update to Y)
    MOVE_BRAND = "move_brand"      # Move Brand X to Master B

class ConsolidationActionStatus(str, Enum):
    HIGH_CONFIDENCE = "high_confidence"  # >= 0.9. Auto-processable (mostly)
    NEEDS_REVIEW = "needs_review"      # >= 0.7 < 0.9. Flag for human
    DISCARDED = "discarded"            # < 0.7. Should be filtered out

class ConsolidationAction(BaseModel):
    action_type: ConsolidationActionType
    source_id: UUID
    target_id: UUID
    reason: str = Field(..., description="Explanation of why this consolidation is correct")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    status: ConsolidationActionStatus = ConsolidationActionStatus.NEEDS_REVIEW

class ConsolidationPlan(BaseModel):
    actions: List[ConsolidationAction]
    generated_at: str  # ISO timestamp
    model_used: str
    total_actions: int
