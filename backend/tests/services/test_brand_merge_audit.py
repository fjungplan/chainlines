import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.models.enums import EditAction, EditStatus, UserRole
from app.services.edit_service import EditService
from app.schemas.sponsors import SponsorMergeRequest
from app.models.user import User

@pytest.mark.asyncio
async def test_create_sponsor_brand_merge_edit_trusted(async_session: AsyncSession):
    # Setup: Admin user, Source & Target brands
    admin = User(user_id=uuid4(), google_id="admin_google", email="admin@test.com", role=UserRole.ADMIN, approved_edits_count=0)
    source_id = uuid4()
    target_id = uuid4()
    master_id = uuid4()
    
    # Create master first
    master = SponsorMaster(master_id=master_id, legal_name="Test Master")
    
    # We'll need some mock brands in DB
    source = SponsorBrand(brand_id=source_id, brand_name="Source Brand", master_id=master_id, default_hex_color="#FF0000")
    target = SponsorBrand(brand_id=target_id, brand_name="Target Brand", master_id=master_id, default_hex_color="#00FF00")
    
    # We'll need some mock brands and user in DB
    async_session.add_all([admin, master, source, target])
    await async_session.flush()
    
    request = SponsorMergeRequest(target_brand_id=target_id, reason="Testing trusted merge")
    
    # Call the new method
    response = await EditService.create_sponsor_brand_merge_edit(async_session, admin, source_id, request)
    
    assert response.status == EditStatus.APPROVED
    assert "Merge created successfully" in response.message
    
    # Verify DB state: Source should be gone
    assert await async_session.get(SponsorBrand, source_id) is None
    
    # Verify Audit Record
    from app.models.edit import EditHistory
    from sqlalchemy import select
    stmt = select(EditHistory).where(EditHistory.entity_id == source_id)
    edit = (await async_session.execute(stmt)).scalar_one_or_none()
    assert edit is not None
    assert edit.action == EditAction.DELETE
    assert edit.snapshot_after["merged_into"] == str(target_id)

@pytest.mark.asyncio
async def test_create_sponsor_brand_merge_edit_regular_editor(async_session: AsyncSession):
    # Setup: Regular Editor
    editor = User(user_id=uuid4(), google_id="editor_google", email="editor@test.com", role=UserRole.EDITOR, approved_edits_count=0)
    source_id = uuid4()
    target_id = uuid4()
    master_id = uuid4()
    
    master = SponsorMaster(master_id=master_id, legal_name="Test Master")
    source = SponsorBrand(brand_id=source_id, brand_name="Source Brand", master_id=master_id, default_hex_color="#FF0000")
    target = SponsorBrand(brand_id=target_id, brand_name="Target Brand", master_id=master_id, default_hex_color="#00FF00")
    async_session.add_all([editor, master, source, target])
    await async_session.flush()
    
    request = SponsorMergeRequest(target_brand_id=target_id, reason="Testing pending merge")
    
    # Call method
    response = await EditService.create_sponsor_brand_merge_edit(async_session, editor, source_id, request)
    
    assert response.status == EditStatus.PENDING
    assert "Merge submitted for moderation" in response.message
    
    # Verify DB state: Source should still exist
    assert await async_session.get(SponsorBrand, source_id) is not None
    
    # Verify Audit Record
    from app.models.edit import EditHistory
    from sqlalchemy import select
    stmt = select(EditHistory).where(EditHistory.entity_id == source_id)
    edit = (await async_session.execute(stmt)).scalar_one_or_none()
    assert edit is not None
    assert edit.status == EditStatus.PENDING
    assert edit.snapshot_before["brand"]["brand_name"] == "Source Brand"
    assert edit.snapshot_after["proposed_merge"]["target_brand_id"] == str(target_id)
