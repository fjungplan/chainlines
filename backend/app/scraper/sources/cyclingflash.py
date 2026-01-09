"""CyclingFlash scraper implementation."""
import re
import hashlib
from typing import Optional, List
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from app.scraper.base import BaseScraper
from app.scraper.llm.models import SponsorInfo

class ScrapedTeamData(BaseModel):
    """Data scraped from a team's detail page."""
    name: str
    uci_code: Optional[str] = None
    tier_level: Optional[int] = None
    country_code: Optional[str] = Field(default=None, description="3-letter IOC/UCI code")
    sponsors: list[SponsorInfo] = Field(default_factory=list)
    previous_season_url: Optional[str] = None
    season_year: int
    extraction_confidence: Optional[float] = Field(
        default=None,
        description="Confidence of sponsor extraction (if LLM was used)"
    )
    available_years: List[int] = Field(
        default_factory=list,
        description="Years available in team history dropdown (for identity matching)"
    )
    dissolution_year: Optional[int] = Field(
        default=None,
        description="Year the team dissolved (derived from max year in identity group)"
    )
    team_identity_id: Optional[str] = Field(
        default=None,
        description="Stable identity hash derived from team history dropdown"
    )

class CyclingFlashParser:
    """Parser for CyclingFlash HTML."""
    
    # Tier section headers as they appear on CyclingFlash
    TIER_HEADERS = {
        1: ["trade team 1", "uci proteam", "uci worldteam"],
        2: ["trade team 2", "uci professional continental team", "uci proteam"],
        3: ["trade team 3", "uci continental team"],
    }
    
    def parse_team_list(self, html: str, target_tier: int = None) -> list[str]:
        """Extract team URLs from list page.
        
        Args:
            html: Raw HTML of team list page
            target_tier: If provided, only return teams from this tier section
            
        Returns:
            List of team URLs (paths)
        """
        soup = BeautifulSoup(html, 'html.parser')
        urls = []
        
        # Simple extraction: all team links
        for link in soup.find_all('a', href=True):
            # Filter out sidebar/nav links (li parents)
            if link.find_parent('li'):
                continue
            href = link.get('href')
            if href and '/team/' in href and not href.endswith('/teams'):
                if href not in urls:
                    urls.append(href)
        
        return urls
    
    def parse_team_list_by_tier(self, html: str) -> dict[int, list[str]]:
        """Parse team list and group URLs by tier section.
        
        This is an optimization for when only specific tiers are needed.
        
        Returns:
            Dict mapping tier level (1, 2, 3) to list of team URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to find tier sections by headers
        result = {1: [], 2: [], 3: []}
        current_tier = None
        
        # Look for section headers (h2, h3, or div with tier keywords)
        for element in soup.find_all(['h2', 'h3', 'div', 'section', 'a']):
            text = element.get_text(strip=True).lower()
            
            # Check if this is a tier header
            for tier, keywords in self.TIER_HEADERS.items():
                if any(kw in text for kw in keywords):
                    current_tier = tier
                    break
            
            # If it's a team link and we know the tier, add it
            if element.name == 'a':
                # Filter out sidebar/nav links (li parents)
                if element.find_parent('li'):
                    continue
                href = element.get('href', '')
                if '/team/' in href and not href.endswith('/teams'):
                    if current_tier and href not in result[current_tier]:
                        result[current_tier].append(href)
        
        return result


    def parse_team_detail(self, html: str, season_year: int, url: str = None) -> ScrapedTeamData:
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
        
        # Map country code
        from app.scraper.utils.country_mapper import map_country_to_code
        country_code = map_country_to_code(country_code)
        
        # Extract TITLE sponsors from team name (most prominent)
        from app.scraper.utils.sponsor_extractor import extract_title_sponsors
        title_sponsors = extract_title_sponsors(name)
        
        # Extract EQUIPMENT sponsors from brand links
        equipment_sponsors = []
        for link in soup.select('a[href*="/brands/"]'):
            sponsor_name = link.get_text(strip=True)
            if sponsor_name and sponsor_name not in equipment_sponsors:
                equipment_sponsors.append(sponsor_name)
        
        # Combine: Title sponsors first (primary), then equipment sponsors
        combined_sponsors = title_sponsors.copy()
        for s in equipment_sponsors:
            if s not in combined_sponsors:  # Avoid duplicates
                combined_sponsors.append(s)
        
        # Convert to SponsorInfo (without parent company at parse time)
        sponsors = [SponsorInfo(brand_name=s) for s in combined_sponsors]
        
        # Extract previous season link (if any)
        # Search for links containing "Season" or similar patterns
        prev_url = None
        prev_link = soup.find('a', string=re.compile(r"Previous Season", re.I))
        if prev_link:
            prev_url = prev_link.get('href')
        
        
        # Extract team identity from Next.js streaming data (editions object)
        # CyclingFlash embeds team lineage in __next_f.push script tags
        # Format: self.__next_f.push([...,"editions":{"slug-2026":"Name (2026)",...},...])
        team_identity_id = None
        
        # Find all script tags containing __next_f.push
        scripts = soup.find_all('script')
        editions_slugs = []
        
        
        for script in scripts:
            script_text = script.string
            if script_text and '\\"editions\\"' in script_text:
                # Extract editions using regex - handles escaped quotes in script
                import json
                try:
                    # Match \"editions\":{...} where {...} contains the slug mappings
                    # The editions object is flat (no nested braces)
                    # Note: script contains escaped quotes like \"editions\":{\"slug\":\"Name\"}
                    match = re.search(r'\\"editions\\":\{([^}]+)\}', script_text)
                    if match:
                        editions_content = match.group(1)
                        # Unescape the content and build valid JSON
                        editions_content = editions_content.replace('\\"', '"')
                        editions_json = '{"editions":{' + editions_content + '}}'
                        editions_data = json.loads(editions_json)
                        editions_slugs = list(editions_data.get('editions', {}).keys())
                        if editions_slugs:
                            break
                except (json.JSONDecodeError, ValueError):
                    continue
        
        # Generate identity from the sorted list of edition slugs
        dissolution_year = None
        
        if editions_slugs:
            # Sort slugs to ensure consistent identity across all pages
            sorted_slugs = sorted(editions_slugs)
            # Create hash from all slugs combined
            identity_source = ':'.join(sorted_slugs)
            team_identity_id = hashlib.md5(identity_source.encode()).hexdigest()[:16]
            
            # Calculate dissolution year
            # If the current season_year is the last year in the editions list,
            # then this team identity effectively dissolves/ends this year.
            years = []
            for slug in sorted_slugs:
                # Typical format: team-name-2023
                # We look for 4 digits at the end of the slug
                m = re.search(r'-(\d{4})$', slug)
                if m:
                    years.append(int(m.group(1)))
            
            if years:
                max_year = max(years)
                # If the max year in the dropdown is LESS than the current real-world year,
                # then the team definitely dissolved/ended in the past.
                # We avoid using <= season_year because for current/future seasons, 
                # max_year equals season_year but the team is active.
                import datetime
                current_year = datetime.datetime.now().year
                
                if max_year < current_year:
                    dissolution_year = max_year
        
        
        return ScrapedTeamData(
            name=name,
            uci_code=uci_code,
            tier_level=tier_level,
            country_code=country_code,
            sponsors=sponsors,
            previous_season_url=prev_url,
            season_year=season_year,
            available_years=[],  # Not using dropdown anymore
            dissolution_year=dissolution_year,
            team_identity_id=team_identity_id
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
    
    async def get_team_list_by_tier(self, year: int, tier: int) -> list[str]:
        """Get list of team URLs for a specific tier in a given year.
        
        This is an optimization - if the site groups teams by tier,
        we can skip fetching details for teams outside the target tier.
        
        Falls back to full list if tier detection fails.
        """
        url = f"{self.BASE_URL}/teams/{year}"
        html = await self.fetch(url)
        
        tier_results = self._parser.parse_team_list_by_tier(html)
        
        if tier_results.get(tier):
            return tier_results[tier]
        
        # Fallback: return all teams if tier parsing didn't work
        return self._parser.parse_team_list(html)
    
    async def get_team(self, path: str, season_year: int) -> ScrapedTeamData:
        """Get team details from a team page."""
        url = f"{self.BASE_URL}{path}" if not path.startswith("http") else path
        html = await self.fetch(url)
        return self._parser.parse_team_detail(html, season_year, path)
