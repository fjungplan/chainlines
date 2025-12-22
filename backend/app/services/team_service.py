from datetime import date
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import TeamNode, TeamEra
from app.schemas.team import (
    TeamNodeCreate, TeamNodeUpdate, 
    TeamEraCreate, TeamEraUpdate
)
from app.core.exceptions import (
    NodeNotFoundException,
    DuplicateEraException,
    ValidationException,
)
from app.services.timeline_service import TimelineService
from app.repositories.team_repository import TeamRepository


class TeamService:
    """Encapsulates business logic for team node and era management."""

    @staticmethod
    async def get_node_with_eras(session: AsyncSession, node_id: uuid.UUID) -> TeamNode:
        # Use repository to ensure consistent eager-loading of eras and sponsors
        node = await TeamRepository.get_by_id(session, node_id)
        if not node:
            # SELECT may begin a transaction implicitly; rollback to clear state
            await session.rollback()
            raise NodeNotFoundException(f"TeamNode {node_id} not found")
        # Defensive: avoid async lazy-load by ensuring eras are present in instance dict
        if 'eras' not in node.__dict__:
            # Fetch eras via repository with eager-loaded sponsors
            eras = await TeamRepository.get_eras_for_node(session, node_id)
            node.__dict__['eras'] = eras
        return node

    @staticmethod
    async def get_eras_by_year(session: AsyncSession, year: int) -> List[TeamEra]:
        if year < 1900 or year > 2100:
            raise ValidationException(f"Year {year} out of allowed range (1900-2100)")
        # Delegate to repository to keep eager-loading consistent
        stmt = select(TeamEra).where(TeamEra.season_year == year)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_nodes(
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        active_in_year: Optional[int] = None,
        tier_level: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[List[TeamNode], int]:
        # Use repository to handle filtering, pagination, and eager-loading
        nodes, total = await TeamRepository.get_all(
            session,
            skip=skip,
            limit=limit,
            active_in_year=active_in_year,
            tier_level=tier_level,
            search=search,
        )
        # Defensive: ensure eras are attached to each node to avoid async lazy-loads later
        # Also compute dynamic fields (latest_team_name, current_tier) for list view
        for n in nodes:
            if 'eras' not in n.__dict__:
                eras = await TeamRepository.get_eras_for_node(session, n.node_id)
                n.__dict__['eras'] = eras
            else:
                eras = n.eras
            
            if eras:
                # Find latest era by season_year
                latest_era = max(eras, key=lambda e: e.season_year)
                n.latest_team_name = latest_era.display_name
                n.latest_uci_code = latest_era.uci_code
                n.current_tier = latest_era.tier_level
                
        return nodes, total

    @staticmethod
    async def get_node_eras(
        session: AsyncSession,
        node_id: uuid.UUID,
        *,
        year_filter: Optional[int] = None,
    ) -> List[TeamEra]:
        # Delegate to repository to apply eager-loading consistently
        return await TeamRepository.get_eras_for_node(
            session, node_id, year_filter=year_filter
        )

    @staticmethod
    async def create_node(session: AsyncSession, data: TeamNodeCreate, user_id: Optional[uuid.UUID] = None) -> TeamNode:
        # Check for unique legal_name
        stmt = select(TeamNode).where(TeamNode.legal_name == data.legal_name)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise ValidationException(f"Team with legal_name '{data.legal_name}' already exists")

        node = TeamNode(
            **data.model_dump(),
            created_by=user_id,
            last_modified_by=user_id
        )
        session.add(node)
        await session.commit()
        await session.refresh(node)
        return node

    @staticmethod
    async def update_node(
        session: AsyncSession, 
        node_id: uuid.UUID, 
        data: TeamNodeUpdate, 
        user_id: Optional[uuid.UUID] = None
    ) -> TeamNode:
        node = await TeamService.get_node_with_eras(session, node_id)
        if not node:
            raise NodeNotFoundException(f"TeamNode {node_id} not found")
        
        update_data = data.model_dump(exclude_unset=True)
        if "legal_name" in update_data:
            # Check uniqueness if name is changing
            if update_data["legal_name"] != node.legal_name:
                stmt = select(TeamNode).where(TeamNode.legal_name == update_data["legal_name"])
                existing = await session.execute(stmt)
                if existing.scalar_one_or_none():
                    raise ValidationException(f"Team with legal_name '{update_data['legal_name']}' already exists")

        for key, value in update_data.items():
            setattr(node, key, value)
        
        node.last_modified_by = user_id
        await session.commit()
        await session.refresh(node)
        return node

    @staticmethod
    async def delete_node(session: AsyncSession, node_id: uuid.UUID) -> bool:
        node = await TeamRepository.get_by_id(session, node_id)
        if not node:
            return False
            
        await session.delete(node)
        await session.commit()
        TimelineService.invalidate_cache()
        return True

    @staticmethod
    async def create_era(
        session: AsyncSession,
        node_id: uuid.UUID,
        data: TeamEraCreate,
        user_id: Optional[uuid.UUID] = None
    ) -> TeamEra:
        # Basic input validations
        if data.season_year < 1900 or data.season_year > 2100:
            raise ValidationException("season_year must be between 1900 and 2100")
        if data.tier_level is not None and data.tier_level not in (1, 2, 3):
            raise ValidationException("tier_level must be 1, 2, or 3 when provided")
        if data.uci_code is not None and (
            len(data.uci_code) != 3 or not data.uci_code.isalpha() or not data.uci_code.isupper()
        ):
            raise ValidationException("uci_code must be exactly 3 uppercase letters")
        if not data.registered_name or data.registered_name.strip() == "":
            raise ValidationException("registered_name cannot be empty")

        # Ensure node exists
        node = await TeamService.get_node_with_eras(session, node_id)
        if not node:
             raise NodeNotFoundException(f"TeamNode {node_id} not found")

        # Duplicate check
        dup_stmt = select(TeamEra).where(
            TeamEra.node_id == node_id, TeamEra.season_year == data.season_year
        )
        dup_result = await session.execute(dup_stmt)
        if dup_result.scalar_one_or_none():
            raise DuplicateEraException(
                f"Era for node {node_id} and year {data.season_year} already exists"
            )

        era = TeamEra(
            **data.model_dump(),
            node_id=node_id,
            created_by=user_id,
            last_modified_by=user_id
        )
        session.add(era)
        await session.commit()
        TimelineService.invalidate_cache()
        await session.refresh(era)
        return era

    @staticmethod
    async def update_era(
        session: AsyncSession,
        era_id: uuid.UUID,
        data: TeamEraUpdate,
        user_id: Optional[uuid.UUID] = None
    ) -> TeamEra:
        stmt = select(TeamEra).where(TeamEra.era_id == era_id)
        result = await session.execute(stmt)
        era = result.scalar_one_or_none()
        if not era:
            raise ValidationException(f"TeamEra {era_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        
        # specific validation logic if needed (years etc)
        
        for key, value in update_data.items():
            setattr(era, key, value)
            
        era.last_modified_by = user_id
        await session.commit()
        TimelineService.invalidate_cache()
        await session.refresh(era)
        return era

    @staticmethod
    async def delete_era(session: AsyncSession, era_id: uuid.UUID) -> bool:
        stmt = select(TeamEra).where(TeamEra.era_id == era_id)
        result = await session.execute(stmt)
        era = result.scalar_one_or_none()
        if not era:
            return False
            
        await session.delete(era)
        await session.commit()
        TimelineService.invalidate_cache()
        return True
