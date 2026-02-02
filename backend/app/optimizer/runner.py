"""
Background runner for genetic optimization.
"""
import logging
import asyncio
from typing import List, Dict, Any, Set
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

logger = logging.getLogger(__name__)

from app.models.precomputed_layout import PrecomputedLayout
from app.models.team import TeamNode, TeamEra
from app.models.sponsor import TeamSponsorLink
from app.models.lineage import LineageEvent
from app.optimizer.genetic_optimizer import GeneticOptimizer
from app.optimizer.fingerprint_service import generate_family_fingerprint, compute_family_hash

import os

# Define log directory relative to backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPTIMIZER_LOGS_DIR = os.path.join(BACKEND_DIR, "logs", "optimizer")

# Global status tracking for background tasks
_optimization_status = {
    "active_tasks": 0,
    "last_run": None,
    "last_error": None
}

def append_optimizer_log(family_hash: str, results: Dict[str, Any], config: Dict[str, Any]):
    """Append a formatted optimization result to the family-specific log file."""
    os.makedirs(OPTIMIZER_LOGS_DIR, exist_ok=True)
    log_path = os.path.join(OPTIMIZER_LOGS_DIR, f"family_{family_hash}.log")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    score = results.get("score", 0.0)
    best_gen = results.get("best_generation", 0)
    total_gens = results.get("total_generations", 0)
    lane_count = results.get("lane_count", 0)
    breakdown = results.get("cost_breakdown", {})
    
    # Extract config for logging
    ga_config = config.get("GENETIC_ALGORITHM", {})
    pop = ga_config.get("POP_SIZE", "N/A")
    mut = ga_config.get("MUTATION_RATE", "N/A")
    pat = ga_config.get("PATIENCE", "N/A")
    tourney = ga_config.get("TOURNAMENT_SIZE", "N/A")
    timeout = ga_config.get("TIMEOUT_SECONDS", "N/A")
    strategies = config.get("MUTATION_STRATEGIES", {})
    strat_str = ", ".join([f"{k}: {v}" for k, v in strategies.items()])
    
    # Weights for breakdown display
    weights = config.get("WEIGHTS", {}) # Might be passed in results if we refactor more
    # If weights not in config, they are in optimizer.weights. 
    # For now assume they are available or use defaults
    
    log_entry = [
        f"[{timestamp}] OPTIMIZATION COMPLETE",
        f"- Outcome: Score {score:.2f} (Achieved at Gen {best_gen} / {total_gens})",
        f"- Configuration: Pop {pop}, Mut {mut}, Tourney {tourney}, Pat {pat}, Timeout {timeout}s",
        f"- Mutation Strategies: {strat_str}",
        f"- Layout: {len(results.get('y_indices', {}))} chains in {lane_count} lanes",
        "- Penalties:"
    ]
    
    # Format penalties breakdown
    # Mapping of breakdown keys to user-friendly names and internal units
    penalty_meta = {
        "ATTRACTION": ("Attraction", "avg dist^2"),
        "BLOCKER": ("Blocker", "count"),
        "CUT_THROUGH": ("Cut Through", "count"),
        "Y_SHAPE": ("Y-Shape", "count"),
        "OVERLAP": ("Overlap", "deficiency"),
        "SPACING": ("Lane Sharing", "spacing bonus"),
    }
    
    for key, (label, unit) in penalty_meta.items():
        data = breakdown.get(key, {"multiplier": 0, "sum": 0.0})
        
        if key == "OVERLAP":
            w_base = weights.get("OVERLAP_BASE", "N/A")
            w_factor = weights.get("OVERLAP_FACTOR", "N/A")
            weight = f"Base {w_base} / Factor {w_factor}"
        elif key == "SPACING":
            weight = weights.get("LANE_SHARING", "N/A")
        else:
            weight = weights.get(key, "N/A")
            
        m = data["multiplier"]
        s = data["sum"]
        log_entry.append(f"  * {label} (Weight {weight}): Multiplier ({unit}) {m:.2f} -> Sum {s:.2f}")

    log_entry.append("-" * 50 + "\n")
    
    try:
        with open(log_path, "a") as f:
            f.write("\n".join(log_entry))
    except Exception as e:
        logger.error(f"Failed to write optimizer log for {family_hash}: {e}")

