import uuid
from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, CheckConstraint, UniqueConstraint, Boolean, Text, TIMESTAMP, Date, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.db.base import Base, utc_now
from app.db.types import GUID

if TYPE_CHECKING:
    from app.models.sponsor import TeamSponsorLink
    from app.models.lineage import LineageEvent

class TeamNode(Base):
    """Persistent team entity (Paying Agent)."""
    __tablename__ = "team_node"
    
    node_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    founding_year: Mapped[int] = mapped_column(Integer, nullable=False)
    dissolution_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owned_by_sponsor_master_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("sponsor_master.master_id", ondelete="SET NULL"), nullable=True)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latest_team_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latest_uci_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    current_tier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # is_active is COMPUTED/GENERATED in DB. We can map it as read-only or just ignore it for writes.
    # SQLAlchemy support for generated columns is improved in 1.3/1.4 but often cleanest to valid as property or explicit column if DB manages it.
    # DDL: generated always as (dissolution_year IS NULL) stored.
    # We will map it but treat as server_default? Or just use a property for logic level.
    # Mapping it allows reading existing value.
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true") 
    
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    last_modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, onupdate=utc_now, nullable=False)
    
    external_ids: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="External source IDs: {wikidata: Q123, ...}")

    # Relationships
    eras: Mapped[List["TeamEra"]] = relationship("TeamEra", back_populates="node", cascade="all, delete-orphan")
    
    # Lineage relationships (using string class names to avoid circular imports during definition)
    outgoing_events: Mapped[List["LineageEvent"]] = relationship(
        "LineageEvent",
        foreign_keys="LineageEvent.predecessor_node_id",
        back_populates="predecessor_node",
        cascade="all, delete-orphan"
    )
    incoming_events: Mapped[List["LineageEvent"]] = relationship(
        "LineageEvent",
        foreign_keys="LineageEvent.successor_node_id",
        back_populates="successor_node",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("current_tier IN (1, 2, 3)", name="check_current_tier"),
    )

    @validates("founding_year")
    def validate_founding_year(self, key, value):
        if value < 1900:
            raise ValueError("founding_year must be >= 1900")
        return value

    def get_predecessors(self) -> List["TeamNode"]:
        """Return list of immediate predecessor nodes via incoming events."""
        return [event.predecessor_node for event in self.incoming_events if event.predecessor_node]

    def get_successors(self) -> List["TeamNode"]:
        """Return list of immediate successor nodes via outgoing events."""
        return [event.successor_node for event in self.outgoing_events if event.successor_node]

class TeamEra(Base):
    """Season-specific team configuration snapshot."""
    __tablename__ = "team_era"
    
    era_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), ForeignKey("team_node.node_id", ondelete="CASCADE"), nullable=False)
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False) # DDL default CURRENT_DATE handled by default arg in pydantic or DB? DB has default.
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    registered_name: Mapped[str] = mapped_column(String(255), nullable=False)
    uci_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    is_name_auto_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_auto_filled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tier_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_license: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_origin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    last_modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, onupdate=utc_now, nullable=False)
    
    wikipedia_history_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Cached Wikipedia History section text")

    node: Mapped["TeamNode"] = relationship("TeamNode", back_populates="eras")
    sponsor_links: Mapped[List["TeamSponsorLink"]] = relationship("TeamSponsorLink", back_populates="era", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("node_id", "season_year", "valid_from", name="uq_node_year_period"),
        CheckConstraint("tier_level IN (1, 2, 3)", name="check_tier_level"),
    )

    @validates("registered_name")
    def validate_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("registered_name cannot be empty")
        return value

    @validates("country_code")
    def validate_country_code(self, key, value):
        if value is not None:
            if len(value) != 3 or not value.isalpha() or not value.isupper():
                raise ValueError("country_code must be 3 uppercase letters (ISO alpha-3)")
        return value

    @validates("uci_code")
    def validate_uci_code(self, key, value):
        if value is not None:
            if len(value) != 3 or not value.isalpha() or not value.isupper():
                raise ValueError("uci_code must be 3 uppercase letters")
        return value

    @validates("tier_level")
    def validate_tier_level(self, key, value):
        if value is not None and value not in (1, 2, 3):
            raise ValueError("tier_level must be 1, 2, or 3")
        return value

    @property
    def display_name(self) -> str:
        if self.uci_code:
            return f"{self.registered_name} ({self.uci_code})"
        return self.registered_name

    @property
    def sponsors_ordered(self) -> List["TeamSponsorLink"]:
        return sorted(self.sponsor_links, key=lambda x: x.rank_order)

    def validate_sponsor_total(self) -> bool:
        total = sum(link.prominence_percent for link in self.sponsor_links)
        return total <= 100
