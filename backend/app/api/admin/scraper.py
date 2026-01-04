"""Scraper admin API endpoints."""
import uuid
import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from app.api.dependencies import require_admin as get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scraper", tags=["scraper"])

class ScraperStartRequest(BaseModel):
    """Request to start scraper."""
    phase: int = 1
    tier: str = "1"
    resume: bool = False
    dry_run: bool = False

class ScraperStartResponse(BaseModel):
    """Response from starting scraper."""
    task_id: str
    message: str

# In-memory task tracking (use Redis in production)
_tasks: dict = {}

async def run_scraper_background(task_id: str, request: ScraperStartRequest):
    """Background task to run scraper."""
    from app.scraper.cli import run_scraper
    
    _tasks[task_id] = {"status": "running", "phase": request.phase}
    
    try:
        await run_scraper(
            phase=request.phase,
            tier=request.tier,
            resume=request.resume,
            dry_run=request.dry_run
        )
        _tasks[task_id]["status"] = "completed"
    except Exception as e:
        logger.error(f"Scraper task {task_id} failed: {e}")
        _tasks[task_id] = {"status": "failed", "error": str(e)}


@router.post("/start", response_model=ScraperStartResponse, status_code=202)
async def start_scraper(
    request: ScraperStartRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_admin_user)
):
    """Start the scraper as a background task."""
    task_id = str(uuid.uuid4())
    
    background_tasks.add_task(
        run_scraper_background,
        task_id,
        request
    )
    
    return ScraperStartResponse(
        task_id=task_id,
        message=f"Scraper Phase {request.phase} started"
    )


@router.get("/status/{task_id}")
async def get_scraper_status(
    task_id: str,
    current_user = Depends(get_current_admin_user)
):
    """Get status of a scraper task."""
    if task_id not in _tasks:
        return {"status": "not_found"}
    return _tasks[task_id]
