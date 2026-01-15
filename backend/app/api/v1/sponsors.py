from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.api.dependencies import get_current_user, require_editor, require_admin, require_trusted_or_higher
from app.models.user import User
from app.schemas.sponsors import (
    SponsorMasterCreate, SponsorMasterUpdate, SponsorMasterResponse,
    SponsorBrandCreate, SponsorBrandUpdate, SponsorBrandResponse,
    SponsorMasterListResponse,
    TeamSponsorLinkCreate, TeamSponsorLinkResponse
)
from app.services.sponsor_service import SponsorService
from app.services.edit_service import EditService
from app.models.enums import EditAction

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
    current_user: User = Depends(require_trusted_or_higher)
):
    """
    Create a new sponsor master.
    Trusted Editors/Admins only.
    """
    # Check duplicate name? DB constraint will raise 400/500 usually
    try:
        master = await SponsorService.create_master(session, data, current_user.user_id)
        
        # Audit Log
        snapshot_after = {
            "master": {
                "master_id": str(master.master_id),
                "legal_name": master.legal_name,
                "industry_sector": master.industry_sector,
            }
        }
        await EditService.record_direct_edit(
            session=session,
            user=current_user,
            entity_type="sponsor_master",
            entity_id=master.master_id,
            action=EditAction.CREATE,
            snapshot_before=None,
            snapshot_after=snapshot_after,
            notes=data.source_notes
        )
        
        await session.commit()
        await session.refresh(master)
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
    current_user: User = Depends(require_trusted_or_higher)
):
    """Update a sponsor master."""
    # Fetch for snapshot
    existing = await session.get(SponsorMaster, master_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsor master not found")
        
    snapshot_before = {
        "master": {
            "master_id": str(existing.master_id),
            "legal_name": existing.legal_name,
            "industry_sector": existing.industry_sector
        }
    }

    result = await SponsorService.update_master(session, master_id, data, current_user.user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sponsor master not found")
        
    snapshot_after = {
        "master": {
            "master_id": str(result.master_id),
            "legal_name": result.legal_name,
            "industry_sector": result.industry_sector
        }
    }
    
    await EditService.record_direct_edit(
        session=session,
        user=current_user,
        entity_type="sponsor_master",
        entity_id=master_id,
        action=EditAction.UPDATE,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
        notes="API Direct Update"
    )
    
    await session.commit()
    await session.refresh(result)
    return result

@router.delete("/masters/{master_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_master(
    master_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a sponsor master."""
    # Fetch for snapshot
    existing = await session.get(SponsorMaster, master_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsor master not found")
        
    snapshot_before = {
        "master": {
            "master_id": str(existing.master_id),
            "legal_name": existing.legal_name
        }
    }

    success = await SponsorService.delete_master(session, master_id)
    if not success:
         # Should catch earlier
         raise HTTPException(status_code=404, detail="Sponsor master not found")
         
    await EditService.record_direct_edit(
        session=session,
        user=current_user,
        entity_type="sponsor_master",
        entity_id=master_id,
        action=EditAction.DELETE,
        snapshot_before=snapshot_before,
        snapshot_after={"deleted": True},
        notes="API Direct Delete"
    )
    
    await session.commit()

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
    current_user: User = Depends(require_trusted_or_higher)
):
    """Add a brand to a master."""
    brand = await SponsorService.add_brand(session, master_id, data, current_user.user_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Sponsor master not found")
    
    # Audit Log
    snapshot_after = {
        "brand": {
            "brand_id": str(brand.brand_id),
            "master_id": str(master_id),
            "brand_name": brand.brand_name,
            "default_hex_color": brand.default_hex_color
        }
    }
    await EditService.record_direct_edit(
        session=session,
        user=current_user,
        entity_type="sponsor_brand",
        entity_id=brand.brand_id,
        action=EditAction.CREATE,
        snapshot_before=None,
        snapshot_after=snapshot_after,
        notes=data.source_notes
    )
    
    await session.commit()
    await session.refresh(brand)
    return brand

@router.put("/brands/{brand_id}", response_model=SponsorBrandResponse)
async def update_brand(
    brand_id: UUID,
    data: SponsorBrandUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher)
):
    """Update a brand."""
    # Fetch
    existing = await session.get(SponsorBrand, brand_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsor brand not found")
        
    snapshot_before = {
        "brand": {
            "brand_id": str(existing.brand_id),
            "brand_name": existing.brand_name,
            "default_hex_color": existing.default_hex_color
        }
    }

    brand = await SponsorService.update_brand(session, brand_id, data, current_user.user_id)
    if not brand:
         raise HTTPException(status_code=404, detail="Sponsor brand not found")
         
    snapshot_after = {
         "brand": {
            "brand_id": str(brand.brand_id),
            "brand_name": brand.brand_name,
            "default_hex_color": brand.default_hex_color
        }
    }
    
    await EditService.record_direct_edit(
        session=session,
        user=current_user,
        entity_type="sponsor_brand",
        entity_id=brand_id,
        action=EditAction.UPDATE,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
        notes="API Direct Update"
    )
    
    await session.commit()
    await session.refresh(brand)
    return brand

@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a brand."""
    # Fetch
    existing = await session.get(SponsorBrand, brand_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsor brand not found")
        
    snapshot_before = {
        "brand": {
            "brand_id": str(existing.brand_id),
            "brand_name": existing.brand_name
        }
    }

    success = await SponsorService.delete_brand(session, brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sponsor brand not found")
        
    await EditService.record_direct_edit(
        session=session,
        user=current_user,
        entity_type="sponsor_brand",
        entity_id=brand_id,
        action=EditAction.DELETE,
        snapshot_before=snapshot_before,
        snapshot_after={"deleted": True},
        notes="API Direct Delete"
    )
    
    await session.commit()

# --- Era Links ---

# --- Era Links ---

@router.put("/eras/{era_id}/links", response_model=List[TeamSponsorLinkResponse])
async def replace_era_links(
    era_id: UUID,
    links: List[TeamSponsorLinkCreate],
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher)
):
    """
    Replace ALL sponsor links for an era with a new list.
    Required for "Batch Save" operations.
    Validates that total prominence is exactly 100%.
    Trusted Users Only.
    """
    # Convert Pydantic models to dicts
    links_data = [l.model_dump() for l in links]
    
    # Snapshot Before
    existing_links = await SponsorService.get_era_sponsor_links(session, era_id)
    snapshot_before = {
        "links": [
            {
                "link_id": str(l.link_id),
                "brand_id": str(l.brand_id), 
                "rank_order": l.rank_order,
                "prominence_percent": l.prominence_percent
            }
            for l in existing_links
        ]
    }
    
    try:
        new_links = await SponsorService.replace_era_sponsor_links(
            session,
            era_id,
            links_data,
            current_user.user_id
        )
        
        snapshot_after = {
            "links": [
                {
                    "link_id": str(l.link_id),
                    "brand_id": str(l.brand_id), 
                    "rank_order": l.rank_order,
                    "prominence_percent": l.prominence_percent
                }
                for l in new_links
            ]
        }
        
        # Log as UPDATE on the Era
        await EditService.record_direct_edit(
            session=session,
            user=current_user,
            entity_type="team_era",
            entity_id=era_id,
            action=EditAction.UPDATE,
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_after,
            notes="API Replace Sponsor Links"
        )
        
        await session.commit()
        # No need to refresh list, service returns refreshed list
        return new_links
    except Exception as e:
        # Pass through validation exceptions
        if "ValidationException" in str(type(e)):
             raise HTTPException(status_code=400, detail=str(e))
        raise e

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
    current_user: User = Depends(require_trusted_or_higher)
):
    """Link a sponsor brand to an era."""
    # Data validation happens in service
    link = await SponsorService.link_sponsor_to_era(
        session,
        era_id,
        data.brand_id,
        data.rank_order,
        data.prominence_percent,
        current_user.user_id
    )
    
    snapshot_after = {
        "link": {
            "link_id": str(link.link_id),
            "era_id": str(era_id),
            "brand_id": str(data.brand_id),
            "rank_order": data.rank_order,
            "prominence_percent": data.prominence_percent
        }
    }
    
    await EditService.record_direct_edit(
        session=session,
        user=current_user,
        entity_type="sponsor_link",
        entity_id=link.link_id,
        action=EditAction.CREATE,
        snapshot_before=None,
        snapshot_after=snapshot_after,
        notes="API Direct Link Create"
    )
    
    await session.commit()
    await session.refresh(link)
    return link

@router.put("/eras/links/{link_id}", response_model=TeamSponsorLinkResponse)
async def update_sponsor_link(
    link_id: UUID,
    data: TeamSponsorLinkCreate, # Reusing Create schema as it has the same fields we need
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher)
):
    """
    Update a sponsor link (prominence, rank, color).
    Trusted Users Only.
    """
    # Fetch for snapshot
    existing = await session.get(TeamSponsorLink, link_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsor link not found")
        
    snapshot_before = {
        "link": {
            "link_id": str(existing.link_id),
            "rank_order": existing.rank_order,
            "prominence_percent": existing.prominence_percent
        }
    }

    # Note: data.brand_id is ignored for updates usually, or we can enforce it matches current
    # For now, we only update mutable fields
    link = await SponsorService.update_sponsor_link(
        session,
        link_id,
        data.prominence_percent,
        data.rank_order,
        data.hex_color_override,
        current_user.user_id
    )
    if not link:
        raise HTTPException(status_code=404, detail="Sponsor link not found")

    snapshot_after = {
        "link": {
            "link_id": str(link.link_id),
            "rank_order": link.rank_order,
            "prominence_percent": link.prominence_percent
        }
    }
    
    await EditService.record_direct_edit(
        session=session,
        user=current_user,
        entity_type="sponsor_link",
        entity_id=link_id,
        action=EditAction.UPDATE,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
        notes="API Direct Link Update"
    )
    
    await session.commit()
    await session.refresh(link)
    return link

@router.delete("/eras/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_sponsor_link(
    link_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trusted_or_higher)
):
    """Remove a sponsor link from an era."""
    # Fetch for snapshot
    existing = await session.get(TeamSponsorLink, link_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsor link not found")
        
    snapshot_before = {
        "link": {
            "link_id": str(existing.link_id),
            "rank_order": existing.rank_order,
            "prominence_percent": existing.prominence_percent
        }
    }

    success = await SponsorService.remove_sponsor_from_era(session, link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sponsor link not found")
        
    await EditService.record_direct_edit(
        session=session,
        user=current_user,
        entity_type="sponsor_link",
        entity_id=link_id,
        action=EditAction.DELETE,
        snapshot_before=snapshot_before,
        snapshot_after={"deleted": True},
        notes="API Direct Link Delete"
    )
    
    await session.commit()
