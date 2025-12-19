from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.dependencies import get_current_user, require_editor, require_admin
from app.models.user import User
from app.schemas.sponsors import (
    SponsorMasterCreate, SponsorMasterUpdate, SponsorMasterResponse,
    SponsorBrandCreate, SponsorBrandUpdate, SponsorBrandResponse,
    SponsorMasterListResponse,
    TeamSponsorLinkCreate, TeamSponsorLinkResponse
)
from app.services.sponsor_service import SponsorService

# Router setup
router = APIRouter(prefix="/api/v1/sponsors", tags=["sponsors"])

# --- Sponsor Masters ---

@router.get("/masters", response_model=List[SponsorMasterListResponse])
async def get_masters(
    query: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List or search sponsor masters.
    """
    if query:
        masters = await SponsorService.search_masters(session, query, limit)
    else:
        masters = await SponsorService.get_all_masters(session, skip, limit)
    
    # Simple transform for list response
    results = []
    for m in masters:
        # Calculate brand count manually or via hybrid if needed. 
        # For now, simplistic length check since we eager loaded brands in service
        count = len(m.brands)
        resp = SponsorMasterListResponse.model_validate(m)
        resp.brand_count = count
        results.append(resp)
        
    return results

@router.get("/masters/{master_id}", response_model=SponsorMasterResponse)
async def get_master(
    master_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    master = await SponsorService.get_master_by_id(session, master_id)
    if not master:
        raise HTTPException(status_code=404, detail="Sponsor master not found")
    return master

@router.post("/masters", response_model=SponsorMasterResponse)
async def create_master(
    data: SponsorMasterCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create a new sponsor master.
    Editors/Admins only.
    """
    # Check duplicate name? DB constraint will raise 400/500 usually
    try:
        master = await SponsorService.create_master(session, data, current_user.user_id)
        return master
    except Exception as e:
        # Generic catch for unique constraint for now
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Sponsor master with this name already exists")
        raise e

@router.put("/masters/{master_id}", response_model=SponsorMasterResponse)
async def update_master(
    master_id: UUID,
    data: SponsorMasterUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """Update a sponsor master."""
    result = await SponsorService.update_master(session, master_id, data, current_user.user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sponsor master not found")
    return result

@router.delete("/masters/{master_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_master(
    master_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a sponsor master.
    Admins only. Warning: will delete all brands.
    """
    success = await SponsorService.delete_master(session, master_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sponsor master not found")

# --- Sponsor Brands ---

@router.get("/brands", response_model=List[SponsorBrandResponse])
async def search_brands(
    query: str = Query(..., min_length=2),
    limit: int = 20,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search brands by name (autocomplete).
    """
    brands = await SponsorService.search_brands(session, query, limit)
    return brands

@router.post("/masters/{master_id}/brands", response_model=SponsorBrandResponse)
async def create_brand(
    master_id: UUID,
    data: SponsorBrandCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """Add a brand to a master."""
    brand = await SponsorService.add_brand(session, master_id, data, current_user.user_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Sponsor master not found")
    return brand

@router.put("/brands/{brand_id}", response_model=SponsorBrandResponse)
async def update_brand(
    brand_id: UUID,
    data: SponsorBrandUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """Update a brand data."""
    brand = await SponsorService.update_brand(session, brand_id, data, current_user.user_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Sponsor brand not found")
    return brand

@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a brand."""
    success = await SponsorService.delete_brand(session, brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sponsor brand not found")

# --- Era Links ---

@router.get("/eras/{era_id}/links", response_model=List[TeamSponsorLinkResponse])
async def get_era_links(
    era_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sponsor links for an era."""
    return await SponsorService.get_era_sponsor_links(session, era_id)

@router.post("/eras/{era_id}/links", response_model=TeamSponsorLinkResponse)
async def link_sponsor_to_era(
    era_id: UUID,
    data: TeamSponsorLinkCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """Link a sponsor brand to an era."""
    # Data validation happens in service
    return await SponsorService.link_sponsor_to_era(
        session,
        era_id,
        data.brand_id,
        data.rank_order,
        data.prominence_percent,
        current_user.user_id
    )

@router.delete("/eras/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_sponsor_link(
    link_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """Remove a sponsor link from an era."""
    success = await SponsorService.remove_sponsor_from_era(session, link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sponsor link not found")
