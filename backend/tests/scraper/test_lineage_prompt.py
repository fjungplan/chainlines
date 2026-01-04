"""Test Lineage Decision LLM prompts."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock


def test_lineage_decision_validates():
    """LineageDecision should validate correctly."""
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    decision = LineageDecision(
        event_type=LineageEventType.LEGAL_TRANSFER,
        confidence=0.95,
        reasoning="Same UCI code, continuous license",
        predecessor_ids=[uuid4()],
        successor_ids=[uuid4()]
    )
    
    assert decision.event_type == LineageEventType.LEGAL_TRANSFER
    assert decision.confidence >= 0.9


def test_lineage_decision_merge_has_multiple_predecessors():
    """MERGE should allow multiple predecessors."""
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    decision = LineageDecision(
        event_type=LineageEventType.MERGE,
        confidence=0.85,
        reasoning="Two teams combined",
        predecessor_ids=[uuid4(), uuid4()],
        successor_ids=[uuid4()]
    )
    
    assert len(decision.predecessor_ids) == 2
    assert len(decision.successor_ids) == 1


def test_lineage_decision_split_has_multiple_successors():
    """SPLIT should allow multiple successors."""
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    decision = LineageDecision(
        event_type=LineageEventType.SPLIT,
        confidence=0.80,
        reasoning="Team dissolved into two",
        predecessor_ids=[uuid4()],
        successor_ids=[uuid4(), uuid4()]
    )
    
    assert len(decision.predecessor_ids) == 1
    assert len(decision.successor_ids) == 2


@pytest.mark.asyncio
async def test_decide_lineage_prompt():
    """ScraperPrompts.decide_lineage should return decision."""
    from app.scraper.llm.prompts import ScraperPrompts
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    mock_service = AsyncMock()
    mock_service.generate_structured = AsyncMock(
        return_value=LineageDecision(
            event_type=LineageEventType.LEGAL_TRANSFER,
            confidence=0.92,
            reasoning="Continuation of same team",
            predecessor_ids=[uuid4()],
            successor_ids=[uuid4()]
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_service)
    
    result = await prompts.decide_lineage(
        predecessor_info="Team A ended 2023, UCI code TJV",
        successor_info="Team B started 2024, UCI code TJV"
    )
    
    assert result.event_type == LineageEventType.LEGAL_TRANSFER
    mock_service.generate_structured.assert_called_once()
