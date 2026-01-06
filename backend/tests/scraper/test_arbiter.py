"""Tests for ConflictArbiter."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.scraper.services.arbiter import (
    ConflictArbiter,
    ArbitrationDecision,
    ArbitrationResult,
)
from app.scraper.sources.cyclingflash import ScrapedTeamData
from app.scraper.orchestration.workers import SourceData


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    service = MagicMock()
    service.generate_structured = AsyncMock()
    return service


@pytest.fixture
def cf_data_1990_2000():
    """CyclingFlash data: team active 1990-2000."""
    return ScrapedTeamData(
        name="Peugeot",
        season_year=2000,
        uci_code="PEU",
        tier_level=1,
    )


@pytest.fixture
def cr_data_1990_2000():
    """CyclingRanking data: same dates as CF."""
    return SourceData(
        source="cyclingranking",
        founded_year=1990,
        dissolved_year=2000,
    )


@pytest.fixture
def cr_data_1990_1986():
    """CyclingRanking data: different dissolved year (conflict)."""
    return SourceData(
        source="cyclingranking",
        founded_year=1912,
        dissolved_year=1986,
    )


@pytest.mark.asyncio
async def test_arbiter_detects_no_conflict(mock_llm_service, cf_data_1990_2000, cr_data_1990_2000):
    """When CF and CR dates match, arbiter returns MERGE without calling LLM."""
    arbiter = ConflictArbiter(mock_llm_service)
    
    result = await arbiter.decide(
        cf_data=cf_data_1990_2000,
        cr_data=cr_data_1990_2000,
        wp_history=None
    )
    
    assert result.decision == ArbitrationDecision.MERGE
    assert result.confidence == 1.0
    assert "No conflict" in result.reasoning
    # LLM should NOT be called when there's no conflict
    mock_llm_service.generate_structured.assert_not_called()


@pytest.mark.asyncio
async def test_arbiter_decides_split(mock_llm_service, cf_data_1990_2000, cr_data_1990_1986):
    """When dates differ, arbiter uses LLM and returns SPLIT decision."""
    # Mock LLM response with high confidence SPLIT
    mock_llm_service.generate_structured.return_value = ArbitrationResult(
        decision=ArbitrationDecision.SPLIT,
        confidence=0.95,
        reasoning="CyclingRanking shows dissolution in 1986, CF shows 2008. Legal entity changed.",
        suggested_lineage_type="SPIRITUAL_SUCCESSION"
    )
    
    arbiter = ConflictArbiter(mock_llm_service)
    
    result = await arbiter.decide(
        cf_data=cf_data_1990_2000,
        cr_data=cr_data_1990_1986,
        wp_history="The team was restructured in 1986 when the original sponsor withdrew."
    )
    
    assert result.decision == ArbitrationDecision.SPLIT
    assert result.confidence == 0.95
    assert result.suggested_lineage_type == "SPIRITUAL_SUCCESSION"
    # LLM SHOULD be called when conflict detected
    mock_llm_service.generate_structured.assert_called_once()


@pytest.mark.asyncio
async def test_arbiter_respects_confidence_threshold(mock_llm_service, cf_data_1990_2000, cr_data_1990_1986):
    """When LLM confidence is below threshold, arbiter returns PENDING."""
    # Mock LLM response with LOW confidence
    mock_llm_service.generate_structured.return_value = ArbitrationResult(
        decision=ArbitrationDecision.SPLIT,
        confidence=0.75,  # Below 0.90 threshold
        reasoning="Uncertain - sources are ambiguous.",
        suggested_lineage_type=None
    )
    
    arbiter = ConflictArbiter(mock_llm_service)
    
    result = await arbiter.decide(
        cf_data=cf_data_1990_2000,
        cr_data=cr_data_1990_1986,
        wp_history=None
    )
    
    # Should return PENDING because confidence < 0.90
    assert result.decision == ArbitrationDecision.PENDING
    assert result.confidence == 0.75
    assert "confidence" in result.reasoning.lower() or "pending" in result.reasoning.lower()
