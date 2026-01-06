from bs4 import BeautifulSoup
from app.scraper.base.scraper import BaseScraper

class FirstCyclingParser:
    def parse_gt_start_list(self, html: str) -> list[str]:
        """Extract team names from GT start list HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        teams = []
        # Look for team links or cells in the table
        for row in soup.select('table tr'):
            team_cell = row.select_one('td:nth-child(2)')
            if team_cell:
                name = team_cell.get_text(strip=True)
                if name:
                    teams.append(name)
        return teams

class FirstCyclingScraper(BaseScraper):
    """Scraper for FirstCycling.com."""
    
    BASE_URL = "https://firstcycling.com"
    RATE_LIMIT_SECONDS = 10.0
    
    GT_RACE_IDS = {
        "giro": 13,
        "tour": 17,
        "vuelta": 23
    }
    
    def __init__(self, **kwargs):
        # Override default delays with 10s crawl delay as requested
        super().__init__(rate_limit=self.RATE_LIMIT_SECONDS, **kwargs)
    
    def get_gt_start_list_url(self, race: str, year: int) -> str:
        """Generate URL for a Grand Tour start list."""
        race_id = self.GT_RACE_IDS[race.lower()]
        return f"{self.BASE_URL}/race.php?r={race_id}&y={year}&k=8"
    
    async def fetch_gt_start_list(self, race: str, year: int) -> str:
        """Fetch Grand Tour start list HTML."""
        url = self.get_gt_start_list_url(race, year)
        return await self.fetch(url)
