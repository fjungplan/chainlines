import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, utc_now
from app.db.types import GUID

class PrecomputedLayout(Base):
    """Storage for optimized family layouts."""
    __tablename__ = "precomputed_layouts"
    
    id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    layout_data: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    data_fingerprint: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    is_stale: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    optimized_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<PrecomputedLayout(hash={self.family_hash[:8]}..., score={self.score:.2f}, optimized_at={self.optimized_at})>"
