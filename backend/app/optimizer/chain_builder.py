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
    
    def is_chain_start(node_id: str) -> bool:
        """
        Determine if a node should start a new chain.
        
        A node is a chain start if:
        1. It has 0 or >1 predecessors (not exactly 1)
        2. Its single predecessor has >1 successors (parent splits)
        3. There's visual overlap with the single predecessor
        """
        p = preds.get(node_id, [])
        
        # 0 or >1 predecessors -> start new chain
        if len(p) != 1:
            return True
        
        parent_id = p[0]
        parent_succs = succs.get(parent_id, [])
        
        # Parent has multiple successors (split) -> start new chain
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
                visited.add(curr)
                chain_nodes.append(node_map[curr])
                
                s = succs.get(curr, [])
                
                # Stop if no successors or >1 successors (split)
                if len(s) != 1:
                    break
                
                next_id = s[0]
                next_preds = preds.get(next_id, [])
                
                # Stop if next node has >1 predecessors (merge)
                if len(next_preds) > 1:
                    break
                
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
