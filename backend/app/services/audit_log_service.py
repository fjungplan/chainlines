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
    async def resolve_entity_name(
        session: AsyncSession,
        entity_type: str,
        entity_id: Union[UUID, str]
    ) -> str:
        """
        Resolve an entity UUID to a human-readable name.
        
        Args:
            session: Database session
            entity_type: Type of entity (team_node, team_era, sponsor_master, etc.)
            entity_id: UUID of the entity
            
        Returns:
            Human-readable name string, or "Unknown" if not found
        """
        # Ensure entity_id is a UUID
        if isinstance(entity_id, str):
            try:
                entity_id = UUID(entity_id)
            except ValueError:
                return str(entity_id)
        
        try:
            etype = entity_type.lower()
            
            if etype in ("team", "team_node", "teamnode"):
                return await AuditLogService._resolve_team_node(session, entity_id)
            elif etype in ("era", "team_era", "teamera"):
                return await AuditLogService._resolve_team_era(session, entity_id)
            elif etype in ("sponsor", "sponsor_master", "sponsormaster"):
                return await AuditLogService._resolve_sponsor_master(session, entity_id)
            elif etype in ("brand", "sponsor_brand", "sponsorbrand"):
                return await AuditLogService._resolve_sponsor_brand(session, entity_id)
            elif etype in ("link", "team_sponsor_link", "teamsponsorlink"):
                return await AuditLogService._resolve_sponsor_link(session, entity_id)
            elif etype in ("lineage", "lineage_event", "lineageevent"):
                return await AuditLogService._resolve_lineage_event(session, entity_id)
            else:
                # Unknown entity type - return ID as string
                return str(entity_id)
        except Exception:
            return "Unknown"
    
    @staticmethod
    async def _resolve_team_node(session: AsyncSession, node_id: UUID) -> str:
        """Resolve TeamNode to display_name or legal_name."""
        node = await session.get(TeamNode, node_id)
        if not node:
            return "Unknown"
        return node.display_name or node.legal_name
    
    @staticmethod
    async def _resolve_team_era(session: AsyncSession, era_id: UUID) -> str:
        """Resolve TeamEra to 'registered_name (year)'."""
        era = await session.get(TeamEra, era_id)
        if not era:
            return "Unknown"
        return f"{era.registered_name} ({era.season_year})"
    
    @staticmethod
    async def _resolve_sponsor_master(session: AsyncSession, master_id: UUID) -> str:
        """Resolve SponsorMaster to display_name or legal_name."""
        master = await session.get(SponsorMaster, master_id)
        if not master:
            return "Unknown"
        return master.display_name or master.legal_name
    
    @staticmethod
    async def _resolve_sponsor_brand(session: AsyncSession, brand_id: UUID) -> str:
        """Resolve SponsorBrand to 'brand_name (master_name)'."""
        brand = await session.get(SponsorBrand, brand_id)
        if not brand:
            return "Unknown"
        
        # Get parent master name
        master = await session.get(SponsorMaster, brand.master_id)
        master_name = (master.display_name or master.legal_name) if master else "Unknown"
        
        return f"{brand.brand_name} ({master_name})"
    
    @staticmethod
    async def _resolve_sponsor_link(session: AsyncSession, link_id: UUID) -> str:
        """Resolve TeamSponsorLink to 'brand → era (year)'."""
        link = await session.get(TeamSponsorLink, link_id)
        if not link:
            return "Unknown"
        
        # Get brand and era names
        brand = await session.get(SponsorBrand, link.brand_id)
        era = await session.get(TeamEra, link.era_id)
        
        brand_name = brand.brand_name if brand else "Unknown Brand"
        era_name = era.registered_name if era else "Unknown Era"
        year = era.season_year if era else "?"
        
        return f"{brand_name} → {era_name} ({year})"
    
    @staticmethod
    async def _resolve_lineage_event(session: AsyncSession, event_id: UUID) -> str:
        """Resolve LineageEvent to 'predecessor → successor (year)'."""
        event = await session.get(LineageEvent, event_id)
        if not event:
            return "Unknown"
        
        # Get predecessor and successor node names
        predecessor = await session.get(TeamNode, event.predecessor_node_id)
        successor = await session.get(TeamNode, event.successor_node_id)
        
        pred_name = (predecessor.display_name or predecessor.legal_name) if predecessor else "Unknown Team"
        succ_name = (successor.display_name or successor.legal_name) if successor else "Unknown Team"
        
        return f"{pred_name} → {succ_name} ({event.event_year})"
    
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
        # TODO: Implement UPDATE and DELETE logic

    @staticmethod
    async def _apply_create(session: AsyncSession, edit: EditHistory) -> None:
        """Apply CREATE action."""
        data = edit.snapshot_after
        
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
                brand_name = s_data["name"]
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
