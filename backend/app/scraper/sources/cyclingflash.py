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
    tier: Optional[str] = None
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
        
        for link in soup.select('.team-list a'):
            href = link.get('href')
            if href and '/team/' in href:
                urls.append(href)
        
        return urls

    def parse_team_detail(self, html: str, season_year: int) -> ScrapedTeamData:
        """Extract team data from detail page."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract name (remove year suffix)
        header = soup.select_one('.team-header h1')
        raw_name = header.get_text(strip=True) if header else "Unknown"
        name = re.sub(r'\s*\(\d{4}\)\s*$', '', raw_name)
        
        # Extract fields
        uci_code = self._get_text(soup, '.uci-code')
        tier = self._get_text(soup, '.tier')
        country_code = self._get_text(soup, '.country')
        
        # Extract sponsors
        sponsors = [s.get_text(strip=True) for s in soup.select('.sponsors .sponsor')]
        
        # Extract previous season link
        prev_link = soup.select_one('.prev-season')
        prev_url = prev_link.get('href') if prev_link else None
        
        return ScrapedTeamData(
            name=name,
            uci_code=uci_code,
            tier=tier,
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
        url = f"{self.BASE_URL}/teams/{year}"
        html = await self.fetch(url)
        return self._parser.parse_team_list(html)
    
    async def get_team(self, path: str, season_year: int) -> ScrapedTeamData:
        """Get team details from a team page."""
        url = f"{self.BASE_URL}{path}" if not path.startswith("http") else path
        html = await self.fetch(url)
        return self._parser.parse_team_detail(html, season_year)
