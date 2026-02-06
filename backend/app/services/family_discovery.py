"""
Family Discovery Service.

Discovers and registers complex families for layout optimization.
Handles both initial discovery (seed) and continuous discovery (reactive).
"""
import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import TeamNode
from app.models.lineage import LineageEvent
from app.models.precomputed_layout import PrecomputedLayout
from app.optimizer.fingerprint_service import generate_family_fingerprint, compute_family_hash

logger = logging.getLogger(__name__)


class FamilyDiscoveryService:
    """
    Service for discovering and registering complex families.
    
    A "family" is any connected component of nodes.
    By default, we discover all families (threshold: 1 node).
    """
    
    def __init__(
        self,
        session: AsyncSession,
        complexity_threshold: int = 1
    ):
        """
        Initialize the discovery service.
        
        Args:
            session: Database session
            complexity_threshold: Minimum number of nodes to consider a family complex
        """
        self.session = session
        self.complexity_threshold = complexity_threshold
    
    async def find_connected_component(self, start_node_id: UUID) -> List[TeamNode]:
        """
        Find all nodes in the connected component containing the given node.
        
        Uses BFS to traverse the graph of lineage events.
        
        Args:
            start_node_id: Starting node ID
            
        Returns:
            List of all nodes in the connected component
        """
        # Fetch all nodes and links upfront for efficient traversal
        nodes_stmt = select(TeamNode)
        nodes_result = await self.session.execute(nodes_stmt)
        all_nodes = {node.node_id: node for node in nodes_result.scalars().all()}
        
        links_stmt = select(LineageEvent)
        links_result = await self.session.execute(links_stmt)
        all_links = links_result.scalars().all()
        
        # Build adjacency list (undirected graph)
        adjacency: Dict[UUID, Set[UUID]] = {}
        for link in all_links:
            pred_id = link.predecessor_node_id
            succ_id = link.successor_node_id
            
            if pred_id not in adjacency:
                adjacency[pred_id] = set()
            if succ_id not in adjacency:
                adjacency[succ_id] = set()
            
            adjacency[pred_id].add(succ_id)
            adjacency[succ_id].add(pred_id)
        
        # BFS from start node
        visited = set()
        queue = [start_node_id]
        visited.add(start_node_id)
        
        while queue:
            current_id = queue.pop(0)
            
            # Add neighbors to queue
            if current_id in adjacency:
                for neighbor_id in adjacency[current_id]:
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append(neighbor_id)
        
        # Return node objects for all visited IDs
        component = [all_nodes[node_id] for node_id in visited if node_id in all_nodes]
        return component
    
    async def assess_family(self, node_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Assess a family and register it if it meets complexity threshold.
        
        Args:
            node_id: Any node ID in the family
            
        Returns:
            Dict with family info if registered, None if below threshold
        """
        # Find the connected component
        component = await self.find_connected_component(node_id)
        
        # Check complexity threshold
        if len(component) < self.complexity_threshold:
            return None
        
        # Get all links within this component
        node_ids = {node.node_id for node in component}
        links_stmt = select(LineageEvent).where(
            LineageEvent.predecessor_node_id.in_(node_ids),
            LineageEvent.successor_node_id.in_(node_ids)
        )
        links_result = await self.session.execute(links_stmt)
        links = links_result.scalars().all()
        
        # EXCLUSION THRESHOLD: Must have at least 1 link to be a "family"
        if not links:
            logger.debug(f"Family with {len(component)} nodes has 0 links, skipping")
            return None
        
        # Prepare data for fingerprinting
        current_year = 2026  # TODO: Use datetime.now().year in production
        chains_data = []
        for node in component:
            end_time = node.dissolution_year if node.dissolution_year else current_year + 1
            chains_data.append({
                "id": str(node.node_id),
                "startTime": node.founding_year,
                "endTime": end_time,
                "founding_year": node.founding_year,
                "dissolution_year": node.dissolution_year,
                "name": node.legal_name
            })
        
        links_data = []
        for link in links:
            links_data.append({
                "id": str(link.event_id),
                "parentId": str(link.predecessor_node_id),
                "childId": str(link.successor_node_id),
                "time": link.event_year
            })
        
        family_data = {
            "chains": chains_data,
            "links": links_data
        }
        
        # Generate fingerprint and hash
        fingerprint = generate_family_fingerprint(family_data, links_data)
        family_hash = compute_family_hash(fingerprint)
        
        # Check if already registered
        existing_stmt = select(PrecomputedLayout).where(
            PrecomputedLayout.family_hash == family_hash
        )
        existing = (await self.session.execute(existing_stmt)).scalar_one_or_none()
        
        if existing:
            logger.debug(f"Family {family_hash[:8]}... already registered")
            return {
                "family_hash": family_hash,
                "node_count": len(component),
                "link_count": len(links),
                "status": "existing"
            }
        
        # Create new PrecomputedLayout record
        layout = PrecomputedLayout(
            family_hash=family_hash,
            layout_data=family_data,
            data_fingerprint=fingerprint,
            score=0.0  # Placeholder score until optimization runs
        )
        
        self.session.add(layout)
        await self.session.flush()
        
        logger.info(
            f"Registered new complex family: {family_hash[:8]}... "
            f"({len(component)} nodes, {len(links)} links)"
        )
        
        return {
            "family_hash": family_hash,
            "node_count": len(component),
            "link_count": len(links),
            "status": "registered"
        }
    
    async def discover_all_families(self) -> List[Dict[str, Any]]:
        """
        Discover all complex families in the database.
        
        This is the "initial discovery" operation that scans the entire graph
        and registers all families that meet the complexity threshold.
        
        Returns:
            List of registered family info dicts
        """
        # 1. PRE-FETCH DATA ONCE
        logger.info("Pre-fetching all nodes and links for discovery...")
        nodes_stmt = select(TeamNode)
        nodes_result = await self.session.execute(nodes_stmt)
        all_nodes = {node.node_id: node for node in nodes_result.scalars().all()}
        
        links_stmt = select(LineageEvent)
        links_result = await self.session.execute(links_stmt)
        all_links = links_result.scalars().all()
        
        if not all_nodes:
            logger.info("No nodes found in database")
            return []
            
        # Build adjacency list (undirected graph) once
        adjacency: Dict[UUID, Set[UUID]] = {}
        for link in all_links:
            pred_id = link.predecessor_node_id
            succ_id = link.successor_node_id
            if pred_id not in adjacency: adjacency[pred_id] = set()
            if succ_id not in adjacency: adjacency[succ_id] = set()
            adjacency[pred_id].add(succ_id)
            adjacency[succ_id].add(pred_id)
        
        # Track which nodes we've already processed
        processed_nodes: Set[UUID] = set()
        registered_families: List[Dict[str, Any]] = []
        
        logger.info(f"Scanning {len(all_nodes)} nodes for families...")
        
        for node_id, node in all_nodes.items():
            if node_id in processed_nodes:
                continue
            
            # 2. BFS IN MEMORY
            visited = set()
            queue = [node_id]
            visited.add(node_id)
            while queue:
                curr_id = queue.pop(0)
                if curr_id in adjacency:
                    for neighbor_id in adjacency[curr_id]:
                        if neighbor_id not in visited:
                            visited.add(neighbor_id)
                            queue.append(neighbor_id)
            
            component_nodes = [all_nodes[vid] for vid in visited if vid in all_nodes]
            
            # Mark all as processed
            processed_nodes.update(visited)
            
            # 3. ASSESS COMPLEXITY
            if len(component_nodes) < self.complexity_threshold:
                continue
            
            # 4. REGISTER FAMILY
            # Get links for this component
            comp_node_ids = set(visited)
            comp_links = [l for l in all_links if l.predecessor_node_id in comp_node_ids and l.successor_node_id in comp_node_ids]
            
            # EXCLUSION THRESHOLD: Must have at least 1 link to be a "family"
            if not comp_links:
                continue
            
            # Fingerprint
            current_year = 2026
            chains_data = []
            for n in component_nodes:
                end_time = n.dissolution_year if n.dissolution_year else current_year + 1
                chains_data.append({
                    "id": str(n.node_id),
                    "startTime": n.founding_year,
                    "endTime": end_time,
                    "founding_year": n.founding_year,
                    "dissolution_year": n.dissolution_year,
                    "name": n.legal_name
                })
            
            links_data = [{
                "id": str(l.event_id),
                "parentId": str(l.predecessor_node_id),
                "childId": str(l.successor_node_id),
                "time": l.event_year
            } for l in comp_links]
            
            family_data = {"chains": chains_data, "links": links_data}
            fingerprint = generate_family_fingerprint(family_data, links_data)
            family_hash = compute_family_hash(fingerprint)
            
            # Check DB
            existing_stmt = select(PrecomputedLayout).where(PrecomputedLayout.family_hash == family_hash)
            existing = (await self.session.execute(existing_stmt)).scalar_one_or_none()
            
            # PRUNE SUPERSEDED LAYOUTS:
            # If any node in this NEW component already exists in an OLD layout, 
            # delete the old layout as it's now stale/incorrect.
            await self._prune_superseded_layouts(comp_node_ids, family_hash)

            if not existing:
                layout = PrecomputedLayout(
                    family_hash=family_hash,
                    layout_data=family_data, # Use node IDs for initial greedy
                    data_fingerprint=fingerprint,
                    score=0.0
                )
                self.session.add(layout)
                registered_families.append({
                    "family_hash": family_hash,
                    "node_count": len(component_nodes),
                    "link_count": len(comp_links),
                    "status": "registered"
                })
        
        await self.session.commit()
        logger.info(f"Discovery complete: {len(registered_families)} complex families registered.")
        return registered_families

    async def _prune_superseded_layouts(self, node_ids: Set[UUID], current_hash: str):
        """
        Delete any PrecomputedLayout records that contain any of the given node_ids
        but have a different family_hash.
        """
        from sqlalchemy import String
        
        # We search for node IDs in the JSONB fingerprint
        # Using a collection of OR clauses for each node ID is most robust
        # though potentially slow for massive families.
        filters = []
        for node_id in node_ids:
            node_id_str = str(node_id)
            filters.append(PrecomputedLayout.data_fingerprint.cast(String).like(f'%{node_id_str}%'))
        
        if not filters:
            return

        # Find any layout that mentions these nodes but isn't the current one
        stmt = (
            delete(PrecomputedLayout)
            .where(PrecomputedLayout.family_hash != current_hash)
            .where(or_(*filters))
        )
        
        result = await self.session.execute(stmt)
        if result.rowcount > 0:
            logger.info(f"Pruned {result.rowcount} superseded layout(s) overlapping with current component.")
