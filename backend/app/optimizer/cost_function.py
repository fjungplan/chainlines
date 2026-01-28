"""
Layout cost calculation for the genetic optimizer.
Ported from frontend/src/utils/layout/utils/costCalculator.js

Evaluates graph layout quality using penalties:
- ATTRACTION: Quadratic distance between parent-child chains
- CUT_THROUGH: Penalty for passing through occupied lanes
- BLOCKER: Penalty for crossing existing vertical segments
- Y_SHAPE: Penalty for tightly squeezing merge/split branches
"""
from typing import List, Dict, Callable, Any

def calculate_single_chain_cost(
    chain: Dict[str, Any],
    y: int,
    chain_parents: Dict[str, List[Dict[str, Any]]],
    chain_children: Dict[str, List[Dict[str, Any]]],
    vertical_segments: List[Dict[str, Any]],
    check_collision: Callable[[int, int, int, str, Dict[str, Any]], bool],
    weights: Dict[str, float]
) -> float:
    """
    Calculate the penalty score for placing a chain at a specific Y position.
    
    Args:
        chain: The chain being placed
        y: The potential Y position (lane index)
        chain_parents: Map of chain ID to parent chain objects
        chain_children: Map of chain ID to child chain objects
        vertical_segments: Array of vertical segment blockers
        check_collision: Collision detection function
        weights: Weight configuration for penalties
    
    Returns:
        Total cost (lower is better)
    """
    attraction_cost = 0.0
    attraction_weight = weights.get("ATTRACTION", 1000.0)

    # Calculate attraction to parents
    parents = chain_parents.get(chain["id"], [])
    if parents:
        avg_parent_y = sum(p["yIndex"] for p in parents) / len(parents)
        dist = abs(y - avg_parent_y)
        attraction_cost += (dist * dist) * attraction_weight

    # Calculate attraction to children
    children_for_attraction = chain_children.get(chain["id"], [])
    if children_for_attraction:
        avg_child_y = sum(c["yIndex"] for c in children_for_attraction) / len(children_for_attraction)
        dist = abs(y - avg_child_y)
        attraction_cost += (dist * dist) * attraction_weight

    # Calculate cut-through cost
    cut_through_cost = 0.0
    cut_through_weight = weights.get("CUT_THROUGH", 10000.0)

    # Check cut-through with parents
    for p in parents:
        y1 = min(p["yIndex"], y)
        y2 = max(p["yIndex"], y)
        if y2 - y1 > 1:
            for lane in range(y1 + 1, y2):
                # Use chain start time for cut-through check (instantaneous cut)
                if check_collision(lane, chain["startTime"], chain["startTime"], chain["id"], chain):
                    cut_through_cost += cut_through_weight

    # Check cut-through with children
    children = chain_children.get(chain["id"], [])
    for c in children:
        y1 = min(y, c["yIndex"])
        y2 = max(y, c["yIndex"])
        if y2 - y1 > 1:
            for lane in range(y1 + 1, y2):
                if check_collision(lane, c["startTime"], c["startTime"], chain["id"], chain):
                    cut_through_cost += cut_through_weight

    # Calculate blocker cost
    blocker_cost = 0.0
    blocker_weight = weights.get("BLOCKER", 5000.0)
    for seg in vertical_segments:
        # Ignore segments that are part of this chain's own connections
        if seg.get("childId") == chain["id"] or seg.get("parentId") == chain["id"]:
            continue
        
        # Check if potential Y position sits inside a vertical segment
        if y > seg["y1"] and y < seg["y2"]:
            # Check if the chain's timespan overlaps the blocker segment's time
            if seg["time"] >= chain["startTime"] and seg["time"] <= chain["endTime"] + 1:
                blocker_cost += blocker_weight

    # Calculate Y-shape cost
    y_shape_cost = 0.0
    y_shape_weight = weights.get("Y_SHAPE", 150.0)

    # Penalty for merging parents being too close (squeezed Y)
    for c in children_for_attraction:
        spouses = chain_parents.get(c["id"], [])
        for spouse in spouses:
            if spouse["id"] == chain["id"]:
                continue
            if abs(spouse["yIndex"] - y) < 2:
                y_shape_cost += y_shape_weight

    # Penalty for splitting children being too close
    for p in parents:
        siblings = chain_children.get(p["id"], [])
        for sib in siblings:
            if sib["id"] == chain["id"]:
                continue
            if abs(sib["yIndex"] - y) < 2:
                y_shape_cost += y_shape_weight

    return attraction_cost + cut_through_cost + blocker_cost + y_shape_cost
