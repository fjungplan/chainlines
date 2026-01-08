"""Test Phase 3 Lineage Connection orchestration."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date

@pytest.mark.asyncio
async def test_boundary_detector_finds_nodes():
    """BoundaryNodeDetector should find teams ending/starting at transition year."""
    from app.scraper.orchestration.phase3 import BoundaryNodeDetector
    from app.models.team import TeamNode, TeamEra
    
    # Setup mock session
    mock_session = AsyncMock()
    
    # Create test nodes
    # Node A: 2024 (Ends at transition year 2024 for 2024->2025)
    node_a = TeamNode(node_id=uuid4(), legal_name="Team A", founding_year=2024)
    node_a.eras = [TeamEra(season_year=2024)]
    
    # Node B: 2025 (Starts at next year 2025)
    node_b = TeamNode(node_id=uuid4(), legal_name="Team B", founding_year=2025)
    node_b.eras = [TeamEra(season_year=2025)]
    
    # Node C: 2024, 2025 (Continuous, not a boundary)
    node_c = TeamNode(node_id=uuid4(), legal_name="Team C", founding_year=2024)
    node_c.eras = [TeamEra(season_year=2024), TeamEra(season_year=2025)]
    
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_session.execute.return_value = mock_result
    mock_result.scalars.return_value.all.return_value = [node_a, node_b, node_c]
    
    detector = BoundaryNodeDetector(session=mock_session)
    # Transition year 2024 (looking for ends in 2024, starts in 2025)
    result = await detector.get_boundary_nodes(transition_year=2024)
    
    # Verify ending nodes
    assert len(result["ending"]) == 1
    assert result["ending"][0]["name"] == "Team A"
    assert result["ending"][0]["year"] == 2024
    
    # Verify starting nodes
    assert len(result["starting"]) == 1
    assert result["starting"][0]["name"] == "Team B"
    assert result["starting"][0]["year"] == 2025

@pytest.mark.asyncio
async def test_lineage_extractor_analyzes_ending_node():
    """LineageExtractor should call LLM to analyze ending nodes."""
    from app.scraper.orchestration.phase3 import LineageExtractor
    from app.models.enums import EditAction
    
    mock_prompts = AsyncMock()
    mock_requests = AsyncMock()
    
    # Mock LLM return
    mock_prompts.extract_lineage_events.return_value = [{
        "event_type": "SUCCEEDED_BY",
        "target_name": "Team B",
        "confidence": 0.95,
        "reasoning": "Explicit mention in history"
    }]
    
    mock_audit = AsyncMock()
    mock_session = AsyncMock()
    
    extractor = LineageExtractor(
        prompts=mock_prompts,
        audit_service=mock_audit,
        session=mock_session,
        system_user_id=uuid4()
    )
    
    node_info = {
        "name": "Team A",
        "has_wikipedia": True,
        "wikipedia_summary": "Team history here...",
        "year": 2024
    }
    
    # Run analysis
    events = await extractor.analyze_ending_node(node_info)
    
    # Verify events returned
    assert len(events) == 1
    assert events[0]["event_type"] == "SUCCEEDED_BY"
    
    # Create audit record
    await extractor.create_lineage_record(node_info, events[0])
    
    # Verify audit call
    mock_audit.create_edit.assert_called_once()
    call_kwargs = mock_audit.create_edit.call_args[1]
    assert call_kwargs["action"] == EditAction.CREATE
    assert call_kwargs["entity_type"] == "LineageEvent"
    assert call_kwargs["new_data"]["source_team"] == "Team A"
    assert call_kwargs["new_data"]["target_team"] == "Team B"

@pytest.mark.asyncio
async def test_lineage_extractor_skips_no_wikipedia():
    """LineageExtractor should skip nodes with no Wikipedia content."""
    from app.scraper.orchestration.phase3 import LineageExtractor
    
    mock_prompts = AsyncMock()
    extractor = LineageExtractor(
        prompts=mock_prompts,
        audit_service=AsyncMock(),
        session=AsyncMock(),
        system_user_id=uuid4()
    )
    
    node_info = {
        "name": "Team A",
        "wikipedia_summary": None, # No content
        "year": 2024
    }
    
    events = await extractor.analyze_ending_node(node_info)
    assert len(events) == 0
    mock_prompts.extract_lineage_events.assert_not_called()

@pytest.mark.asyncio
async def test_lineage_extractor_updates_dissolution_year_on_fold():
    """LineageExtractor should update TeamNode.dissolution_year when FOLDED event is detected."""
    from app.scraper.orchestration.phase3 import LineageExtractor
    from app.models.team import TeamNode
    
    mock_prompts = AsyncMock()
    mock_audit = AsyncMock()
    mock_session = AsyncMock()
    
    # Create a real TeamNode to verify mutation
    node = TeamNode(node_id=uuid4(), legal_name="Team A", founding_year=2020)
    assert node.dissolution_year is None  # Initially null
    
    extractor = LineageExtractor(
        prompts=mock_prompts,
        audit_service=mock_audit,
        session=mock_session,
        system_user_id=uuid4()
    )
    
    node_info = {
        "id": node.node_id,
        "name": "Team A",
        "year": 2024,
        "_node": node  # Pass the actual node for mutation
    }
    
    fold_event = {
        "event_type": "FOLDED",
        "target_name": None,
        "confidence": 0.95,
        "reasoning": "Team folded after 2024 season"
    }
    
    # Create lineage record (should update dissolution_year)
    await extractor.create_lineage_record(node_info, fold_event)
    
    # Verify dissolution_year was updated
    assert node.dissolution_year == 2024

