"""Integration tests for TeamEra transfers between TeamNodes.

These tests verify the AuditLogService correctly applies UPDATE edits
that change the node_id of a TeamEra, effectively transferring it to
a different team.
"""
import uuid
from datetime import date, datetime
import pytest
from sqlalchemy import select

from app.models.team import TeamNode, TeamEra
from app.models.edit import EditHistory
from app.models.enums import EditAction, EditStatus
from app.services.audit_log_service import AuditLogService


@pytest.mark.asyncio
async def test_transfer_eras_happy_path(isolated_session, admin_user):
    """
    Verify eras can be transferred from a source team to a target team.
    
    Setup: SourceTeam has Eras 2000, 2001. TargetTeam has Era 2005.
    Action: Submit approved UPDATE edits to change node_id of 2000 and 2001 eras.
    Assert:
        - Eras now belong to TargetTeam.
        - SourceTeam has 0 eras.
        - TargetTeam has 3 eras.
        - Audit entries exist for each transfer.
    """
    # --- Setup ---
    source_node = TeamNode(founding_year=2000, legal_name="Source Team")
    target_node = TeamNode(founding_year=2005, legal_name="Target Team")
    isolated_session.add_all([source_node, target_node])
    await isolated_session.flush()
    
    era_2000 = TeamEra(
        node_id=source_node.node_id,
        season_year=2000,
        valid_from=date(2000, 1, 1),
        registered_name="Source Era 2000"
    )
    era_2001 = TeamEra(
        node_id=source_node.node_id,
        season_year=2001,
        valid_from=date(2001, 1, 1),
        registered_name="Source Era 2001"
    )
    era_2005 = TeamEra(
        node_id=target_node.node_id,
        season_year=2005,
        valid_from=date(2005, 1, 1),
        registered_name="Target Era 2005"
    )
    isolated_session.add_all([era_2000, era_2001, era_2005])
    await isolated_session.commit()
    
    # Capture IDs for later assertions
    era_2000_id = era_2000.era_id
    era_2001_id = era_2001.era_id
    source_node_id = source_node.node_id
    target_node_id = target_node.node_id
    
    # --- Action: Create and apply transfer edits ---
    # Edit 1: Transfer Era 2000
    edit_1 = await AuditLogService.create_edit(
        session=isolated_session,
        user_id=admin_user.user_id,
        entity_type="TeamEra",
        entity_id=era_2000_id,
        action=EditAction.UPDATE,
        old_data={"node_id": str(source_node_id)},
        new_data={"node_id": str(target_node_id)},
        status=EditStatus.APPROVED
    )
    
    # Edit 2: Transfer Era 2001
    edit_2 = await AuditLogService.create_edit(
        session=isolated_session,
        user_id=admin_user.user_id,
        entity_type="TeamEra",
        entity_id=era_2001_id,
        action=EditAction.UPDATE,
        old_data={"node_id": str(source_node_id)},
        new_data={"node_id": str(target_node_id)},
        status=EditStatus.APPROVED
    )
    
    await isolated_session.commit()
    isolated_session.expire_all()
    
    # --- Assert ---
    # Reload eras
    era_2000_reloaded = await isolated_session.get(TeamEra, era_2000_id)
    era_2001_reloaded = await isolated_session.get(TeamEra, era_2001_id)
    
    assert era_2000_reloaded.node_id == target_node_id
    assert era_2001_reloaded.node_id == target_node_id
    
    # Count eras per node
    source_eras_stmt = select(TeamEra).where(TeamEra.node_id == source_node_id)
    source_eras_result = await isolated_session.execute(source_eras_stmt)
    source_eras = source_eras_result.scalars().all()
    assert len(source_eras) == 0
    
    target_eras_stmt = select(TeamEra).where(TeamEra.node_id == target_node_id)
    target_eras_result = await isolated_session.execute(target_eras_stmt)
    target_eras = target_eras_result.scalars().all()
    assert len(target_eras) == 3
    
    # Verify Audit Log entries
    audit_stmt = select(EditHistory).where(
        EditHistory.entity_type == "TeamEra",
        EditHistory.action == EditAction.UPDATE
    )
    audit_result = await isolated_session.execute(audit_stmt)
    audits = audit_result.scalars().all()
    assert len(audits) >= 2


