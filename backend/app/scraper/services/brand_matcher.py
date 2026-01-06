from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.team import TeamEra
from app.models.sponsor import TeamSponsorLink, SponsorBrand, SponsorMaster
from app.scraper.llm.models import SponsorInfo, BrandMatchResult
import re

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

    async def analyze_words(self, team_name: str) -> BrandMatchResult:
        """
        Check if all words in team name match known brands.
        Returns analysis result indicating if LLM is needed.
        """
        # Tokenize: split on non-alphanumeric, keep words
        words = re.findall(r'\b[\w]+\b', team_name)
        
        known_brands = []
        unmatched_words = []
        
        for word in words:
            # Exact match against brand_name
            # Case-insensitive match might be better, but prompt said exact match against brand_name
            # The user code snippet uses: select(SponsorBrand).where(SponsorBrand.brand_name == word).limit(1)
            stmt = select(SponsorBrand).where(SponsorBrand.brand_name == word).limit(1)
            result = await self._session.execute(stmt)
            brand = result.scalar_one_or_none()
            
            if brand:
                known_brands.append(word)
            else:
                unmatched_words.append(word)
        
        needs_llm = len(unmatched_words) > 0
        
        logger.debug(
            f"Word analysis for '{team_name}': "
            f"{len(known_brands)} known, {len(unmatched_words)} unknown, "
            f"LLM needed: {needs_llm}"
        )
        
        return BrandMatchResult(
            known_brands=known_brands,
            unmatched_words=unmatched_words,
            needs_llm=needs_llm
        )
