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
    
    response = []
    for layout in layouts:
        chain_count = 0
        link_count = 0
        founding_year_min = None
        
        # Simple extraction from JSON
        if layout.layout_data:
            chains = layout.layout_data.get("chains", [])
            chain_count = len(chains)
            link_count = len(layout.layout_data.get("links", []))
            
            # Find oldest year for display/sorting (optional)
            # founding_year_min = min(c.get("startTime", 9999) for c in chains) if chains else None

        response.append({
            "family_hash": layout.family_hash,
            "node_count": chain_count, # Approx proxy
            "link_count": link_count,
            "score": layout.score,
            "optimized_at": layout.optimized_at,
            "status": "cached" # TODO: Integrate with invalidation status
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


# Helper for background task session management
async def run_optimization_wrapper(hashes: List[str]):
    from app.db.database import async_session_maker
    async with async_session_maker() as session:
        async with session.begin():
            await run_optimization(hashes, session)
