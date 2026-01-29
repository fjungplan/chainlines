"""
Test: Backend Chain Builder

Verifies that the backend's chain-building logic exactly matches
the frontend's chainBuilder.js rules:

1. Strict 1:1 predecessor/successor relationship
2. No visual overlap (parentEnd + 1 > childStart breaks chain)  
3. Merge points (>1 predecessor) start a new chain
"""
import pytest
from app.optimizer.chain_builder import build_chains


class TestChainBuilder:
    """Tests for chain-building logic parity with frontend."""

    def test_simple_linear_chain(self):
        """
        A -> B -> C (all 1:1, no overlap)
        Should produce 1 chain with 3 nodes.
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995},
            {"id": "B", "founding_year": 1996, "dissolution_year": 2000},
            {"id": "C", "founding_year": 2001, "dissolution_year": 2005},
        ]
        links = [
            {"parentId": "A", "childId": "B"},
            {"parentId": "B", "childId": "C"},
        ]
        
        chains = build_chains(nodes, links)
        
        assert len(chains) == 1
        assert len(chains[0]["nodes"]) == 3
        assert chains[0]["nodes"][0]["id"] == "A"
        assert chains[0]["nodes"][1]["id"] == "B"
        assert chains[0]["nodes"][2]["id"] == "C"

    def test_visual_overlap_breaks_chain(self):
        """
        A (1990-1997) -> B (1996-2000)
        Parent end + 1 = 1998 > 1996 = child start -> BREAK CHAIN
        Should produce 2 separate chains.
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1997},
            {"id": "B", "founding_year": 1996, "dissolution_year": 2000},
        ]
        links = [
            {"parentId": "A", "childId": "B"},
        ]
        
        chains = build_chains(nodes, links)
        
        assert len(chains) == 2
        assert chains[0]["nodes"][0]["id"] == "A"
        assert chains[1]["nodes"][0]["id"] == "B"

    def test_split_creates_separate_chains(self):
        """
        A -> B (A has 2 successors: B and C)
        A -> C
        Should produce 3 chains (A, B, C each separate because A splits).
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995},
            {"id": "B", "founding_year": 1996, "dissolution_year": 2000},
            {"id": "C", "founding_year": 1997, "dissolution_year": 2001},
        ]
        links = [
            {"parentId": "A", "childId": "B"},
            {"parentId": "A", "childId": "C"},
        ]
        
        chains = build_chains(nodes, links)
        
        # A splits into B and C, so all three are separate chains
        assert len(chains) == 3

    def test_merge_creates_separate_chains(self):
        """
        A -> C (C has 2 predecessors: A and B)
        B -> C
        Should produce 3 chains (A, B, C because C merges).
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995},
            {"id": "B", "founding_year": 1991, "dissolution_year": 1996},
            {"id": "C", "founding_year": 1997, "dissolution_year": 2000},
        ]
        links = [
            {"parentId": "A", "childId": "C"},
            {"parentId": "B", "childId": "C"},
        ]
        
        chains = build_chains(nodes, links)
        
        # C has 2 predecessors (merge), so all three are separate chains
        assert len(chains) == 3

    def test_no_links_all_separate(self):
        """
        A, B, C with no links -> 3 separate chains.
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995},
            {"id": "B", "founding_year": 1996, "dissolution_year": 2000},
            {"id": "C", "founding_year": 2001, "dissolution_year": 2005},
        ]
        links = []
        
        chains = build_chains(nodes, links)
        
        assert len(chains) == 3

    def test_chain_uses_first_node_id_as_key(self):
        """
        Chain ID should be based on the first node's ID for frontend matching.
        """
        nodes = [
            {"id": "first-uuid", "founding_year": 1990, "dissolution_year": 1995},
            {"id": "second-uuid", "founding_year": 1996, "dissolution_year": 2000},
        ]
        links = [
            {"parentId": "first-uuid", "childId": "second-uuid"},
        ]
        
        chains = build_chains(nodes, links)
        
        assert len(chains) == 1
        # The chain's lookup key should be the first node's ID
        assert chains[0]["id"] == "first-uuid"

    def test_chain_time_range_spans_all_nodes(self):
        """
        Chain's startTime should be first node's founding_year.
        Chain's endTime should be last node's dissolution_year (or current year if null).
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995},
            {"id": "B", "founding_year": 1996, "dissolution_year": 2000},
            {"id": "C", "founding_year": 2001, "dissolution_year": 2005},
        ]
        links = [
            {"parentId": "A", "childId": "B"},
            {"parentId": "B", "childId": "C"},
        ]
        
        chains = build_chains(nodes, links)
        
        assert chains[0]["startTime"] == 1990
        assert chains[0]["endTime"] == 2005
