from sqlalchemy import Column, String, Text, TIMESTAMP, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, utc_now
from app.db.types import GUID
from app.models.enums import EditAction, EditStatus
import uuid

class EditHistory(Base):
    __tablename__ = "edit_history"
    
    edit_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(GUID(), nullable=False)
    user_id = Column(GUID(), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    action = Column(Enum(EditAction, native_enum=False), nullable=False)
    status = Column(Enum(EditStatus, native_enum=False), default=EditStatus.PENDING, nullable=False)
    reviewed_by = Column(GUID(), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    reviewed_at = Column(TIMESTAMP, nullable=True)
    review_notes = Column(Text, nullable=True)
    # Revert tracking fields
    reverted_by = Column(GUID(), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    reverted_at = Column(TIMESTAMP, nullable=True)
    # Use JSON instead of JSONB for SQLite compatibility (Postgres will use JSONB automatically)
    snapshot_before = Column(JSON, nullable=True)
    snapshot_after = Column(JSON, nullable=False)
    source_url = Column(String(500), nullable=True)
    source_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    reverter = relationship("User", foreign_keys=[reverted_by])
