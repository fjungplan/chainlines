from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.team import TeamEra
from app.models.sponsor import TeamSponsorLink, SponsorBrand, SponsorMaster
from app.scraper.llm.models import SponsorInfo

logger = logging.getLogger(__name__)

class BrandMatcherService:
    """Checks team names against known brands in database."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._team_name_cache: dict[str, List[SponsorInfo]] = {}
    
    async def check_team_name(self, team_name: str) -> Optional[List[SponsorInfo]]:
        """
        Check if exact team name has been processed before.
        Returns cached sponsors if found, None otherwise.
        """
        # 1. Check in-memory cache
        if team_name in self._team_name_cache:
            logger.debug(f"Team name cache HIT (in-memory): {team_name}")
            return self._team_name_cache[team_name]
        
        # 2. Query TeamEra table
        # We use selectinload to eagerly load the sponsor links and brand/master details
        stmt = (
            select(TeamEra)
            .where(TeamEra.registered_name == team_name)
            .options(
                selectinload(TeamEra.sponsor_links)
                .selectinload(TeamSponsorLink.brand)
                .selectinload(SponsorBrand.master)
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        team_era = result.scalar_one_or_none()
        
        if team_era and team_era.sponsor_links:
            logger.debug(f"Team name cache HIT (DB): {team_name}")
            sponsors = []
            # Sort by rank_order to ensure consistency
            sorted_links = sorted(team_era.sponsor_links, key=lambda x: x.rank_order)
            for link in sorted_links:
                sponsor_info = SponsorInfo(
                    brand_name=link.brand.brand_name,
                    parent_company=link.brand.master.legal_name if link.brand.master else None
                )
                sponsors.append(sponsor_info)
            
            # Cache for session
            self._team_name_cache[team_name] = sponsors
            return sponsors
        
        logger.debug(f"Team name cache MISS: {team_name}")
        return None
