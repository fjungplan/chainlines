"""Integration tests for SponsorBrand transfers between SponsorMasters.

These tests verify the AuditLogService correctly applies UPDATE edits
that change the master_id of a SponsorBrand, effectively transferring it to
a different sponsor master.
"""
import uuid
from datetime import datetime
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.sponsor import SponsorMaster, SponsorBrand
from app.models.edit import EditHistory
from app.models.enums import EditAction, EditStatus
from app.services.audit_log_service import AuditLogService


@pytest.mark.asyncio
async def test_transfer_brand_happy_path(isolated_session, admin_user):
    """
    Verify a brand can be transferred from one sponsor master to another.
    
    Setup: SponsorA has Brand1. SponsorB has Brand2.
    Action: Submit approved UPDATE edit to change Brand1's master_id to SponsorB.
    Assert:
        - Brand1 now belongs to SponsorB.
        - SponsorA has 0 brands.
        - SponsorB has 2 brands.
        - Audit entry exists for the transfer.
    """
    # --- Setup ---
    sponsor_a = SponsorMaster(legal_name="Sponsor A Test")
    sponsor_b = SponsorMaster(legal_name="Sponsor B Test")
    isolated_session.add_all([sponsor_a, sponsor_b])
    await isolated_session.flush()
    
    brand_1 = SponsorBrand(
        master_id=sponsor_a.master_id,
        brand_name="Brand 1",
        default_hex_color="#ff0000"
    )
    brand_2 = SponsorBrand(
        master_id=sponsor_b.master_id,
        brand_name="Brand 2",
        default_hex_color="#00ff00"
    )
    isolated_session.add_all([brand_1, brand_2])
    await isolated_session.commit()
    
    # Capture IDs
    brand_1_id = brand_1.brand_id
    sponsor_a_id = sponsor_a.master_id
    sponsor_b_id = sponsor_b.master_id
    
    # --- Action: Create and apply transfer edit ---
    await AuditLogService.create_edit(
        session=isolated_session,
        user_id=admin_user.user_id,
        entity_type="SponsorBrand",
        entity_id=brand_1_id,
        action=EditAction.UPDATE,
        old_data={"master_id": str(sponsor_a_id)},
        new_data={"master_id": str(sponsor_b_id)},
        status=EditStatus.APPROVED
    )
    
    await isolated_session.commit()
    isolated_session.expire_all()
    
    # --- Assert ---
    # Reload brand
    brand_1_reloaded = await isolated_session.get(SponsorBrand, brand_1_id)
    assert brand_1_reloaded.master_id == sponsor_b_id
    
    # Count brands per sponsor
    sponsor_a_brands_stmt = select(SponsorBrand).where(SponsorBrand.master_id == sponsor_a_id)
    sponsor_a_brands = (await isolated_session.execute(sponsor_a_brands_stmt)).scalars().all()
    assert len(sponsor_a_brands) == 0
    
    sponsor_b_brands_stmt = select(SponsorBrand).where(SponsorBrand.master_id == sponsor_b_id)
    sponsor_b_brands = (await isolated_session.execute(sponsor_b_brands_stmt)).scalars().all()
    assert len(sponsor_b_brands) == 2
    
    # Verify Audit Log entry
    audit_stmt = select(EditHistory).where(
        EditHistory.entity_type == "SponsorBrand",
        EditHistory.entity_id == brand_1_id,
        EditHistory.action == EditAction.UPDATE
    )
    audits = (await isolated_session.execute(audit_stmt)).scalars().all()
    assert len(audits) >= 1
    assert audits[0].status == EditStatus.APPROVED


@pytest.mark.asyncio
async def test_transfer_brand_pending_for_editor(isolated_session, test_user_new):
    """
    Verify brand transfer creates PENDING status for regular EDITOR users.
    
    Setup: SponsorA has Brand1.
    Action: Submit UPDATE edit as EDITOR (status=PENDING).
    Assert:
        - Brand1 still belongs to SponsorA (no immediate change).
        - Audit entry exists with PENDING status.
    """
    # --- Setup ---
    sponsor_a = SponsorMaster(legal_name="Sponsor A Pending Test")
    sponsor_b = SponsorMaster(legal_name="Sponsor B Pending Test")
    isolated_session.add_all([sponsor_a, sponsor_b])
    await isolated_session.flush()
    
    brand_1 = SponsorBrand(
        master_id=sponsor_a.master_id,
        brand_name="Brand Pending",
        default_hex_color="#0000ff"
    )
    isolated_session.add(brand_1)
    await isolated_session.commit()
    
    brand_1_id = brand_1.brand_id
    sponsor_a_id = sponsor_a.master_id
    sponsor_b_id = sponsor_b.master_id
    
    # --- Action: Create PENDING transfer edit ---
    await AuditLogService.create_edit(
        session=isolated_session,
        user_id=test_user_new.user_id,
        entity_type="SponsorBrand",
        entity_id=brand_1_id,
        action=EditAction.UPDATE,
        old_data={"master_id": str(sponsor_a_id)},
        new_data={"master_id": str(sponsor_b_id)},
        status=EditStatus.PENDING  # EDITOR: pending
    )
    
    await isolated_session.commit()
    isolated_session.expire_all()
    
    # --- Assert ---
    # Brand should NOT have moved yet
    brand_1_reloaded = await isolated_session.get(SponsorBrand, brand_1_id)
    assert brand_1_reloaded.master_id == sponsor_a_id
    
    # Verify Audit Log entry with PENDING
    audit_stmt = select(EditHistory).where(
        EditHistory.entity_type == "SponsorBrand",
        EditHistory.entity_id == brand_1_id,
        EditHistory.status == EditStatus.PENDING
    )
    audits = (await isolated_session.execute(audit_stmt)).scalars().all()
    assert len(audits) >= 1


