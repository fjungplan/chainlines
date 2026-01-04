"""CyclingFlash scraper implementation."""
import re
from typing import Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from app.scraper.base import BaseScraper

class ScrapedTeamData(BaseModel):
    """Data extracted from a team page."""
    name: str
    uci_code: Optional[str] = None
    tier_level: Optional[int] = None
    country_code: Optional[str] = Field(
        default=None,
        description="3-letter IOC/UCI country code (e.g., NED, GER, ITA, FRA)"
    )
    sponsors: list[str] = []
    previous_season_url: Optional[str] = None
    season_year: int

class CyclingFlashParser:
    """Parser for CyclingFlash HTML."""
    
    def parse_team_list(self, html: str) -> list[str]:
        """Extract team URLs from list page."""
        soup = BeautifulSoup(html, 'html.parser')
        urls = []
        
        # New structure uses team-card or simply links containing /team/
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            # Filter for team links, ensuring we don't pick up duplicates or root links
            if href and '/team/' in href and not href.endswith('/teams'):
                # Avoid duplicates in the list
                if href not in urls:
                    urls.append(href)
        
        return urls

    def parse_team_detail(self, html: str, season_year: int) -> ScrapedTeamData:
        """Extract team data from detail page."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract name from H1 (remove year suffix)
        header = soup.select_one('h1')
        raw_name = header.get_text(strip=True) if header else "Unknown"
        name = re.sub(r'\s*\(\d{4}\)\s*$', '', raw_name)
        
        # Metadata table parsing
        uci_code = None
        raw_tier = None
        country_code = None
        
        table = soup.find('table')
        if table:
            for tr in table.find_all('tr'):
                cells = tr.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    if 'code' in label:
                        uci_code = value
                    elif 'category' in label:
                        raw_tier = value
                    elif 'country' in label:
                        country_code = value

        # Map tier level
        from app.scraper.utils.tier_mapper import map_tier_label_to_level
        tier_level = map_tier_label_to_level(raw_tier, season_year)
        
        # Extract sponsors from brand links
        sponsors = []
        for link in soup.select('a[href*="/brands/"]'):
            sponsor_name = link.get_text(strip=True)
            if sponsor_name and sponsor_name not in sponsors:
                sponsors.append(sponsor_name)
        
        # Extract previous season link (if any)
        # Search for links containing "Season" or similar patterns
        prev_url = None
        prev_link = soup.find('a', string=re.compile(r"Previous Season", re.I))
        if prev_link:
            prev_url = prev_link.get('href')
        
        return ScrapedTeamData(
            name=name,
            uci_code=uci_code,
            tier_level=tier_level,
            country_code=country_code,
            sponsors=sponsors,
            previous_season_url=prev_url,
            season_year=season_year
        )

    def _get_text(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Safely extract text from selector."""
        elem = soup.select_one(selector)
        return elem.get_text(strip=True) if elem else None

class CyclingFlashScraper(BaseScraper):
    """Scraper for CyclingFlash website."""
    
    BASE_URL = "https://cyclingflash.com"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._parser = CyclingFlashParser()
    
    async def get_team_list(self, year: int) -> list[str]:
        """Get list of team URLs for a given year."""
        # The URL often redirects to /teams/{year}/road/men
        url = f"{self.BASE_URL}/teams/{year}"
        html = await self.fetch(url)
        return self._parser.parse_team_list(html)
    
    async def get_team(self, path: str, season_year: int) -> ScrapedTeamData:
        """Get team details from a team page."""
        url = f"{self.BASE_URL}{path}" if not path.startswith("http") else path
        html = await self.fetch(url)
        return self._parser.parse_team_detail(html, season_year)
