
import pytest
from app.optimizer.cost_function import calculate_single_chain_cost

MOCK_WEIGHTS = {
    "ATTRACTION": 1000.0,
    "CUT_THROUGH": 10000.0,
    "BLOCKER": 5000.0,
    "Y_SHAPE": 150.0,
    "OVERLAP_BASE": 500000.0,
    "OVERLAP_FACTOR": 10000.0
}

def create_chain(id, y_index=0, start_time=2000, end_time=2010):
    return {"id": id, "yIndex": y_index, "startTime": start_time, "endTime": end_time}

def test_cost_breakdown_format():
    """Verify that calculate_single_chain_cost can return a breakdown dictionary."""
    parent = create_chain("p1", y_index=0)
    chain = create_chain("c1", start_time=2000, end_time=2010)
    
    # 1. Setup an attraction penalty
    # dist = 5 -> attraction = 25 * 1000 = 25000
    chain_parents = {"c1": [parent]}
    
    # 2. Setup a cut-through penalty
    # collision at lane 2. 
    def check_collision(lane, start, end, exclude_id, chain_obj):
        return lane == 2 

    # 3. Setup a blocker penalty
    # Vertical segment at y=3 (which is between 0 and 5)
    vertical_segments = [{
        "y1": 1,
        "y2": 4,
        "time": 2005,
        "childId": "other",
        "parentId": "other2"
    }]

    result = calculate_single_chain_cost(
        chain,
        5,
        chain_parents,
        {},
        vertical_segments,
        check_collision,
        MOCK_WEIGHTS,
        return_breakdown=True
    )

    assert isinstance(result, dict)
    assert "total" in result
    assert "breakdown" in result
    
    breakdown = result["breakdown"]
    
    # Attraction: dist=5, dist^2=25
    assert breakdown["ATTRACTION"]["multiplier"] == 25.0
    assert breakdown["ATTRACTION"]["sum"] == 25000.0
    
    # Cut-through: lanes 1, 2, 3, 4. 
    # check_collision(2, ...) is True -> 1 collision
    assert breakdown["CUT_THROUGH"]["multiplier"] == 1
    assert breakdown["CUT_THROUGH"]["sum"] == 10000.0
    
    # Blocker: seg at y=3 is between y=0 and y=5? Wait, it says "if y > seg[y1] and y < seg[y2]"
    # My chain is at y=5. Seg is at y1=1, y2=4. 
    # 5 is NOT between 1 and 4.
    # Let's adjust seg to y1=0, y2=10. 5 IS between 0 and 10.
    # AND seg[time]=2005 is between 2000 and 2011 (end+1).
    vertical_segments[0]["y1"] = 0
    vertical_segments[0]["y2"] = 10
    
    result = calculate_single_chain_cost(
        chain,
        5,
        chain_parents,
        {},
        vertical_segments,
        check_collision,
        MOCK_WEIGHTS,
        return_breakdown=True
    )
    
    breakdown = result["breakdown"]
    assert breakdown["BLOCKER"]["multiplier"] == 1
    assert breakdown["BLOCKER"]["sum"] == 5000.0
