"""
Chain Builder for Backend Optimizer

Ports the frontend's chainBuilder.js logic to Python.
This ensures the optimizer works with the same concept of "chains"
as the frontend, preventing mismatch when applying cached layouts.

Rules for chain building:
1. Strict 1:1 predecessor/successor relationship
2. No visual overlap (parentEnd + 1 > childStart breaks chain)
3. Merge points (>1 predecessor) start a new chain
"""
from typing import List, Dict, Any, Set, Optional
from datetime import datetime


def build_chains(
    nodes: List[Dict[str, Any]], 
    links: List[Dict[str, Any]],
    current_year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Decompose nodes into linear "chains" (sequences of nodes).
    
    A chain is formed when nodes have 1:1 predecessor/successor relationships
    and no visual overlap.
    
    Args:
        nodes: List of node dicts with id, founding_year, dissolution_year
        links: List of link dicts with parentId, childId
        current_year: Optional current year for nodes without dissolution_year
        
    Returns:
        List of chain dicts with id, nodes, startTime, endTime
    """
    if current_year is None:
        current_year = datetime.now().year
    
    # Build node lookup map
    node_map: Dict[str, Dict] = {n["id"]: n for n in nodes}
    
    # Build predecessor and successor maps
    preds: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
    succs: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
    
    for link in links:
        parent_id = link["parentId"]
        child_id = link["childId"]
        
        if parent_id in node_map and child_id in node_map:
            preds[child_id].append(parent_id)
            succs[parent_id].append(child_id)
    
    chains: List[Dict[str, Any]] = []
    visited: Set[str] = set()

    # Link lookup map: (parent, child) -> link object
    link_map: Dict[tuple, Dict] = {}
    for link in links:
        link_map[(link["parentId"], link["childId"])] = link
    
    def get_end_year(node: Dict) -> int:
        """
        Get the visual end year of a node (dissolution_year, last era, or current_year).
        Matches frontend logic: if no dissolution, try to use last era.
        """
        if node.get("dissolution_year"):
            return node["dissolution_year"]
            
        # Zombie Node Check: If no dissolution but has eras, use the last era
        eras = node.get("eras") or []
        if eras:
            # Safely find max year to avoid sorting assumption
            try:
                # Handle both dict objects and potentially other formats if data varies
                max_era_year = max(e.get("year", 0) for e in eras)
                if max_era_year > 0:
                    return max_era_year
            except Exception:
                pass
                
        return current_year

    def is_primary_continuation(parent_id: str, child_id: str) -> bool:
        """
        Determine if the link is a 'primary' temporal continuation.
        Used to resolve merges: if one parent connects at the child's birth,
        it claims the chain, while others are treated as secondary mergers.
        """
        link = link_map.get((parent_id, child_id))
        child = node_map.get(child_id)
        
        if not link or not child:
            return False
            
        link_year = link.get("year")
        child_start = child.get("founding_year")
        
        if link_year is None or child_start is None:
            return False
            
        # Tolerance: Link matches child start year (allowing for +/- 1 year fuzziness)
        # e.g. GBC(End 1977) -> Link(1978) -> Malvor(Start 1978)
        return abs(link_year - child_start) <= 1
    
    def get_primary_predecessors(node_id: str) -> List[str]:
        """Return list of predecessors that are primary continuations."""
        return [p_id for p_id in preds.get(node_id, []) 
                if is_primary_continuation(p_id, node_id)]

    def is_chain_start(node_id: str) -> bool:
        """
        Determine if a node should start a new chain.
        """
        p = preds.get(node_id, [])
        num_preds = len(p)
        
        # Case 1: No predecessors -> Always start
        if num_preds == 0:
            return True
            
        # Case 2: Multiple Predecessors (Merge)
        if num_preds > 1:
            # CHECK PRIORITY: If there is EXACTLY ONE primary predecessor,
            # we do NOT start a chain (we let the primary parent continue).
            # If 0 or >1 primary predecessors, it's ambiguous -> Start new chain.
            primary_preds = get_primary_predecessors(node_id)
            if len(primary_preds) == 1:
                return False
            return True
        
        # Case 3: Single Predecessor
        parent_id = p[0]
        parent_succs = succs.get(parent_id, [])
        
        # Parent has multiple successors (split) -> start new chain
        # (Splits always break chains in current logic to avoid forks)
        if len(parent_succs) > 1:
            return True
        
        # Check for visual overlap
        parent_node = node_map.get(parent_id)
        my_node = node_map.get(node_id)
        
        if parent_node and my_node:
            parent_end = get_end_year(parent_node)
            my_start = my_node["founding_year"]
            
            # Visual overlap: parent renders to (parent_end + 1), check if that > my_start
            if parent_end + 1 > my_start:
                return True
        
        return False
    
    # Build chains starting from chain-start nodes
    for node in nodes:
        node_id = node["id"]
        
        if node_id in visited:
            continue
        
        if is_chain_start(node_id):
            chain_nodes: List[Dict] = []
            curr = node_id
            
            while curr:
                # Cycle detection / Re-visit check
                if curr in visited:
                    break

                visited.add(curr)
                chain_nodes.append(node_map[curr])
                
                s = succs.get(curr, [])
                
                # Stop if no successors or >1 successors (split)
                # Splits are hard breaks.
                if len(s) != 1:
                    break
                
                next_id = s[0]
                next_preds = preds.get(next_id, [])
                
                # Handling Merges (next node has >1 predecessors)
                if len(next_preds) > 1:
                    # Only continue if 'curr' is the Primary Predecessor.
                    # AND if it is the ONLY primary predecessor.
                    
                    if not is_primary_continuation(curr, next_id):
                        break
                        
                    primary_preds = get_primary_predecessors(next_id)
                    if len(primary_preds) != 1:
                        break
                        
                    # If we are the one true parent, continue.
                
                # Check for visual overlap before continuing
                curr_node = node_map.get(curr)
                next_node = node_map.get(next_id)
                
                if curr_node and next_node:
                    curr_end = get_end_year(curr_node)
                    next_start = next_node["founding_year"]
                    
                    # Visual overlap -> break chain
                    if curr_end + 1 > next_start:
                        break
                
                curr = next_id
            
            if chain_nodes:
                # Use first node's ID as the chain ID (for frontend matching)
                first_node = chain_nodes[0]
                last_node = chain_nodes[-1]
                
                chains.append({
                    "id": first_node["id"],
                    "nodes": chain_nodes,
                    "startTime": first_node["founding_year"],
                    "endTime": get_end_year(last_node),
                })
    
    return chains
