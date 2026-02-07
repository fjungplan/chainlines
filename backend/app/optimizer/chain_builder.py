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

    from app.models.enums import LineageEventType

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
    
    def get_chosen_successor(node_id: str) -> Optional[str]:
        """
        Identify the unique 'chosen' successor that continues this node's chain.
        - If 1 successor: always return it (Rule 1).
        - If multiple: return the one with LEGAL_TRANSFER if unique (Rule 2).
        """
        s_ids = succs.get(node_id, [])
        if len(s_ids) == 0:
            return None
        if len(s_ids) == 1:
            return s_ids[0]
            
        # Resolve Split: Check for unique LEGAL_TRANSFER
        legal_succs = [s_id for s_id in s_ids 
                       if link_map.get((node_id, s_id), {}).get("type") == LineageEventType.LEGAL_TRANSFER]
        
        if len(legal_succs) == 1:
            return legal_succs[0]
        return None

    def get_chosen_predecessor(node_id: str) -> Optional[str]:
        """
        Identify the unique 'chosen' predecessor that this node continues the chain from.
        - If 1 predecessor: always return it (Rule 1).
        - If multiple: return the one with LEGAL_TRANSFER if unique (Rule 2).
        """
        p_ids = preds.get(node_id, [])
        if len(p_ids) == 0:
            return None
        if len(p_ids) == 1:
            return p_ids[0]
            
        # Resolve Merge: Check for unique LEGAL_TRANSFER
        # We only count those that are also temporally primary continuations
        legal_preds = [p_id for p_id in p_ids 
                       if link_map.get((p_id, node_id), {}).get("type") == LineageEventType.LEGAL_TRANSFER
                       and is_primary_continuation(p_id, node_id)]
        
        if len(legal_preds) == 1:
            return legal_preds[0]
        return None

    def is_chain_start(node_id: str) -> bool:
        """
        Determine if a node should start a new chain.
        """
        # A node starts a chain if it has no chosen predecessor,
        # OR if its chosen predecessor has a different chosen successor (split conflict).
        p_id = get_chosen_predecessor(node_id)
        if not p_id:
            return True
            
        # Check if parent chooses US as the primary continuation
        if get_chosen_successor(p_id) != node_id:
            return True
            
        # Check for visual overlap
        parent_node = node_map.get(p_id)
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
                
                # Find the unique logical continuation
                next_id = get_chosen_successor(curr)
                if not next_id:
                    break
                
                # Symmetry check: handle merges
                # The next node MUST choose MUST choose US as its primary predecessor
                if get_chosen_predecessor(next_id) != curr:
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
