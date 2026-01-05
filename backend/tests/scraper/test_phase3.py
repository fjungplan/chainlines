"""Test Phase 3 Lineage Connection orchestration."""
import pytest
from datetime import date

def test_orphan_detector_finds_gaps():
    """OrphanDetector should find teams with year gaps."""
    from app.scraper.orchestration.phase3 import OrphanDetector
    
    teams = [
        {"node_id": "a", "name": "Team A", "end_year": 2022},
        {"node_id": "b", "name": "Team B", "start_year": 2023},
        {"node_id": "c", "name": "Team C", "end_year": 2020},
    ]
    
    detector = OrphanDetector()
    candidates = detector.find_candidates(teams)
    
    # Should match Team A (ended 2022) with Team B (started 2023)
    assert len(candidates) >= 1
    assert any(c["predecessor"]["name"] == "Team A" for c in candidates)

def test_orphan_detector_ignores_large_gaps():
    """OrphanDetector should ignore gaps > 2 years."""
    from app.scraper.orchestration.phase3 import OrphanDetector
    
    teams = [
        {"node_id": "a", "name": "Team A", "end_year": 2018},
        {"node_id": "b", "name": "Team B", "start_year": 2023},
    ]
    
    detector = OrphanDetector(max_gap_years=2)
    candidates = detector.find_candidates(teams)
    
    assert len(candidates) == 0

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

@pytest.mark.asyncio
async def test_lineage_service_creates_event():
    """LineageConnectionService should create lineage events."""
    from app.scraper.orchestration.phase3 import LineageConnectionService
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    mock_prompts = AsyncMock()
    mock_prompts.decide_lineage = AsyncMock(
        return_value=LineageDecision(
            event_type=LineageEventType.LEGAL_TRANSFER,
            confidence=0.95,
            reasoning="Same team",
            predecessor_ids=[uuid4()],
            successor_ids=[uuid4()]
        )
    )
    
    mock_audit = AsyncMock()
    mock_session = AsyncMock()
    
    service = LineageConnectionService(
        prompts=mock_prompts,
        audit_service=mock_audit,
        session=mock_session,
        system_user_id=uuid4()
    )
    
    await service.connect(
        predecessor_info="Team A 2022",
        successor_info="Team B 2023"
    )
    
    mock_prompts.decide_lineage.assert_called_once()
    mock_audit.create_edit.assert_called_once()

@pytest.mark.asyncio
async def test_lineage_service_handles_no_connection():
    """LineageConnectionService should NOT create event for NO_CONNECTION."""
    from app.scraper.orchestration.phase3 import LineageConnectionService
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    mock_prompts = AsyncMock()
    mock_prompts.decide_lineage = AsyncMock(
        return_value=LineageDecision(
            event_type=None,
            confidence=0.99,
            reasoning="Totally different teams",
            predecessor_ids=[],
            successor_ids=[]
        )
    )
    
    mock_audit = AsyncMock()
    mock_session = AsyncMock()
    
    service = LineageConnectionService(
        prompts=mock_prompts,
        audit_service=mock_audit,
        session=mock_session,
        system_user_id=uuid4()
    )
    
    await service.connect(
        predecessor_info="Team X 2010",
        successor_info="Team Y 2025"
    )
    
    # Should check with LLM but NOT create an edit
    mock_prompts.decide_lineage.assert_called_once()
    mock_audit.create_edit.assert_not_called()
