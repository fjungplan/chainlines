"""
Base database models and mixins for SQLAlchemy.
"""
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Get current UTC time (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    def __repr__(self) -> str:
        """Generate a helpful string representation for debugging."""
        columns = ", ".join(
            [f"{k}={repr(v)}" for k, v in self.__dict__.items() if not k.startswith("_")]
        )
        return f"<{self.__class__.__name__}({columns})>"


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamp columns."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=utc_now, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=utc_now, 
        onupdate=utc_now, 
        nullable=False
    )
