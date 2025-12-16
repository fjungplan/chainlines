from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base, utc_now
from app.db.types import GUID
from app.models.enums import UserRole
import uuid

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    google_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255))
    avatar_url = Column(String(500))
    role = Column(Enum(UserRole, native_enum=False), default=UserRole.EDITOR, nullable=False)
    approved_edits_count = Column(Integer, default=0, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    banned_reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    last_login_at = Column(TIMESTAMP, nullable=True)

    # Relationships aren't strictly DDL but useful for ORM navigation.
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_moderator(self) -> bool:
        return self.role == UserRole.MODERATOR

    def is_trusted(self) -> bool:
        return self.role == UserRole.TRUSTED_EDITOR

    def can_edit(self) -> bool:
        """Check if user can create/edit content (and is not banned)."""
        if self.is_banned:
            return False
        return self.role in (UserRole.EDITOR, UserRole.TRUSTED_EDITOR, UserRole.MODERATOR, UserRole.ADMIN)
