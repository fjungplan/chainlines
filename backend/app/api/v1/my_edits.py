"""
My Edits API endpoints.

Provides endpoints for users to view their own edit history.
Accessible to any authenticated user, but filtered to their own submissions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, cast, String
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.edit import EditHistory
from app.models.enums import EditStatus
from app.schemas.audit_log import (
    AuditLogEntryResponse, 
    AuditLogDetailResponse, 
    AuditLogListResponse,
    UserSummary
)
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/api/v1/my-edits", tags=["my-edits"])


def _generate_edit_summary(edit: EditHistory) -> str:
    """Generate a human-readable summary of the edit."""
    action = edit.action.value if edit.action else "UPDATE"
    entity_type = edit.entity_type or "entity"
    
    snap = edit.snapshot_after or {}
    # Try to extract a meaningful identifier from the snapshot
    name = (
        snap.get("registered_name") or
        snap.get("legal_name") or
        snap.get("brand_name") or
        snap.get("display_name") or
        ""
    )
    
    if name:
        return f"{action} {entity_type}: {name}"
    return f"{action} {entity_type}"


@router.get("", response_model=AuditLogListResponse)
async def list_my_edits(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search term (entity, summary, notes)"),
    status: Optional[List[str]] = Query(None, description="Filter by status(es)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO 8601)"),
    sort_by: str = Query("created_at", description="Field to sort by", pattern="^(created_at|status|action|entity_type)$"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of edits submitted by the current user.
    
    Supports filtering by status, entity type, date range, and search.
    """
    # Build query - always filter by current user
    stmt = select(EditHistory).where(EditHistory.user_id == current_user.user_id)
    
    # Search functionality
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                EditHistory.source_notes.ilike(search_term),
                EditHistory.review_notes.ilike(search_term),
                cast(EditHistory.snapshot_after, String).ilike(search_term)
            )
        )
    
    # Status filter
    if status is not None and len(status) > 0:
        status_values = [EditStatus(s) for s in status]
        stmt = stmt.where(EditHistory.status.in_(status_values))
    
    # Entity type filter
    if entity_type:
        normalized_input = entity_type.replace("_", "").lower()
        stmt = stmt.where(
            func.replace(func.lower(EditHistory.entity_type), "_", "") == normalized_input
        )
    
    # Date range filter
    if start_date:
        if start_date.tzinfo:
            start_date = start_date.replace(tzinfo=None)
        stmt = stmt.where(EditHistory.created_at >= start_date)
    if end_date:
        if end_date.tzinfo:
            end_date = end_date.replace(tzinfo=None)
        stmt = stmt.where(EditHistory.created_at <= end_date)
    
    # Count query
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # Apply ordering
    sort_column = getattr(EditHistory, sort_by, EditHistory.created_at)
    if sort_order == "asc":
        stmt = stmt.order_by(sort_column.asc())
    else:
        stmt = stmt.order_by(sort_column.desc())
    
    # Pagination
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    edits = result.scalars().all()
    
    # Build response items
    items = []
    for edit in edits:
        # Get submitter info (should be current user, but fetch for consistency)
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
        
        # Resolve entity name using shared service logic
        # This ensures consistency with Audit Log and Detail views
        entity_name = await AuditLogService.resolve_entity_name(
            session, 
            edit.entity_type, 
            edit.entity_id,
            snapshot=edit.snapshot_after
        )
        
        items.append(AuditLogEntryResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            entity_type=edit.entity_type,
            entity_name=entity_name,
            action=edit.action.value if edit.action else "UPDATE",
            summary=_generate_edit_summary(edit),
            submitted_by=submitter_summary,
            submitted_at=edit.created_at,
            reviewed_by=reviewer_summary,
            reviewed_at=edit.reviewed_at
        ))
    
    return AuditLogListResponse(items=items, total=total)


