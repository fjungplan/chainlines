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
from app.schemas.edits import (
    EditMetadataRequest,
    EditMetadataResponse,
    MergeEventRequest,
    SplitEventRequest,
    CreateTeamRequest,
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
                "tier_level": era.tier_level,
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
    
    @staticmethod
    async def _apply_metadata_changes(
        session: AsyncSession,
        era: TeamEra,
        node: TeamNode,
        changes: Dict,
        user: User
    ):
        """Apply metadata changes to an era and/or node"""
        # Apply era-level changes
        if 'registered_name' in changes:
            era.registered_name = changes['registered_name']
        if 'uci_code' in changes:
            era.uci_code = changes['uci_code']
        if 'tier_level' in changes:
            era.tier_level = changes['tier_level']
        
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
