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


class MemoireScraper(BaseScraper):
    """Scraper for Memoire du Cyclisme."""

    BASE_URL = "http://www.memoire-du-cyclisme.eu"

    def __init__(self, **kwargs):
        super().__init__(min_delay=3.0, max_delay=6.0, **kwargs)
        self._parser = MemoireParser()

    async def get_team(self, slug: str) -> Dict[str, Any]:
        """Get enrichment data for a team."""
        # Note: Exact URL structure varies, generic placeholder logic
        url = f"{self.BASE_URL}/{slug}"
        html = await self.fetch(url)
        return self._parser.parse_team(html)
