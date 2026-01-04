from datetime import datetime
import uuid
import enum
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, utc_now
from app.db.types import GUID

class ScraperRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ScraperRun(Base):
    """Log of a scraper execution."""
    __tablename__ = "scraper_runs"

    run_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phase: Mapped[int] = mapped_column(Integer, nullable=False) # 0 for All Phases
    tier: Mapped[str] = mapped_column(String, nullable=True) # "1", "2", "3", "all", or None
    start_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    status: Mapped[ScraperRunStatus] = mapped_column(
        Enum(ScraperRunStatus), 
        default=ScraperRunStatus.PENDING,
        nullable=False
    )
    
    items_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