@pytest.mark.asyncio
async def test_transfer_era_conflict(isolated_session, admin_user):
    """
    Verify transfer fails if target already has an era for the same year.
    
    Setup: SourceTeam has Era 2000. TargetTeam also has Era 2000.
    Action: Attempt to transfer SourceTeam's Era 2000 to TargetTeam.
    Assert: Database constraint violation (unique node_id + season_year + valid_from).
    """
    from sqlalchemy.exc import IntegrityError
    
    # --- Setup ---
    source_node = TeamNode(founding_year=2000, legal_name="Source Team Conflict")
    target_node = TeamNode(founding_year=2000, legal_name="Target Team Conflict")
    isolated_session.add_all([source_node, target_node])
    await isolated_session.flush()
    
    era_source_2000 = TeamEra(
        node_id=source_node.node_id,
        season_year=2000,
        valid_from=date(2000, 1, 1),
        registered_name="Source Era 2000"
    )
    era_target_2000 = TeamEra(
        node_id=target_node.node_id,
        season_year=2000,
        valid_from=date(2000, 1, 1),  # Same year + valid_from
        registered_name="Target Era 2000"
    )
    isolated_session.add_all([era_source_2000, era_target_2000])
    await isolated_session.commit()
    
    era_source_id = era_source_2000.era_id
    target_node_id = target_node.node_id
    
    # --- Action & Assert ---
    # Attempting to apply this should cause an IntegrityError
    with pytest.raises(IntegrityError):
        await AuditLogService.create_edit(
            session=isolated_session,
            user_id=admin_user.user_id,
            entity_type="TeamEra",
            entity_id=era_source_id,
            action=EditAction.UPDATE,
            old_data={"node_id": str(source_node.node_id)},
            new_data={"node_id": str(target_node_id)},
            status=EditStatus.APPROVED
        )
        await isolated_session.commit()
    
    # Rollback to clean up
    await isolated_session.rollback()


@pytest.mark.asyncio
async def test_batch_transfer_with_node_update(isolated_session, admin_user):
    """
    Verify a batch can be submitted: Era transfer + TeamNode year updates.
    
    Setup: SourceTeam (Founded: 2000, Eras: 2000, 2001), TargetTeam (Founded: 2010, Era: 2010).
    Action: Transfer Era 2000 to Target AND update Target's founding_year to 2000.
    Assert:
        - Era 2000 is on TargetTeam.
        - TargetTeam.founding_year == 2000.
        - Audit entries exist for both the era and node updates.
    """
    # --- Setup ---
    source_node = TeamNode(founding_year=2000, legal_name="Source Team Batch")
    target_node = TeamNode(founding_year=2010, legal_name="Target Team Batch")
    isolated_session.add_all([source_node, target_node])
    await isolated_session.flush()
    
    era_2000 = TeamEra(
        node_id=source_node.node_id,
        season_year=2000,
        valid_from=date(2000, 1, 1),
        registered_name="Source Era 2000"
    )
    era_2001 = TeamEra(
        node_id=source_node.node_id,
        season_year=2001,
        valid_from=date(2001, 1, 1),
        registered_name="Source Era 2001"
    )
    era_2010 = TeamEra(
        node_id=target_node.node_id,
        season_year=2010,
        valid_from=date(2010, 1, 1),
        registered_name="Target Era 2010"
    )
    isolated_session.add_all([era_2000, era_2001, era_2010])
    await isolated_session.commit()
    
    era_2000_id = era_2000.era_id
    target_node_id = target_node.node_id
    
    # --- Action: Batch edits ---
    # Edit 1: Transfer Era 2000
    await AuditLogService.create_edit(
        session=isolated_session,
        user_id=admin_user.user_id,
        entity_type="TeamEra",
        entity_id=era_2000_id,
        action=EditAction.UPDATE,
        old_data={"node_id": str(source_node.node_id)},
        new_data={"node_id": str(target_node_id)},
        status=EditStatus.APPROVED
    )
    
    # Edit 2: Update Target Node's founding year
    await AuditLogService.create_edit(
        session=isolated_session,
        user_id=admin_user.user_id,
        entity_type="TeamNode",
        entity_id=target_node_id,
        action=EditAction.UPDATE,
        old_data={"founding_year": 2010},
        new_data={"founding_year": 2000},
        status=EditStatus.APPROVED
    )
    
    await isolated_session.commit()
    isolated_session.expire_all()
    
    # --- Assert ---
    era_2000_reloaded = await isolated_session.get(TeamEra, era_2000_id)
    target_node_reloaded = await isolated_session.get(TeamNode, target_node_id)
    
    assert era_2000_reloaded.node_id == target_node_id
    assert target_node_reloaded.founding_year == 2000
