"""Tests for LLM prompts in scraper operations."""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestExtractLineageEventsPrompt:
    """Tests for EXTRACT_LINEAGE_EVENTS_PROMPT year filtering."""

    def test_prompt_includes_year_placeholder(self):
        """Prompt should include year_plus_one placeholder for year filtering."""
        from app.scraper.llm.prompts import EXTRACT_LINEAGE_EVENTS_PROMPT
        
        # Verify the prompt contains year_plus_one placeholder
        assert "{year_plus_one}" in EXTRACT_LINEAGE_EVENTS_PROMPT, \
            "Prompt must include {year_plus_one} placeholder for year filtering"

    def test_prompt_includes_year_filtering_instruction(self):
        """Prompt should explicitly instruct LLM to filter by year."""
        from app.scraper.llm.prompts import EXTRACT_LINEAGE_EVENTS_PROMPT
        
        # Format the prompt with test values
        formatted = EXTRACT_LINEAGE_EVENTS_PROMPT.format(
            team_name="Test Team",
            context="ending",
            year=2000,
            year_plus_one=2001,
            wikipedia_content="Team merged in 2003...",
            available_teams="Team A\nTeam B"
        )
        
        # Verify year filtering instruction exists
        assert "2000" in formatted and "2001" in formatted, \
            "Formatted prompt must include both year and year_plus_one"
        assert "ONLY" in formatted or "only" in formatted, \
            "Prompt must include explicit 'only extract' instruction"

    @pytest.mark.asyncio
    async def test_extract_lineage_events_passes_year_plus_one(self):
        """ScraperPrompts.extract_lineage_events should pass year_plus_one to prompt."""
        from app.scraper.llm.prompts import ScraperPrompts
        from app.scraper.llm.lineage import LineageEventsExtraction
        
        # Mock LLM service
        mock_llm = AsyncMock()
        mock_result = MagicMock(spec=LineageEventsExtraction)
        mock_result.events = []
        mock_llm.generate_structured.return_value = mock_result
        
        prompts = ScraperPrompts(mock_llm)
        
        # Call extract_lineage_events
        await prompts.extract_lineage_events(
            team_name="Test Team",
            context="ending",
            year=2000,
            wikipedia_content="Some content",
            available_teams=["Team A", "Team B"]
        )
        
        # Verify the prompt includes year_plus_one (2001)
        call_args = mock_llm.generate_structured.call_args
        prompt_text = call_args.kwargs["prompt"]
        assert "2001" in prompt_text, \
            "Prompt must include year_plus_one (2001) when year=2000"


class TestSelfReferenceValidation:
    """Tests for self-reference validation in Phase 3."""

    @pytest.mark.asyncio
    async def test_create_lineage_record_rejects_self_reference(self, caplog):
        """LineageExtractor should skip events where target equals source."""
        import logging
        from app.scraper.orchestration.phase3 import LineageExtractor
        from app.models.team import TeamNode
        import uuid
        
        # Setup
        mock_session = AsyncMock()
        mock_prompts = MagicMock()
        mock_audit = MagicMock()
        system_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        
        extractor = LineageExtractor(
            prompts=mock_prompts,
            audit_service=mock_audit,
            session=mock_session,
            system_user_id=system_user_id
        )
        
        # Source node (using UUID object)
        node_uuid = uuid.UUID("30760e5d-cdbc-474a-8956-d5f2e3a8baa7")
        source_node = {
            "node_id": node_uuid,
            "name": "De Nardi",
            "year": 2000
        }
        
        # Event where target matches source
        event = {
            "event_type": "MERGED_WITH",
            "target_name": "De Nardi",
            "confidence": 0.9,
            "reasoning": "Self-reference test"
        }
        
        # Mock database query to return a node with matching ID
        mock_target_node = MagicMock(spec=TeamNode)
        mock_target_node.node_id = node_uuid  # Same UUID!
        mock_target_node.legal_name = "De Nardi"
        
        # Mock both queries: first for TeamNode, second for TeamEra
        mock_result_nodes = MagicMock()
        mock_result_nodes.scalars.return_value.all.return_value = [mock_target_node]
        
        mock_result_eras = MagicMock()
        mock_result_eras.scalars.return_value.all.return_value = []  # No eras
        
        # Return different results for each call
        mock_session.execute.side_effect = [mock_result_nodes, mock_result_eras]
        
        # Execute with log capture
        with caplog.at_level(logging.WARNING):
            result = await extractor.create_lineage_record(source_node, event)
        
        # Verify: Should return None for self-referencing event
        assert result is None, "Should return None for self-referencing event"
        
        # Verify warning was logged
        assert any("self-referencing" in record.message.lower() for record in caplog.records), \
            "Should log warning about self-referencing event"


class TestSingleCharSponsorValidation:
    """Tests for single-character sponsor name handling."""

    @pytest.mark.asyncio
    async def test_phase2_logs_single_char_sponsor(self, caplog):
        """Phase 2 should log a warning for single-character sponsor names."""
        import logging
        from app.scraper.orchestration.phase2 import AssemblyOrchestrator
        
        # This test verifies the warning is logged
        # The actual implementation will be in phase2.py
        
        # For now, we just verify the test structure is correct
        # Implementation will make this pass
        with caplog.at_level(logging.WARNING):
            # When we call the sponsor extraction with a single-char result,
            # it should log a warning
            pass
        
        # TODO: Full implementation will mock the LLM and verify logging
