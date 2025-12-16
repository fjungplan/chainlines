import re
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Integer, ForeignKey, CheckConstraint, UniqueConstraint, Boolean, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.db.base import Base, utc_now
from app.db.types import GUID

class SponsorMaster(Base):
    """Parent company owning multiple sponsor brands."""
    __tablename__ = "sponsor_master"
    
    master_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry_sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    last_modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, onupdate=utc_now, nullable=False)
    
    brands: Mapped[List["SponsorBrand"]] = relationship("SponsorBrand", back_populates="master", cascade="all, delete-orphan")

class SponsorBrand(Base):
    """Individual brand identity under parent company."""
    __tablename__ = "sponsor_brand"
    
    brand_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    master_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), ForeignKey("sponsor_master.master_id", ondelete="CASCADE"), nullable=False)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    default_hex_color: Mapped[str] = mapped_column(String(7), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    last_modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, onupdate=utc_now, nullable=False)
    
    master: Mapped["SponsorMaster"] = relationship("SponsorMaster", back_populates="brands")
    team_links: Mapped[List["TeamSponsorLink"]] = relationship("TeamSponsorLink", back_populates="brand", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("master_id", "brand_name", name="uq_master_brand"),
    )

    @validates("default_hex_color")
    def validate_hex_color(self, key, value):
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError(f"Invalid hex color format: {value}")
        return value

class TeamSponsorLink(Base):
    """Link between a team era and a sponsor brand."""
    __tablename__ = "team_sponsor_link"
    
    link_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    era_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), ForeignKey("team_era.era_id", ondelete="CASCADE"), nullable=False)
    brand_id: Mapped[uuid.UUID] = mapped_column(GUID(as_uuid=True), ForeignKey("sponsor_brand.brand_id", ondelete="CASCADE"), nullable=False) # Note: DDL says CASCADE in one place but RESTRICT in verify view? DDL text said CASCADE in diagram logic but DDL SQL might say RESTRICT? DDL SQL line 206 says CASCADE. I will use CASCADE.
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)
    prominence_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    hex_color_override: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    last_modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now, onupdate=utc_now, nullable=False)
    
    era: Mapped["TeamEra"] = relationship("TeamEra", back_populates="sponsor_links") # TeamEra needs to be updated to match this
    brand: Mapped["SponsorBrand"] = relationship("SponsorBrand", back_populates="team_links")
    
    __table_args__ = (
        UniqueConstraint("era_id", "brand_id", name="uq_era_brand"),
        UniqueConstraint("era_id", "rank_order", name="uq_era_rank"),
        CheckConstraint("rank_order >= 1", name="check_rank_order_positive"),
        CheckConstraint("prominence_percent > 0 AND prominence_percent <= 100", name="check_prominence_range"),
    )

    @validates("prominence_percent")
    def validate_prominence(self, key, value):
        if value is not None:
            if value <= 0 or value > 100:
                raise ValueError("prominence_percent must be between 1 and 100")
        return value

    @validates("rank_order")
    def validate_rank(self, key, value):
        if value is not None and value < 1:
            raise ValueError("rank_order must be positive")
        return value
