from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class PendingEditResponse(BaseModel):
    edit_id: str
    edit_type: str
    user_email: str
    user_display_name: Optional[str]
    target_info: Dict[str, Any]  # Information about what's being edited
    changes: Dict[str, Any]
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReviewEditRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None

class ReviewEditResponse(BaseModel):
    edit_id: str
    status: str
    message: str

class ModerationStatsResponse(BaseModel):
    pending_count: int
    approved_today: int
    rejected_today: int
    pending_by_type: Dict[str, int]
