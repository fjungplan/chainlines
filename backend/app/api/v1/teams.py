from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.team_repository import TeamRepository
from app.schemas.team import (
    TeamNodeWithEras,
    TeamNodeResponse,
    TeamEraResponse,
    TeamListResponse,
)
from app.core.exceptions import NodeNotFoundException


router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


@router.get("/{node_id}", response_model=TeamNodeWithEras)
async def get_team(
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return a single TeamNode with its eras.

    Eager-loads related eras (and lineage events for future use).
    """
    node = await TeamRepository.get_by_id(db, node_id)
    if not node:
        raise NodeNotFoundException(f"TeamNode {node_id} not found")
    return node


@router.get("/{node_id}/eras", response_model=list[TeamEraResponse])
async def get_team_eras(
    node_id: UUID,
    year: Optional[int] = Query(default=None, ge=1900, le=2100),
    db: AsyncSession = Depends(get_db),
):
    """Return all TeamEra records for a given team node.

    Optional `year` filters to a specific season; results ordered by season_year DESC.
    """
    # Ensure node exists for 404 semantics
    node = await TeamRepository.get_by_id(db, node_id)
    if not node:
        raise NodeNotFoundException(f"TeamNode {node_id} not found")
    eras = await TeamRepository.get_eras_for_node(db, node_id, year_filter=year)
    return eras


@router.get("", response_model=TeamListResponse)
async def list_teams(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_in_year: Optional[int] = Query(default=None, ge=1900, le=2100),
    tier_level: Optional[int] = Query(default=None, ge=1, le=3),
    db: AsyncSession = Depends(get_db),
):
    """List teams with pagination and optional filters.

    - active_in_year: only teams with an era in that year
    - tier_level: only teams having any era with the given tier
    """
    nodes, total = await TeamRepository.get_all(
        db,
        skip=skip,
        limit=limit,
        active_in_year=active_in_year,
        tier_level=tier_level,
    )
    return {
        "items": nodes,
        "total": total,
        "skip": skip,
        "limit": limit,
    }
