"""
Service layer for Audit Log functionality.

Provides methods for:
- Resolving entity UUIDs to human-readable names
- Formatting edits for review with resolved names
- Permission checking for moderation actions
- Revert/re-apply logic (to be implemented in later steps)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from app.models.team import TeamNode, TeamEra
from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.models.lineage import LineageEvent
from app.models.user import User
from app.models.enums import EditAction, EditStatus
from app.models.edit import EditHistory



class AuditLogService:
    """
    Service for audit log operations.
    
    Handles entity name resolution, edit formatting, and moderation actions.
    """
    
    @staticmethod
    @staticmethod
    def _unwrap_snapshot(data: Optional[Dict]) -> Optional[Dict]:
        """
        Unwrap nested snapshot data if present.
        
        Handles cases where scrapers wrap payload in entity keys like:
        { "node": { ... } } or { "lineage_event": { ... } }
        """
        if not data:
            return None
            
        unwrap_keys = ["node", "era", "master", "brand", "link", "event", "lineage_event"]
        flattened = data.copy()

        for key in unwrap_keys:
            if key in data and isinstance(data[key], dict):
                # Found a wrapper key, return its content
                return data[key]
                
        return flattened

    @staticmethod
    async def resolve_entity_name(
        session: AsyncSession,
        entity_type: str,
        entity_id: Union[UUID, str],
        snapshot: Optional[Dict] = None
    ) -> str:
        """
        Resolve an entity UUID to a human-readable name.
        
        Args:
            session: Database session
            entity_type: Type of entity (team_node, team_era, sponsor_master, etc.)
            entity_id: UUID of the entity
            snapshot: Optional snapshot data (used as fallback for PENDING CREATEs)
            
        Returns:
            Human-readable name string, or "Unknown" if not found
        """
        # Ensure entity_id is a UUID
        if isinstance(entity_id, str):
            try:
                entity_id = UUID(entity_id)
            except ValueError:
                return str(entity_id)
        
        # Unwrap snapshot once here so sub-methods don't have to
        unwrapped_snapshot = AuditLogService._unwrap_snapshot(snapshot)
        
        try:
            etype = entity_type.lower()
            
            if etype in ("team", "team_node", "teamnode"):
                return await AuditLogService._resolve_team_node(session, entity_id, unwrapped_snapshot)
            elif etype in ("era", "team_era", "teamera"):
                return await AuditLogService._resolve_team_era(session, entity_id, unwrapped_snapshot)
            elif etype in ("sponsor", "sponsor_master", "sponsormaster"):
                return await AuditLogService._resolve_sponsor_master(session, entity_id, unwrapped_snapshot)
            elif etype in ("brand", "sponsor_brand", "sponsorbrand"):
                return await AuditLogService._resolve_sponsor_brand(session, entity_id, unwrapped_snapshot)
            elif etype in ("link", "team_sponsor_link", "teamsponsorlink"):
                return await AuditLogService._resolve_sponsor_link(session, entity_id, unwrapped_snapshot)
            elif etype in ("lineage", "lineage_event", "lineageevent"):
                return await AuditLogService._resolve_lineage_event(session, entity_id, unwrapped_snapshot)
            else:
                # Unknown entity type - return ID as string
                return str(entity_id)
        except Exception:
            return "Unknown"
    
    @staticmethod
    async def _resolve_team_node(session: AsyncSession, node_id: UUID, snapshot: Optional[Dict] = None) -> str:
        """Resolve TeamNode to display_name or legal_name."""
        node = await session.get(TeamNode, node_id)
        if node:
            return node.display_name or node.legal_name
            
        # Fallback to snapshot
        if snapshot:
            return snapshot.get("display_name") or snapshot.get("legal_name") or "Unknown"
            
        return "Unknown"
    
    @staticmethod
    async def _resolve_team_era(session: AsyncSession, era_id: UUID, snapshot: Optional[Dict] = None) -> str:
        """Resolve TeamEra to 'registered_name (year)'."""
        era = await session.get(TeamEra, era_id)
        if era:
            return f"{era.registered_name} ({era.season_year})"
            
        # Fallback to snapshot
        if snapshot:
            name = snapshot.get("registered_name") or "Unknown"
            year = snapshot.get("season_year") or "?"
            return f"{name} ({year})"
            
        return "Unknown"
    
    @staticmethod
    async def _resolve_sponsor_master(session: AsyncSession, master_id: UUID, snapshot: Optional[Dict] = None) -> str:
        """Resolve SponsorMaster to display_name or legal_name."""
        master = await session.get(SponsorMaster, master_id)
        if master:
            return master.display_name or master.legal_name
            
        # Fallback to snapshot
        if snapshot:
            return snapshot.get("display_name") or snapshot.get("legal_name") or "Unknown"
            
        return "Unknown"
    
    @staticmethod
    async def _resolve_sponsor_brand(session: AsyncSession, brand_id: UUID, snapshot: Optional[Dict] = None) -> str:
        """Resolve SponsorBrand to 'brand_name (master_name)'."""
        brand = await session.get(SponsorBrand, brand_id)
        if brand:
            # Get parent master name
            master = await session.get(SponsorMaster, brand.master_id)
            master_name = (master.display_name or master.legal_name) if master else "Unknown"
            return f"{brand.brand_name} ({master_name})"
            
        # Fallback to snapshot
        if snapshot:
            brand_name = snapshot.get("brand_name") or "Unknown"
            # We assume we can't easily resolve master name from snapshot ID here without extra query
            # but usually brand name is enough for identification
            return brand_name
            
        return "Unknown"
    
    @staticmethod
    async def _resolve_sponsor_link(session: AsyncSession, link_id: UUID, snapshot: Optional[Dict] = None) -> str:
        """Resolve TeamSponsorLink to 'brand → era (year)'."""
        link = await session.get(TeamSponsorLink, link_id)
        if link:
            # Get brand and era names
            brand = await session.get(SponsorBrand, link.brand_id)
            era = await session.get(TeamEra, link.era_id)
            
            brand_name = brand.brand_name if brand else "Unknown Brand"
            era_name = era.registered_name if era else "Unknown Era"
            year = era.season_year if era else "?"
            return f"{brand_name} → {era_name} ({year})"
            
        # Fallback: snapshot for link creation usually contains brand_id/era_id
        # We could resolve them, but it's complex. Return "New Sponsorship" or similar?
        return "Sponsorship Link"
    
    @staticmethod
    async def _resolve_lineage_event(session: AsyncSession, event_id: UUID, snapshot: Optional[Dict] = None) -> str:
        """Resolve LineageEvent to 'predecessor → successor (year)'."""
        # Try DB first
        event = await session.get(LineageEvent, event_id)
        
        pred_id = None
        succ_id = None
        year = "?"
        pred_name = "Unknown Team"
        succ_name = "Unknown Team"
        
        if event:
            pred_id = event.predecessor_node_id
            succ_id = event.successor_node_id
            year = event.event_year
        elif snapshot:
            # Fallback to snapshot for PENDING CREATE
            # Snapshot keys for lineage create might be "predecessor_id", "successor_id"
            # OR "source_node", "target_team" (names directly) as seen in screenshots
            try:
                # 1. Try ID based resolution (support multiple key variations)
                p_str = snapshot.get("predecessor_id") or snapshot.get("predecessor_node_id")
                s_str = snapshot.get("successor_id") or snapshot.get("successor_node_id")
                if p_str: pred_id = UUID(p_str)
                if s_str: succ_id = UUID(s_str)
                
                # 2. Try Name based resolution (if IDs missing)
                if not pred_id and "source_node" in snapshot:
                    pred_name = snapshot["source_node"]
                if not succ_id and "target_team" in snapshot:
                    succ_name = snapshot["target_team"]
                    
                year = snapshot.get("event_year") or snapshot.get("year") or "?"
            except ValueError:
                pass
        
        if not pred_id and not succ_id and not event and pred_name == "Unknown Team" and succ_name == "Unknown Team":
            return "Unknown"

        # Resolve Node Names from IDs if we have them
        if pred_id:
            predecessor = await session.get(TeamNode, pred_id)
            if predecessor:
                pred_name = predecessor.display_name or predecessor.legal_name
        
        if succ_id:
            successor = await session.get(TeamNode, succ_id)
            if successor:
                succ_name = successor.display_name or successor.legal_name
        
        return f"{pred_name} → {succ_name} ({year})"
    
    # =========================================================================
    # Permission Checking
    # =========================================================================
    
    @staticmethod
    def can_moderate_edit(current_user: User, edit_submitter: User) -> bool:
        """
        Check if the current user can moderate an edit submitted by another user.
        
        Permission rules:
        - Admins can moderate any edit
        - Moderators can moderate edits by editors and other moderators
        - Moderators CANNOT moderate edits submitted by admins
        - Editors cannot moderate any edits
        
        Args:
            current_user: The user attempting to moderate
            edit_submitter: The user who submitted the edit
            
        Returns:
            True if moderation is allowed, False otherwise
        """
        from app.models.enums import UserRole
        
        # Must be at least a moderator to moderate anything
        if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN):
            return False
        
        # Admins can moderate anything
        if current_user.role == UserRole.ADMIN:
            return True
        
        # Moderators cannot touch admin-submitted edits
        if edit_submitter.role == UserRole.ADMIN:
            return False
        
        # Moderators can moderate everything else
        return True
    
    # =========================================================================
    # Chronology Checking
    # =========================================================================
    
    @staticmethod
    async def is_most_recent_approved(
        session: AsyncSession,
        edit: "EditHistory"
    ) -> bool:
        """
        Check if this edit is the most recent APPROVED edit for its entity.
        
        Used to determine if a revert is allowed - only the most recent
        approved edit can be reverted.
        
        Args:
            session: Database session
            edit: The edit to check
            
        Returns:
            True if this is the most recent approved edit for the entity
        """
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus
        
        # If this edit is not approved, it cannot be the "most recent approved"
        if edit.status != EditStatus.APPROVED:
            return False
        
        # Find any approved edits for the same entity that are newer
        stmt = select(EditHistory).where(
            EditHistory.entity_type == edit.entity_type,
            EditHistory.entity_id == edit.entity_id,
            EditHistory.status == EditStatus.APPROVED,
            EditHistory.reviewed_at > edit.reviewed_at,
            EditHistory.edit_id != edit.edit_id
        )
        result = await session.execute(stmt)
        newer_approved = result.scalars().first()
        
        # If there are no newer approved edits, this is the most recent
        return newer_approved is None
    
    # =========================================================================
    # Revert Operations
    # =========================================================================
    
    @staticmethod
    async def revert_edit(
        session: AsyncSession,
        edit: "EditHistory",
        reverter: User,
        notes: Optional[str] = None
    ) -> "RevertResponse":
        """
        Revert an approved edit to restore the entity to its previous state.
        
        Requirements:
        - Edit must be APPROVED status
        - Edit must be the most recent approved edit for the entity
        - Reverter must have permission to moderate edits from the submitter
        
        Args:
            session: Database session
            edit: The edit to revert
            reverter: The user performing the revert
            notes: Optional notes explaining the revert
            
        Returns:
            RevertResponse with status and message
            
        Raises:
            ValueError: If edit is not approved or not most recent
            PermissionError: If reverter lacks permission
        """
        from app.models.enums import EditStatus
        from app.schemas.audit_log import ReviewEditResponse
        
        # Validate edit is approved
        if edit.status != EditStatus.APPROVED:
            raise ValueError("Cannot revert: edit is not approved")
        
        # Check chronology - must be most recent approved
        is_most_recent = await AuditLogService.is_most_recent_approved(session, edit)
        if not is_most_recent:
            raise ValueError("Cannot revert: this edit is not the most recent approved edit for this entity")
        
        # Get the edit submitter for permission check
        submitter = await session.get(User, edit.user_id)
        if submitter and not AuditLogService.can_moderate_edit(reverter, submitter):
            raise PermissionError("You do not have permission to revert this edit")
        
        # Perform the revert - update edit status
        edit.status = EditStatus.REVERTED
        edit.reverted_by = reverter.user_id
        edit.reverted_at = datetime.utcnow()
        
        if notes:
            # Append revert notes to existing review notes
            if edit.review_notes:
                edit.review_notes = f"{edit.review_notes}\n\nReverted: {notes}"
            else:
                edit.review_notes = f"Reverted: {notes}"
        
        # CRITICAL: Rollback the data to previous state
        # If the edit was CREATE, we need to DELETE
        # If the edit was UPDATE, we need to restore snapshot_before
        # If the edit was DELETE, we need to recreate from snapshot_before
        if edit.action == EditAction.CREATE:
            # Revert CREATE by deleting the entity
            await AuditLogService._apply_delete(session, edit)
        elif edit.action == EditAction.UPDATE:
            # Revert UPDATE by applying the before snapshot
            # We reuse _apply_update to handle entity loading, unwrapping, and field setting
            if edit.snapshot_before:
                await AuditLogService._apply_update(session, edit, override_data=edit.snapshot_before)
        elif edit.action == EditAction.DELETE:
            # Revert DELETE by recreating the entity from snapshot_before
            # This is complex and edge-case, may need to be implemented later
            # For now, log a warning
            import logging
            logging.warning(f"Reverting DELETE action not fully implemented for edit {edit.edit_id}")
        
        await session.commit()
        
        return ReviewEditResponse(
            edit_id=str(edit.edit_id),
            status="REVERTED",
            message="Edit reverted successfully"
        )
    
    @staticmethod
    async def reapply_edit(
        session: AsyncSession,
        edit: "EditHistory",
        approver: User,
        notes: Optional[str] = None
    ) -> "ReviewEditResponse":
        """
        Re-apply a reverted or rejected edit.
        
        Requirements:
        - Edit must be REVERTED or REJECTED status
        - No newer approved edits for the same entity can exist
        - Approver must have permission to moderate edits from the submitter
        
        Args:
            session: Database session
            edit: The edit to re-apply
            approver: The user performing the re-apply
            notes: Optional notes explaining the re-apply
            
        Returns:
            ReviewEditResponse with status and message
            
        Raises:
            ValueError: If edit status is not reverted/rejected or newer approved exists
            PermissionError: If approver lacks permission
        """
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus
        from app.schemas.audit_log import ReviewEditResponse
        
        # Validate edit is reverted or rejected
        if edit.status not in (EditStatus.REVERTED, EditStatus.REJECTED):
            raise ValueError("Cannot re-apply: edit is not reverted or rejected")
        
        # Check for newer approved edits for the same entity
        has_newer_approved = await AuditLogService._has_newer_approved_edit(
            session, edit
        )
        if has_newer_approved:
            raise ValueError("Cannot re-apply: a newer approved edit exists for this entity")
        
        # Get the edit submitter for permission check
        submitter = await session.get(User, edit.user_id)
        if submitter and not AuditLogService.can_moderate_edit(approver, submitter):
            raise PermissionError("You do not have permission to re-apply this edit")
        
        # Perform the re-apply - update edit status to approved
        edit.status = EditStatus.APPROVED
        edit.reviewed_by = approver.user_id
        edit.reviewed_at = datetime.utcnow()
        
        if notes:
            # Append re-apply notes to existing review notes
            if edit.review_notes:
                edit.review_notes = f"{edit.review_notes}\n\nRe-applied: {notes}"
            else:
                edit.review_notes = f"Re-applied: {notes}"
        
        # Apply the edit to the database (re-apply the snapshot_after changes)
        await AuditLogService.apply_edit(session, edit)
        
        await session.commit()
        
        return ReviewEditResponse(
            edit_id=str(edit.edit_id),
            status="APPROVED",
            message="Edit re-applied successfully"
        )
    
    @staticmethod
    async def _has_newer_approved_edit(
        session: AsyncSession,
        edit: "EditHistory"
    ) -> bool:
        """
        Check if there are newer approved edits for the same entity.
        
        Used to determine if a re-apply is safe - we can't re-apply if
        another edit has been approved since this one was reverted/rejected.
        """
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus
        
        # Find any approved edits for the same entity that are newer
        # Uses created_at for comparison since reviewed_at might be null for rejected edits
        stmt = select(EditHistory).where(
            EditHistory.entity_type == edit.entity_type,
            EditHistory.entity_id == edit.entity_id,
            EditHistory.status == EditStatus.APPROVED,
            EditHistory.created_at >= edit.created_at,
            EditHistory.edit_id != edit.edit_id
        )
        result = await session.execute(stmt)
        newer_approved = result.scalars().first()
        
        return newer_approved is not None

    @staticmethod
    async def create_edit(
        session: AsyncSession,
        user_id: UUID,
        entity_type: str,
        entity_id: Optional[UUID],
        action: EditAction,
        old_data: Optional[Dict],
        new_data: Dict,
        status: EditStatus = EditStatus.PENDING,
        source_url: Optional[str] = None
    ) -> EditHistory:
        """
        Create a new edit history record.
        
        Args:
            session: Database session
            user_id: User performing the edit
            entity_type: Type of entity
            entity_id: ID of the entity (can be None for CREATE)
            action: Type of action (CREATE, UPDATE, DELETE)
            old_data: Previous state (None for CREATE)
            new_data: New state
            status: Status of the edit (PENDING, APPROVED)
            source_url: Optional URL of the data source
            
        Returns:
            The created EditHistory object
        """
        import uuid
        
        edit = EditHistory(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id or uuid.uuid4(),
            action=action,
            status=status,
            snapshot_before=old_data,
            snapshot_after=new_data,
            source_url=source_url,
            created_at=datetime.utcnow()
        )
        
        # Auto-approve high confidence scraper edits
        if status == EditStatus.APPROVED:
            edit.reviewed_by = user_id
            edit.reviewed_at = datetime.utcnow()
            edit.review_notes = "System: Auto-approved (High Confidence)"
            
        session.add(edit)
        await session.flush()
        
        # If auto-approved, apply changes immediately
        if status == EditStatus.APPROVED:
            await AuditLogService.apply_edit(session, edit)
            
        return edit

    @staticmethod
    async def apply_edit(session: AsyncSession, edit: EditHistory) -> None:
        """Apply approved edit to the domain model."""
        if edit.status != EditStatus.APPROVED:
            return

        if edit.action == EditAction.CREATE:
            await AuditLogService._apply_create(session, edit)
        elif edit.action == EditAction.UPDATE:
            await AuditLogService._apply_update(session, edit)
        elif edit.action == EditAction.DELETE:
            await AuditLogService._apply_delete(session, edit)

    @staticmethod
    async def _apply_create(session: AsyncSession, edit: EditHistory) -> None:
        """Apply CREATE action."""
        data = edit.snapshot_after
        
        # Unwrap nested data if present (consistency with update)
        unwrap_keys = ["node", "era", "master", "brand", "link", "event", "lineage_event"]
        for key in unwrap_keys:
            if key in data and isinstance(data[key], dict):
                data = data[key]
                break
        
        if edit.entity_type == "TeamEra":
            node = None
            team_identity_id = data.get("team_identity_id")
            
            # First, try to find node by team_identity_id (handles name changes)
            if team_identity_id:
                # PostgreSQL JSONB query for external_ids.cyclingflash_identity
                stmt = select(TeamNode).where(
                    TeamNode.external_ids["cyclingflash_identity"].astext == team_identity_id
                )
                result = await session.execute(stmt)
                node = result.scalar_one_or_none()
            
            # Fallback: try to find by legal_name (backward compatibility)
            if not node:
                stmt = select(TeamNode).where(TeamNode.legal_name == data["registered_name"])
                result = await session.execute(stmt)
                node = result.scalar_one_or_none()
            
            if not node:
                # Create new node with identity stored in external_ids
                external_ids = {}
                if team_identity_id:
                    external_ids["cyclingflash_identity"] = team_identity_id
                
                if not data.get("registered_name"):
                        raise ValueError("Cannot create TeamNode: Missing 'registered_name' in snapshot")
                if not data.get("season_year"):
                        raise ValueError("Cannot create TeamNode: Missing 'season_year' (founding_year) in snapshot")

                node = TeamNode(
                    node_id=edit.entity_id, # Using same ID for simplicity if 1:1, but usually distinct. 
                    # Actually, TeamEra is the entity. Node is separate.
                    # We need to find or create the Node.
                    legal_name=data["registered_name"],
                    founding_year=data["season_year"],
                    external_ids=external_ids if external_ids else None
                )
                session.add(node)
                await session.flush()
            
            # Create Era
            if not data.get("season_year"):
                 raise ValueError("Cannot create TeamEra: Missing 'season_year' in snapshot")
            if not data.get("registered_name"):
                 raise ValueError("Cannot create TeamEra: Missing 'registered_name' in snapshot")
                 
            era = TeamEra(
                era_id=edit.entity_id,
                node_id=node.node_id,
                season_year=data["season_year"],
                valid_from=datetime.strptime(data["valid_from"], "%Y-%m-%d").date(),
                registered_name=data["registered_name"],
                uci_code=data.get("uci_code"),
                country_code=data.get("country_code"),
                tier_level=data.get("tier_level")
            )
            session.add(era)
            await session.flush()
            
            # Create Sponsor Links
            sponsors_data = data.get("sponsors", [])
            for idx, s_data in enumerate(sponsors_data):
                brand_name = s_data.get("name")
                if not brand_name:
                    raise ValueError(f"Cannot create Sponsor Link: Missing 'name' for sponsor at index {idx}")
                    
                prominence = s_data.get("prominence", 0)
                parent_name = s_data.get("parent_company") # Will be added to payload in phase2.py
                
                # 1. Resolve/Create Master
                master = None
                if parent_name:
                    stmt = select(SponsorMaster).where(SponsorMaster.legal_name == parent_name)
                    result = await session.execute(stmt)
                    master = result.scalar_one_or_none()
                    if not master:
                        master = SponsorMaster(legal_name=parent_name)
                        session.add(master)
                        await session.flush()
                
                # 2. Resolve/Create Brand
                # Try simple match first
                stmt = select(SponsorBrand).where(SponsorBrand.brand_name == brand_name)
                if master:
                    stmt = stmt.where(SponsorBrand.master_id == master.master_id)
                
                result = await session.execute(stmt)
                brand = result.scalar_one_or_none()
                
                if not brand:
                    # If no master but we need one for the brand schema?
                    # Schema implies master_id is FK.
                    if not master:
                        # Implicit self-master
                        stmt = select(SponsorMaster).where(SponsorMaster.legal_name == brand_name)
                        result = await session.execute(stmt)
                        master = result.scalar_one_or_none()
                        if not master:
                            master = SponsorMaster(legal_name=brand_name)
                            session.add(master)
                            await session.flush()
            
                    brand = SponsorBrand(
                        brand_name=brand_name,
                        master_id=master.master_id,
                        default_hex_color=s_data.get("brand_color") or "#000000"  # Use extracted color or fallback
                    )
                    session.add(brand)
                    await session.flush()

                # 3. Create Link
                link = TeamSponsorLink(
                    era_id=era.era_id,
                    brand_id=brand.brand_id,
                    prominence_percent=prominence,
                    rank_order=idx + 1
                )
                session.add(link)

        elif edit.entity_type in ("lineage", "lineage_event", "lineageevent"):
            # Create Lineage Event
            # Snapshot should have: predecessor_id, successor_id, event_year, type, etc.
            # OR resolved names: source_node, target_team
            
            # OR resolved names: source_node, target_team
            
            # Try to resolve IDs from names if IDs are missing (Scraper fallback)
            # Log analysis showed scraper creates 'event' wrapper with keys: predecessor_node_id, successor_node_id
            pred_id = data.get("predecessor_id") or data.get("predecessor_node_id")
            succ_id = data.get("successor_id") or data.get("successor_node_id")
            
            if not pred_id and "source_node" in data:
                # Find by display_name or legal_name (case-insensitive)
                stmt = select(TeamNode).where(TeamNode.legal_name.ilike(data["source_node"]))
                result = await session.execute(stmt)
                p_node = result.scalar_one_or_none()
                if p_node:
                    pred_id = p_node.node_id
            
            if not succ_id and "target_team" in data:
                stmt = select(TeamNode).where(TeamNode.legal_name.ilike(data["target_team"]))
                result = await session.execute(stmt)
                s_node = result.scalar_one_or_none()
                if s_node:
                    succ_id = s_node.node_id
            
                if isinstance(pred_id, str): pred_id = UUID(pred_id)
                if isinstance(succ_id, str): succ_id = UUID(succ_id)
                
                event_year = data.get("event_year") or data.get("year")
                
                if not event_year:
                     # LOUD FAIL as requested by user
                     raise ValueError("Event Year is missing in snapshot")

                event = LineageEvent(
                    event_id=edit.entity_id,
                    predecessor_node_id=pred_id,
                    successor_node_id=succ_id,
                    event_year=event_year,
                    event_type=data.get("event_type", "MERGE") # Default to MERGE or provided type
                )
                session.add(event)
                await session.flush()
            else:
                # Log warning or error? 
                # If we can't find nodes, we can't create the link.
                import logging
                logging.error(f"Could not resolve nodes for LineageEvent create: {data}")
                raise ValueError(f"Could not resolve nodes for lineage event. Source: '{data.get('source_node')}', Target: '{data.get('target_team')}'")


    @staticmethod
    async def _apply_update(session: AsyncSession, edit: EditHistory, override_data: Optional[Dict] = None) -> None:
        """
        Apply UPDATE action by updating entity fields.
        
        Args:
            session: Database session
            edit: The edit record
            override_data: Optional data to use instead of edit.snapshot_after (e.g. for reverts)
        """
        data = override_data if override_data is not None else edit.snapshot_after
        entity_type = edit.entity_type.lower()
        
        # Load the entity
        entity = None
        if entity_type in ("team", "team_node", "teamnode"):
            entity = await session.get(TeamNode, edit.entity_id)
        elif entity_type in ("era", "team_era", "teamera"):
            entity = await session.get(TeamEra, edit.entity_id)
        elif entity_type in ("sponsor", "sponsor_master", "sponsormaster"):
            entity = await session.get(SponsorMaster, edit.entity_id)
        elif entity_type in ("brand", "sponsor_brand", "sponsorbrand"):
            entity = await session.get(SponsorBrand, edit.entity_id)
        elif entity_type in ("link", "team_sponsor_link", "teamsponsorlink"):
            entity = await session.get(TeamSponsorLink, edit.entity_id)
        elif entity_type in ("lineage", "lineage_event", "lineageevent"):
            entity = await session.get(LineageEvent, edit.entity_id)
        
        if not entity:
            raise ValueError(f"Entity {edit.entity_id} of type {edit.entity_type} not found")
        
        # Unwrap nested data if present (e.g. { "node": { ... } } from scraper)
        unwrap_keys = ["node", "era", "master", "brand", "link", "event", "lineage_event"]
        flattened_data = data.copy()
        
        for key in unwrap_keys:
            if key in data and isinstance(data[key], dict):
                # If the snapshot contains the wrapper key, use its content
                flattened_data = data[key]
                break
        
        # Update fields from snapshot (flattened)
        for key, value in flattened_data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        await session.flush()

    @staticmethod
    async def _apply_delete(session: AsyncSession, edit: EditHistory) -> None:
        """Apply DELETE action by removing the entity."""
        entity_type = edit.entity_type.lower()
        
        # Load the entity
        entity = None
        if entity_type in ("team", "team_node", "teamnode"):
            entity = await session.get(TeamNode, edit.entity_id)
        elif entity_type in ("era", "team_era", "teamera"):
            entity = await session.get(TeamEra, edit.entity_id)
        elif entity_type in ("sponsor", "sponsor_master", "sponsormaster"):
            entity = await session.get(SponsorMaster, edit.entity_id)
        elif entity_type in ("brand", "sponsor_brand", "sponsorbrand"):
            entity = await session.get(SponsorBrand, edit.entity_id)
        elif entity_type in ("link", "team_sponsor_link", "teamsponsorlink"):
            entity = await session.get(TeamSponsorLink, edit.entity_id)
        elif entity_type in ("lineage", "lineage_event", "lineageevent"):
            entity = await session.get(LineageEvent, edit.entity_id)
        
        if entity:
            await session.delete(entity)
            await session.flush()