@router.get("/{edit_id}", response_model=AuditLogDetailResponse)
async def get_my_edit_detail(
    edit_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full details of a single edit.
    
    Users can only view their own edits, unless they are a Moderator or Admin.
    """
    edit = await session.get(EditHistory, edit_id)
    if not edit:
        raise HTTPException(status_code=404, detail="Edit not found")
    
    # Permission check: must be owner OR moderator/admin
    is_owner = edit.user_id == current_user.user_id
    is_moderator = current_user.role in (UserRole.MODERATOR, UserRole.ADMIN)
    
    if not is_owner and not is_moderator:
        raise HTTPException(status_code=403, detail="You can only view your own edits")
    
    # Get submitter info
    submitter = await session.get(User, edit.user_id)
    submitter_summary = UserSummary(
        user_id=str(submitter.user_id) if submitter else "unknown",
        display_name=submitter.display_name if submitter else "Unknown",
        email=submitter.email if submitter else "unknown@example.com"
    )
    
    # Reviewer info
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
        session, edit.entity_type, edit.entity_id, snapshot=edit.snapshot_after
    )
    
    # Permission flags - only moderators can perform moderation actions
    can_approve = False
    can_reject = False
    can_revert = False
    can_reapply = False
    
    if is_moderator and submitter:
        can_approve = edit.status == EditStatus.PENDING and AuditLogService.can_moderate_edit(current_user, submitter)
        can_reject = edit.status == EditStatus.PENDING and AuditLogService.can_moderate_edit(current_user, submitter)
        
        if edit.status == EditStatus.APPROVED and AuditLogService.can_moderate_edit(current_user, submitter):
            can_revert = await AuditLogService.is_most_recent_approved(session, edit)
        
        if edit.status in (EditStatus.REVERTED, EditStatus.REJECTED) and AuditLogService.can_moderate_edit(current_user, submitter):
            can_reapply = not await AuditLogService._has_newer_approved_edit(session, edit)
            
    # Hydrate snapshot with resolved names for UI display
    hydrated_snapshot_after = await _hydrate_snapshot(session, edit.entity_type, edit.snapshot_after)
    
    return AuditLogDetailResponse(
        edit_id=str(edit.edit_id),
        status=edit.status.value,
        entity_type=edit.entity_type,
        entity_name=entity_name,
        action=edit.action.value if edit.action else "UPDATE",
        submitted_by=submitter_summary,
        submitted_at=edit.created_at,
        reviewed_by=reviewer_summary,
        reviewed_at=edit.reviewed_at,
        summary=_generate_edit_summary(edit),
        snapshot_before=edit.snapshot_before,
        snapshot_after=hydrated_snapshot_after,
        source_url=edit.source_url,
        source_notes=edit.source_notes,
        review_notes=edit.review_notes,
        can_approve=can_approve,
        can_reject=can_reject,
        can_revert=can_revert,
        can_reapply=can_reapply
    )


async def _hydrate_snapshot(session: AsyncSession, entity_type: str, snapshot: Optional[dict]) -> Optional[dict]:
    """
    Inject resolved names into snapshot data for UI display.
    """
    if not snapshot:
        return None
        
    hydrated = snapshot.copy()
    etype = entity_type.lower()
    
    # Helper to unwrap (similar to service layer)
    inner = hydrated
    inner_key = None
    unwrap_keys = ["node", "era", "master", "brand", "link", "event", "lineage_event"]
    for key in unwrap_keys:
        if key in hydrated and isinstance(hydrated[key], dict):
            inner = hydrated[key]
            inner_key = key
            break
            
    if etype in ("lineage", "lineage_event", "lineageevent"):
        # Resolve predecessor/successor IDs
        pred_id = inner.get("predecessor_id") or inner.get("predecessor_node_id")
        succ_id = inner.get("successor_id") or inner.get("successor_node_id")
        
        # Only resolve if name is missing
        has_pred_name = inner.get("source_node") or inner.get("predecessor_names")
        has_succ_name = inner.get("target_team") or inner.get("successor_names")
        
        from uuid import UUID
        from app.models.team import TeamNode
        
        if pred_id and not has_pred_name:
            try:
                if isinstance(pred_id, str): pred_id = UUID(pred_id)
                node = await session.get(TeamNode, pred_id)
                if node:
                    inner["source_node"] = node.display_name or node.legal_name
            except (ValueError, Exception):
                pass
                
        if succ_id and not has_succ_name:
            try:
                if isinstance(succ_id, str): succ_id = UUID(succ_id)
                node = await session.get(TeamNode, succ_id)
                if node:
                    inner["target_team"] = node.display_name or node.legal_name
            except (ValueError, Exception):
                pass

    elif etype in ("sponsor_link", "teamsponsorlink", "link"):
        # Resolve Era and Brand names for Sponsor Links
        era_id = inner.get("era_id")
        brand_id = inner.get("brand_id")
        
        from uuid import UUID
        from app.models.team import TeamEra
        from app.models.sponsor import SponsorBrand
        
        if era_id and not inner.get("era_name"):
            try:
                if isinstance(era_id, str): era_id = UUID(era_id)
                era = await session.get(TeamEra, era_id)
                if era:
                    inner["era_name"] = f"{era.registered_name} ({era.season_year})"
            except (ValueError, Exception):
                pass
                
        if brand_id and not inner.get("brand_name"):
            try:
                if isinstance(brand_id, str): brand_id = UUID(brand_id)
                brand = await session.get(SponsorBrand, brand_id)
                if brand:
                    inner["brand_name"] = brand.brand_name
            except (ValueError, Exception):
                pass
    
    if inner_key:
        hydrated[inner_key] = inner
    else:
        hydrated = inner
        
    return hydrated
