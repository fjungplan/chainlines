from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.db.database import get_db
from app.api.dependencies import require_admin
from app.models.user import User
from app.models.edit import Edit, EditStatus
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
    stmt = select(Edit).where(Edit.status == EditStatus.PENDING)
    if edit_type:
        stmt = stmt.where(Edit.edit_type == edit_type)
    stmt = stmt.order_by(Edit.created_at.asc()).offset(skip).limit(limit)
    result = await session.execute(stmt)
    edits = result.scalars().all()
    return [await ModerationService.format_edit_for_review(session, edit) for edit in edits]

@router.post("/review/{edit_id}", response_model=ReviewEditResponse)
async def review_edit(
    edit_id: str,
    request: ReviewEditRequest,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Approve or reject a pending edit"""
    edit = await session.get(Edit, edit_id)
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
