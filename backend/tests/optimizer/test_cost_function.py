"""
Tests for the layout cost function.
Ported from frontend/tests/utils/layout/costCalculator.test.js
"""
import pytest
from app.optimizer.cost_function import calculate_single_chain_cost

# Weights from frontend config
MOCK_WEIGHTS = {
    "ATTRACTION": 1000.0,
    "CUT_THROUGH": 10000.0,
    "BLOCKER": 5000.0,
    "Y_SHAPE": 150.0
}

def create_chain(id, y_index=0, start_time=2000, end_time=2010):
    """Helper to create chain objects"""
    return {
        "id": id,
        "yIndex": y_index,
        "startTime": start_time,
        "endTime": end_time
    }

def test_return_0_cost_for_isolated_chain():
    """Isolated chain with no parents/children should have 0 cost"""
    chain = create_chain("c1")
    chain_parents = {}
    chain_children = {}
    vertical_segments = []
    
    def check_collision(lane, start, end, exclude_id, chain_obj):
        return False

    cost = calculate_single_chain_cost(
        chain,
        0,
        chain_parents,
        chain_children,
        vertical_segments,
        check_collision,
        MOCK_WEIGHTS
    )

    assert cost == 0

def test_calculate_attraction_cost_to_parents():
    """Parent at y=0, placing child at y=10"""
    parent = create_chain("p1", y_index=0)
    chain = create_chain("c1")
    chain_parents = {"c1": [parent]}
    chain_children = {}
    
    def check_collision(lane, start, end, exclude_id, chain_obj):
        return False

    cost = calculate_single_chain_cost(
        chain,
        10,
        chain_parents,
        chain_children,
        [],
        check_collision,
        MOCK_WEIGHTS
    )

    # dist = 10. Cost = 10^2 * weight
    expected_cost = 100 * MOCK_WEIGHTS["ATTRACTION"]
    assert cost == expected_cost

def test_calculate_attraction_cost_to_children():
    """Child at y=10, placing parent at y=0"""
    child = create_chain("child1", y_index=10)
    chain = create_chain("p1")
    chain_parents = {}
    chain_children = {"p1": [child]}
    
    def check_collision(lane, start, end, exclude_id, chain_obj):
        return False

    cost = calculate_single_chain_cost(
        chain,
        0,
        chain_parents,
        chain_children,
        [],
        check_collision,
        MOCK_WEIGHTS
    )

    # dist = 10. Cost = 10^2 * weight
    expected_cost = 100 * MOCK_WEIGHTS["ATTRACTION"]
    assert cost == expected_cost

def test_calculate_cut_through_cost():
    """Parent at y=0, placing child at y=5, collision at y=2"""
    parent = create_chain("p1", y_index=0)
    chain = create_chain("c1")
    chain_parents = {"c1": [parent]}
    chain_children = {}
    
    # Mock collision check: returns true for lane 2
    def check_collision(lane, start, end, exclude_id, chain_obj):
        return lane == 2

    cost = calculate_single_chain_cost(
        chain,
        5,
        chain_parents,
        chain_children,
        [],
        check_collision,
        MOCK_WEIGHTS
    )

    # Attraction: 5^2 * ATTRACTION
    # Cut-through: 1 collision * CUT_THROUGH
    expected_attraction = 25 * MOCK_WEIGHTS["ATTRACTION"]
    expected_cut_through = MOCK_WEIGHTS["CUT_THROUGH"]

    assert cost == expected_attraction + expected_cut_through

def test_calculate_blocker_cost():
    """Placing chain at y=5 with vertical segment blocking"""
    chain = create_chain("c1", y_index=0, start_time=2000, end_time=2010)
    chain_parents = {}
    chain_children = {}
    # Vertical segment from y=0 to y=10 that blocks (time covers chain)
    vertical_segments = [{
        "y1": 0,
        "y2": 10,
        "time": 2005,
        "childId": "other1",
        "parentId": "other2"
    }]
    
    def check_collision(lane, start, end, exclude_id, chain_obj):
        return False

    cost = calculate_single_chain_cost(
        chain,
        5,
        chain_parents,
        chain_children,
        vertical_segments,
        check_collision,
        MOCK_WEIGHTS
    )

    assert cost == MOCK_WEIGHTS["BLOCKER"]

def test_ignore_blockers_that_are_its_own_segments():
    """Own segments should not count as blockers"""
    chain = create_chain("c1", y_index=0, start_time=2000, end_time=2010)
    vertical_segments = [{
        "y1": 0,
        "y2": 10,
        "time": 2005,
        "childId": "c1",  # It's my own child link
        "parentId": "p1"
    }]
    
    def check_collision(lane, start, end, exclude_id, chain_obj):
        return False

    cost = calculate_single_chain_cost(
        chain,
        5,
        {},
        {},
        vertical_segments,
        check_collision,
        MOCK_WEIGHTS
    )

    assert cost == 0

def test_calculate_y_shape_cost_for_splits():
    """Y-shape penalty for merging parents being too close"""
    # Scenario: Merge
    # Child c1 has parents me and spouse.
    # Placing me at y=5.
    # spouse is at y=5 (diff=0).
    # Should apply penalty.
    
    me = create_chain("me")
    spouse = create_chain("spouse", y_index=5)
    child = create_chain("child", y_index=5)

    chain_children = {"me": [child]}
    # Child's parents are me and spouse
    chain_parents = {"child": [me, spouse]}

    def check_collision(lane, start, end, exclude_id, chain_obj):
        return False

    cost = calculate_single_chain_cost(
        me,
        5,  # Placing me at same Y as spouse
        chain_parents,
        chain_children,
        [],
        check_collision,
        MOCK_WEIGHTS
    )

    # Note: attraction to child (y=5) is 0.
    # Y-shape penalty applies because spouse.yIndex - y = 5 - 5 = 0 < 2
    assert cost == MOCK_WEIGHTS["Y_SHAPE"]
