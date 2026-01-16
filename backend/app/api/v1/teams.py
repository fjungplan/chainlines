from __future__ import annotations

from typing import Optional
from uuid import UUID
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.team_service import TeamService
from app.core.etag import compute_etag
from app.schemas.team import (
    TeamNodeWithEras,
    TeamNodeResponse,
    TeamEraResponse,
    TeamListResponse,
    TeamNodeCreate,
    TeamNodeUpdate,
    TeamEraCreate,
    TeamEraUpdate,
)
from app.api.dependencies import get_current_user, require_editor, require_admin, require_trusted_or_higher
from app.models.user import User
from app.models.team import TeamEra
from app.schemas.team_detail import TeamHistoryResponse
from app.services.team_detail_service import TeamDetailService
from app.core.exceptions import NodeNotFoundException
from app.services.edit_service import EditService
from app.models.enums import EditAction, EditStatus


router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


@router.get("/{node_id}", response_model=TeamNodeWithEras)
async def get_team(
    node_id: UUID,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Return a single TeamNode with its eras.

    Eager-loads related eras (and lineage events for future use).
    """
    node = await TeamService.get_node_with_eras(db, node_id)
    if not node:
        raise NodeNotFoundException(f"TeamNode {node_id} not found")
    # Conditional ETag handling
    body = jsonable_encoder(node)
    etag = compute_etag(body)
    inm = request.headers.get("if-none-match") if request else None
    if inm == etag:
        resp = Response(status_code=304)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "max-age=300"
        return resp
    if response:
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "max-age=300"
    return node


@router.post("", response_model=TeamNodeResponse, status_code=201)
async def create_team_node(
    data: TeamNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher),
):
    """Create a new TeamNode."""
    node = await TeamService.create_node(db, data, current_user.user_id)
    
    # Audit Log
    snapshot_after = {
        "node": {
            "node_id": str(node.node_id),
            "legal_name": node.legal_name,
            "founding_year": node.founding_year,
            "dissolution_year": node.dissolution_year
        }
    }
    await EditService.record_direct_edit(
        session=db,
        user=current_user,
        entity_type="team_node",
        entity_id=node.node_id,
        action=EditAction.CREATE,
        snapshot_before=None,
        snapshot_after=snapshot_after,
        notes="API Direct Create"
    )
    
    await db.commit()
    await db.refresh(node)
    return node


@router.put("/{node_id}", response_model=TeamNodeResponse)
async def update_team_node(
    node_id: UUID,
    data: TeamNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher),
):
    """Update a TeamNode."""
    # Fetch for snapshot_before
    existing = await TeamService.get_node_with_eras(db, node_id) # Using this helper as it's available
    if not existing:
        raise NodeNotFoundException(f"TeamNode {node_id} not found")
        
    snapshot_before = {
        "node": {
            "node_id": str(existing.node_id),
            "legal_name": existing.legal_name,
            "founding_year": existing.founding_year,
            "dissolution_year": existing.dissolution_year
        }
    }

    node = await TeamService.update_node(db, node_id, data, current_user.user_id)
    
    snapshot_after = {
        "node": {
            "node_id": str(node.node_id),
            "legal_name": node.legal_name,
            "founding_year": node.founding_year,
            "dissolution_year": node.dissolution_year
        }
    }
    
    await EditService.record_direct_edit(
        session=db,
        user=current_user,
        entity_type="team_node",
        entity_id=node.node_id,
        action=EditAction.UPDATE,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
        notes="API Direct Update"
    )
    
    await db.commit()
    await db.refresh(node)
    return node


@router.delete("/{node_id}", status_code=204)
async def delete_team_node(
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a TeamNode."""
    # Fetch for snapshot_before
    existing = await TeamService.get_node_with_eras(db, node_id)
    if not existing:
         raise NodeNotFoundException(f"TeamNode {node_id} not found")

    snapshot_before = {
        "node": {
            "node_id": str(existing.node_id),
            "legal_name": existing.legal_name,
            "founding_year": existing.founding_year
        }
    }

    success = await TeamService.delete_node(db, node_id)
    if not success:
        # Should catch this earlier with check above, but safe to keep
        raise NodeNotFoundException(f"TeamNode {node_id} not found")
        
    await EditService.record_direct_edit(
        session=db,
        user=current_user,
        entity_type="team_node",
        entity_id=node_id,
        action=EditAction.DELETE,
        snapshot_before=snapshot_before,
        snapshot_after={"deleted": True},
        notes="API Direct Delete"
    )
    
    await db.commit()


@router.get("/{node_id}/history", response_model=TeamHistoryResponse)
async def get_team_history(node_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    """Mobile-optimized chronological history for a team node with ETag support."""
    history = await TeamDetailService.get_team_history(db, str(node_id))
    if not history:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Compute ETag for conditional requests
    payload = history.model_dump_json()
    etag = hashlib.md5(payload.encode("utf-8")).hexdigest()
    
    # If-None-Match handling: return 304 if client's ETag matches
    inm = request.headers.get("If-None-Match")
    if inm and inm.strip() == etag:
        response = Response(status_code=304)
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "max-age=300"
        return response
    
    # Return full response with caching headers
    response = Response(content=payload, media_type="application/json")
    response.headers["Cache-Control"] = "max-age=300"
    response.headers["ETag"] = etag
    return response


@router.get("/{node_id}/eras", response_model=list[TeamEraResponse])
async def get_team_eras(
    node_id: UUID,
    request: Request,
    response: Response,
    year: Optional[int] = Query(default=None, ge=1900, le=2100),
    db: AsyncSession = Depends(get_db),
):
    """Return all TeamEra records for a given team node.

    Optional `year` filters to a specific season; results ordered by season_year DESC.
    """
    # Ensure node exists for 404 semantics
    node = await TeamService.get_node_with_eras(db, node_id)
    if not node:
        raise NodeNotFoundException(f"TeamNode {node_id} not found")
    eras = await TeamService.get_node_eras(db, node_id, year_filter=year)
    body = jsonable_encoder(eras)
    etag = compute_etag(body)
    inm = request.headers.get("if-none-match") if request else None
    if inm == etag:
        resp = Response(status_code=304)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "max-age=300"
        return resp
    if response:
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "max-age=300"
    return eras


@router.post("/{node_id}/eras", response_model=TeamEraResponse, status_code=201)
async def create_team_era(
    node_id: UUID,
    data: TeamEraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher),
):
    """Add a new Era to a TeamNode."""
    era = await TeamService.create_era(db, node_id, data, current_user.user_id)
    
    # Audit Log
    snapshot_after = {
        "era": {
            "era_id": str(era.era_id),
            "node_id": str(era.node_id),
            "season_year": era.season_year,
            "registered_name": era.registered_name,
            "uci_code": era.uci_code
        }
    }
    
    await EditService.record_direct_edit(
        session=db,
        user=current_user,
        entity_type="team_era",
        entity_id=era.era_id,
        action=EditAction.CREATE,
        snapshot_before=None,
        snapshot_after=snapshot_after,
        notes="API Direct Create"
    )
    
    await db.commit()
    await db.refresh(era)
    return era


@router.put("/eras/{era_id}", response_model=TeamEraResponse)
async def update_team_era(
    era_id: UUID,
    data: TeamEraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher),
):
    """Update a TeamEra."""
    # Fetch for snapshot_before
    existing = await db.get(TeamEra, era_id)
    if not existing:
        raise HTTPException(status_code=404, detail="TeamEra not found")
        
    snapshot_before = {
        "era": {
            "era_id": str(existing.era_id),
            "node_id": str(existing.node_id),
            "season_year": existing.season_year,
            "registered_name": existing.registered_name,
            "uci_code": existing.uci_code
        }
    }

    era = await TeamService.update_era(db, era_id, data, current_user.user_id)
    
    snapshot_after = {
        "era": {
            "era_id": str(era.era_id),
            "node_id": str(era.node_id),
            "season_year": era.season_year,
            "registered_name": era.registered_name,
            "uci_code": era.uci_code
        }
    }
    
    await EditService.record_direct_edit(
        session=db,
        user=current_user,
        entity_type="team_era",
        entity_id=era.era_id,
        action=EditAction.UPDATE,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
        notes="API Direct Update"
    )
    
    await db.commit()
    await db.refresh(era)
    return era


