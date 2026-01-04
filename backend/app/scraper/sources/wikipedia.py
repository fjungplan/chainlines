"""Wikipedia scraper implementation."""
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from app.scraper.base import BaseScraper


class WikipediaParser:
    """Parser for Wikipedia HTML."""

    # Keywords for "Founded" in supported languages
    FOUNDED_KEYWORDS = {
        "en": ["founded", "established"],
        "de": ["gründung", "gegründet"],
        "fr": ["fondation", "date de fondation", "création"],
        "it": ["fondazione"],
        "es": ["fundación", "fecha de fundación"],
        "nl": ["opgericht", "oprichting"],
    }

    def parse_team(self, html: str, lang: str = "en") -> Dict[str, Any]:
        """Extract team data from Wikipedia page."""
        soup = BeautifulSoup(html, "html.parser")
        founded_year = None
        
        # Look for Infobox
        infobox = soup.select_one("table.infobox")
        if infobox:
            founded_year = self._extract_founded_from_infobox(infobox, lang)
        
        return {"founded_year": founded_year}

    def _extract_founded_from_infobox(self, infobox: Any, lang: str) -> Optional[int]:
        """Extract founded year from infobox rows."""
        keywords = self.FOUNDED_KEYWORDS.get(lang.lower(), self.FOUNDED_KEYWORDS["en"])
        
        for row in infobox.select("tr"):
            header = row.select_one("th")
            if not header:
                continue
            
            header_text = header.get_text().strip().lower()
            if any(k in header_text for k in keywords):
                cell = row.select_one("td")
                if cell:
                    # Look for 4 digits
                    match = re.search(r"(\d{4})", cell.get_text())
                    if match:
                        return int(match.group(1))
        return None


class WikipediaScraper(BaseScraper):
    """Scraper for Wikipedia (Multi-language)."""

    def __init__(self, **kwargs):
        super().__init__(min_delay=3.0, max_delay=6.0, **kwargs)
        self._parser = WikipediaParser()

    async def get_team(self, slug: str, lang: str = "en") -> Dict[str, Any]:
        """Fetch team data from Wikipedia."""
        url = f"https://{lang}.wikipedia.org/wiki/{slug}"
        html = await self.fetch(url)
        return self._parser.parse_team(html, lang)
