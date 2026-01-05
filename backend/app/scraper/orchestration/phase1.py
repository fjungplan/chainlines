"""Phase 1: Discovery and Sponsor Collection."""
from typing import Set, List, Optional

class SponsorCollector:
    """Collects unique sponsor names across all teams."""
    
    def __init__(self):
        self._names: Set[str] = set()
    
    def add(self, sponsors: List[str]) -> None:
        """Add sponsor names to collection."""
        for name in sponsors:
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
        monitor: Optional[ScraperStatusMonitor] = None
    ):
        self._scraper = scraper
        self._checkpoint = checkpoint_manager
        self._collector = SponsorCollector()
        self._monitor = monitor
    
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
                    logger.info(f"    - Sponsors: {', '.join(data.sponsors) if data.sponsors else 'None'}")
                    
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
            sponsor_names=self._collector.get_all()
        ))

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
