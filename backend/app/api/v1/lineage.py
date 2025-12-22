from typing import List
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.lineage_service import LineageService
from app.schemas.lineage import LineageListResponse
from app.core.etag import compute_etag

router = APIRouter(prefix="/api/v1/lineage", tags=["lineage"])

@router.get("", response_model=LineageListResponse)
async def list_lineage_events(
    request: Request,
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: str = Query(None, description="Search by predecessor or successor team name"),
    db: AsyncSession = Depends(get_db)
):
    """
    List lineage events with pagination and optional search.
    """
    service = LineageService(db)
    events, total = await service.list_events(skip=skip, limit=limit, search=search)
    
    payload = {
        "items": events,
        "total": total
    }
    
    # ETag handling
    body = jsonable_encoder(payload)
    etag = compute_etag(body)
    inm = request.headers.get("if-none-match") if request else None
    
    if inm == etag:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "max-age=60"})
        
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "max-age=60"
    
    return payload


@router.get("/{event_id}")
async def get_lineage_event(
    event_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single lineage event by ID.
    """
    service = LineageService(db)
    event = await service.get_event_by_id(event_id)
    
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lineage event not found")
    
    return event
