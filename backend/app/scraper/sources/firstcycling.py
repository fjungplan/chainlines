from bs4 import BeautifulSoup
import re
from app.scraper.base.scraper import BaseScraper

class FirstCyclingParser:
    def parse_gt_start_list(self, html: str) -> list[str]:
        """Extract team names from GT start list HTML.
        
        Team names are in thead > th > a[href*='team.php'] elements.
        Each team has a table with the team name in the header.
        """
        soup = BeautifulSoup(html, 'html.parser')
        teams = []
        
        # Team names are in thead > th > a[href contains 'team.php']
        for link in soup.select('thead th a[href*="team.php"]'):
            name = link.get_text(strip=True)
            # Normalize internal whitespace (collapse multiple spaces/newlines)
            name = re.sub(r'\s+', ' ', name).strip()
            if name and name not in teams:  # Avoid duplicates
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
        # Filter out bot user agents to avoid 403s on FirstCycling
        from app.scraper.base.user_agent import _USER_AGENTS
        browser_agents = [ua for ua in _USER_AGENTS if "Bot" not in ua]
        self._user_agent._agents = browser_agents
    
    def get_gt_start_list_url(self, race: str, year: int) -> str:
        """Generate URL for a Grand Tour start list."""
        race_id = self.GT_RACE_IDS[race.lower()]
        return f"{self.BASE_URL}/race.php?r={race_id}&y={year}&k=8"
    
    async def fetch_gt_start_list(self, race: str, year: int) -> str:
        """Fetch Grand Tour start list HTML using curl.exe to bypass Cloudflare TLS detection."""
        url = self.get_gt_start_list_url(race, year)
        
        # Check cache first via base method if it was implemented (it is in BaseScraper)
        if self._cache:
            cached = self._cache.get(url, domain=self._get_domain(url))
            if cached:
                return cached
        
        # Rate limiting
        await self._rate_limiter.wait()
        
        print(f"Fetching via curl: {url}")
        import subprocess
        import asyncio
        
        ua = self._user_agent.get()
        cmd = [
            "curl.exe", "-s", "-L",
            "-H", f"User-Agent: {ua}",
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            url
        ]
        
        # Run curl in a thread pool to avoid blocking async loop
        def run_curl():
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
            if result.returncode != 0:
                raise Exception(f"Curl failed with return code {result.returncode}: {result.stderr}")
            if "Cloudflare" in result.stdout and "challenge-platform" in result.stdout:
                 if len(result.stdout) < 10000: # Heuristic for challenge page
                    raise Exception("Cloudflare challenge detected in curl output")
            return result.stdout

        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, run_curl)
        
        # Save to cache if successful
        if self._cache and content:
            self._cache.set(url, content, domain=self._get_domain(url))
            
        return content
