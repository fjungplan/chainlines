"""CyclingRanking scraper implementation."""
import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from app.scraper.base import BaseScraper


class CyclingRankingParser:
    """Parser for CyclingRanking HTML."""

    def parse_team(self, html: str) -> Dict[str, Any]:
        """Extract team data from page."""
        soup = BeautifulSoup(html, "html.parser")

        founded = None
        founded_elem = soup.select_one('.founded')
        if founded_elem:
            match = re.search(r"(\d{4})", founded_elem.get_text())
            if match:
                founded = int(match.group(1))

        return {"founded_year": founded}


class CyclingRankingScraper(BaseScraper):
    """Scraper for CyclingRanking website."""

    BASE_URL = "https://cyclingranking.com"

    def __init__(self, **kwargs):
        super().__init__(min_delay=3.0, max_delay=6.0, **kwargs)
        self._parser = CyclingRankingParser()

    async def get_team(self, team_slug: str) -> Dict[str, Any]:
        """Get enrichment data for a team."""
        url = f"{self.BASE_URL}/team/{team_slug}"
        html = await self.fetch(url)
        return self._parser.parse_team(html)
