from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, TYPE_CHECKING
from bs4 import BeautifulSoup
import logging

if TYPE_CHECKING:
    from app.scraper.base.scraper import BaseScraper

logger = logging.getLogger(__name__)

from pydantic import BaseModel

class SourceData(BaseModel):
    """Data returned by a source worker."""
    source: str
    raw_content: Optional[str] = None
    founded_year: Optional[int] = None
    dissolved_year: Optional[int] = None
    history_text: Optional[str] = None
    extra: Dict[str, Any] = {}

class SourceWorker(ABC):
    """Abstract base for source-specific workers."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source."""
        pass
    
    @abstractmethod
    async def fetch(self, url: str) -> Optional[SourceData]:
        """Fetch and parse data from this source."""
        pass

class WikipediaWorker(SourceWorker):
    source_name = "wikipedia"
    
    def __init__(self, scraper: "BaseScraper"):
        self._scraper = scraper
    
    async def fetch(self, url: str) -> Optional[SourceData]:
        try:
            html = await self._scraper.fetch(url)
            return self._parse(html)
        except Exception as e:
            logger.warning(f"Wikipedia fetch failed: {e}")
            return None
    
    def _parse(self, html: str) -> SourceData:
        soup = BeautifulSoup(html, 'html.parser')
        
        history_text = None
        # Find History header (usually h2 with id="History" or text "History")
        # Wikipedia often uses <span class="mw-headline" id="History">History</span> inside h2
        history_header = soup.find(id="History")
        if history_header:
            content = []
            # The header is often inside an h2, so we look for siblings of the h2
            # history_header might be the span inside h2, or the h2 itself if found differently.
            # If finding by ID, it finds the span usually. The parent is the h2.
            parent = history_header.parent if history_header.name != 'h2' else history_header
            
            for sibling in parent.find_next_siblings():
                if sibling.name == 'h2':
                    break
                # Skip some elements if needed, but gathering text is usually enough
                text = sibling.get_text(strip=True)
                if text:
                    content.append(text)
            
            if content:
                history_text = '\n'.join(content)
        
        founded_year = self._extract_founded_year(soup)
        
        return SourceData(
            source=self.source_name,
            history_text=history_text,
            founded_year=founded_year
        )
    
    def _extract_founded_year(self, soup: BeautifulSoup) -> Optional[int]:
        try:
            infobox = soup.find("table", class_="infobox")
            if not infobox:
                return None
                
            for tr in infobox.find_all("tr"):
                th = tr.find("th")
                if th and "Founded" in th.get_text():
                    td = tr.find("td")
                    if td:
                        text = td.get_text(strip=True)
                        # Extract first 4 digit number
                        import re
                        match = re.search(r'\d{4}', text)
                        if match:
                            return int(match.group(0))
        except Exception:
            return None
        return None

class CyclingRankingWorker(SourceWorker):
    source_name = "cyclingranking"

    def __init__(self, scraper: "BaseScraper"):
        self._scraper = scraper

    async def fetch(self, url: str) -> Optional[SourceData]:
        try:
            html = await self._scraper.fetch(url)
            return self._parse(html)
        except Exception as e:
            logger.warning(f"CyclingRanking fetch failed: {e}")
            return None

    def _parse(self, html: str) -> SourceData:
        soup = BeautifulSoup(html, 'html.parser')
        
        founded_year = self._extract_year(soup, "founded")
        dissolved_year = self._extract_year(soup, "dissolved")

        return SourceData(
            source=self.source_name,
            founded_year=founded_year,
            dissolved_year=dissolved_year
        )

    def _extract_year(self, soup: BeautifulSoup, class_name: str) -> Optional[int]:
        import re
        element = soup.find(class_=class_name)
        if element:
            text = element.get_text(strip=True)
            match = re.search(r'\d{4}', text)
            if match:
                return int(match.group(0))
        return None

class MemoireWorker(SourceWorker):
    source_name = "memoire"
    WAYBACK_PREFIX = "https://web.archive.org/web/2020/"
    
    def __init__(self, scraper: "BaseScraper"):
        self._scraper = scraper
    
    async def fetch(self, original_url: str) -> Optional[SourceData]:
        wayback_url = f"{self.WAYBACK_PREFIX}{original_url}"
        try:
            html = await self._scraper.fetch(wayback_url)
            return self._parse(html)
        except Exception as e:
            logger.warning(f"Memoire fetch failed: {e}")
            return None

    def _parse(self, html: str) -> SourceData:
        return SourceData(
            source=self.source_name,
            raw_content=html
        )

