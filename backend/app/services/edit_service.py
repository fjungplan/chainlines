from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from typing import Dict
from uuid import UUID
import uuid
import json

from app.models.edit import EditHistory
from app.models.team import TeamEra, TeamNode
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType, EditAction, EditStatus
from app.models.user import User, UserRole
from app.models.sponsor import SponsorBrand, SponsorMaster
from app.schemas.edits import (
    EditMetadataRequest,
    EditMetadataResponse,
    MergeEventRequest,
    SplitEventRequest,
    CreateTeamRequest,
    CreateTeamRequest,
    UpdateNodeRequest,
    LineageEditRequest,
)


class EditService:
    @staticmethod
    async def create_metadata_edit(
        session: AsyncSession,
        user: User,
        request: EditMetadataRequest
    ) -> EditMetadataResponse:
        """Create a metadata edit (may be auto-approved for trusted users)"""
        # Get the target era
        try:
            era_id = UUID(request.era_id)
        except (ValueError, AttributeError):
            raise ValueError("Invalid era_id format")
        
        era = await session.get(TeamEra, era_id)
        if not era:
            raise ValueError("Era not found")
        
        # Get the team node (needed for node-level changes)
        node = await session.get(TeamNode, era.node_id, options=[selectinload(TeamNode.eras)])
        if not node:
            raise ValueError("Team node not found")
        
        # Build changes dict (only include fields that are being changed)
        changes = {}
        if request.registered_name:
            changes['registered_name'] = request.registered_name
        if request.uci_code:
            changes['uci_code'] = request.uci_code
        if request.tier_level:
            changes['tier_level'] = request.tier_level
        if request.uci_code:
            changes['uci_code'] = request.uci_code
        if request.country_code:
            changes['country_code'] = request.country_code
        if request.valid_from:
            changes['valid_from'] = request.valid_from
        if request.founding_year is not None:
            changes['founding_year'] = request.founding_year
        if request.dissolution_year is not None:
            changes['dissolution_year'] = request.dissolution_year
        
        if not changes:
            raise ValueError("No changes specified")
        
        # Capture snapshot_before for audit
        snapshot_before = {
            "era": {
                "era_id": str(era.era_id),
                "registered_name": era.registered_name,
                "uci_code": era.uci_code,
                "country_code": era.country_code,
                "tier_level": era.tier_level,
                "valid_from": era.valid_from.isoformat() if era.valid_from else None,
            },
            "node": {
                "node_id": str(node.node_id),
                "founding_year": node.founding_year,
                "dissolution_year": node.dissolution_year,
            }
        }
        
        # Auto-approve for trusted users and admins
        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN]:
            # Apply changes immediately
            await EditService._apply_metadata_changes(session, era, node, changes, user)
            
            # Capture snapshot_after
            snapshot_after = {
                "era": {
                    "era_id": str(era.era_id),
                    "registered_name": era.registered_name,
                    "uci_code": era.uci_code,
                    "tier_level": era.tier_level,
                },
                "node": {
                    "node_id": str(node.node_id),
                    "founding_year": node.founding_year,
                    "dissolution_year": node.dissolution_year,
                }
            }
            
            # Create audit record
            edit = EditHistory(
                entity_type="team_era",
                entity_id=era_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            
            # Increment approved edits count
            user.approved_edits_count += 1
            
            message = "Edit approved and applied immediately"
        else:
            # For pending edits, snapshot_after contains the *proposed* changes
            snapshot_after = dict(snapshot_before)
            if 'registered_name' in changes:
                snapshot_after['era']['registered_name'] = changes['registered_name']
            if 'uci_code' in changes:
                snapshot_after['era']['uci_code'] = changes['uci_code']
            if 'tier_level' in changes:
                snapshot_after['era']['tier_level'] = changes['tier_level']
            if 'uci_code' in changes:
                snapshot_after['era']['uci_code'] = changes['uci_code']
            if 'country_code' in changes:
                snapshot_after['era']['country_code'] = changes['country_code']
            if 'valid_from' in changes:
                snapshot_after['era']['valid_from'] = changes['valid_from'].isoformat()
            if 'founding_year' in changes:
                snapshot_after['node']['founding_year'] = changes['founding_year']
            if 'dissolution_year' in changes:
                snapshot_after['node']['dissolution_year'] = changes['dissolution_year']
            
            edit = EditHistory(
                entity_type="team_era",
                entity_id=era_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.PENDING,
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Edit submitted for moderation"
        
        session.add(edit)
        await session.commit()
        await session.refresh(edit)
        
        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )
        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )

    @staticmethod
    async def create_era_edit(
        session: AsyncSession,
        user: User,
        request: "CreateEraEditRequest" 
    ) -> EditMetadataResponse:
        """Create a new era edit (create era)"""
        from app.services.team_service import TeamService 
        from app.schemas.team import TeamEraCreate

        # Validate node exists
        try:
            node_id = UUID(request.node_id)
        except (ValueError, AttributeError):
            raise ValueError("Invalid node_id format")

        node = await TeamService.get_node_with_eras(session, node_id)
        if not node:
             raise ValueError("Team node not found")
        
        # Build TeamEraCreate data (we default valid_from to Jan 1 of season year for now)
        era_create_data = TeamEraCreate(
            season_year=request.season_year,
            registered_name=request.registered_name,
            valid_from=date(request.season_year, 1, 1),
            uci_code=request.uci_code,
            country_code=request.country_code,
            tier_level=request.tier_level,
            source_origin=f"user_{user.user_id}",
            is_manual_override=True,
            is_auto_filled=False
        )

        snapshot_before = None # Creation

        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN, UserRole.MODERATOR]:
             # Apply immediately
             era = await TeamService.create_era(session, node_id, era_create_data, user.user_id)
             
             snapshot_after = {
                 "era": {
                     "era_id": str(era.era_id),
                     "registered_name": era.registered_name,
                     "season_year": era.season_year
                 }
             }

             edit = EditHistory(
                entity_type="team_era",
                entity_id=era.era_id,
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason
             )
             user.approved_edits_count += 1
             message = "Era created successfully"
        else:
            # Pending
            snapshot_after = {
                "proposed_era": {
                    **era_create_data.model_dump(mode='json'),
                    "node_id": str(node.node_id)
                }
            }
            edit = EditHistory(
                entity_type="team_era",
                entity_id=uuid.uuid4(), # Placeholder
                user_id=user.user_id,
                action=EditAction.CREATE, 
                status=EditStatus.PENDING,
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Era creation submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)

        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )
    @staticmethod
    async def _apply_metadata_changes(
        session: AsyncSession,
        era: TeamEra,
        node: TeamNode,
        changes: Dict,
        user: User
    ) -> None:
        """Apply metadata changes to an era and/or node"""
        # Apply era-level changes
        if 'registered_name' in changes:
            era.registered_name = changes['registered_name']
        if 'uci_code' in changes:
            era.uci_code = changes['uci_code']
        if 'country_code' in changes:
            era.country_code = changes['country_code']
        if 'tier_level' in changes:
            era.tier_level = changes['tier_level']
        if 'valid_from' in changes:
            era.valid_from = changes['valid_from']
        
        # Apply node-level changes
        if 'founding_year' in changes:
            node.founding_year = changes['founding_year']
        if 'dissolution_year' in changes:
            # Allow setting to None if explicitly passed as None
            node.dissolution_year = changes['dissolution_year']
        
        # Mark as manual override to prevent scraper from overwriting
        era.is_manual_override = True
        era.source_origin = f"user_{user.user_id}"
        era.last_modified_by = user.user_id
        era.updated_at = datetime.utcnow()
        node.last_modified_by = user.user_id
        node.updated_at = datetime.utcnow()
        
        await session.commit()
    
    @staticmethod
    async def create_merge_edit(
        session: AsyncSession,
        user: User,
        request: MergeEventRequest
    ) -> EditMetadataResponse:
        """
        Create a merge event edit.
        """
        # Validate source nodes exist
        source_nodes = []
        for node_id_str in request.source_node_ids:
            try:
                node_id = UUID(node_id_str)
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid node_id format: {node_id_str}")
            
            # Eager-load eras relationship to avoid lazy loading in async context
            stmt = select(TeamNode).where(TeamNode.node_id == node_id).options(selectinload(TeamNode.eras))
            result = await session.execute(stmt)
            node = result.scalar_one_or_none()
            
            if not node:
                raise ValueError(f"Team node {node_id_str} not found")
            
            source_nodes.append(node)
        
        # Capture snapshot_before
        snapshot_before = {
            "source_nodes": [
                {
                    "node_id": str(n.node_id),
                    "legal_name": n.legal_name,
                    "dissolution_year": n.dissolution_year
                }
                for n in source_nodes
            ]
        }
        
        # Auto-approve for trusted users and admins
        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN]:
            # Apply merge immediately with validated nodes
            new_node = await EditService._apply_merge(session, request, user, source_nodes)
            
            # Capture snapshot_after
            snapshot_after = {
                "source_nodes": [
                    {
                        "node_id": str(n.node_id),
                        "legal_name": n.legal_name,
                        "dissolution_year": n.dissolution_year
                    }
                    for n in source_nodes
                ],
                "new_node": {
                    "node_id": str(new_node.node_id),
                    "legal_name": new_node.legal_name,
                    "founding_year": new_node.founding_year
                }
            }
            
            # Create audit record for the merge operation
            edit = EditHistory(
                entity_type="lineage_event",
                entity_id=new_node.node_id,  # Link to the resultant node
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            
            user.approved_edits_count += 1
            message = "Merge created successfully"
        else:
            # Pending merge - snapshot_after shows what WILL happen
            snapshot_after = {
                "source_nodes": snapshot_before["source_nodes"],
                "proposed_merge": {
                    "new_team_name": request.new_team_name,
                    "new_team_tier": request.new_team_tier,
                    "merge_year": request.merge_year
                }
            }
            
            edit = EditHistory(
                entity_type="lineage_event",
                entity_id=source_nodes[0].node_id,  # Link to first source node
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.PENDING,
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Merge submitted for moderation"
        
        session.add(edit)
        await session.commit()
        await session.refresh(edit)
        
        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )
    
    @staticmethod
    async def _apply_merge(
        session: AsyncSession,
        request: MergeEventRequest,
        user: User,
        validated_source_nodes: list[TeamNode]
    ) -> TeamNode:
        """Apply a merge: close old nodes, create new node with links"""
        # Generate a legal name since request doesn't provide one for merges yet
        generated_legal_name = f"{request.new_team_name} ({request.merge_year})"
        
        # Create new team node (WITHOUT is_active - it's a generated column!)
        new_node = TeamNode(
            founding_year=request.merge_year,
            legal_name=generated_legal_name,
            display_name=request.new_team_name,
            created_by=user.user_id
        )
        session.add(new_node)
        await session.flush()  # Get node_id
        
        # Create first era for new team
        new_era = TeamEra(
            node_id=new_node.node_id,
            season_year=request.merge_year,
            valid_from=date(request.merge_year, 1, 1),
            registered_name=request.new_team_name,
            tier_level=request.new_team_tier,
            source_origin=f"user_{user.user_id}",
            is_manual_override=True,
            created_by=user.user_id
        )
        session.add(new_era)
        
        # Close source nodes and create lineage links using validated nodes
        for source_node in validated_source_nodes:
            # Set dissolution year
            source_node.dissolution_year = request.merge_year
            source_node.last_modified_by = user.user_id
            source_node.updated_at = datetime.utcnow()
            
            # Create MERGE lineage event
            lineage_event = LineageEvent(
                predecessor_node_id=source_node.node_id,
                successor_node_id=new_node.node_id,
                event_year=request.merge_year,
                event_type=LineageEventType.MERGE,
                notes=f"Merged into {request.new_team_name}",
                created_by=user.user_id
            )
            session.add(lineage_event)
        
        await session.commit()
        return new_node
    
    @staticmethod
    async def create_team_edit(
        session: AsyncSession,
        user: User,
        request: CreateTeamRequest
    ) -> EditMetadataResponse:
        """Create a brand new team (node + initial era)."""

        snapshot_before = None  # No prior state for CREATE operations
        
        # Auto-approve for trusted users and admins
        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN]:
            # Apply immediately
            node = TeamNode(
                founding_year=request.founding_year,
                legal_name=request.legal_name,
                display_name=request.registered_name,
                created_by=user.user_id
            )
            session.add(node)
            await session.flush()

            era = TeamEra(
                node_id=node.node_id,
                season_year=request.founding_year,
                valid_from=date(request.founding_year, 1, 1),
                registered_name=request.registered_name,
                uci_code=request.uci_code,
                tier_level=request.tier_level,
                source_origin=f"user_{user.user_id}",
                is_manual_override=True,
                created_by=user.user_id
            )
            session.add(era)
            await session.flush()

            # Capture snapshot_after
            snapshot_after = {
                "node": {
                    "node_id": str(node.node_id),
                    "legal_name": node.legal_name,
                    "founding_year": node.founding_year
                },
                "era": {
                    "era_id": str(era.era_id),
                    "registered_name": era.registered_name,
                    "uci_code": era.uci_code,
                    "tier_level": era.tier_level
                }
            }
            
            # Create audit record
            edit = EditHistory(
                entity_type="team_node",
                entity_id=node.node_id,
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason or "Team created"
            )

            user.approved_edits_count += 1
            message = "Team created successfully"
        else:
            # Pending creation - snapshot_after shows what WILL be created
            snapshot_after = {
                "proposed_team": {
                    "legal_name": request.legal_name,
                    "registered_name": request.registered_name,
                    "founding_year": request.founding_year,
                    "uci_code": request.uci_code,
                    "tier_level": request.tier_level
                }
            }
            
            edit = EditHistory(
                entity_type="team_node",
                entity_id=uuid.uuid4(),  # Placeholder ID for pending creates
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.PENDING,
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason or "Team creation pending review"
            )
            message = "Team creation submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)

        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )

    @staticmethod
    async def create_split_edit(
        session: AsyncSession,
        user: User,
        request: SplitEventRequest
    ) -> EditMetadataResponse:
        """
        Create a split event edit.
        """
        # Validate source node exists
        try:
            node_id = UUID(request.source_node_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid node_id format: {request.source_node_id}")

        stmt = select(TeamNode).where(TeamNode.node_id == node_id).options(selectinload(TeamNode.eras))
        result = await session.execute(stmt)
        source_node = result.scalar_one_or_none()

        if not source_node:
            raise ValueError("Source team not found")

        # Capture snapshot_before
        snapshot_before = {
            "source_node": {
                "node_id": str(source_node.node_id),
                "legal_name": source_node.legal_name,
                "dissolution_year": source_node.dissolution_year
            }
        }
        
        # Auto-approve for trusted users and admins
        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN]:
            # Apply split immediately
            new_nodes = await EditService._apply_split(session, request, user, source_node)

            # Capture snapshot_after
            snapshot_after = {
                "source_node": {
                    "node_id": str(source_node.node_id),
                    "legal_name": source_node.legal_name,
                    "dissolution_year": source_node.dissolution_year
                },
                "new_nodes": [
                    {
                        "node_id": str(n.node_id),
                        "legal_name": n.legal_name,
                        "founding_year": n.founding_year
                    }
                    for n in new_nodes
                ]
            }
            
            # Create audit record
            edit = EditHistory(
                entity_type="lineage_event",
                entity_id=source_node.node_id,
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )

            user.approved_edits_count += 1
            message = "Split created successfully"
        else:
            # Pending split
            snapshot_after = {
                "source_node": snapshot_before["source_node"],
                "proposed_split": {
                    "split_year": request.split_year,
                    "new_teams": [
                        {"name": t.name, "tier": t.tier}
                        for t in request.new_teams
                    ]
                }
            }
            
            edit = EditHistory(
                entity_type="lineage_event",
                entity_id=source_node.node_id,
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.PENDING,
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Split submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)

        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )

    @staticmethod
    async def _apply_split(
        session: AsyncSession,
        request: SplitEventRequest,
        user: User,
        source_node: TeamNode
    ) -> list[TeamNode]:
        """Apply a split: close old node, create new nodes with links"""
        # Close source node
        source_node.dissolution_year = request.split_year
        source_node.last_modified_by = user.user_id
        source_node.updated_at = datetime.utcnow()

        new_nodes = []
        
        # Create new team nodes
        for new_team_info in request.new_teams:
            unique_suffix = str(uuid.uuid4())[:8]
            gen_legal_name = f"{new_team_info.name} ({request.split_year}) [{unique_suffix}]"

            # Create new node (WITHOUT is_active - it's generated!)
            new_node = TeamNode(
                founding_year=request.split_year,
                legal_name=gen_legal_name,
                display_name=new_team_info.name,
                created_by=user.user_id
            )
            session.add(new_node)
            await session.flush()  # Get node_id
            new_nodes.append(new_node)

            # Create first era
            new_era = TeamEra(
                node_id=new_node.node_id,
                season_year=request.split_year,
                valid_from=date(request.split_year, 1, 1),
                registered_name=new_team_info.name,
                tier_level=new_team_info.tier,
                source_origin=f"user_{user.user_id}",
                is_manual_override=True,
                created_by=user.user_id
            )
            session.add(new_era)

            # Create SPLIT lineage event
            lineage_event = LineageEvent(
                predecessor_node_id=source_node.node_id,
                successor_node_id=new_node.node_id,
                event_year=request.split_year,
                event_type=LineageEventType.SPLIT,
                notes=f"Split from source team into {new_team_info.name}",
                created_by=user.user_id
            )
            session.add(lineage_event)

        await session.commit()
        return new_nodes

    @staticmethod
    async def create_node_edit(
        session: AsyncSession,
        user: User,
        request: UpdateNodeRequest
    ) -> EditMetadataResponse:
        """Create a node edit (update)"""
        try:
            node_id = UUID(request.node_id)
        except (ValueError, AttributeError):
            raise ValueError("Invalid node_id format")

        node = await session.get(TeamNode, node_id)
        if not node:
            raise ValueError("Team node not found")

        # Protection Checks
        is_mod = user.role in [UserRole.MODERATOR, UserRole.ADMIN]
        if node.is_protected and not is_mod:
            raise ValueError("Cannot edit protected record")
        
        if request.is_protected is not None and request.is_protected != node.is_protected:
            if not is_mod:
                raise ValueError("Only moderators can change protection status")

        # Build changes
        changes = {}
        if request.legal_name is not None: changes['legal_name'] = request.legal_name
        if request.display_name is not None: changes['display_name'] = request.display_name
        if request.founding_year is not None: changes['founding_year'] = request.founding_year
        if request.dissolution_year is not None: changes['dissolution_year'] = request.dissolution_year
        if request.source_url is not None: changes['source_url'] = request.source_url
        if request.source_notes is not None: changes['source_notes'] = request.source_notes
        if request.is_protected is not None: changes['is_protected'] = request.is_protected

        if not changes:
            raise ValueError("No changes specified")

        snapshot_before = {
            "node": {
                "node_id": str(node.node_id),
                "legal_name": node.legal_name,
                "display_name": node.display_name,
                "founding_year": node.founding_year,
                "dissolution_year": node.dissolution_year,
                "is_protected": node.is_protected
            }
        }

        # Auto-approve for trusted/admin/mod
        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN, UserRole.MODERATOR]:
            # Apply immediately
            for k, v in changes.items():
                setattr(node, k, v)
            
            node.last_modified_by = user.user_id
            node.updated_at = datetime.utcnow()
            
            snapshot_after = {
                "node": {
                    "node_id": str(node.node_id),
                    "legal_name": node.legal_name,
                    "display_name": node.display_name,
                    "founding_year": node.founding_year,
                    "dissolution_year": node.dissolution_year,
                    "is_protected": node.is_protected
                }
            }

            edit = EditHistory(
                entity_type="team_node",
                entity_id=node.node_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            user.approved_edits_count += 1
            message = "Team updated successfully"
        else:
            # Pending
            snapshot_after = dict(snapshot_before)
            for k, v in changes.items():
                snapshot_after['node'][k] = v
            
            edit = EditHistory(
                entity_type="team_node",
                entity_id=node.node_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.PENDING,
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Update submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)

        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )

    @staticmethod
    async def create_lineage_edit(
        session: AsyncSession,
        user: User,
        request: LineageEditRequest
    ) -> EditMetadataResponse:
        """Create a new lineage connection (event)"""
        # Validate nodes
        try:
            pred_id = UUID(request.predecessor_node_id)
            succ_id = UUID(request.successor_node_id)
        except (ValueError, AttributeError):
            raise ValueError("Invalid node ID format")

        if pred_id == succ_id:
            raise ValueError("Predecessor and Successor cannot be the same node")

        pred_node = await session.get(TeamNode, pred_id)
        succ_node = await session.get(TeamNode, succ_id)

        if not pred_node:
            raise ValueError(f"Predecessor node {pred_id} not found")
        if not succ_node:
            raise ValueError(f"Successor node {succ_id} not found")

        # Protection Check
        is_mod = user.role in [UserRole.MODERATOR, UserRole.ADMIN]
        if request.is_protected and not is_mod:
            raise ValueError("Only moderators can create protected lineage events")

        snapshot_before = None # Create
        
        # Prepare Create Data
        create_data = {
            "predecessor_node_id": str(pred_node.node_id),
            "successor_node_id": str(succ_node.node_id),
            "event_year": request.event_year,
            "event_type": request.event_type.value,
            "event_date": request.event_date.isoformat() if request.event_date else None,
            "notes": request.notes,
            "source_url": request.source_url,
            "is_protected": request.is_protected or False
        }

        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN, UserRole.MODERATOR]:
            # Apply Immediately
            event = LineageEvent(
                predecessor_node_id=pred_node.node_id,
                successor_node_id=succ_node.node_id,
                event_year=request.event_year,
                event_type=request.event_type,
                event_date=request.event_date,
                notes=request.notes,
                source_url=request.source_url,
                is_protected=request.is_protected or False,
                created_by=user.user_id
            )
            session.add(event)
            await session.flush()

            snapshot_after = {"event": create_data, "event_id": str(event.event_id)}
            
            edit = EditHistory(
                entity_type="lineage_event",
                entity_id=event.event_id,
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            user.approved_edits_count += 1
            message = "Lineage event created successfully"
        else:
            # Pending
            snapshot_after = {"proposed_event": create_data}
            
            edit = EditHistory(
                entity_type="lineage_event",
                entity_id=uuid.uuid4(), # Placeholder
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.PENDING,
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Lineage event submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)

        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )

    @staticmethod
    async def update_lineage_edit(
        session: AsyncSession,
        user: User,
        request: LineageEditRequest
    ) -> EditMetadataResponse:
        """Update an existing lineage event"""
        if not request.event_id:
            raise ValueError("Event ID required for update")
        
        try:
            event_id = UUID(request.event_id)
        except ValueError:
            raise ValueError("Invalid Event ID")
            
        event = await session.get(LineageEvent, event_id)
        if not event:
            raise ValueError("Lineage event not found")
            
        # Protection Check
        is_mod = user.role in [UserRole.MODERATOR, UserRole.ADMIN]
        if event.is_protected and not is_mod:
            raise ValueError("Cannot edit protected lineage event")
            
        if request.is_protected is not None and request.is_protected != event.is_protected:
            if not is_mod:
                raise ValueError("Only moderators can change protection status")
                
        # Validate Nodes (if changing)
        pred_id = UUID(request.predecessor_node_id)
        succ_id = UUID(request.successor_node_id)
        
        if pred_id == succ_id:
             raise ValueError("Predecessor and Successor cannot be the same node")

        # Snapshot Before
        snapshot_before = {
            "event": {
                "event_id": str(event.event_id),
                "predecessor_node_id": str(event.predecessor_node_id),
                "successor_node_id": str(event.successor_node_id),
                "event_year": event.event_year,
                "event_type": event.event_type.value,
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "notes": event.notes,
                "is_protected": event.is_protected
            }
        }
        
        changes = {
            "predecessor_node_id": str(pred_id),
            "successor_node_id": str(succ_id),
            "event_year": request.event_year,
            "event_type": request.event_type.value,
            "event_date": request.event_date.isoformat() if request.event_date else None,
            "notes": request.notes,
            "source_url": request.source_url,
            "is_protected": request.is_protected if request.is_protected is not None else event.is_protected
        }

        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN, UserRole.MODERATOR]:
            # Apply Immediately
            event.predecessor_node_id = pred_id
            event.successor_node_id = succ_id
            event.event_year = request.event_year
            event.event_type = request.event_type
            event.event_date = request.event_date
            event.notes = request.notes
            event.source_url = request.source_url
            if request.is_protected is not None:
                event.is_protected = request.is_protected
            
            event.last_modified_by = user.user_id
            event.updated_at = datetime.utcnow()
            
            snapshot_after = {"event": changes}
            
            edit = EditHistory(
                entity_type="lineage_event",
                entity_id=event.event_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            user.approved_edits_count += 1
            message = "Lineage event updated successfully"
        else:
            # Pending
            snapshot_after = {"proposed_event": changes}
            
            edit = EditHistory(
                entity_type="lineage_event",
                entity_id=event.event_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.PENDING,
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Update submitted for moderation"
            
        session.add(edit)
        await session.commit()
        await session.refresh(edit)
        
        return EditMetadataResponse(
            edit_id=str(edit.edit_id),
            status=edit.status.value,
            message=message
        )

    @staticmethod
    async def create_sponsor_master_edit(
        session: AsyncSession,
        user: User,
        request: "SponsorMasterEditRequest"
    ) -> EditMetadataResponse:
        """Create a new sponsor master."""
        from app.services.sponsor_service import SponsorService
        from app.schemas.sponsors import SponsorMasterCreate

        snapshot_before = None

        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN, UserRole.MODERATOR]:
            data = SponsorMasterCreate(
                legal_name=request.legal_name,
                display_name=request.display_name,
                industry_sector=request.industry_sector,
                source_url=request.source_url,
                source_notes=request.source_notes,
                is_protected=request.is_protected or False
            )
            master = await SponsorService.create_master(session, data, user.user_id)
            
            snapshot_after = {
                "master": {
                    "master_id": str(master.master_id),
                    "legal_name": master.legal_name
                }
            }
            
            edit = EditHistory(
                entity_type="sponsor_master",
                entity_id=master.master_id,
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            user.approved_edits_count += 1
            message = "Sponsor created successfully"
        else:
            snapshot_after = {
                "proposed_sponsor": {
                    "legal_name": request.legal_name,
                    "display_name": request.display_name,
                    "industry_sector": request.industry_sector,
                    "source_url": request.source_url,
                    "source_notes": request.source_notes
                }
            }
            edit = EditHistory(
                entity_type="sponsor_master",
                entity_id=uuid.uuid4(), 
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.PENDING,
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Sponsor creation submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)
        return EditMetadataResponse(edit_id=str(edit.edit_id), status=edit.status.value, message=message)

    @staticmethod
    async def update_sponsor_master_edit(
        session: AsyncSession,
        user: User,
        request: "SponsorMasterEditRequest"
    ) -> EditMetadataResponse:
        """Update an existing sponsor master."""
        from app.services.sponsor_service import SponsorService
        from app.schemas.sponsors import SponsorMasterUpdate
        
        try:
            master_id = UUID(request.master_id)
        except (ValueError, AttributeError):
            raise ValueError("Invalid master_id")

        master = await SponsorService.get_master_by_id(session, master_id)
        if not master:
            raise ValueError("Sponsor master not found")

        is_mod = user.role in [UserRole.MODERATOR, UserRole.ADMIN]
        if master.is_protected and not is_mod:
            raise ValueError("Cannot edit protected record")
            
        changes = {}
        if request.legal_name: changes['legal_name'] = request.legal_name
        if request.display_name is not None: changes['display_name'] = request.display_name
        if request.industry_sector is not None: changes['industry_sector'] = request.industry_sector
        if request.source_url is not None: changes['source_url'] = request.source_url
        if request.source_notes is not None: changes['source_notes'] = request.source_notes
        
        if request.is_protected is not None:
             if not is_mod:
                 raise ValueError("Only moderators can change protection status")
             changes['is_protected'] = request.is_protected

        if not changes:
             raise ValueError("No changes specified")

        snapshot_before = {
            "master": {
                "master_id": str(master.master_id),
                "legal_name": master.legal_name,
                "display_name": master.display_name,
                "industry_sector": master.industry_sector,
                "is_protected": master.is_protected
            }
        }

        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN, UserRole.MODERATOR]:
            data = SponsorMasterUpdate(**changes)
            updated = await SponsorService.update_master(session, master_id, data, user.user_id)
            
            snapshot_after = {
                "master": {
                    "master_id": str(updated.master_id),
                    "legal_name": updated.legal_name,
                    "display_name": updated.display_name,
                    "is_protected": updated.is_protected
                }
            }
            
            edit = EditHistory(
                entity_type="sponsor_master",
                entity_id=master.master_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            user.approved_edits_count += 1
            message = "Sponsor updated successfully"
        else:
            snapshot_after = {
                "master": snapshot_before["master"],
                "proposed_changes": changes
            }
            edit = EditHistory(
                entity_type="sponsor_master",
                entity_id=master.master_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.PENDING,
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Update submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)
        return EditMetadataResponse(edit_id=str(edit.edit_id), status=edit.status.value, message=message)

    @staticmethod
    async def create_sponsor_brand_edit(
        session: AsyncSession,
        user: User,
        request: "SponsorBrandEditRequest"
    ) -> EditMetadataResponse:
        """Create a new sponsor brand."""
        from app.services.sponsor_service import SponsorService
        from app.schemas.sponsors import SponsorBrandCreate

        try:
            master_id = UUID(request.master_id)
        except:
             raise ValueError("Invalid master_id")

        # Verify master exists
        master = await SponsorService.get_master_by_id(session, master_id)
        if not master:
            raise ValueError("Sponsor master not found")

        snapshot_before = None

        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN, UserRole.MODERATOR]:
            data = SponsorBrandCreate(
                brand_name=request.brand_name,
                display_name=request.display_name,
                default_hex_color=request.default_hex_color,
                source_url=request.source_url,
                source_notes=request.source_notes,
                is_protected=request.is_protected or False
            )
            brand = await SponsorService.add_brand(session, master_id, data, user.user_id)
            
            snapshot_after = {
                "brand": {
                    "brand_id": str(brand.brand_id),
                    "brand_name": brand.brand_name,
                    "master_id": str(brand.master_id)
                }
            }
            
            edit = EditHistory(
                entity_type="sponsor_brand",
                entity_id=brand.brand_id,
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            user.approved_edits_count += 1
            message = "Brand created successfully"
        else:
            snapshot_after = {
                "proposed_brand": {
                    "master_id": str(master_id),
                    "brand_name": request.brand_name,
                    "default_hex_color": request.default_hex_color
                }
            }
            edit = EditHistory(
                entity_type="sponsor_brand",
                entity_id=uuid.uuid4(),
                user_id=user.user_id,
                action=EditAction.CREATE,
                status=EditStatus.PENDING,
                snapshot_before=None,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            message = "Brand creation submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)
        return EditMetadataResponse(edit_id=str(edit.edit_id), status=edit.status.value, message=message)

    @staticmethod
    async def update_sponsor_brand_edit(
        session: AsyncSession,
        user: User,
        request: "SponsorBrandEditRequest"
    ) -> EditMetadataResponse:
        """Update an existing sponsor brand."""
        from app.services.sponsor_service import SponsorService
        from app.schemas.sponsors import SponsorBrandUpdate

        try:
            brand_id = UUID(request.brand_id)
        except:
             raise ValueError("Invalid brand_id")

        # Get existing brand (need a getter in service or query directly)
        # SponsorService doesn't have get_brand_by_id helper easily public? update_brand selects it.
        # I'll check update_brand or just use session.get(SponsorBrand)
        brand = await session.get(SponsorBrand, brand_id)
        if not brand:
             raise ValueError("Brand not found")

        is_mod = user.role in [UserRole.MODERATOR, UserRole.ADMIN]
        if brand.is_protected and not is_mod:
            raise ValueError("Cannot edit protected brand")

        changes = {}
        if request.brand_name: changes['brand_name'] = request.brand_name
        if request.display_name is not None: changes['display_name'] = request.display_name
        if request.default_hex_color: changes['default_hex_color'] = request.default_hex_color
        if request.source_url is not None: changes['source_url'] = request.source_url
        if request.source_notes is not None: changes['source_notes'] = request.source_notes
        
        if request.is_protected is not None:
             if not is_mod:
                 raise ValueError("Only moderators can change protection status")
             changes['is_protected'] = request.is_protected

        if not changes:
             raise ValueError("No changes specified")

        snapshot_before = {
            "brand": {
                 "brand_id": str(brand.brand_id),
                 "brand_name": brand.brand_name,
                 "default_hex_color": brand.default_hex_color,
                 "is_protected": brand.is_protected
            }
        }

        if user.role in [UserRole.TRUSTED_EDITOR, UserRole.ADMIN, UserRole.MODERATOR]:
            data = SponsorBrandUpdate(**changes)
            updated = await SponsorService.update_brand(session, brand_id, data, user.user_id)
            
            snapshot_after = {
                "brand": {
                    "brand_id": str(updated.brand_id),
                    "brand_name": updated.brand_name,
                    "default_hex_color": updated.default_hex_color,
                    "is_protected": updated.is_protected
                }
            }
            
            edit = EditHistory(
                entity_type="sponsor_brand",
                entity_id=brand.brand_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.APPROVED,
                reviewed_by=user.user_id,
                reviewed_at=datetime.utcnow(),
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
            user.approved_edits_count += 1
            message = "Brand updated successfully"
        else:
             snapshot_after = {
                 "brand": snapshot_before["brand"],
                 "proposed_changes": changes
             }
             edit = EditHistory(
                entity_type="sponsor_brand",
                entity_id=brand.brand_id,
                user_id=user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.PENDING,
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
                source_notes=request.reason
            )
             message = "Update submitted for moderation"

        session.add(edit)
        await session.commit()
        await session.refresh(edit)
        return EditMetadataResponse(edit_id=str(edit.edit_id), status=edit.status.value, message=message)