@router.delete("/eras/{era_id}", status_code=204)
async def delete_team_era(
    era_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher),
):
    """Delete a TeamEra."""
    # Fetch for snapshot_before
    existing = await db.get(TeamEra, era_id)
    if not existing:
        raise HTTPException(status_code=404, detail="TeamEra not found")

    snapshot_before = {
        "era": {
            "era_id": str(existing.era_id),
            "node_id": str(existing.node_id),
            "season_year": existing.season_year,
            "registered_name": existing.registered_name
        }
    }

    success = await TeamService.delete_era(db, era_id)
    if not success:
         # Should catch this earlier, but safe
        raise HTTPException(status_code=404, detail="TeamEra not found")
        
    await EditService.record_direct_edit(
        session=db,
        user=current_user,
        entity_type="team_era",
        entity_id=era_id,
        action=EditAction.DELETE,
        snapshot_before=snapshot_before,
        snapshot_after={"deleted": True},
        notes="API Direct Delete"
    )
    
    await db.commit()


@router.get("", response_model=TeamListResponse)
async def list_teams(
    request: Request,
    response: Response,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_in_year: Optional[int] = Query(default=None, ge=1900, le=2100),
    tier_level: Optional[int] = Query(default=None, ge=1, le=3),
    search: Optional[str] = Query(default=None, min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """List teams with pagination and optional filters.

    - active_in_year: only teams with an era in that year
    - tier_level: only teams having any era with the given tier
    - search: fuzzy match on legal_name or display_name
    """
    nodes, total = await TeamService.list_nodes(
        db,
        skip=skip,
        limit=limit,
        active_in_year=active_in_year,
        tier_level=tier_level,
        search=search,
    )
    payload = {
        "items": nodes,
        "total": total,
        "skip": skip,
        "limit": limit,
    }
    body = jsonable_encoder(payload)
    etag = compute_etag(body)
    inm = request.headers.get("if-none-match") if request else None
    if inm == etag:
        resp = Response(status_code=304)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "max-age=300"
        return resp
    if response:
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "max-age=300"
    return payload
