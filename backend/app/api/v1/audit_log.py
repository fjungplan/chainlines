"""
Audit Log API endpoints.

Provides endpoints for viewing and managing edit history.
Accessible to Moderators and Admins only.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.api.dependencies import require_moderator
from app.models.user import User
from app.models.edit import EditHistory
from app.models.enums import EditStatus
from app.schemas.audit_log import AuditLogEntryResponse, UserSummary
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/api/v1/audit-log", tags=["audit-log"])


@router.get("", response_model=List[AuditLogEntryResponse])
async def list_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[List[str]] = Query(None, description="Filter by status(es)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    user_id: Optional[str] = Query(None, description="Filter by submitter user ID"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    """
    Get list of edits for the audit log.
    
    Defaults to showing only PENDING edits if no status filter is provided.
    Results are sorted by created_at descending (newest first).
    """
    # Build query
    stmt = select(EditHistory)
    
    # Status filter - default to PENDING only if not specified
    if status:
        status_values = [EditStatus(s) for s in status]
        stmt = stmt.where(EditHistory.status.in_(status_values))
    else:
        stmt = stmt.where(EditHistory.status == EditStatus.PENDING)
    
    # Entity type filter
    if entity_type:
        stmt = stmt.where(EditHistory.entity_type == entity_type)
    
    # User filter
    if user_id:
        stmt = stmt.where(EditHistory.user_id == user_id)
    
    # Sort: newest first
    stmt = stmt.order_by(EditHistory.created_at.desc()).offset(skip).limit(limit)
    
    result = await session.execute(stmt)
    edits = result.scalars().all()
    
    # Format each edit with resolved entity names
    entries = []
    for edit in edits:
        # Get submitter info
        submitter = await session.get(User, edit.user_id)
        submitter_summary = UserSummary(
            user_id=str(submitter.user_id) if submitter else "unknown",
            display_name=submitter.display_name if submitter else "Unknown",
            email=submitter.email if submitter else "unknown@example.com"
        )
        
        # Get reviewer info if applicable
        reviewer_summary = None
        if edit.reviewed_by:
            reviewer = await session.get(User, edit.reviewed_by)
            if reviewer:
                reviewer_summary = UserSummary(
                    user_id=str(reviewer.user_id),
                    display_name=reviewer.display_name,
                    email=reviewer.email
                )
        
        # Resolve entity name
        entity_name = await AuditLogService.resolve_entity_name(
            session, edit.entity_type, edit.entity_id
        )
        
        entries.append(AuditLogEntryResponse(
            edit_id=str(edit.edit_id),
            entity_type=edit.entity_type,
            entity_name=entity_name,
            action=edit.action.value if edit.action else "UPDATE",
            status=edit.status.value,
            submitted_by=submitter_summary,
            submitted_at=edit.created_at,
            reviewed_by=reviewer_summary,
            reviewed_at=edit.reviewed_at,
            summary=_generate_edit_summary(edit)
        ))
    
    return entries


@router.get("/pending-count")
async def get_pending_count(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    """
    Get the count of pending edits.
    
    Used for the notification badge in the UI.
    """
    stmt = select(func.count(EditHistory.edit_id)).where(
        EditHistory.status == EditStatus.PENDING
    )
    result = await session.execute(stmt)
    count = result.scalar()
    
    return {"count": count or 0}


def _generate_edit_summary(edit: EditHistory) -> str:
    """Generate a human-readable summary of the edit."""
    action = edit.action.value if edit.action else "modified"
    
    if edit.snapshot_after:
        # Get the first key as a hint of what changed
        changed_keys = list(edit.snapshot_after.keys())
        if changed_keys:
            key_hint = changed_keys[0]
            if len(changed_keys) > 1:
                return f"Changed {key_hint} and {len(changed_keys) - 1} other field(s)"
            return f"Changed {key_hint}"
    
    return f"{action} entity"