@pytest.mark.asyncio
async def test_transfer_brand_conflict(isolated_session, admin_user):
    """
    Verify transfer fails if target sponsor already has a brand with the same name.
    
    Setup: SponsorA has "Shared Brand". SponsorB also has "Shared Brand".
    Action: Attempt to transfer SponsorA's "Shared Brand" to SponsorB.
    Assert: IntegrityError due to unique constraint (master_id, brand_name).
    """
    # --- Setup ---
    sponsor_a = SponsorMaster(legal_name="Sponsor A Conflict")
    sponsor_b = SponsorMaster(legal_name="Sponsor B Conflict")
    isolated_session.add_all([sponsor_a, sponsor_b])
    await isolated_session.flush()
    
    brand_a = SponsorBrand(
        master_id=sponsor_a.master_id,
        brand_name="Shared Brand",
        default_hex_color="#111111"
    )
    brand_b = SponsorBrand(
        master_id=sponsor_b.master_id,
        brand_name="Shared Brand",  # Same name!
        default_hex_color="#222222"
    )
    isolated_session.add_all([brand_a, brand_b])
    await isolated_session.commit()
    
    brand_a_id = brand_a.brand_id
    sponsor_b_id = sponsor_b.master_id
    
    # --- Action & Assert ---
    with pytest.raises(IntegrityError):
        await AuditLogService.create_edit(
            session=isolated_session,
            user_id=admin_user.user_id,
            entity_type="SponsorBrand",
            entity_id=brand_a_id,
            action=EditAction.UPDATE,
            old_data={"master_id": str(sponsor_a.master_id)},
            new_data={"master_id": str(sponsor_b_id)},
            status=EditStatus.APPROVED
        )
        await isolated_session.commit()
    
    await isolated_session.rollback()


@pytest.mark.asyncio
async def test_transfer_multiple_brands(isolated_session, admin_user):
    """
    Verify multiple brands can be transferred in a batch.
    
    Setup: SponsorA has Brand1, Brand2, Brand3. SponsorB has none.
    Action: Transfer Brand1 and Brand2 to SponsorB.
    Assert:
        - Brand1 and Brand2 belong to SponsorB.
        - Brand3 remains with SponsorA.
    """
    # --- Setup ---
    sponsor_a = SponsorMaster(legal_name="Sponsor A Batch")
    sponsor_b = SponsorMaster(legal_name="Sponsor B Batch")
    isolated_session.add_all([sponsor_a, sponsor_b])
    await isolated_session.flush()
    
    brand_1 = SponsorBrand(master_id=sponsor_a.master_id, brand_name="Brand Batch 1", default_hex_color="#aaaaaa")
    brand_2 = SponsorBrand(master_id=sponsor_a.master_id, brand_name="Brand Batch 2", default_hex_color="#bbbbbb")
    brand_3 = SponsorBrand(master_id=sponsor_a.master_id, brand_name="Brand Batch 3", default_hex_color="#cccccc")
    isolated_session.add_all([brand_1, brand_2, brand_3])
    await isolated_session.commit()
    
    brand_1_id = brand_1.brand_id
    brand_2_id = brand_2.brand_id
    brand_3_id = brand_3.brand_id
    sponsor_a_id = sponsor_a.master_id
    sponsor_b_id = sponsor_b.master_id
    
    # --- Action: Transfer Brand1 and Brand2 ---
    await AuditLogService.create_edit(
        session=isolated_session,
        user_id=admin_user.user_id,
        entity_type="SponsorBrand",
        entity_id=brand_1_id,
        action=EditAction.UPDATE,
        old_data={"master_id": str(sponsor_a_id)},
        new_data={"master_id": str(sponsor_b_id)},
        status=EditStatus.APPROVED
    )
    
    await AuditLogService.create_edit(
        session=isolated_session,
        user_id=admin_user.user_id,
        entity_type="SponsorBrand",
        entity_id=brand_2_id,
        action=EditAction.UPDATE,
        old_data={"master_id": str(sponsor_a_id)},
        new_data={"master_id": str(sponsor_b_id)},
        status=EditStatus.APPROVED
    )
    
    await isolated_session.commit()
    isolated_session.expire_all()
    
    # --- Assert ---
    brand_1_reloaded = await isolated_session.get(SponsorBrand, brand_1_id)
    brand_2_reloaded = await isolated_session.get(SponsorBrand, brand_2_id)
    brand_3_reloaded = await isolated_session.get(SponsorBrand, brand_3_id)
    
    assert brand_1_reloaded.master_id == sponsor_b_id
    assert brand_2_reloaded.master_id == sponsor_b_id
    assert brand_3_reloaded.master_id == sponsor_a_id  # Unchanged
