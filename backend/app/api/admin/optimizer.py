"""
Admin API for controlling the layout optimizer.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.api.dependencies import require_admin, get_db
from app.models.precomputed_layout import PrecomputedLayout
from app.optimizer.runner import run_optimization, get_optimization_status

router = APIRouter() # Prefix handled in main.py

class FamilyMetadata(BaseModel):
    family_hash: str
    node_count: int
    score: float
    optimized_at: datetime
    status: str = "valid"  # Placeholder

class OptimizeRequest(BaseModel):
    family_hashes: List[str]

class OptimizeResponse(BaseModel):
    message: str
    task_id: str  # Mock task ID

@router.get("/families", response_model=List[Dict[str, Any]])
async def get_families(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_admin)
):
    """
    Get list of all cached families and their metadata.
    """
    stmt = select(PrecomputedLayout)
    result = await db.execute(stmt)
    layouts = result.scalars().all()
    
    # Get active hashes from runner
    status_info = get_optimization_status()
    active_hashes = status_info.get("active_hashes", set())
    
    response = []
    for layout in layouts:
        node_count = 0
        link_count = 0
        family_name = "Unknown Family"
        
        # Flatten chains if they are actual chain objects (containing a 'nodes' list)
        chains = layout.layout_data.get("chains", []) if layout.layout_data else []
        all_nodes_to_check = []
        for item in chains:
            if "nodes" in item and isinstance(item["nodes"], list):
                all_nodes_to_check.extend(item["nodes"])
            else:
                all_nodes_to_check.append(item)
        
        node_count = len(all_nodes_to_check)
        
        # Pull link count from layout_data if available, fallback to fingerprint
        layout_links = layout.layout_data.get("links", []) if layout.layout_data else []
        if layout_links:
            link_count = len(layout_links)
        elif layout.data_fingerprint:
            link_count = len(layout.data_fingerprint.get("link_ids", []))
            
        # Resolve Family Name: Longest node (era span), ties go to younger (higher founding year)
        if all_nodes_to_check:
            
            current_year = 2026 # TODO: Consistent with discovery service
            best_node = None
            max_duration = -1
            
            for node in all_nodes_to_check:
                name = node.get("name")
                if not name:
                    continue
                
                # Try to get duration from eras first (most accurate for longevity)
                eras = node.get("eras", [])
                if eras:
                    duration = len(eras)
                else:
                    # Fallback to year span
                    start = node.get("founding_year") or node.get("startTime", 0)
                    end = node.get("dissolution_year") or node.get("endTime")
                    if end is None:
                        end = current_year
                    duration = end - start
                
                founding = node.get("founding_year") or node.get("startTime", 0)
                
                if duration > max_duration:
                    max_duration = duration
                    best_node = node
                elif duration == max_duration:
                    # Tie-break: Prefer node with more eras if same duration, then younger
                    if best_node:
                        best_eras_count = len(best_node.get("eras", []))
                        curr_eras_count = len(eras)
                        if curr_eras_count > best_eras_count:
                            best_node = node
                        elif curr_eras_count == best_eras_count:
                            if founding > (best_node.get("founding_year") or best_node.get("startTime", 0)):
                                best_node = node
            
            # Final fallback
            if not best_node and all_nodes_to_check:
                for node in all_nodes_to_check:
                    if node.get("name"):
                        best_node = node
                        break
            
            if best_node:
                family_name = best_node.get("name", "Unknown Node")

        # Determine Status
        is_actually_optimized = layout.optimized_at is not None and layout.score > 0
        
        # EXCLUSION THRESHOLD: Must have at least 2 nodes and 1 link to be a "family"
        if node_count < 2 or link_count < 1:
            continue

        if layout.family_hash in active_hashes:
            status = "optimizing"
        elif layout.is_stale:
            status = "stale"
        elif not is_actually_optimized:
            status = "pending"
        else:
            status = "cached"

        response.append({
            "family_hash": layout.family_hash,
            "family_name": family_name,
            "node_count": node_count,
            "link_count": link_count,
            "score": layout.score,
            "optimized_at": layout.optimized_at.isoformat() if is_actually_optimized and layout.optimized_at else None,
            "status": status
        })
    
    return response

@router.post("/optimize", status_code=202, response_model=OptimizeResponse)
async def trigger_optimization(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_admin)
):
    """
    Trigger background optimization for specific families.
    """
    if not request.family_hashes:
        raise HTTPException(status_code=400, detail="No families specified")
        
    # Run in background
    # Note: We pass db session, but FastAPI dependency session is scoped to request.
    # Ideally should create new session in background task.
    # But `run_optimization` signature takes session.
    # For now, we'll rely on the runner creating its own session or refactoring.
    # Refactoring runner to take session_maker or similar is better, but to keep it simple:
    # We will pass the function to background_tasks which will run it. 
    # BUT request-scoped DB session will close.
    # Fix: We need a wrapper that creates a session.
    
    background_tasks.add_task(run_optimization_wrapper, request.family_hashes)
    
    return OptimizeResponse(
        message="Optimization started",
        task_id="bg-task"
    )

@router.get("/status")
async def get_status(
    user = Depends(require_admin)
):
    """Get optimizer status."""
    return get_optimization_status()

@router.get("/families/{family_hash}/logs")
async def get_family_logs(
    family_hash: str,
    user = Depends(require_admin)
):
    """
    Retrieve the log file for a specific family.
    """
    from app.optimizer.runner import OPTIMIZER_LOGS_DIR
    import os
    
    log_path = os.path.join(OPTIMIZER_LOGS_DIR, f"family_{family_hash}.log")
    
    if not os.path.exists(log_path):
        # Return empty list or 404? 
        # Scraper logs usually return empty if not found or a placeholder.
        # Let's return a 404 if the file doesn't exist to be explicit.
        raise HTTPException(status_code=404, detail="Log file not found for this family")
    
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
        return lines
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {e}")


@router.post("/discover", status_code=202)
async def discover_families(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_admin)
):
    """
    Trigger background scan for all families (continuous discovery).
    """
    background_tasks.add_task(run_discovery_wrapper)
    return {"message": "Discovery scan started"}


# Helper for background task session management
async def run_discovery_wrapper():
    from app.db.database import async_session_maker
    from app.services.family_discovery import FamilyDiscoveryService
    async with async_session_maker() as session:
        # Require at least 2 nodes and 1 link for a component to be considered a 'family'
        service = FamilyDiscoveryService(session, complexity_threshold=2)
        await service.discover_all_families()


async def run_optimization_wrapper(hashes: List[str]):
    from app.db.database import async_session_maker
    async with async_session_maker() as session:
        async with session.begin():
            await run_optimization(hashes, session)
