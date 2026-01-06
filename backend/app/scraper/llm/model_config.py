"""Model configuration for prompt-specific LLM routing.

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


@dataclass(frozen=True)
class ModelPair:
    """Configuration for a primary/fallback model pair."""
    primary_model: str
    fallback_model: str


# Prompt-to-model routing configuration
# Optimized for cost: simpler prompts use cheaper models
MODEL_ROUTING: Dict[PromptType, ModelPair] = {
    # Team data extraction: Flash is fast and cheap, Chat as fallback
    PromptType.EXTRACT_TEAM_DATA: ModelPair(
        primary_model="gemini-2.5-flash",
        fallback_model="deepseek-chat"
    ),
    # Lineage decisions require deep reasoning
    PromptType.DECIDE_LINEAGE: ModelPair(
        primary_model="deepseek-reasoner",
        fallback_model="gemini-2.5-pro"
    ),
    # Sponsor extraction: Chat is sufficient, Flash as fallback
    PromptType.SPONSOR_EXTRACTION: ModelPair(
        primary_model="deepseek-chat",
        fallback_model="gemini-2.5-flash"
    ),
}