async def run_optimization(family_hashes: List[str], db: AsyncSession):
    """
    Run optimization for specified families in background.
    """
    _optimization_status["active_tasks"] += 1
    _optimization_status["last_run"] = datetime.utcnow()
    
    try:
        optimizer = GeneticOptimizer()
        
        # Load full config for logging purposes
        from app.api.admin.optimizer_config import load_config
        full_config = load_config()
        
        # 1. Fetch layouts
        stmt = select(PrecomputedLayout).where(PrecomputedLayout.family_hash.in_(family_hashes))
        result = await db.execute(stmt)
        layouts = result.scalars().all()
        
        for layout in layouts:
            try:
                # ... (node/link fetching logic remains same) ...
                fingerprint = layout.data_fingerprint
                node_ids = fingerprint.get("node_ids", [])
                
                if not node_ids:
                    logger.warning(f"Empty node_ids for layout {layout.family_hash}")
                    continue
                
                from sqlalchemy.orm import selectinload
                # Eager load eras and their sponsor links + brands for color calculation
                nodes_stmt = select(TeamNode).where(TeamNode.node_id.in_(node_ids)).options(
                    selectinload(TeamNode.eras).selectinload(TeamEra.sponsor_links).selectinload(TeamSponsorLink.brand)
                )
                nodes_res = await db.execute(nodes_stmt)
                nodes = nodes_res.scalars().all()
                
                # ... links fetching remains same ...
                links_stmt = select(LineageEvent).where(
                    or_(
                        LineageEvent.predecessor_node_id.in_(node_ids),
                        LineageEvent.successor_node_id.in_(node_ids)
                    )
                )
                links_res = await db.execute(links_stmt)
                links = links_res.scalars().all()
                
                valid_node_ids = set(str(n.node_id) for n in nodes)
                valid_links = []
                for link in links:
                    if str(link.predecessor_node_id) in valid_node_ids and str(link.successor_node_id) in valid_node_ids:
                        valid_links.append(link)
                
                from app.optimizer.chain_builder import build_chains
                current_year = datetime.now().year
                
                nodes_data = [
                    {
                        "id": str(node.node_id), 
                        "founding_year": node.founding_year, 
                        "dissolution_year": node.dissolution_year, 
                        "name": node.legal_name,
                        "eras": [
                            {
                                "year": e.season_year,
                                "name": e.registered_name,
                                "sponsors": [
                                    {
                                        "id": str(link.brand_id),
                                        "brand": link.brand.brand_name,
                                        "color": link.hex_color_override or link.brand.default_hex_color or "#888888",
                                        "prominence": link.prominence_percent
                                    } for link in e.sponsor_links
                                ]
                            } for e in node.eras
                        ]
                    } for node in nodes
                ]
                links_data = [
                    {
                        "id": str(link.event_id), 
                        "parentId": str(link.predecessor_node_id), 
                        "childId": str(link.successor_node_id),
                        "source": str(link.predecessor_node_id),
                        "target": str(link.successor_node_id),
                        "year": link.event_year, 
                        "type": link.event_type
                    } for link in valid_links
                ]
                chains_data = build_chains(nodes_data, links_data, current_year)
                
                family_data = {"chains": chains_data, "links": links_data}
                
                # 3. Run Optimizer
                opt_result = await asyncio.to_thread(
                    optimizer.optimize, 
                    family_data, 
                    timeout_seconds=optimizer.timeout_seconds
                )
                
                # 4. Persistence & Logging
                append_optimizer_log(layout.family_hash, opt_result, full_config)
                
                # 5. Update Layout
                y_indices = opt_result["y_indices"]
                new_fingerprint = generate_family_fingerprint(family_data, links_data)
                new_hash = compute_family_hash(new_fingerprint)
                
                # Ensure backward compatibility by keeping flat keys at top level
                layout_result = {**y_indices}
                layout_result["y_indices"] = y_indices
                layout_result["chains"] = chains_data
                layout_result["links"] = links_data
                
                layout.layout_data = layout_result
                layout.data_fingerprint = new_fingerprint
                layout.family_hash = new_hash
                layout.score = opt_result["score"]
                layout.optimized_at = datetime.utcnow()
                
                db.add(layout)
                
            except Exception as e:
                logger.error(f"Error optimizing family {layout.family_hash}: {e}")
                _optimization_status["last_error"] = str(e)
        
        logger.info(f"Optimization complete. Updated {len(layouts)} families.")
        
    except Exception as e:
        logger.error(f"Optimization run failed: {e}")
        _optimization_status["last_error"] = str(e)
    finally:
        _optimization_status["active_tasks"] -= 1

def get_optimization_status():
    return _optimization_status
