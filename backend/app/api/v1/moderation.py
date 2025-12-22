from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.db.database import get_db
from app.api.dependencies import require_admin
from app.models.user import User
from app.models.edit import EditHistory, EditStatus
from app.schemas.moderation import (
    PendingEditResponse,
    ReviewEditRequest,
    ReviewEditResponse,
    ModerationStatsResponse
)
from app.services.moderation_service import ModerationService

router = APIRouter(prefix="/api/v1/moderation", tags=["moderation"])

@router.get("/pending", response_model=List[PendingEditResponse])
async def get_pending_edits(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    edit_type: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get list of pending edits for moderation"""
    stmt = select(EditHistory).where(EditHistory.status == EditStatus.PENDING)
    
    if edit_type:
        if edit_type == "SPONSOR":
            stmt = stmt.where(EditHistory.entity_type.in_(["sponsor_master", "sponsor_brand"]))
        elif edit_type == "METADATA":
            stmt = stmt.where(EditHistory.entity_type.in_(["team_node", "team_era"]))
        elif edit_type in ["MERGE", "SPLIT"]:
            stmt = stmt.where(EditHistory.entity_type == "lineage_event")
        elif edit_type == "CREATE":
            # Approximating CREATE to team creation for now, or all creates?
            # Usually creates are specific types.
            pass
            
    stmt = stmt.order_by(EditHistory.created_at.asc()).offset(skip).limit(limit)
    result = await session.execute(stmt)
    edits = result.scalars().all()
    
    # Optional: manual post-filtering for Merge/Split/Create if strictness needed
    # (Skipping for performance/simplicity, acceptable to return mixed related types)
    
    return [await ModerationService.format_edit_for_review(session, edit) for edit in edits]

@router.post("/review/{edit_id}", response_model=ReviewEditResponse)
async def review_edit(
    edit_id: str,
    request: ReviewEditRequest,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Approve or reject a pending edit"""
    edit = await session.get(EditHistory, edit_id)
    if not edit:
        raise HTTPException(status_code=404, detail="Edit not found")
    if edit.status != EditStatus.PENDING:
        raise HTTPException(status_code=400, detail="Edit is not pending")
    # Enforce rejection notes in backend
    if request.approved is False and (not request.notes or not request.notes.strip()):
        raise HTTPException(status_code=400, detail="Rejection notes are required when rejecting an edit.")
    result = await ModerationService.review_edit(
        session,
        edit,
        admin,
        request.approved,
        request.notes
    )
    return result

@router.get("/stats", response_model=ModerationStatsResponse)
async def get_moderation_stats(
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get moderation statistics"""
    return await ModerationService.get_stats(session)
