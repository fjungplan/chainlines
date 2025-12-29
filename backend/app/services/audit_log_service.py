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
            if entity_type == "team_node":
                return await AuditLogService._resolve_team_node(session, entity_id)
            elif entity_type == "team_era":
                return await AuditLogService._resolve_team_era(session, entity_id)
            elif entity_type == "sponsor_master":
                return await AuditLogService._resolve_sponsor_master(session, entity_id)
            elif entity_type == "sponsor_brand":
                return await AuditLogService._resolve_sponsor_brand(session, entity_id)
            elif entity_type == "team_sponsor_link":
                return await AuditLogService._resolve_sponsor_link(session, entity_id)
            elif entity_type == "lineage_event":
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
