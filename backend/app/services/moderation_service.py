from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional, Dict

from app.models.edit import EditHistory, EditStatus
from app.models.enums import EditAction, EditType
from app.models.user import User, UserRole
from app.models.team import TeamEra, TeamNode
from app.schemas.moderation import (
    PendingEditResponse,
    ReviewEditResponse,
    ModerationStatsResponse
)

class ModerationService:
    @staticmethod
    def _get_edit_type(edit: EditHistory) -> EditType:
        if edit.entity_type == "lineage_event":
            snap = edit.snapshot_after or {}
            if "proposed_merge" in snap:
                return EditType.MERGE
            if "proposed_split" in snap:
                return EditType.SPLIT
        if edit.entity_type in ["team_node", "team_era"]:
            if edit.action == EditAction.CREATE:
                return EditType.CREATE
            if edit.action == EditAction.UPDATE:
                return EditType.METADATA
        if edit.entity_type in ["sponsor_master", "sponsor_brand"]:
            return EditType.SPONSOR
        return EditType.METADATA

    @staticmethod
    def _derive_changes(edit: EditHistory) -> Dict:
        # For display in frontend
        # This creates a 'changes' dict similar to what frontend expects
        snap_after = edit.snapshot_after or {}
        snap_before = edit.snapshot_before or {}
        
        edit_type = ModerationService._get_edit_type(edit)
        
        if edit_type == EditType.CREATE:
            if "proposed_team" in snap_after:
                return {"create_team": snap_after["proposed_team"]}
            if "proposed_era" in snap_after:
                return {"create_era": snap_after["proposed_era"]}
            if "source_node" in snap_after: # Split/Merge creation logic? 
                # Actually Splits/Merges are CREATE lineage_events
                pass
        
        if edit_type == EditType.METADATA:
            # Diff logic
            changes = {}
            # Check Era fields
            era_after = snap_after.get('era', {})
            era_before = snap_before.get('era', {})
            for k, v in era_after.items():
                if v != era_before.get(k):
                    changes[k] = v
            
            # Check Node fields
            node_after = snap_after.get('node', {})
            node_before = snap_before.get('node', {})
            for k, v in node_after.items():
                if v != node_before.get(k):
                    changes[k] = v
            return changes
            
        if edit_type == EditType.MERGE:
            return snap_after.get("proposed_merge", {})
            
        if edit_type == EditType.SPLIT:
            return snap_after.get("proposed_split", {})
            
        if edit_type == EditType.SPONSOR:
            if "proposed_sponsor" in snap_after: return snap_after["proposed_sponsor"]
            if "proposed_brand" in snap_after: return snap_after["proposed_brand"]
            if "proposed_changes" in snap_after: return snap_after["proposed_changes"]
            
        return snap_after

    @staticmethod
    async def format_edit_for_review(
        session: AsyncSession,
        edit: EditHistory
    ) -> PendingEditResponse:
        user = await session.get(User, edit.user_id)
        
        edit_type = ModerationService._get_edit_type(edit)
        changes = ModerationService._derive_changes(edit)
        
        target_info = {}
        # Try to extract target info from snapshot (more reliable than DB fetch if entity doesn't exist yet)
        snap = edit.snapshot_after or {}
        
        if "era" in snap:
            target_info = {
                'type': 'era',
                'era_id': snap['era'].get('era_id'),
                'team_name': snap['era'].get('registered_name'),
                'year': snap['era'].get('season_year') or snap.get('node', {}).get('founding_year') # Fallback
            }
        elif "node" in snap:
            target_info = {
                'type': 'node',
                'node_id': snap['node'].get('node_id'),
                'founding_year': snap['node'].get('founding_year')
            }
        elif "proposed_team" in snap:
             target_info = {
                'type': 'new_team',
                'team_name': snap['proposed_team'].get('registered_name'),
                'founding_year': snap['proposed_team'].get('founding_year')
             }
        elif "proposed_era" in snap:
             target_info = {
                'type': 'new_era',
                'team_name': snap['proposed_era'].get('registered_name'),
                'year': snap['proposed_era'].get('season_year')
             }
        elif "proposed_sponsor" in snap:
             target_info = {
                 'type': 'new_sponsor',
                 'sponsor_name': snap['proposed_sponsor'].get('legal_name')
             }
        elif "proposed_brand" in snap:
             target_info = {
                 'type': 'new_brand',
                 'brand_name': snap['proposed_brand'].get('brand_name'),
                 'master_id': snap['proposed_brand'].get('master_id')
             }
        elif "master" in snap:
             target_info = {
                 'type': 'sponsor_master',
                 'sponsor_name': snap['master'].get('legal_name')
             }
        elif "brand" in snap:
             target_info = {
                 'type': 'sponsor_brand',
                 'brand_name': snap['brand'].get('brand_name')
             }
             
        return PendingEditResponse(
            edit_id=str(edit.edit_id),
            edit_type=edit_type.value,
            user_email=user.email if user else "Unknown",
            user_display_name=user.display_name if user else "Unknown",
            target_info=target_info,
            changes=changes,
            reason=edit.source_notes or "",
            created_at=edit.created_at
        )

    @staticmethod
    async def review_edit(
        session: AsyncSession,
        edit: EditHistory,
        admin: User,
        approved: bool,
        notes: Optional[str] = None
    ) -> ReviewEditResponse:
        import logging
        logger = logging.getLogger("moderation")
        
        edit_type = ModerationService._get_edit_type(edit)
        
        if approved:
            edit.status = EditStatus.APPROVED
            edit.reviewed_by = admin.user_id
            edit.reviewed_at = datetime.utcnow()
            edit.review_notes = notes
            try:
                # Use centralized apply logic from AuditLogService
                from app.services.audit_log_service import AuditLogService
                await AuditLogService.apply_edit(session, edit)
                
                user = await session.get(User, edit.user_id)
                if user:
                    user.approved_edits_count += 1
                    logger.info(f"Edit {edit.edit_id} approved. User {user.user_id} count: {user.approved_edits_count}")
                    if user.role == UserRole.EDITOR and user.approved_edits_count >= 5:
                        # Auto-promote logic? maybe.
                        pass
                
                message = "Edit approved and applied"
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to apply edit {edit.edit_id}: {str(e)}", exc_info=True)
                raise ValueError(f"Failed to apply edit: {str(e)}")
        else:
            edit.status = EditStatus.REJECTED
            edit.reviewed_by = admin.user_id
            edit.reviewed_at = datetime.utcnow()
            edit.review_notes = notes or "Edit rejected by moderator"
            message = "Edit rejected"
        
        await session.commit()
        return ReviewEditResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )


