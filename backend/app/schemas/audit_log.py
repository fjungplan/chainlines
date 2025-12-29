"""
Pydantic schemas for the Audit Log feature.

These schemas define the API request/response models for the audit log endpoints,
which provide both moderation queue and audit history functionality.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, date


class UserSummary(BaseModel):
    """Minimal user information for display in audit log entries."""
    user_id: str
    display_name: Optional[str]
    email: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogEntryResponse(BaseModel):
    """
    Summary of an edit for the audit log list view.
    
    Contains all columns needed for the grid display, with human-readable
    entity names (not UUIDs).
    """
    edit_id: str
    status: str  # PENDING, APPROVED, REJECTED, REVERTED
    entity_type: str  # TEAM, ERA, SPONSOR, BRAND, SPONSOR_LINK, LINEAGE
    entity_name: str  # Human-readable name (resolved from UUID)
    action: str  # CREATE, UPDATE, DELETE
    submitted_by: UserSummary
    submitted_at: datetime
    reviewed_by: Optional[UserSummary] = None
    reviewed_at: Optional[datetime] = None
    summary: str  # Reason → Internal Note → Rejection notes (priority)

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: List[AuditLogEntryResponse]
    total: int



class AuditLogDetailResponse(BaseModel):
    """
    Full details of an edit for the detail/diff view.
    
    Includes before/after snapshots with human-readable names and
    permission flags indicating what actions the current user can take.
    """
    edit_id: str
    status: str
    entity_type: str
    entity_name: str
    action: str
    submitted_by: UserSummary
    submitted_at: datetime
    reviewed_by: Optional[UserSummary] = None
    reviewed_at: Optional[datetime] = None
    summary: str
    # Detailed snapshots with human-readable names
    snapshot_before: Optional[Dict[str, Any]] = None
    snapshot_after: Dict[str, Any]
    source_url: Optional[str] = None
    source_notes: Optional[str] = None
    review_notes: Optional[str] = None
    # Permission flags for current user
    can_approve: bool
    can_reject: bool
    can_revert: bool  # Only if most recent approved and user has permission
    can_reapply: bool  # Only if reverted/rejected and chronologically valid

    model_config = ConfigDict(from_attributes=True)


class AuditLogFilters(BaseModel):
    """Query parameters for filtering the audit log list."""
    status: Optional[List[str]] = None  # Default handled in endpoint
    entity_type: Optional[str] = None
    user_id: Optional[str] = None  # Filter by submitter
    entity_id: Optional[str] = None  # Filter by specific entity
    entity_search: Optional[str] = None  # Search by entity name
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class ReviewEditRequest(BaseModel):
    """Request body for approving or rejecting an edit."""
    approved: bool
    notes: Optional[str] = None


class ReviewEditResponse(BaseModel):
    """Response after reviewing an edit."""
    edit_id: str
    status: str
    message: str


class RevertRequest(BaseModel):
    """Request body for reverting an approved edit."""
    notes: Optional[str] = None


class ReapplyRequest(BaseModel):
    """Request body for re-applying a reverted or rejected edit."""
    notes: Optional[str] = None


class AuditLogStatsResponse(BaseModel):
    """Statistics for the audit log dashboard."""
    pending_count: int
    approved_today: int
    rejected_today: int
    reverted_today: int
    pending_by_type: Dict[str, int]
