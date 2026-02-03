import pytest
import uuid
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sponsor import SponsorBrand, SponsorMaster
from app.models.enums import EditAction, EditStatus, UserRole
from app.services.edit_service import EditService
from app.schemas.edits import SponsorBrandEditRequest

@pytest.mark.asyncio
async def test_update_brand_transfer_audit(async_session: AsyncSession):
    # 1. Setup Data
    source_master = SponsorMaster(
        master_id=uuid.uuid4(),
        legal_name="Source Sponsor",
        industry_sector="Tech"
    )
    target_master = SponsorMaster(
        master_id=uuid.uuid4(),
        legal_name="Target Sponsor",
        industry_sector="Energy"
    )
    brand = SponsorBrand(
        brand_id=uuid.uuid4(),
        master_id=source_master.master_id,
        brand_name="Brand to Transfer",
        default_hex_color="#112233"
    )
    
    async_session.add(source_master)
    async_session.add(target_master)
    async_session.add(brand)
    await async_session.commit()

    # Create a user
    from app.models.user import User
    user = User(
        user_id=uuid.uuid4(),
        google_id="google-trusted-123",
        email="trusted@example.com",
        display_name="Trusted User",
        role=UserRole.ADMIN # Direct approval
    )
    async_session.add(user)
    await async_session.commit()

    # 2. Prepare Request (Partial update: just master_id)
    # TDD EXPECTATION: This should now SUCCEED
    request = SponsorBrandEditRequest(
        brand_id=str(brand.brand_id),
        master_id=str(target_master.master_id),
        reason="Transferring brand to new owner"
    )

    # 3. Execute update
    result = await EditService.update_sponsor_brand_edit(async_session, user, request)
    
    # 4. Verify Transfer
    await async_session.refresh(brand)
    # TDD EXPECTATION: This might FAIL if EditService ignores master_id!
    assert brand.master_id == target_master.master_id
    
    # 5. Verify Audit Log
    from app.models.edit import EditHistory
    from sqlalchemy import select
    
    edit_stmt = select(EditHistory).where(EditHistory.edit_id == UUID(result.edit_id))
    edit = (await async_session.execute(edit_stmt)).scalar()
    
    # TDD EXPECTATION: master_id is likely missing from snapshots currently!
    assert "master_id" in edit.snapshot_before["brand"]
    assert str(edit.snapshot_before["brand"]["master_id"]) == str(source_master.master_id)
    assert str(edit.snapshot_after["brand"]["master_id"]) == str(target_master.master_id)
