"""Phase 1: Discovery and Sponsor Collection."""
from typing import Set, List, Optional, Union, Tuple, Dict, TYPE_CHECKING
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
from app.scraper.services.gt_relevance import GTRelevanceIndex

class DiscoveryService:
    """Orchestrates Phase 1: Team discovery and sponsor collection."""
    
    def __init__(
        self,
        scraper: CyclingFlashScraper,
        checkpoint_manager: CheckpointManager,
        monitor: Optional[ScraperStatusMonitor] = None,
        session: Optional[AsyncSession] = None,
        llm_prompts: Optional["ScraperPrompts"] = None,
        gt_index: Optional[GTRelevanceIndex] = None
    ):
        self._scraper = scraper
        self._checkpoint = checkpoint_manager
        self._collector = SponsorCollector()
        self._monitor = monitor
        self._session = session
        self._llm_prompts = llm_prompts
        self._gt_index = gt_index or GTRelevanceIndex()
        self._retry_queue: List[Tuple[str, dict]] = []  # (team_name, context)
        
        # Initialize brand matcher if session available
        self._brand_matcher = BrandMatcherService(session) if session else None
        
        # Initialize enricher once to enable LLM caching across teams
        # (Previously created per-team, resetting the in-memory cache)
        self._enricher = None
        if session and llm_prompts:
            from app.scraper.services.enrichment import TeamEnrichmentService
            self._enricher = TeamEnrichmentService(session, llm_prompts)
        
        # Team history tracking for gap backfill
        self._team_histories: Dict[str, List[int]] = {}  # team_name -> available_years from dropdown
        self._scraped_teams: Dict[str, Set[int]] = {}     # team_name -> years already scraped
        self._url_by_team: Dict[str, str] = {}            # team_name -> base URL for backfilling
        
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
        team_urls: list[tuple[str, int]] = []  # Changed to (URL, year) tuples
        
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

                    # 1. First apply tier targeting if manually requested
                    if tier_level and data.tier_level != tier_level:
                        logger.info(f"{prefix}: SKIPPING '{data.name}' - Target Tier {tier_level} vs Found {data.tier_level}")
                        continue

                    # 2. Then apply relevance rules (Dual Seeding)
                    if not self._is_relevant(data.name, data.tier_level, year):
                        logger.info(f"{prefix}: SKIPPING '{data.name}' - Irrelevant via rules (Tier {data.tier_level} in {year})")
                        continue
                        
                    logger.info(f"{prefix}: COLLECTED '{data.name}'")
                    logger.info(f"    - Details: UCI: {data.uci_code}, Country: {data.country_code}, Tier: {data.tier_level}")
                    
                    # Enrich with LLM data (reusing single enricher for cache benefits)
                    if self._enricher:
                        data = await self._enricher.enrich_team_data(data)

                    sponsor_names = [s.brand_name for s in data.sponsors]
                    logger.info(f"    - Sponsors: {', '.join(sponsor_names) if sponsor_names else 'None'}")
                    
                    # Store (URL, year) tuple to ensure correct year is processed in Phase 2
                    url_year_pair = (url, year)
                    if url_year_pair not in team_urls:
                        team_urls.append(url_year_pair)
                        self._collector.add(data.sponsors)
                        
                        # Track for backfill: store available_years and scraped year
                        if data.available_years:
                            self._team_histories[data.name] = data.available_years
                        self._scraped_teams.setdefault(data.name, set()).add(year)
                        self._url_by_team[data.name] = url.rsplit('-', 1)[0]  # Base URL without year
                        
                        # Save checkpoint periodically
                        if i % 10 == 0 or i == len(urls):
                            self._save_checkpoint(team_urls)
                            logger.info(f"    - Checkpoint saved ({len(team_urls)} unique teams in queue)")
                        
            except Exception as e:
                logger.error(f"Error in year {year}: {e}")
                self._save_checkpoint(team_urls)
                raise
        
        # Backfill gaps in team history (PASS 2)
        team_urls = await self._backfill_gaps(team_urls)
        
        # Process retry queue at end of all years
        await self._process_retry_queue()
        
        # CRITICAL: Save final checkpoint with all URLs including backfilled ones
        self._save_checkpoint(team_urls)
        logger.info(f"Final checkpoint saved with {len(team_urls)} team-year pairs")
        
        return DiscoveryResult(
            team_urls=team_urls,
            sponsor_names=self._collector.get_all()
        )
    
    def _is_relevant(self, team_name: str, tier: int, year: int) -> bool:
        """
        Apply relevance filtering rules.
        - Post-1999: Keep Tier 1 and 2 only.
        - 1991-1998: Keep Tier 1. Keep Tier 2 ONLY if in GT index.
        - Pre-1991: Keep ONLY if in GT index.
        """
        if year >= 1999:
            return tier in (1, 2)
        elif year >= 1991:
            if tier == 1:
                return True
            elif tier == 2:
                return self._gt_index.is_relevant(team_name, year)
            return False
        else:  # Pre-1991
            return self._gt_index.is_relevant(team_name, year)

    def _save_checkpoint(self, team_urls: list[tuple[str, int]]) -> None:
        """Save current progress."""
        self._checkpoint.save(CheckpointData(
            phase=1,
            team_queue=team_urls,
        ))
    
    async def _backfill_gaps(
        self,
        team_urls: list[tuple[str, int]]
    ) -> list[tuple[str, int]]:
        """
        Backfill missing years to preserve lineage continuity (PASS 2).
        
        Uses team history dropdown data to identify gaps in scraped years
        and adds missing years to the queue if they close a gap.
        """
        if not self._team_histories:
            logger.debug("No team histories collected, skipping backfill")
            return team_urls
        
        backfilled = 0
        for team_name, available_years in self._team_histories.items():
            scraped_years = self._scraped_teams.get(team_name, set())
            base_url = self._url_by_team.get(team_name)
            
            if not base_url or not scraped_years:
                continue
            
            # Find gaps: years in dropdown but not scraped
            missing_years = set(available_years) - scraped_years
            
            for year in sorted(missing_years, reverse=True):
                # Only backfill if it closes a gap (has adjacent scraped years)
                if self._closes_gap(year, scraped_years):
                    url_for_year = f"{base_url}-{year}"
                    url_year_pair = (url_for_year, year)
                    
                    if url_year_pair not in team_urls:
                        team_urls.append(url_year_pair)
                        backfilled += 1
                        logger.info(f"Backfilling '{team_name}' ({year}) to close gap")
        
        if backfilled > 0:
            logger.info(f"Backfill complete: added {backfilled} team-year pairs")
            self._save_checkpoint(team_urls)
        
        return team_urls
    
    def _closes_gap(self, year: int, scraped_years: Set[int]) -> bool:
        """
        Check if year is between two scraped years (closes a gap).
        
        Args:
            year: The year to check
            scraped_years: Set of already scraped years for this team
            
        Returns:
            True if this year closes a gap, False otherwise
        """
        if not scraped_years or len(scraped_years) < 2:
            return False
        
        sorted_years = sorted(scraped_years)
        # Check if year falls between min and max scraped years
        return min(sorted_years) < year < max(sorted_years)
    
    async def _extract_with_resilience(
        self,
        team_name: str,
        country_code: Optional[str],
        season_year: int,
        partial_matches: List[str]
    ) -> Tuple[List[SponsorInfo], float]:
        """
        Extract sponsors with full multi-tier resilience.
        Tier 1: Gemini → Tier 2: Deepseek → Tier 3: Exponential backoff retries
        
        Args:
            team_name: The team name to extract sponsors from.
            country_code: 3-letter IOC/UCI country code.
            season_year: Season year for context.
            partial_matches: Known brands from word-level matching.
            
        Returns:
            Tuple of (sponsors, confidence).
        """
        import asyncio
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # The LLM service already has Gemini → Deepseek fallback built-in
                llm_result = await self._llm_prompts.extract_sponsors_from_name(
                    team_name=team_name,
                    season_year=season_year,
                    country_code=country_code,
                    partial_matches=partial_matches
                )
                
                logger.info(
                    f"LLM extraction successful for '{team_name}' (attempt {attempt + 1}/{max_retries})"
                )
                
                # Detailed logging of LLM output
                log_msg = [
                    f"    - Confidence: {llm_result.confidence:.2f}",
                    f"    - Reasoning: {llm_result.reasoning}"
                ]
                
                sponsors_str = []
                for s in llm_result.sponsors:
                    s_str = f"'{s.brand_name}'"
                    if s.parent_company:
                        s_str += f" (Parent: {s.parent_company})"
                    sponsors_str.append(s_str)
                log_msg.append(f"    - Sponsors: {', '.join(sponsors_str)}")
                
                if llm_result.team_descriptors:
                    log_msg.append(f"    - Descriptors: {', '.join(llm_result.team_descriptors)}")
                if llm_result.filler_words:
                    log_msg.append(f"    - Fillers: {', '.join(llm_result.filler_words)}")
                    
                for msg in log_msg:
                    logger.info(msg)

                return llm_result.sponsors, llm_result.confidence
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"LLM extraction failed for '{team_name}' "
                        f"(attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # All retries exhausted
                    logger.error(
                        f"LLM extraction failed for '{team_name}' after {max_retries} attempts: {e}"
                    )
                    raise
    
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
        
        
        # Level 3: Call LLM with full resilience
        try:
            return await self._extract_with_resilience(
                team_name=team_name,
                country_code=country_code,
                season_year=season_year,
                partial_matches=match_result.known_brands
            )
            
        except Exception as e:
            # Final fallback after all resilience measures exhausted
            logger.exception(f"All extraction attempts failed for '{team_name}': {e}")
            
            # Add to retry queue
            self._retry_queue.append((team_name, {
                "country_code": country_code,
                "season_year": season_year,
                "partial_matches": match_result.known_brands if match_result else []
            }))
            
            logger.info(f"Added '{team_name}' to retry queue ({len(self._retry_queue)} items)")
            
            # Fallback: simple pattern extraction with lower confidence
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.2
    
    async def _process_retry_queue(self) -> None:
        """Process all items in retry queue at end of year."""
        if not self._retry_queue:
            logger.info("Retry queue is empty, skipping")
            return
        
        logger.info(f"Processing retry queue: {len(self._retry_queue)} items")
        
        retry_items = self._retry_queue.copy()
        self._retry_queue.clear()
        
        import asyncio
        
        for team_name, context in retry_items:
            try:
                logger.info(f"Retrying sponsor extraction for '{team_name}'")
                
                # Wait a bit between retries to avoid rate limits
                await asyncio.sleep(1)
                
                sponsors, confidence = await self._extract_sponsors(
                    team_name=team_name,
                    country_code=context["country_code"],
                    season_year=context["season_year"]
                )
                
                if confidence > 0.5:
                    logger.info(f"Retry successful for '{team_name}': {len(sponsors)} sponsors")
                else:
                    logger.warning(f"Retry fallback for '{team_name}': low confidence {confidence}")
                    
            except Exception as e:
                logger.exception(f"Retry failed for '{team_name}': {e}")

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
