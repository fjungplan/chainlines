
import pytest
from app.optimizer.chain_builder import build_chains

def test_chain_strict_adjacency():
    """
    User scenario: Node A End + 1 = Node B Start.
    Should form a SINGLE chain.
    """
    nodes = [
        {"id": "A", "founding_year": 2000, "dissolution_year": 2005},
        {"id": "B", "founding_year": 2006, "dissolution_year": 2010}
    ]
    links = [
        {"source": "A", "target": "B", "parentId": "A", "childId": "B"}
    ]
    
    chains = build_chains(nodes, links, current_year=2024)
    
    assert len(chains) == 1
    chain = chains[0]
    assert len(chain["nodes"]) == 2
    assert chain["nodes"][0]["id"] == "A"
    assert chain["nodes"][1]["id"] == "B"

def test_chain_gap():
    """
    Gap scenario: Node A End = 2005, Node B Start = 2008.
    Should form a SINGLE chain (gaps allowed).
    """
    nodes = [
        {"id": "A", "founding_year": 2000, "dissolution_year": 2005},
        {"id": "B", "founding_year": 2008, "dissolution_year": 2010}
    ]
    links = [
        {"source": "A", "target": "B", "parentId": "A", "childId": "B"}
    ]
    
    chains = build_chains(nodes, links, current_year=2024)
    
    assert len(chains) == 1
    assert len(chains[0]["nodes"]) == 2

def test_chain_overlap_fails():
    """
    Overlap scenario: Node A End = 2005, Node B Start = 2005.
    Should BREAK chain (visual overlap).
    """
    nodes = [
        {"id": "A", "founding_year": 2000, "dissolution_year": 2005},
        {"id": "B", "founding_year": 2005, "dissolution_year": 2010}
    ]
    links = [
        {"source": "A", "target": "B", "parentId": "A", "childId": "B"}
    ]
    
    chains = build_chains(nodes, links, current_year=2024)
    
    # Should be 2 chains because of overlap break
    assert len(chains) == 2
    assert chains[0]["nodes"][0]["id"] == "A"
    assert chains[1]["nodes"][0]["id"] == "B"

def test_chain_active_parent_fails():
    """
    Active parent scenario: Node A (Active), Node B Start = 2006.
    Parent extends to Current Year (2024).
    2024 > 2006 -> Overlap. Should BREAK chain.
    """
    nodes = [
        {"id": "A", "founding_year": 2000, "dissolution_year": None}, # Active
        {"id": "B", "founding_year": 2006, "dissolution_year": 2010}
    ]
    links = [
        {"source": "A", "target": "B", "parentId": "A", "childId": "B"}
    ]
    
    chains = build_chains(nodes, links, current_year=2024)
    
    assert len(chains) == 2

def test_chain_zombie_node_backend_failure():
    """
    Zombie Node scenario: Node A has NO dissolution_year (None),
    BUT it effectively ended in 2005 (Last Era).
    Node B starts in 2006.
    
    Current Backend Logic: Treats A as Active (End 2024).
    2024 + 1 > 2006 -> Overlap -> BREAK.
    
    Desired Logic: Should detect 'Zombie' status and use Last Era (2005).
    2005 + 1 > 2006 -> No Overlap -> CHAIN.
    """
    nodes = [
        {"id": "A", "founding_year": 2000, "dissolution_year": None, "eras": [{"name": "A", "year": 2005}]},
        {"id": "B", "founding_year": 2006, "dissolution_year": 2010}
    ]
    links = [
        {"source": "A", "target": "B", "parentId": "A", "childId": "B"}
    ]
    
    chains = build_chains(nodes, links, current_year=2024)
    
    # CURRENTLY FAILS (Expects 1, gets 2)
    assert len(chains) == 1
    assert len(chains[0]["nodes"]) == 2
