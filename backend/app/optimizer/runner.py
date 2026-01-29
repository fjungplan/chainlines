"""
Background runner for genetic optimization.
"""
import logging
import asyncio
from typing import List, Dict, Any, Set
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.precomputed_layout import PrecomputedLayout
from app.models.team import TeamNode
from app.models.lineage import LineageEvent
from app.optimizer.genetic_optimizer import GeneticOptimizer
from app.optimizer.fingerprint_service import generate_family_fingerprint, compute_family_hash

logger = logging.getLogger(__name__)

# Global status tracking (simple in-memory for now)
_optimization_status = {
    "active_tasks": 0,
    "last_run": None,
    "last_error": None
}

async def run_optimization(family_hashes: List[str], db: AsyncSession):
    """
    Run optimization for specified families in background.
    
    1. Fetch existing layouts to identify nodes.
    2. Re-fetch current data for those nodes.
    3. Run genetic optimizer.
    4. Save updated layout and fingerprint.
    """
    _optimization_status["active_tasks"] += 1
    _optimization_status["last_run"] = datetime.utcnow()
    
    try:
        optimizer = GeneticOptimizer()
        
        # 1. Fetch layouts
        stmt = select(PrecomputedLayout).where(PrecomputedLayout.family_hash.in_(family_hashes))
        result = await db.execute(stmt)
        layouts = result.scalars().all()
        
        for layout in layouts:
            try:
                # Get node IDs from fingerprint
                fingerprint = layout.data_fingerprint
                node_ids = fingerprint.get("node_ids", [])
                
                if not node_ids:
                    logger.warning(f"Empty node_ids for layout {layout.family_hash}")
                    continue
                
                # 2. Fetch fresh data
                nodes_stmt = select(TeamNode).where(TeamNode.node_id.in_(node_ids))
                nodes_res = await db.execute(nodes_stmt)
                nodes = nodes_res.scalars().all()
                
                # Fetch links between these nodes
                # We assume CLOSED world (only optimizing existing set)
                # In full implementation, we'd check for new external connections
                links_stmt = select(LineageEvent).where(
                    or_(
                        LineageEvent.predecessor_node_id.in_(node_ids),
                        LineageEvent.successor_node_id.in_(node_ids)
                    )
                )
                links_res = await db.execute(links_stmt)
                links = links_res.scalars().all()
                
                # Filter links to only those where both ends are in our set
                # (or should we include all? If we include external links, we miss the external nodes)
                # For safety, keep closed world:
                valid_node_ids = set(str(n.node_id) for n in nodes)
                valid_links = []
                for link in links:
                    p_id = str(link.predecessor_node_id)
                    s_id = str(link.successor_node_id)
                    if p_id in valid_node_ids and s_id in valid_node_ids:
                        valid_links.append(link)
                
                # 3. Prepare data for optimizer
                current_year = datetime.now().year
                
                chains_data = []
                for node in nodes:
                    end_time = node.dissolution_year if node.dissolution_year else current_year + 1
                    chains_data.append({
                        "id": str(node.node_id),
                        "startTime": node.founding_year,
                        "endTime": end_time,
                        "founding_year": node.founding_year, # Kept for fingerprint
                        "dissolution_year": node.dissolution_year, # Kept for fingerprint
                        # Preserve existing name for UI
                        "name": node.legal_name 
                    })
                    
                links_data = []
                for link in valid_links:
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
                
                # 4. Run Optimizer
                opt_result = optimizer.optimize(family_data, timeout_seconds=600)
                
                # 5. Update Layout
                # Store only the Y-index mapping (chainId -> yIndex)
                # Frontend expects: { "chain-id-1": 0, "chain-id-2": 1, ... }
                y_indices = opt_result["y_indices"]
                
                # Generate new fingerprint (might have changed if dates changed)
                new_fingerprint = generate_family_fingerprint(family_data, links_data)
                new_hash = compute_family_hash(new_fingerprint)
                
                layout.layout_data = y_indices  # Store ONLY the y-index mapping
                layout.data_fingerprint = new_fingerprint
                layout.family_hash = new_hash
                layout.score = opt_result["score"]
                layout.optimized_at = datetime.utcnow()
                
                db.add(layout)
                
            except Exception as e:
                logger.error(f"Error optimizing family {layout.family_hash}: {e}")
                _optimization_status["last_error"] = str(e)
        
        # Don't commit here - the wrapper's session.begin() context manager handles it
        logger.info(f"Optimization complete. Updated {len(layouts)} families.")
        
    except Exception as e:
        logger.error(f"Optimization run failed: {e}")
        _optimization_status["last_error"] = str(e)
    finally:
        _optimization_status["active_tasks"] -= 1

def get_optimization_status():
    return _optimization_status
