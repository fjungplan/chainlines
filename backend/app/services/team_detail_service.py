from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.team import TeamNode, TeamEra
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType
from app.models.sponsor import TeamSponsorLink
from app.schemas.sponsor import SponsorLinkResponse
from app.schemas.team_detail import (
    TeamHistoryResponse,
    TeamHistoryEra,
    LineageSummary,
    TransitionInfo,
)


class TeamDetailService:
    @staticmethod
    async def get_team_history(session: AsyncSession, node_id: str) -> Optional[TeamHistoryResponse]:
        stmt = (
            select(TeamNode)
            .where(TeamNode.node_id == node_id)
            .options(
                selectinload(TeamNode.eras)
                .selectinload(TeamEra.sponsor_links)
                .selectinload(TeamSponsorLink.brand),
                selectinload(TeamNode.incoming_events)
                .selectinload(LineageEvent.predecessor_node)
                .selectinload(TeamNode.eras),
                selectinload(TeamNode.outgoing_events)
                .selectinload(LineageEvent.successor_node)
                .selectinload(TeamNode.eras),
            )
        )
        result = await session.execute(stmt)
        team: Optional[TeamNode] = result.scalar_one_or_none()
        if not team:
            return None

        eras_sorted = sorted(team.eras, key=lambda e: e.season_year)
        current_year = datetime.utcnow().year

        timeline: List[TeamHistoryEra] = []
        for era in eras_sorted:
            status = TeamDetailService.calculate_era_status(
                era, current_year, team.dissolution_year
            )
            predecessor = TeamDetailService._find_predecessor_event(team, era)
            successor = TeamDetailService._find_successor_event(team, era)
            
            # Map sponsors
            era_sponsors = []
            if era.sponsor_links:
                # Sort by rank_order
                sorted_links = sorted(era.sponsor_links, key=lambda s: s.rank_order)
                for link in sorted_links:
                    if link.brand: # Ensure brand is loaded
                        era_sponsors.append(
                            SponsorLinkResponse(
                                link_id=link.link_id,
                                brand_id=link.brand_id,
                                rank_order=link.rank_order,
                                prominence_percent=link.prominence_percent,
                                hex_color_override=link.hex_color_override,
                                brand_name=link.brand.brand_name,
                                color=link.hex_color_override if link.hex_color_override else link.brand.default_hex_color
                            )
                        )

            timeline.append(
                TeamHistoryEra(
                    year=era.season_year,
                    name=era.registered_name,
                    tier=era.tier_level,
                    uci_code=era.uci_code,
                    country_code=era.country_code,
                    status=status,
                    predecessor=predecessor,
                    successor=successor,
                    sponsors=era_sponsors
                )
            )

        lineage_summary = LineageSummary(
            has_predecessors=len(team.incoming_events) > 0,
            has_successors=len(team.outgoing_events) > 0,
            spiritual_succession=any(e.event_type == LineageEventType.SPIRITUAL_SUCCESSION for e in team.incoming_events)
            or any(e.event_type == LineageEventType.SPIRITUAL_SUCCESSION for e in team.outgoing_events),
        )

        return TeamHistoryResponse(
            node_id=str(team.node_id),
            founding_year=team.founding_year,
            dissolution_year=team.dissolution_year,
            timeline=timeline,
            lineage_summary=lineage_summary,
        )

    @staticmethod
    def calculate_era_status(
        era: TeamEra, current_year: int, dissolution_year: Optional[int]
    ) -> str:
        if dissolution_year is not None and era.season_year >= dissolution_year:
            return "dissolved"
        if era.season_year == current_year and dissolution_year is None:
            return "active"
        if era.season_year < current_year:
            return "historical"
        return "active"

    @staticmethod
    def _event_to_transition(event: LineageEvent, name: str) -> TransitionInfo:
        return TransitionInfo(
            year=event.event_year,
            name=name,
            event_type=TeamDetailService._classify_transition(event),
        )

    @staticmethod
    def _classify_transition(event: LineageEvent) -> str:
        if event.event_type == LineageEventType.MERGE:
            return "MERGED_INTO"
        if event.event_type == LineageEventType.SPIRITUAL_SUCCESSION:
            return "REVIVAL"
        if event.event_type == LineageEventType.LEGAL_TRANSFER:
            return "ACQUISITION"
        if event.event_type == LineageEventType.SPLIT:
            return "SPLIT"
        return str(event.event_type)

    @staticmethod
    def _find_predecessor_event(team: TeamNode, era: TeamEra) -> Optional[TransitionInfo]:
        # predecessor: incoming event targeting this node with same or previous year
        candidates = [e for e in team.incoming_events if e.event_year <= era.season_year]
        if not candidates:
            return None
        event = max(candidates, key=lambda e: e.event_year)
        name = None
        if event.predecessor_node and event.predecessor_node.eras:
            prev_eras = sorted(event.predecessor_node.eras, key=lambda x: x.season_year)
            name = prev_eras[-1].registered_name
        return TeamDetailService._event_to_transition(event, name or "")

    @staticmethod
    def _find_successor_event(team: TeamNode, era: TeamEra) -> Optional[TransitionInfo]:
        # successor: outgoing event from this node after or at era year
        candidates = [e for e in team.outgoing_events if e.event_year >= era.season_year]
        if not candidates:
            return None
        event = min(candidates, key=lambda e: e.event_year)
        name = None
        if event.successor_node and event.successor_node.eras:
            next_eras = sorted(event.successor_node.eras, key=lambda x: x.season_year)
            name = next_eras[0].registered_name
        return TeamDetailService._event_to_transition(event, name or "")
