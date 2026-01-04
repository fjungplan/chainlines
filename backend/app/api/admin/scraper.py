"""Scraper admin API endpoints."""
import uuid
import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from app.api.dependencies import require_admin as get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scraper", tags=["scraper"])

"""Scraper admin API endpoints."""
import uuid
import logging
import asyncio
from typing import Optional, List
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel

from app.api.dependencies import require_admin as get_current_admin_user, get_db
from app.scraper.checkpoint import CheckpointManager
from app.models.run_log import ScraperRun, ScraperRunStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scraper", tags=["scraper"])

CHECKPOINT_PATH = Path("./scraper_checkpoint.json")
LOG_DIR = Path("logs/scraper")

class ScraperStartRequest(BaseModel):
    """Request to start scraper."""
    phase: int = 1
    tier: str = "1"
    resume: bool = False
    dry_run: bool = False # Restored for Data Visibility
    start_year: int = 2025
    end_year: int = 1990

class ScraperStartResponse(BaseModel):
    """Response from starting scraper."""
    task_id: str
    message: str

class ScraperRunResponse(BaseModel):
    """Scraper run info."""
    run_id: uuid.UUID
    phase: int
    tier: Optional[str]
    status: ScraperRunStatus
    started_at: datetime
    completed_at: Optional[datetime]
    items_processed: int
    error_message: Optional[str]
    duration_seconds: Optional[float] = None
    
    class Config:
        from_attributes = True

class ScraperRunListResponse(BaseModel):
    items: List[ScraperRunResponse]
    total: int

async def run_scraper_with_logging(run_id: uuid.UUID, request: ScraperStartRequest):
    """Run scraper with file logging and DB updates."""
    # Re-import to avoid circular
    from app.db.database import async_session_maker
    
    # Setup Logger
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"run_{run_id}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Attach to 'app.scraper' logger to capture all scraper events
    scraper_logger = logging.getLogger("app.scraper")
    scraper_logger.addHandler(file_handler)
    scraper_logger.setLevel(logging.INFO)
    
    # Also log strictly local events
    local_logger = logging.getLogger("scraper_runner")
    local_logger.addHandler(file_handler)
    local_logger.setLevel(logging.INFO)

    try:
        # Update run status to RUNNING
        async with async_session_maker() as session:
             async with session.begin():
                run = await session.get(ScraperRun, run_id)
                if run:
                    run.status = ScraperRunStatus.RUNNING

        local_logger.info(f"Starting Scraper Run {run_id}")
        local_logger.info(f"Params: {request.model_dump()}")
        
        # Import CLI logic
        from app.scraper.cli import run_scraper
        
        phases_to_run = []
        if request.phase == 0:
            phases_to_run = [1, 2, 3] # TODO: Implement 2 and 3 fully
            local_logger.info("Running ALL PHASES (Sequential)")
        else:
            phases_to_run = [request.phase]
            
        for phase in phases_to_run:
            local_logger.info(f"--- Starting Phase {phase} ---")
            await run_scraper(
                phase=phase,
                tier=request.tier,
                resume=request.resume,
                dry_run=request.dry_run,
                start_year=request.start_year,
                end_year=request.end_year
            )
            local_logger.info(f"--- Phase {phase} Completed ---")
            
        # Success
        async with async_session_maker() as session:
             async with session.begin():
                run = await session.get(ScraperRun, run_id)
                if run:
                    run.status = ScraperRunStatus.COMPLETED
                    run.completed_at = datetime.utcnow()
                    
    except Exception as e:
        local_logger.error(f"Scraper Failed: {e}", exc_info=True)
        async with async_session_maker() as session:
             async with session.begin():
                run = await session.get(ScraperRun, run_id)
                if run:
                    run.status = ScraperRunStatus.FAILED
                    run.completed_at = datetime.utcnow()
                    run.error_message = str(e)
    finally:
        scraper_logger.removeHandler(file_handler)
        local_logger.removeHandler(file_handler)
        file_handler.close()


@router.get("/checkpoint")
async def get_checkpoint(current_user = Depends(get_current_admin_user)):
    """Get current checkpoint metadata."""
    manager = CheckpointManager(CHECKPOINT_PATH)
    data = manager.load()
    if not data:
        raise HTTPException(status_code=404, detail="No checkpoint found")
    return data

@router.post("/start", response_model=ScraperStartResponse, status_code=202)
async def start_scraper(
    request: ScraperStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Start the scraper as a background task."""
    
    # Create DB Record
    run_id = uuid.uuid4()
    run = ScraperRun(
        run_id=run_id,
        phase=request.phase,
        tier=request.tier,
        start_year=request.start_year,
        end_year=request.end_year,
        status=ScraperRunStatus.PENDING
    )
    db.add(run)
    await db.commit()
    
    background_tasks.add_task(
        run_scraper_with_logging,
        run_id,
        request
    )
    
    return ScraperStartResponse(
        task_id=str(run_id),
        message=f"Scraper started (Run ID: {run_id})"
    )

@router.get("/runs", response_model=ScraperRunListResponse)
async def list_scraper_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """List past scraper runs."""
    query = select(ScraperRun).order_by(desc(ScraperRun.started_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Count total
    count_query = select(func.count()).select_from(ScraperRun)
    count_res = await db.execute(count_query)
    total = count_res.scalar_one()
    
    return ScraperRunListResponse(items=items, total=total)

@router.get("/runs/{run_id}/logs")
async def get_run_logs(
    run_id: uuid.UUID,
    current_user = Depends(get_current_admin_user)
):
    """Get logs for a specific run."""
    log_file = LOG_DIR / f"run_{run_id}.log"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log not found")
        
    content = log_file.read_text(encoding="utf-8")
    return PlainTextResponse(content)
