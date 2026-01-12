import pytest
from uuid import UUID
from app.services.timeline_service import TimelineService
from app.models.team import TeamNode, TeamEra
from app.models.lineage import LineageEvent


@pytest.mark.asyncio
async def test_get_graph_data_accepts_focus_node_id(db_session):
    """Test that get_graph_data accepts focus_node_id parameter."""
    service = TimelineService(db_session)
    
    # Should not raise an error when focus_node_id is provided
    result = await service.get_graph_data(
        start_year=1900,
        end_year=2026,
        include_dissolved=True,
        tier_filter=None,
        focus_node_id=None  # Explicitly passing None should work
    )
    
    assert result is not None
    assert "nodes" in result
    assert "links" in result


@pytest.mark.asyncio
async def test_focus_mode_returns_only_lineage_nodes(db_session, sample_lineage_data):
    """Test that focus_node_id filters to only connected nodes."""
    service = TimelineService(db_session)
    
    # sample_lineage_data fixture creates: NodeA -> NodeB -> NodeC
    # and unrelated NodeD
    focus_node_id = str(sample_lineage_data["node_b_id"])
    
    result = await service.get_graph_data(
        start_year=1900,
        end_year=2026,
        include_dissolved=True,
        tier_filter=None,
        focus_node_id=focus_node_id
    )
    
    node_ids = {n['id'] for n in result['nodes']}
    
    # Should include NodeB (focused), NodeA (predecessor), and NodeC (successor)
    assert sample_lineage_data["node_a_id"] in node_ids
    assert sample_lineage_data["node_b_id"] in node_ids
    assert sample_lineage_data["node_c_id"] in node_ids
    
    # Should NOT include unrelated NodeD
    assert sample_lineage_data["node_d_id"] not in node_ids
    
    # Should have 3 nodes in total
    assert len(result['nodes']) == 3


@pytest.mark.asyncio
async def test_focus_mode_includes_all_links_in_lineage(db_session, sample_lineage_data):
    """Test that links connect only nodes in the focused lineage."""
    service = TimelineService(db_session)
    
    focus_node_id = str(sample_lineage_data["node_b_id"])
    
    result = await service.get_graph_data(
        start_year=1900,
        end_year=2026,
        include_dissolved=True,
        tier_filter=None,
        focus_node_id=focus_node_id
    )
    
    node_ids = {n['id'] for n in result['nodes']}
    
    # Verify all links connect nodes in the result set
    for link in result['links']:
        assert link['source'] in node_ids, f"Link source {link['source']} not in lineage"
        assert link['target'] in node_ids, f"Link target {link['target']} not in lineage"
    
    # Should have 2 links: A->B and B->C
    assert len(result['links']) == 2


@pytest.mark.asyncio
async def test_focus_mode_with_nonexistent_node_returns_empty(db_session):
    """Test that focusing on a non-existent node returns empty result."""
    service = TimelineService(db_session)
    
    fake_uuid = "00000000-0000-0000-0000-000000000999"
    
    result = await service.get_graph_data(
        start_year=1900,
        end_year=2026,
        include_dissolved=True,
        tier_filter=None,
        focus_node_id=fake_uuid
    )
    
    # Should return empty nodes and links
    assert len(result['nodes']) == 0
    assert len(result['links']) == 0


@pytest.mark.asyncio
async def test_focus_mode_with_complex_lineage(db_session, complex_lineage_data):
    """Test lineage finding with branching (multiple predecessors/successors)."""
    service = TimelineService(db_session)
    
    # complex_lineage_data: NodeA -> NodeB -> NodeC
    #                              ↘ NodeD ↗
    # Focusing on NodeB should include A, B, C, D
    focus_node_id = str(complex_lineage_data["node_b_id"])
    
    result = await service.get_graph_data(
        start_year=1900,
        end_year=2026,
        include_dissolved=True,
        tier_filter=None,
        focus_node_id=focus_node_id
    )
    
    node_ids = {n['id'] for n in result['nodes']}
    
    # All connected nodes should be included
    assert complex_lineage_data["node_a_id"] in node_ids
    assert complex_lineage_data["node_b_id"] in node_ids
    assert complex_lineage_data["node_c_id"] in node_ids
    assert complex_lineage_data["node_d_id"] in node_ids
    
    assert len(result['nodes']) == 4


@pytest.mark.asyncio
async def test_focus_mode_respects_other_filters(db_session, sample_lineage_data):
    """Test that focus mode works with year and tier filters."""
    service = TimelineService(db_session)
    
    focus_node_id = str(sample_lineage_data["node_b_id"])
    
    # Filter to a year range that excludes NodeA (founded in 1990)
    # but includes NodeB (1995) and NodeC (2000)
    result = await service.get_graph_data(
        start_year=1993,
        end_year=2026,
        include_dissolved=True,
        tier_filter=None,
        focus_node_id=focus_node_id
    )
    
    node_ids = {n['id'] for n in result['nodes']}
    
    # NodeA should be filtered out by year range
    # But NodeB and NodeC should remain
    assert sample_lineage_data["node_b_id"] in node_ids
    assert sample_lineage_data["node_c_id"] in node_ids
    
    # The lineage filter is applied AFTER other filters
    # so NodeA won't be in the lineage calculation
    assert len(result['nodes']) <= 3
