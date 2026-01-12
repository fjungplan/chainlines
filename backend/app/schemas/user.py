from typing import Optional, List
from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr, ConfigDict
from app.db.types import GUID
from app.models.enums import UserRole

class UserBase(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserRead(UserBase):
    user_id: uuid.UUID
    role: UserRole
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserAdminRead(UserRead):
    """
    admin-only fields
    """
    email: str
    google_id: str
    is_banned: bool
    banned_reason: Optional[str] = None
    last_login_at: Optional[datetime] = None
    approved_edits_count: int

class UserUpdateAdmin(BaseModel):
    role: Optional[UserRole] = None
    is_banned: Optional[bool] = None
    banned_reason: Optional[str] = None

class UserListResponse(BaseModel):
    items: List[UserAdminRead]
    total: int
