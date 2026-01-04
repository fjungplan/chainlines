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

class DiscoveryService:
    """Orchestrates Phase 1: Team discovery and sponsor collection."""
    
    def __init__(
        self,
        scraper: CyclingFlashScraper,
        checkpoint_manager: CheckpointManager
    ):
        self._scraper = scraper
        self._checkpoint = checkpoint_manager
        self._collector = SponsorCollector()
    
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
            try:
                urls = await self._scraper.get_team_list(year)
                for url in urls:
                    # Even if URL is already in queue, we might need to check other seasons
                    # but Phase 1 builds the "skeleton" of unique nodes later.
                    # For now, we collect all URLs that match the tier in any year.
                    data = await self._scraper.get_team(url, year)
                    
                    if tier_level and data.tier_level != tier_level:
                        continue
                        
                    if url not in team_urls:
                        team_urls.append(url)
                        self._collector.add(data.sponsors)
                        
                        # Save checkpoint periodically
                        self._save_checkpoint(team_urls)
                        
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
