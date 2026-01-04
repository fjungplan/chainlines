"""Memoire du Cyclisme scraper."""
import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from app.scraper.base import BaseScraper


class MemoireParser:
    """Parser for Memoire du Cyclisme HTML."""

    def parse_team(self, html: str) -> Dict[str, Any]:
        """Extract team data from page."""
        soup = BeautifulSoup(html, "html.parser")
        founded = None
        
        # Text search is often more reliable on unstructured sites
        text = soup.get_text()
        
        # Look for "Année d'existence: 19XX"
        match = re.search(r"Année d'existence[:\s]+(\d{4})", text, re.IGNORECASE)
        if match:
            founded = int(match.group(1))
            
        return {"founded_year": founded}


from app.scraper.sources.wayback import WaybackScraper

class MemoireScraper(BaseScraper):
    """Scraper for Memoire du Cyclisme via Wayback Machine (site is offline)."""

    BASE_URL = "http://www.memoire-du-cyclisme.eu"

    def __init__(self, **kwargs):
        # We don't use BaseScraper's fetch directly, we use Wayback's
        # But we initialize it to keep interface consistent if needed,
        # or just initialize the sub-scraper.
        super().__init__(**kwargs)
        self._parser = MemoireParser()
        self._wayback = WaybackScraper(**kwargs)

    async def get_team(self, slug: str) -> Dict[str, Any]:
        """Get enrichment data for a team via Archive.org."""
        target_url = f"{self.BASE_URL}/{slug}"
        
        # 1. Find newest snapshot
        snapshot = await self._wayback.get_newest_snapshot(target_url)
        if not snapshot or "url" not in snapshot:
            return {"founded_year": None}
            
        # 2. Fetch content from Archive.org
        html = await self._wayback.fetch_archived_page(snapshot["url"])
        
        # 3. Parse
        return self._parser.parse_team(html)
