"""Scraper status monitoring."""
import asyncio
import logging
import uuid
from sqlalchemy import select
from app.db.database import async_session_maker
from app.models.run_log import ScraperRun, ScraperRunStatus

logger = logging.getLogger(__name__)

class ScraperAbortedError(Exception):
    """Raised when scraper is aborted by user."""
    pass

class ScraperStatusMonitor:
    """Monitors scraper status and handles interruptions."""
    
    def __init__(self, run_id: uuid.UUID):
        self.run_id = run_id
        
    async def check_status(self):
        """Check current status. 
        
        If PAUSED, waits until resumed.
        If ABORTED, raises ScraperAbortedError.
        """
        while True:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(ScraperRun.status).where(ScraperRun.run_id == self.run_id)
                )
                status = result.scalar_one_or_none()
                
            if status == ScraperRunStatus.ABORTED:
                raise ScraperAbortedError("Scraper aborted by user request")
                
            if status == ScraperRunStatus.PAUSED:
                logger.info("Scraper PAUSED. Waiting for resume signal...")
                await asyncio.sleep(2) # Poll frequent when paused
                continue
                
            # If RUNNING or PENDING, proceed
            break
