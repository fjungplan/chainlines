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
                if edit_type == EditType.METADATA:
                    await ModerationService._apply_metadata_edit(session, edit)
                elif edit_type == EditType.CREATE:
                    await ModerationService._apply_create_edit(session, edit)
                elif edit_type == EditType.MERGE:
                    await ModerationService._apply_merge_edit(session, edit)
                elif edit_type == EditType.SPLIT:
                    await ModerationService._apply_split_edit(session, edit)
                
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

    @staticmethod
    async def _apply_metadata_edit(session: AsyncSession, edit: EditHistory):
        # Apply proposed changes from snapshot_after
        snap = edit.snapshot_after or {}
        
        era = None
        node = None
        
        # Determine target using ID in snapshot or entity_id
        # Actually edit.entity_id is the target ID.
        
        if edit.entity_type == "team_era":
             era = await session.get(TeamEra, edit.entity_id)
             if era:
                 proposed = snap.get('era', {})
                 if 'registered_name' in proposed: era.registered_name = proposed['registered_name']
                 if 'uci_code' in proposed: era.uci_code = proposed['uci_code']
                 if 'country_code' in proposed: era.country_code = proposed['country_code']
                 if 'tier_level' in proposed: era.tier_level = proposed['tier_level']
                 if 'valid_from' in proposed: era.valid_from = datetime.fromisoformat(proposed['valid_from']).date() if proposed['valid_from'] else None
                 
                 era.updated_at = datetime.utcnow()
                 
             # Check if node needs update too
             if 'node' in snap:
                 n_prop = snap.get('node', {})
                 node = await session.get(TeamNode, era.node_id if era else edit.entity_id) # Fallback?
                 if node:
                     if 'founding_year' in n_prop: node.founding_year = n_prop['founding_year']
                     if 'dissolution_year' in n_prop: node.dissolution_year = n_prop['dissolution_year']
                     node.updated_at = datetime.utcnow()

        elif edit.entity_type == "team_node":
             node = await session.get(TeamNode, edit.entity_id)
             if node:
                 n_prop = snap.get('node', {})
                 if 'legal_name' in n_prop: node.legal_name = n_prop['legal_name']
                 if 'display_name' in n_prop: node.display_name = n_prop['display_name']
                 if 'founding_year' in n_prop: node.founding_year = n_prop['founding_year']
                 if 'dissolution_year' in n_prop: node.dissolution_year = n_prop['dissolution_year']
                 if 'is_protected' in n_prop: node.is_protected = n_prop['is_protected']
                 node.updated_at = datetime.utcnow()
        
        await session.flush() # Commit handled by caller

    @staticmethod
    async def _apply_create_edit(session: AsyncSession, edit: EditHistory):
        from app.services.team_service import TeamService 
        from app.schemas.team import TeamEraCreate
        
        snap = edit.snapshot_after or {}
        
        if "proposed_team" in snap:
            # Create Team Node + Era
            p = snap["proposed_team"]
            node = TeamNode(
                founding_year=p['founding_year'],
                legal_name=p['legal_name'],
                display_name=p['registered_name'],
                created_by=edit.user_id
            )
            session.add(node)
            await session.flush()
            
            era = TeamEra(
                node_id=node.node_id,
                season_year=p['founding_year'],
                valid_from=date(p['founding_year'], 1, 1),
                registered_name=p['registered_name'],
                uci_code=p.get('uci_code'),
                tier_level=p['tier_level'],
                source_origin=f"user_{edit.user_id}",
                is_manual_override=True,
                created_by=edit.user_id
            )
            session.add(era)
        
        elif "proposed_era" in snap:
            # Create Era only
            p = snap["proposed_era"]
            # We need node_id. Where is it?
            # CreateEraEditRequest has node_id. But it's not in snapshot explicitly?
            # It should be! 
            # In EditService.create_era_edit, we didn't put node_id in snapshot_after!
            # We need to fix EditService to include node_id in snapshot if we want to apply it later!
            # Or use edit.target_node_id? But EditHistory doesn't have target_node_id column?
            # It has `entity_id` (which is a placeholder UUID for pending create).
            # So `entity_id` is useless for finding the PARENT node.
            # We MUST have `node_id` in `proposed_era` snapshot.
            
            # Assuming I will fix EditService to include node_id:
            node_id_str = p.get('node_id')
            if not node_id_str:
                 # Fallback: maybe it's in source_notes or we can't apply?
                 raise ValueError("Missing node_id in snapshot for era creation")
                 
            node_id = UUID(node_id_str)
            
            era_create = TeamEraCreate(
                season_year=p['season_year'],
                registered_name=p['registered_name'],
                valid_from=date(p['season_year'], 1, 1),
                uci_code=p.get('uci_code'),
                country_code=p.get('country_code'),
                tier_level=p.get('tier_level'),
                source_origin=f"user_{edit.user_id}",
                is_manual_override=True
            )
            await TeamService.create_era(session, node_id, era_create, edit.user_id)


    @staticmethod
    async def _apply_merge_edit(session: AsyncSession, edit: EditHistory):
        from app.services.edit_service import EditService
        from app.schemas.edits import MergeEventRequest
        
        snap = edit.snapshot_after or {}
        proposed = snap.get("proposed_merge", {})
        
        # We need to reconstruct the request
        # source_nodes in snapshot_before or snapshot_after['source_nodes']
        # We need the IDs.
        snap_before = edit.snapshot_before or {}
        source_nodes_data = snap_before.get("source_nodes", [])
        source_node_ids = [n['node_id'] for n in source_nodes_data]
        
        request = MergeEventRequest(
            source_node_ids=source_node_ids,
            merge_year=proposed.get('merge_year'),
            new_team_name=proposed.get('new_team_name'),
            new_team_tier=proposed.get('new_team_tier'),
            reason=edit.source_notes
        )
        
        # We need to validate source nodes again as EditService._apply_merge expects objects
        # Fetch them
        validated_source_nodes = []
        for nid in source_node_ids:
             n = await session.get(TeamNode, UUID(nid))
             if n: validated_source_nodes.append(n)
        
        if len(validated_source_nodes) != len(source_node_ids):
            raise ValueError("Some source nodes for merge no longer exist")
            
        await EditService._apply_merge(session, request, await session.get(User, edit.user_id), validated_source_nodes)

    @staticmethod
    async def _apply_split_edit(session: AsyncSession, edit: EditHistory):
        from app.services.edit_service import EditService
        from app.schemas.edits import SplitEventRequest, NewTeamInfo
        
        snap = edit.snapshot_after or {}
        proposed = snap.get("proposed_split", {})
        
        request = SplitEventRequest(
            source_node_id=str(edit.entity_id), # Split is on the source node (stored as entity_id)
            split_year=proposed.get('split_year'),
            new_teams=[
                NewTeamInfo(name=t['name'], tier=t['tier'])
                for t in proposed.get('new_teams', [])
            ],
            reason=edit.source_notes
        )
        
        source_node = await session.get(TeamNode, edit.entity_id)
        if not source_node:
            raise ValueError("Source node for split not found")
            
        await EditService._apply_split(session, request, await session.get(User, edit.user_id), source_node)


    @staticmethod
    async def get_stats(session: AsyncSession) -> ModerationStatsResponse:
        pending_stmt = select(func.count(EditHistory.edit_id)).where(
            EditHistory.status == EditStatus.PENDING
        )
        pending_result = await session.execute(pending_stmt)
        pending_count = pending_result.scalar()
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        approved_today_stmt = select(func.count(EditHistory.edit_id)).where(
            and_(
                EditHistory.status == EditStatus.APPROVED,
                EditHistory.reviewed_at >= today_start
            )
        )
        approved_result = await session.execute(approved_today_stmt)
        approved_today = approved_result.scalar()
        rejected_today_stmt = select(func.count(EditHistory.edit_id)).where(
            and_(
                EditHistory.status == EditStatus.REJECTED,
                EditHistory.reviewed_at >= today_start
            )
        )
        rejected_result = await session.execute(rejected_today_stmt)
        rejected_today = rejected_result.scalar()
        pending_by_type_stmt = select(EditHistory).where(EditHistory.status == EditStatus.PENDING)
        result = await session.execute(pending_by_type_stmt)
        all_pending = result.scalars().all()
        
        pending_by_type = {}
        for edit in all_pending:
            etype = ModerationService._get_edit_type(edit).value
            pending_by_type[etype] = pending_by_type.get(etype, 0) + 1
        return ModerationStatsResponse(
            pending_count=pending_count,
            approved_today=approved_today,
            rejected_today=rejected_today,
            pending_by_type=pending_by_type
        )
