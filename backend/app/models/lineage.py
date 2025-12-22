from typing import Optional
import uuid
from datetime import datetime, date

from sqlalchemy import Column, ForeignKey, Integer, Text, Enum, CheckConstraint, DateTime, Date, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, utc_now
from app.db.types import GUID
from app.models.team import TeamNode
from app.models.enums import LineageEventType
# Ensure User is registered for relationship resolution
from app.models.user import User

class LineageEvent(Base):
    __tablename__ = "lineage_event"

    event_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    predecessor_node_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), ForeignKey("team_node.node_id", ondelete="CASCADE"), nullable=False)
    successor_node_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), ForeignKey("team_node.node_id", ondelete="CASCADE"), nullable=False)
    event_year: Mapped[int] = mapped_column(Integer, nullable=False)
    event_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    event_type: Mapped[LineageEventType] = mapped_column(Enum(LineageEventType, name="event_type_enum", native_enum=False), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    last_modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    predecessor_node: Mapped["TeamNode"] = relationship("TeamNode", foreign_keys=[predecessor_node_id], back_populates="outgoing_events")
    successor_node: Mapped["TeamNode"] = relationship("TeamNode", foreign_keys=[successor_node_id], back_populates="incoming_events")
    
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    last_modified_by_user: Mapped["User"] = relationship("User", foreign_keys=[last_modified_by])

    __table_args__ = (
        CheckConstraint('predecessor_node_id != successor_node_id', name='check_not_circular'),
        CheckConstraint('event_year >= 1900 AND event_year <= 2100', name='check_event_year'),
    )

    def is_merge(self):
        return self.event_type == LineageEventType.MERGE

    def is_split(self):
        return self.event_type == LineageEventType.SPLIT

    def is_spiritual(self):
        return self.event_type == LineageEventType.SPIRITUAL_SUCCESSION
