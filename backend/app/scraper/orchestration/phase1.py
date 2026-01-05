"""Phase 1: Discovery and Sponsor Collection."""
from typing import Set, List, Optional, Union, Tuple, TYPE_CHECKING
from app.scraper.llm.models import SponsorInfo
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.services.brand_matcher import BrandMatcherService

if TYPE_CHECKING:
    from app.scraper.llm.prompts import ScraperPrompts

class SponsorCollector:
    """Collects unique sponsor names across all teams."""
    
    def __init__(self):
        self._names: Set[str] = set()
    
    def add(self, sponsors: Union[List[str], List[SponsorInfo]]) -> None:
        """Add sponsor names to collection."""
        for s in sponsors:
            name = s.brand_name if isinstance(s, SponsorInfo) else s
            if name and name.strip():
                self._names.add(name.strip())
    
    def get_all(self) -> Set[str]:
        """Get all unique sponsor names."""
        return self._names.copy()

import logging
from dataclasses import dataclass
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from app.scraper.checkpoint import CheckpointManager, CheckpointData

logger = logging.getLogger(__name__)

@dataclass
class DiscoveryResult:
    """Result of Phase 1 discovery."""
    team_urls: list[str]
    sponsor_names: set[str]

from app.scraper.monitor import ScraperStatusMonitor

class DiscoveryService:
    """Orchestrates Phase 1: Team discovery and sponsor collection."""
    
    def __init__(
        self,
        scraper: CyclingFlashScraper,
        checkpoint_manager: CheckpointManager,
        monitor: Optional[ScraperStatusMonitor] = None,
        session: Optional[AsyncSession] = None,
        llm_prompts: Optional["ScraperPrompts"] = None
    ):
        self._scraper = scraper
        self._checkpoint = checkpoint_manager
        self._collector = SponsorCollector()
        self._monitor = monitor
        self._session = session
        self._llm_prompts = llm_prompts
        
        # Initialize brand matcher if session available
        self._brand_matcher = BrandMatcherService(session) if session else None
        
        logger.info(
            f"DiscoveryService initialized with "
            f"LLM extraction: {llm_prompts is not None}, "
            f"Brand matching: {self._brand_matcher is not None}"
        )

    
    async def discover_teams(
        self,
        start_year: int,
        end_year: int,
        tier_level: Optional[int] = None
    ) -> DiscoveryResult:
        """Discover all teams and collect sponsor names."""
        checkpoint = self._checkpoint.load()
        team_urls: list[str] = []
        
        if checkpoint and checkpoint.phase == 1:
            team_urls = checkpoint.team_queue.copy()
            self._collector._names = checkpoint.sponsor_names.copy()
            logger.info(f"Resuming from checkpoint with {len(team_urls)} teams")
        
        for year in range(start_year, end_year - 1, -1):  # Backwards
            # Check for Pause/Abort call
            if self._monitor:
                await self._monitor.check_status()
                
            try:
                # Use tier-optimized fetch if filtering by tier
                if tier_level:
                    urls = await self._scraper.get_team_list_by_tier(year, tier_level)
                    logger.info(f"Found {len(urls)} Tier {tier_level} teams for year {year}. Starting detail extraction...")
                else:
                    urls = await self._scraper.get_team_list(year)
                    logger.info(f"Found {len(urls)} total teams for year {year}. Starting detail extraction...")
                
                for i, url in enumerate(urls, 1):
                    # Check for Pause/Abort every 5 teams
                    if self._monitor and i % 5 == 0:
                        await self._monitor.check_status()
                    
                    data = await self._scraper.get_team(url, year)
                    
                    prefix = f"Team {i}/{len(urls)} [{year}]"
                    if tier_level and data.tier_level != tier_level:
                        logger.info(f"{prefix}: SKIPPING '{data.name}' - Target Tier {tier_level} vs Found {data.tier_level}")
                        continue
                        
                    logger.info(f"{prefix}: COLLECTED '{data.name}'")
                    logger.info(f"    - Details: UCI: {data.uci_code}, Country: {data.country_code}, Tier: {data.tier_level}")
                    sponsor_names = [s.brand_name for s in data.sponsors]
                    logger.info(f"    - Sponsors: {', '.join(sponsor_names) if sponsor_names else 'None'}")
                    
                    if url not in team_urls:
                        team_urls.append(url)
                        self._collector.add(data.sponsors)
                        
                        # Save checkpoint periodically
                        if i % 10 == 0 or i == len(urls):
                            self._save_checkpoint(team_urls)
                            logger.info(f"    - Checkpoint saved ({len(team_urls)} unique teams in queue)")
                        
            except Exception as e:
                logger.error(f"Error in year {year}: {e}")
                self._save_checkpoint(team_urls)
                raise
        
        return DiscoveryResult(
            team_urls=team_urls,
            sponsor_names=self._collector.get_all()
        )
    
    def _save_checkpoint(self, team_urls: list[str]) -> None:
        """Save current progress."""
        self._checkpoint.save(CheckpointData(
            phase=1,
            team_queue=team_urls,
        ))
    
    async def _extract_sponsors(
        self,
        team_name: str,
        country_code: Optional[str],
        season_year: int
    ) -> Tuple[List[SponsorInfo], float]:
        """
        Extract sponsors from team name with multi-tier caching.
        Returns (sponsors, confidence).
        """
        # Fallback if no LLM/DB available
        if not self._brand_matcher or not self._llm_prompts:
            logger.warning(f"No LLM/BrandMatcher available, using pattern fallback for '{team_name}'")
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.5
        
        # Level 1: Check team name cache (exact match)
        cached = await self._brand_matcher.check_team_name(team_name)
        if cached:
            logger.info(f"Using cached sponsors for '{team_name}'")
            return cached, 1.0
        
        # Level 2: Check brand coverage (word-level matching)
        match_result = await self._brand_matcher.analyze_words(team_name)
        
        if not match_result.needs_llm:
            # All words are known brands - no LLM needed
            logger.info(f"All brands known for '{team_name}', skipping LLM")
            sponsors = [SponsorInfo(brand_name=b) for b in match_result.known_brands]
            return sponsors, 1.0
        
        # Level 3: Call LLM for unknown words
        try:
            logger.info(f"Calling LLM for '{team_name}' (unknown: {match_result.unmatched_words})")
            llm_result = await self._llm_prompts.extract_sponsors_from_name(
                team_name=team_name,
                season_year=season_year,
                country_code=country_code,
                partial_matches=match_result.known_brands
            )
            
            logger.debug(
                f"LLM extraction complete for '{team_name}': "
                f"{len(llm_result.sponsors)} sponsors, confidence={llm_result.confidence}"
            )
            return llm_result.sponsors, llm_result.confidence
            
        except Exception as e:
            logger.exception(f"LLM extraction failed for '{team_name}': {e}")
            # Fallback: simple pattern extraction
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.3

from pydantic import BaseModel
from typing import Optional

class SponsorResolution(BaseModel):
    """LLM-resolved sponsor information."""
    raw_name: str
    master_name: str
    brand_name: str
    hex_color: str
    confidence: float
    reasoning: Optional[str] = None
