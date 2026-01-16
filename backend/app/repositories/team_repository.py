from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import TeamNode, TeamEra
from app.models.sponsor import TeamSponsorLink
from app.models.lineage import LineageEvent


class TeamRepository:
    @staticmethod
    async def get_by_id(session: AsyncSession, node_id: UUID) -> Optional[TeamNode]:
        stmt = (
            select(TeamNode)
            .where(TeamNode.node_id == node_id)
            .options(
                # Eager-load eras with sponsors and brand to prevent lazy loads
                selectinload(TeamNode.eras)
                .selectinload(TeamEra.sponsor_links)
                .selectinload(TeamSponsorLink.brand),
                # Eager-load lineage events and their related nodes' eras to avoid async lazy loads
                selectinload(TeamNode.outgoing_events)
                .selectinload(LineageEvent.successor_node)
                .selectinload(TeamNode.eras)
                .selectinload(TeamEra.sponsor_links)
                .selectinload(TeamSponsorLink.brand),
                selectinload(TeamNode.incoming_events)
                .selectinload(LineageEvent.predecessor_node)
                .selectinload(TeamNode.eras)
                .selectinload(TeamEra.sponsor_links)
                .selectinload(TeamSponsorLink.brand),
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
        search: Optional[str] = None,
    ) -> Tuple[List[TeamNode], int]:
        from sqlalchemy import or_

        # Base selectable
        base_stmt = select(TeamNode)

        if search:
            from sqlalchemy import or_
            # Normalize search term for accent insensitivity
            # Note: unaccent removes accents, ilike handles case.
            search_query = f"%{search}%"
            unaccented_query = func.unaccent(search_query)

            base_stmt = base_stmt.where(
                or_(
                    func.unaccent(TeamNode.legal_name).ilike(unaccented_query),
                    func.unaccent(TeamNode.display_name).ilike(unaccented_query),
                    # Search across ALL eras using exists (any) to find historical names/codes/sponsors
                    TeamNode.eras.any(func.unaccent(TeamEra.registered_name).ilike(unaccented_query)),
                    TeamNode.eras.any(func.unaccent(TeamEra.uci_code).ilike(unaccented_query))
                )
            )

        if active_in_year is not None:
            # Filter nodes that have eras in the given year
            base_stmt = (
                base_stmt.join(TeamEra, TeamEra.node_id == TeamNode.node_id)
                .where(TeamEra.season_year == active_in_year)
            )

        if tier_level is not None:
            # Filter by tier_level via eras; a team is included if any era matches tier
            # Join is needed only if not already joined (active_in_year handles it if present)
            # Actually, if we search, we are on TeamNode.
            # If active_in_year is NOT None, we joined TeamEra already.
            # But wait, we need to join TeamEra correctly.
            # The previous logic was: if active_in_year is None check joint.
            # Let's clean up logic:
            if active_in_year is None:
                 base_stmt = base_stmt.join(TeamEra, TeamEra.node_id == TeamNode.node_id)
            base_stmt = base_stmt.where(TeamEra.tier_level == tier_level)

        # Total count (distinct nodes if joins present)
        count_stmt = select(func.count(distinct(TeamNode.node_id)))
        
        # Apply filters to count statement
        # (Naive approach: reconstruct logic. Safer approach: use filtered subquery, but reconstruction is standard here)
        count_stmt = count_stmt.select_from(TeamNode)
        
        if search:
            # Re-apply same search logic for count
            # Note: imports (func, or_) are available from previous block or top level if moved
            # But local import in previous block scope is not available here unless we re-import or move it up
            from sqlalchemy import or_
            
            search_query = f"%{search}%"
            unaccented_query = func.unaccent(search_query)
            
            count_stmt = count_stmt.where(
                or_(
                    func.unaccent(TeamNode.legal_name).ilike(unaccented_query),
                    func.unaccent(TeamNode.display_name).ilike(unaccented_query),
                    TeamNode.eras.any(func.unaccent(TeamEra.registered_name).ilike(unaccented_query)),
                    TeamNode.eras.any(func.unaccent(TeamEra.uci_code).ilike(unaccented_query))
                )
            )

        if active_in_year is not None or tier_level is not None:
            if active_in_year is not None or tier_level is not None:
                count_stmt = count_stmt.join(TeamEra, TeamEra.node_id == TeamNode.node_id)
            if active_in_year is not None:
                count_stmt = count_stmt.where(TeamEra.season_year == active_in_year)
            if tier_level is not None:
                count_stmt = count_stmt.where(TeamEra.tier_level == tier_level)

        total = (await session.execute(count_stmt)).scalar_one()

        # Data query with pagination and eager loading of eras for convenience
        data_stmt = (
            base_stmt.options(
                selectinload(TeamNode.eras)
                .selectinload(TeamEra.sponsor_links)
                .selectinload(TeamSponsorLink.brand)
            ).offset(skip).limit(limit)
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
        stmt = (
            select(TeamEra)
            .where(TeamEra.node_id == node_id)
            .options(
                # Eager-load sponsors and their brand to avoid async lazy loads downstream
                selectinload(TeamEra.sponsor_links)
                .selectinload(TeamSponsorLink.brand)
            )
        )
        if year_filter is not None:
            stmt = stmt.where(TeamEra.season_year == year_filter)
        stmt = stmt.order_by(TeamEra.season_year.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
