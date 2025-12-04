from sqlalchemy import Column, ForeignKey, Integer, Text, Enum, CheckConstraint, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base, utc_now
from app.db.types import GUID
from app.models.enums import EventType
import uuid

class LineageEvent(Base):
    __tablename__ = "lineage_event"

    event_id = Column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    previous_node_id = Column(GUID(as_uuid=True), ForeignKey("team_node.node_id", ondelete="SET NULL"), nullable=True)
    next_node_id = Column(GUID(as_uuid=True), ForeignKey("team_node.node_id", ondelete="SET NULL"), nullable=True)
    event_year = Column(Integer, nullable=False)
    event_type = Column(Enum(EventType, name="event_type_enum"), nullable=False)
    notes = Column(Text, nullable=True)
    # Use application-level UTC timestamps for cross-dialect compatibility (SQLite/Postgres)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    previous_node = relationship("TeamNode", foreign_keys=[previous_node_id], back_populates="outgoing_events")
    next_node = relationship("TeamNode", foreign_keys=[next_node_id], back_populates="incoming_events")

    __table_args__ = (
        CheckConstraint('(previous_node_id IS NOT NULL OR next_node_id IS NOT NULL)', name='ck_lineage_event_node_not_null'),
        CheckConstraint('event_year >= 1900', name='ck_lineage_event_year_min'),
    )

    def is_merge(self):
        return self.event_type == EventType.MERGE

    def is_split(self):
        return self.event_type == EventType.SPLIT

    def is_spiritual(self):
        return self.event_type == EventType.SPIRITUAL_SUCCESSION

    def validate(self):
        # At least one node must be set (enforced by DB)
        if not self.previous_node_id and not self.next_node_id:
            raise ValueError("At least one of previous_node_id or next_node_id must be set.")
        # event_year must be within the range of connected nodes
        if self.previous_node and self.previous_node.founding_year:
            if self.event_year < self.previous_node.founding_year:
                raise ValueError("event_year cannot be before previous node's founding_year.")
        if self.next_node and self.next_node.dissolution_year:
            if self.event_year > self.next_node.dissolution_year:
                raise ValueError("event_year cannot be after next node's dissolution_year.")

    def __repr__(self):
        return f"<LineageEvent {self.event_id} {self.event_type} {self.event_year}>"
