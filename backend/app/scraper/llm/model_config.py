x"""Model configuration for prompt-specific LLM routing.

This module defines which LLM models should be used for each prompt type,
enabling cost optimization by using cheaper models for simpler tasks.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict


class PromptType(Enum):
    """Enum for different prompt types used in the scraper."""
    EXTRACT_TEAM_DATA = "extract_team_data"
    DECIDE_LINEAGE = "decide_lineage"
    SPONSOR_EXTRACTION = "sponsor_extraction"
    CONFLICT_ARBITRATION = "conflict_arbitration"


@dataclass(frozen=True)
class ModelPair:
    """Configuration for a primary/fallback model pair."""
    primary_model: str
    fallback_model: str


# Prompt-to-model routing configuration
# Optimized for cost: simpler prompts use cheaper models
MODEL_ROUTING: Dict[PromptType, ModelPair] = {
    # 1. Team Data Extraction:
    # Task: Simple information extraction from HTML.
    # Choice: Gemini Flash is the cheapest/fastest option and sufficient for this simple task.
    PromptType.EXTRACT_TEAM_DATA: ModelPair(
        primary_model="gemini-2.5-flash",
        fallback_model="deepseek-chat"
    ),

    # 2. Lineage Decisions:
    # Task: Complex reasoning about history, dates, and identity changes.
    # Choice: DeepSeek Reasoner (R1) provides superior chain-of-thought logic essential for avoiding lineage errors.
    # Trade-off: Higher cost than Flash, but necessary for correctness.
    PromptType.DECIDE_LINEAGE: ModelPair(
        primary_model="deepseek-reasoner",
        fallback_model="gemini-2.5-pro"
    ),

    # 3. Sponsor Extraction:
    # Task: Identification of brands, colors, and industries; requires world knowledge.
    # Choice: DeepSeek Chat (V3) offers GPT-4 class world knowledge at a very low price point (~$0.14/1M).
    # Trade-off: Slightly more expensive than Flash, but significantly better at distinguishing
    # subtle brand/team names and knowing specific brand colors without hallucination.
    PromptType.SPONSOR_EXTRACTION: ModelPair(
        primary_model="deepseek-chat",
        fallback_model="gemini-2.5-flash"
    ),

    # 4. Conflict Arbitration:
    # Task: Resolving contradictory data points with logic.
    # Choice: DeepSeek Reasoner (R1) is best for acting as a logical judge.
    PromptType.CONFLICT_ARBITRATION: ModelPair(
        primary_model="deepseek-reasoner",
        fallback_model="gemini-2.5-pro"
    ),
}
