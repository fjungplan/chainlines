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
    weights: Dict[str, float],
    y_slots: Dict[int, List[Dict[str, Any]]] = None,
    return_breakdown: bool = False
) -> Any:
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
        y_slots: Map of lane index to list of slot occupancies
        return_breakdown: If True, returns a dict with total and breakdown
    
    Returns:
        Total cost (lower is better) or a dict if return_breakdown is True
    """
    attraction_multiplier = 0.0
    attraction_weight = weights.get("ATTRACTION", 1000.0)

    # Calculate attraction to parents
    parents = chain_parents.get(chain["id"], [])
    if parents:
        avg_parent_y = sum(p["yIndex"] for p in parents) / len(parents)
        dist = abs(y - avg_parent_y)
        attraction_multiplier += dist * dist

    # Calculate attraction to children
    children_for_attraction = chain_children.get(chain["id"], [])
    if children_for_attraction:
        avg_child_y = sum(c["yIndex"] for c in children_for_attraction) / len(children_for_attraction)
        dist = abs(y - avg_child_y)
        attraction_multiplier += dist * dist
    
    attraction_cost = attraction_multiplier * attraction_weight

    # Calculate cut-through cost
    cut_through_count = 0
    cut_through_weight = weights.get("CUT_THROUGH", 10000.0)

    # Check cut-through with parents
    for p in parents:
        y1 = min(p["yIndex"], y)
        y2 = max(p["yIndex"], y)
        if y2 - y1 > 1:
            for lane in range(y1 + 1, y2):
                if check_collision(lane, chain["startTime"], chain["startTime"], chain["id"], chain):
                    cut_through_count += 1

    # Check cut-through with children
    children = chain_children.get(chain["id"], [])
    for c in children:
        y1 = min(y, c["yIndex"])
        y2 = max(y, c["yIndex"])
        if y2 - y1 > 1:
            for lane in range(y1 + 1, y2):
                if check_collision(lane, c["startTime"], c["startTime"], chain["id"], chain):
                    cut_through_count += 1
    
    cut_through_cost = cut_through_count * cut_through_weight

    # Calculate blocker cost
    blocker_count = 0
    blocker_weight = weights.get("BLOCKER", 5000.0)
    for seg in vertical_segments:
        if seg.get("childId") == chain["id"] or seg.get("parentId") == chain["id"]:
            continue
        
        if y > seg["y1"] and y < seg["y2"]:
            if seg["time"] >= chain["startTime"] and seg["time"] <= chain["endTime"] + 1:
                blocker_count += 1
    
    blocker_cost = blocker_count * blocker_weight

    # Calculate Y-shape cost
    y_shape_count = 0
    y_shape_weight = weights.get("Y_SHAPE", 150.0)

    for c in children_for_attraction:
        spouses = chain_parents.get(c["id"], [])
        for spouse in spouses:
            if spouse["id"] == chain["id"]:
                continue
            if abs(spouse["yIndex"] - y) < 2:
                y_shape_count += 1

    for p in parents:
        siblings = chain_children.get(p["id"], [])
        for sib in siblings:
            if sib["id"] == chain["id"]:
                continue
            if abs(sib["yIndex"] - y) < 2:
                y_shape_count += 1
    
    y_shape_cost = y_shape_count * y_shape_weight

    # Overlap Penalty (formerly Lane Sharing)
    overlap_deficiency = 0.0
    overlap_base_weight = weights.get("OVERLAP_BASE", 500000.0)
    overlap_factor_weight = weights.get("OVERLAP_FACTOR", 10000.0)
    
    # We'll also track "overlap_count" for the multiplier if we want a simple count, 
    # but "deficiency" is more accurate for the scale. 
    # Let's return total overlap cost separately.
    overlap_total_cost = 0.0
    
    # Spacing incentive (negative cost)
    spacing_incentive = 0.0
    lane_sharing_weight = weights.get("LANE_SHARING", 0.0)

    if y_slots:
        slots_at_y = y_slots.get(y, [])
        for slot in slots_at_y:
            if slot.get("chainId") == chain["id"]:
                continue
            
            gap = max(
                slot["start"] - chain["endTime"],
                chain["startTime"] - slot["end"]
            )
            
            is_family = False
            neighbor_id = slot.get("chainId")
            
            if neighbor_id in [p["id"] for p in parents]:
                is_family = True
            elif not is_family:
                 for child_list in chain_children.values():
                     if any(c["id"] == neighbor_id for c in child_list):
                         is_family = True
                         break
            
            overlap_penalty = 0.0
            if is_family:
                if gap < 0:
                    magnitude = abs(gap)
                    overlap_deficiency += magnitude
                    overlap_penalty = overlap_base_weight + (magnitude * overlap_factor_weight)
            else:
                if gap < 2:
                    magnitude = 2 - gap
                    overlap_deficiency += magnitude
                    overlap_penalty = overlap_base_weight + (magnitude * overlap_factor_weight)
            
            overlap_total_cost += overlap_penalty
            
            if overlap_penalty == 0 and lane_sharing_weight > 0 and gap > 0:
                spacing_incentive += (lane_sharing_weight / (10 ** (gap - 1)))

    total = attraction_cost + cut_through_cost + blocker_cost + y_shape_cost + overlap_total_cost + spacing_incentive

    if return_breakdown:
        return {
            "total": total,
            "breakdown": {
                "ATTRACTION": {"multiplier": attraction_multiplier, "sum": attraction_cost},
                "CUT_THROUGH": {"multiplier": cut_through_count, "sum": cut_through_cost},
                "BLOCKER": {"multiplier": blocker_count, "sum": blocker_cost},
                "Y_SHAPE": {"multiplier": y_shape_count, "sum": y_shape_cost},
                "OVERLAP": {"multiplier": overlap_deficiency, "sum": overlap_total_cost},
                "SPACING": {"multiplier": 0, "sum": spacing_incentive} # Incentive is a bonus
            }
        }

    return total
