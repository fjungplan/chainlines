"""
Audit Log API endpoints.

Provides endpoints for viewing and managing edit history.
Accessible to Moderators and Admins only.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, cast, String
from typing import List, Optional
from datetime import datetime


from app.db.database import get_db
from app.api.dependencies import require_moderator
from app.models.user import User
from app.models.edit import EditHistory
from app.models.enums import EditStatus
from app.schemas.audit_log import AuditLogEntryResponse, AuditLogDetailResponse, UserSummary, AuditLogListResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/api/v1/audit-log", tags=["audit-log"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search term (entity, submitter, summary)"),
    status: Optional[List[str]] = Query(None, description="Filter by status(es)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    user_id: Optional[str] = Query(None, description="Filter by submitter user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO 8601)"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, status, ...)", pattern="^(created_at|status|action|entity_type)$"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)", pattern="^(asc|desc)$"),
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
    
    # Search functionality
    if search:
        # Join with User to search submitter name
        stmt = stmt.join(User, EditHistory.user_id == User.user_id, isouter=True)
        
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.display_name.ilike(search_term),
                EditHistory.source_notes.ilike(search_term),
                EditHistory.review_notes.ilike(search_term),
                # Cast JSON to string to search content (rudimentary full-text for snapshots)
                cast(EditHistory.snapshot_after, String).ilike(search_term)
            )
        )
    
    # Status filter
    # - If status is provided and non-empty: filter by those statuses
    # - If status is provided but empty: return no results (user deselected all)
    # - If status is None (not provided): default to PENDING (backward compatibility)
    if status is not None:
        if len(status) > 0:
            status_values = [EditStatus(s) for s in status]
            stmt = stmt.where(EditHistory.status.in_(status_values))
        else:
            # Empty array means user deselected all statuses - return no results
            stmt = stmt.where(False)
    elif not search:
        # If searching, we likely want to see everything unless status is explicit
        # But if no search and no status parameter, default to PENDING
        stmt = stmt.where(EditHistory.status == EditStatus.PENDING)
    
    # Entity type filter - normalize for case-insensitive match (handles snake_case vs PascalCase)
    if entity_type:
        # Normalize by removing underscores and lowercasing for comparison
        # This allows "team_node" to match "TeamNode"
        normalized_input = entity_type.replace("_", "").lower()
        stmt = stmt.where(
            func.replace(func.lower(EditHistory.entity_type), "_", "") == normalized_input
        )
    
    # User filter
    if user_id:
        stmt = stmt.where(EditHistory.user_id == user_id)

    # Date range filter
    if start_date:
        # Ensure naive datetime for comparison with naive DB timestamp
        if start_date.tzinfo:
            start_date = start_date.replace(tzinfo=None)
        stmt = stmt.where(EditHistory.created_at >= start_date)
    if end_date:
        if end_date.tzinfo:
            end_date = end_date.replace(tzinfo=None)
        stmt = stmt.where(EditHistory.created_at <= end_date)

    # Get total count
    # We need to ensure the count query respects the same joins/filters
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(total_stmt)).scalar_one()

    # Sort
    sort_column = getattr(EditHistory, sort_by)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())
    
    # Secondary sort by ID for stability
    stmt = stmt.order_by(EditHistory.edit_id)
    # Execute query
    # Applying offset/limit after order_by for correct pagination
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    edits = result.scalars().all()
    
    # Transform to response schema
    items = []
    for edit in edits:
        # Resolve entity name using shared service logic
        entity_name = await AuditLogService.resolve_entity_name(
            session, 
            edit.entity_type, 
            edit.entity_id,
            snapshot=edit.snapshot_after
        )
        
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
        
        items.append(AuditLogEntryResponse(
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
        
    return AuditLogListResponse(items=items, total=total)


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


@router.get("/{edit_id}", response_model=AuditLogDetailResponse)
async def get_audit_log_detail(
    edit_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    """
    Get full details of a single edit.
    
    Returns the edit with resolved entity names, snapshots, and permission flags
    indicating what actions the current user can take.
    """
    edit = await session.get(EditHistory, edit_id)
    if not edit:
        raise HTTPException(status_code=404, detail="Edit not found")
    
    # Get submitter and reviewer info
    submitter = await session.get(User, edit.user_id)
    submitter_summary = UserSummary(
        user_id=str(submitter.user_id) if submitter else "unknown",
        display_name=submitter.display_name if submitter else "Unknown",
        email=submitter.email if submitter else "unknown@example.com"
    )
    
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
    
    # Determine permission flags based on current user and edit state
    can_approve = edit.status == EditStatus.PENDING and AuditLogService.can_moderate_edit(current_user, submitter)
    can_reject = edit.status == EditStatus.PENDING and AuditLogService.can_moderate_edit(current_user, submitter)
    
    # Can revert only if approved, most recent, and has permission
    can_revert = False
    if edit.status == EditStatus.APPROVED and submitter and AuditLogService.can_moderate_edit(current_user, submitter):
        can_revert = await AuditLogService.is_most_recent_approved(session, edit)
    
    # Can reapply only if reverted/rejected, no newer approved, and has permission
    can_reapply = False
    if edit.status in (EditStatus.REVERTED, EditStatus.REJECTED) and submitter and AuditLogService.can_moderate_edit(current_user, submitter):
        can_reapply = not await AuditLogService._has_newer_approved_edit(session, edit)
        
    # Hydrate snapshot with resolved names for UI display
    # This ensures "Unknown" IDs in diff views (like Lineage) are replaced with names if possible
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
    
    Ideally this would be done by the frontend, but the frontend lacks DB access
    to resolve IDs if they aren't already in the snapshot.
    """
    if not snapshot:
        return None
        
    hydrated = snapshot.copy()
    etype = entity_type.lower()
    
    # Helper to unwrap (similar to service layer)
    # We need to peek inside wrapper keys to find the IDs
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
        
        # Only resolve if name is missing from snapshot logic
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
    
    # If we unwrapped, put it back
    if inner_key:
        hydrated[inner_key] = inner
    else:
        hydrated = inner
        
    return hydrated


@router.post("/{edit_id}/revert")
async def revert_edit(
    edit_id: str,
    request: dict = {},
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    """
    Revert an approved edit.
    
    Only the most recent approved edit for an entity can be reverted.
    Moderators cannot revert edits submitted by admins.
    """
    from app.schemas.audit_log import RevertRequest
    
    edit = await session.get(EditHistory, edit_id)
    if not edit:
        raise HTTPException(status_code=404, detail="Edit not found")
    
    try:
        result = await AuditLogService.revert_edit(
            session, edit, current_user, notes=request.get("notes")
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{edit_id}/reapply")
async def reapply_edit(
    edit_id: str,
    request: dict = {},
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    """
    Re-apply a reverted or rejected edit.
    
    Cannot re-apply if a newer approved edit exists for the entity.
    Moderators cannot re-apply edits submitted by admins.
    """
    from app.schemas.audit_log import ReapplyRequest
    
    edit = await session.get(EditHistory, edit_id)
    if not edit:
        raise HTTPException(status_code=404, detail="Edit not found")
    
    try:
        result = await AuditLogService.reapply_edit(
            session, edit, current_user, notes=request.get("notes")
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
