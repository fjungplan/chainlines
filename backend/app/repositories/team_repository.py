from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import TeamNode, TeamEra


class TeamRepository:
    @staticmethod
    async def get_by_id(session: AsyncSession, node_id: UUID) -> Optional[TeamNode]:
        stmt = (
            select(TeamNode)
            .where(TeamNode.node_id == node_id)
            .options(
                selectinload(TeamNode.eras),
                selectinload(TeamNode.outgoing_events),
                selectinload(TeamNode.incoming_events),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        active_in_year: Optional[int] = None,
        tier_level: Optional[int] = None,
    ) -> Tuple[List[TeamNode], int]:
        # Base selectable
        base_stmt = select(TeamNode)

        if active_in_year is not None:
            # Filter nodes that have eras in the given year
            base_stmt = (
                base_stmt.join(TeamEra, TeamEra.node_id == TeamNode.node_id)
                .where(TeamEra.season_year == active_in_year)
            )

        if tier_level is not None:
            # Filter by tier_level via eras; a team is included if any era matches tier
            if active_in_year is None:
                base_stmt = base_stmt.join(TeamEra, TeamEra.node_id == TeamNode.node_id)
            base_stmt = base_stmt.where(TeamEra.tier_level == tier_level)

        # Total count (distinct nodes if joins present)
        count_stmt = select(func.count(distinct(TeamNode.node_id)))
        if active_in_year is not None or tier_level is not None:
            # replicate joins/filters for count
            count_stmt = count_stmt.select_from(TeamNode)
            if active_in_year is not None or tier_level is not None:
                count_stmt = count_stmt.join(TeamEra, TeamEra.node_id == TeamNode.node_id)
            if active_in_year is not None:
                count_stmt = count_stmt.where(TeamEra.season_year == active_in_year)
            if tier_level is not None:
                count_stmt = count_stmt.where(TeamEra.tier_level == tier_level)

        total = (await session.execute(count_stmt)).scalar_one()

        # Data query with pagination and eager loading of eras for convenience
        data_stmt = (
            base_stmt.options(selectinload(TeamNode.eras)).offset(skip).limit(limit)
        )
        nodes = list((await session.execute(data_stmt)).scalars().unique().all())
        return nodes, int(total)

    @staticmethod
    async def get_eras_for_node(
        session: AsyncSession,
        node_id: UUID,
        *,
        year_filter: Optional[int] = None,
    ) -> List[TeamEra]:
        stmt = select(TeamEra).where(TeamEra.node_id == node_id)
        if year_filter is not None:
            stmt = stmt.where(TeamEra.season_year == year_filter)
        stmt = stmt.order_by(TeamEra.season_year.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
