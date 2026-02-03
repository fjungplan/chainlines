import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sponsor import SponsorMaster, SponsorBrand

@pytest.mark.asyncio
async def test_safe_delete_master_safeguard(
    client: AsyncClient, 
    db_session: AsyncSession, 
    admin_user_token: str
):
    """
    Test that deleting a SponsorMaster with existing brands fails,
    verifying the safeguard is (or will be) in place.
    """
    # 1. Setup Master with Brand
    master = SponsorMaster(legal_name="Safe Delete Test")
    db_session.add(master)
    await db_session.flush()
    
    brand = SponsorBrand(
        master_id=master.master_id,
        brand_name="Dependent Brand",
        default_hex_color="#000000"
    )
    db_session.add(brand)
    await db_session.commit()
    
    master_id = master.master_id
    
    # 2. Attempt Delete (Admin)
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = await client.delete(f"/api/v1/sponsors/masters/{master_id}", headers=headers)
    
    # 3. Assert Failure (Should be 400 Bad Request or 409 Conflict, usually 400 for logic)
    # If currently missing safeguard, this might be 500 (integrity) or 204 (cascade).
    # We want it to be 400/409 with specific message.
    assert response.status_code in [400, 409], f"Should fail, got {response.status_code}"
    assert "cannot delete" in response.json()["detail"].lower() or "brands" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_safe_delete_empty_master(
    client: AsyncClient, 
    db_session: AsyncSession, 
    admin_user_token: str
):
    """
    Test that deleting an EMPTY SponsorMaster succeeds.
    """
    # 1. Setup Empty Master
    master = SponsorMaster(legal_name="Empty Delete Test")
    db_session.add(master)
    await db_session.commit()
    
    master_id = master.master_id
    
    # 2. Attempt Delete
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = await client.delete(f"/api/v1/sponsors/masters/{master_id}", headers=headers)
    
    # 3. Assert Success
    assert response.status_code == 204
    
    # Verify DB
    deleted = await db_session.get(SponsorMaster, master_id)
    assert deleted is None
