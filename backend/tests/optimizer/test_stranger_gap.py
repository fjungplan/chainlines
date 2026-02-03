"""
Test: Stranger Gap Enforcement

Verifies that:
1. Strangers touching (gap=1) is penalized (Gap >= 2 required)
2. Family touching (gap=1) is allowed (Gap >= 0 required)
"""
import pytest
from app.optimizer.cost_function import calculate_single_chain_cost

def mock_check_collision(*args):
    return False

def test_stranger_touching_penalty():
    """
    Strangers touching (gap=1) should strictly be penalized.
    Example: A ends 1995, B starts 1996. Gap = 1. 
    User wants "at least a year gap between" -> Gap >= 2.
    """
    chain = {"id": "B", "startTime": 1996, "endTime": 2000, "founding_year": 1996}
    # Stranger A occupies 1990-1995 in same lane
    y_slots = {
        0: [{"chainId": "A", "start": 1990, "end": 1995}]
    }
    
    weights = {
        "OVERLAP_BASE": 1000.0,
        "OVERLAP_FACTOR": 100.0,
        "LANE_SHARING": 0  # Disable soft sharing to focus on overlap
    }
    
    cost = calculate_single_chain_cost(
        chain=chain,
        y=0,
        chain_parents={},
        chain_children={},
        vertical_segments=[],
        check_collision=mock_check_collision,
        weights=weights,
        y_slots=y_slots
    )
    
    # helper calculate: gap = 1996 - 1995 = 1.
    # Current logic: gap < 1 checks? 1 < 1 is False -> No penalty.
    # New logic: gap < 2 checks? 1 < 2 is True -> Penalty!
    assert cost > 0, "Strangers touching (gap=1) must be penalized!"

def test_family_touching_allowed():
    """
    Family touching (gap=1) should NOT be penalized.
    Example: A (Parent) ends 1995, B (Child) starts 1996. Gap = 1.
    """
    chain = {"id": "B", "startTime": 1996, "endTime": 2000, "founding_year": 1996}
    # Parent A occupies 1990-1995 in same lane
    y_slots = {
        0: [{"chainId": "A", "start": 1990, "end": 1995}]
    }
    
    # Define relationship (Parent must have yIndex for attraction calc)
    chain_parents = {"B": [{"id": "A", "yIndex": 0}]}
    
    weights = {
        "OVERLAP_BASE": 1000.0,
        "OVERLAP_FACTOR": 100.0,
        "LANE_SHARING": 0
    }
    
    cost = calculate_single_chain_cost(
        chain=chain,
        y=0,
        chain_parents=chain_parents,
        chain_children={},
        vertical_segments=[],
        check_collision=mock_check_collision,
        weights=weights,
        y_slots=y_slots
    )
    
    assert cost == 0, "Family touching (gap=1) should be allowed!"

def test_stranger_gap_adequate():
    """
    Strangers with 1 year gap (gap=2) should be allowed.
    Example: A ends 1995, Gap 1996, B starts 1997. Gap = 2.
    """
    chain = {"id": "B", "startTime": 1997, "endTime": 2000, "founding_year": 1997}
    y_slots = {
        0: [{"chainId": "A", "start": 1990, "end": 1995}]
    }
    
    weights = {
        "OVERLAP_BASE": 1000.0,
        "OVERLAP_FACTOR": 100.0,
        "LANE_SHARING": 0
    }
    
    cost = calculate_single_chain_cost(
        chain=chain,
        y=0,
        chain_parents={},
        chain_children={},
        vertical_segments=[],
        check_collision=mock_check_collision,
        weights=weights,
        y_slots=y_slots
    )
    
    assert cost == 0, "Strangers with 1 year gap (gap=2) should be allowed!"
