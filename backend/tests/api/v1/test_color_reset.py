import pytest
from httpx import AsyncClient
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.models.team import TeamNode, TeamEra
from app.models.user import User
from app.api.dependencies import get_db

@pytest.mark.asyncio
async def test_reset_hex_color_to_null(
    client: AsyncClient, 
    db_session: AsyncSession, 
    trusted_user_token: str
):
    """
    Test that setting hex_color_override to null correctly removes the override.
    This verifies that the API Schema accepts `Optional[str] = None` and doesn't
    fail regex validation on explicit null, and that the Service updates it correctly.
    """
    # 1. Setup Data
    node = TeamNode(founding_year=2010, legal_name="Color Reset Test Node")
    db_session.add(node)
    await db_session.flush()
    
    era = TeamEra(
        node_id=node.node_id, 
        season_year=2021, 
        valid_from=date(2021, 1, 1), 
        registered_name="Color Reset Team"
    )
    db_session.add(era)
    await db_session.flush()
    
    master = SponsorMaster(legal_name="Color Reset Master")
    db_session.add(master)
    await db_session.flush()
    
    brand = SponsorBrand(
        master_id=master.master_id, 
        brand_name="Color Brand", 
        default_hex_color="#000000"
    )
    db_session.add(brand)
    await db_session.flush()
    
    # Create link WITH an override initially
    link = TeamSponsorLink(
        era_id=era.era_id,
        brand_id=brand.brand_id,
        rank_order=1,
        prominence_percent=100,
        hex_color_override="#FF0000" # Calculated Red
    )
    db_session.add(link)
    await db_session.commit()
    
    link_id = link.link_id
    
    # 2. Call API to Reset (set to null)
    headers = {"Authorization": f"Bearer {trusted_user_token}"}
    payload = {
        "brand_id": str(brand.brand_id), # Required by schema create reuse, though ignored by update logic usually
        "rank_order": 1,
        "prominence_percent": 100, 
        "hex_color_override": None 
    }
    
    response = await client.put(f"/api/v1/sponsors/eras/links/{link_id}", json=payload, headers=headers)
    
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["hex_color_override"] is None
    
    # 3. Verify in DB
    # Refresh session to ensure we read from DB
    await db_session.refresh(link)
    assert link.hex_color_override is None
