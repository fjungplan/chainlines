import pytest
from app.optimizer.chain_builder import build_chains
from app.models.enums import LineageEventType

class TestChainBuilderRefinement:
    """Reproduction tests for clarified chain-building logic."""

    def test_single_legal_transfer_priority_merge(self):
        """
        Merge case: 
        A -> B (LEGAL_TRANSFER)
        C -> B (SPIRITUAL_SUCCESSION)
        B should continue A's chain because there is exactly one LEGAL_TRANSFER.
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995, "name": "Team A", "eras": [{"year": 1995}]},
            {"id": "B", "founding_year": 1996, "dissolution_year": 2000, "name": "Team B", "eras": [{"year": 1996}]},
            {"id": "C", "founding_year": 1990, "dissolution_year": 1995, "name": "Team C", "eras": [{"year": 1995}]},
        ]
        links = [
            {"parentId": "A", "childId": "B", "type": LineageEventType.LEGAL_TRANSFER, "year": 1996},
            {"parentId": "C", "childId": "B", "type": LineageEventType.SPIRITUAL_SUCCESSION, "year": 1996},
        ]
        
        chains = build_chains(nodes, links)
        
        # A and B should be in the same chain
        a_chain = next(c for c in chains if any(n["id"] == "A" for n in c["nodes"]))
        assert "B" in [n["id"] for n in a_chain["nodes"]]
        assert len(chains) == 2 # [A, B] and [C]

    def test_single_legal_transfer_priority_split(self):
        """
        Split case:
        A -> B (LEGAL_TRANSFER)
        A -> C (SPLIT)
        A and B should remain in the same chain because there is exactly one LEGAL_TRANSFER.
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995, "eras": [{"year": 1995}]},
            {"id": "B", "founding_year": 1996, "dissolution_year": 2000, "eras": [{"year": 1996}]},
            {"id": "C", "founding_year": 1996, "dissolution_year": 2000, "eras": [{"year": 1996}]},
        ]
        links = [
            {"parentId": "A", "childId": "B", "type": LineageEventType.LEGAL_TRANSFER, "year": 1996},
            {"parentId": "A", "childId": "C", "type": LineageEventType.SPLIT, "year": 1996},
        ]
        
        chains = build_chains(nodes, links)
        
        # A and B should be in the same chain
        a_chain = next(c for c in chains if any(n["id"] == "A" for n in c["nodes"]))
        assert "B" in [n["id"] for n in a_chain["nodes"]]
        assert "C" not in [n["id"] for n in a_chain["nodes"]]
        assert len(chains) == 2 # [A, B] and [C]

    def test_ambiguity_breaks_chain_multiple_legal_transfers(self):
        """
        Ambiguity case:
        A -> B (LEGAL_TRANSFER)
        A -> C (LEGAL_TRANSFER)
        Multiple legal transfers should break the chain.
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995, "eras": [{"year": 1995}]},
            {"id": "B", "founding_year": 1996, "dissolution_year": 2000, "eras": [{"year": 1996}]},
            {"id": "C", "founding_year": 1996, "dissolution_year": 2000, "eras": [{"year": 1996}]},
        ]
        links = [
            {"parentId": "A", "childId": "B", "type": LineageEventType.LEGAL_TRANSFER, "year": 1996},
            {"parentId": "A", "childId": "C", "type": LineageEventType.LEGAL_TRANSFER, "year": 1996},
        ]
        
        chains = build_chains(nodes, links)
        
        # All three should be separate chains
        assert len(chains) == 3
        for chain in chains:
            assert len(chain["nodes"]) == 1

    def test_merge_ambiguity_breaks_chain_multiple_legal_transfers(self):
        """
        Ambiguity case:
        A -> C (LEGAL_TRANSFER)
        B -> C (LEGAL_TRANSFER)
        C has multiple legal predecessors -> Break.
        """
        nodes = [
            {"id": "A", "founding_year": 1990, "dissolution_year": 1995, "eras": [{"year": 1995}]},
            {"id": "B", "founding_year": 1990, "dissolution_year": 1995, "eras": [{"year": 1995}]},
            {"id": "C", "founding_year": 1996, "dissolution_year": 2000, "eras": [{"year": 1996}]},
        ]
        links = [
            {"parentId": "A", "childId": "C", "type": LineageEventType.LEGAL_TRANSFER, "year": 1996},
            {"parentId": "B", "childId": "C", "type": LineageEventType.LEGAL_TRANSFER, "year": 1996},
        ]
        
        chains = build_chains(nodes, links)
        
        # All three should be separate chains
        assert len(chains) == 3
