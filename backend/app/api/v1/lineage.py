from typing import List
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.lineage_service import LineageService
from app.schemas.lineage import LineageListResponse
from app.core.etag import compute_etag
from app.api.dependencies import require_admin
from app.models.user import User
from app.models.lineage import LineageEvent
from app.services.edit_service import EditService
from app.models.enums import EditAction, EditStatus

router = APIRouter(prefix="/api/v1/lineage", tags=["lineage"])

@router.get("", response_model=LineageListResponse)
async def list_lineage_events(
    request: Request,
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: str = Query(None, description="Search by predecessor or successor team name"),
    sort_by: str = Query("event_year", description="Field to sort by"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db)
):
    """
    List lineage events with pagination and optional search.
    """
    service = LineageService(db)
    events, total = await service.list_events(
        skip=skip, 
        limit=limit, 
        search=search,
        sort_by=sort_by,
        order=order
    )
    
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


@router.delete("/{event_id}", status_code=204)
async def delete_lineage_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a lineage event.
    Admins only.
    """
    import uuid
    try:
        e_uuid = uuid.UUID(event_id)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lineage event not found")

    # Fetch for snapshot
    event = await db.get(LineageEvent, e_uuid)
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lineage event not found")
        
    snapshot_before = {
        "event": {
            "event_id": str(event.event_id),
            "event_type": event.event_type.value,
            "event_year": event.event_year,
            "predecessor_node_id": str(event.predecessor_node_id) if event.predecessor_node_id else None,
            "successor_node_id": str(event.successor_node_id) if event.successor_node_id else None
        }
    }

    service = LineageService(db)
    success = await service.delete_event(e_uuid)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lineage event not found")
        
    await EditService.record_direct_edit(
        session=db,
        user=current_user,
        entity_type="lineage_event",
        entity_id=e_uuid,
        action=EditAction.DELETE,
        snapshot_before=snapshot_before,
        snapshot_after={"deleted": True},
        notes="API Direct Delete"
    )
    
    await db.commit()
