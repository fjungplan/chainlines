"""Phase 2.5: Node Enrichment - Wikipedia scraping once per node."""
import logging
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import TeamNode
from app.scraper.base.scraper import BaseScraper
from app.scraper.services.wikidata import WikidataResolver

logger = logging.getLogger(__name__)

# Wikipedia language codes to scrape (in priority order)
WIKI_LANGUAGES = ["en", "fr", "de", "nl", "it", "es"]


class NodeEnrichmentService:
    """
    Enriches TeamNodes with Wikipedia content for lineage analysis.
    
    Scrapes Wikipedia history section in all 6 languages and concatenates
    the content into TeamNode.wikipedia_summary.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        scraper: BaseScraper,
        wikidata_resolver: WikidataResolver
    ):
        self._session = session
        self._scraper = scraper
        self._wikidata = wikidata_resolver
    
    async def enrich_all_nodes(self) -> int:
        """
        Enrich all TeamNodes that don't have wikipedia_summary yet.
        
        Returns:
            Number of nodes enriched
        """
        # Find nodes without Wikipedia summary
        stmt = select(TeamNode).where(TeamNode.wikipedia_summary.is_(None))
        result = await self._session.execute(stmt)
        nodes = result.scalars().all()
        
        if not nodes:
            logger.info("Phase 2.5: All nodes already have Wikipedia summaries")
            return 0
        
        logger.info(f"Phase 2.5: Enriching {len(nodes)} nodes with Wikipedia content")
        enriched_count = 0
        
        for i, node in enumerate(nodes, 1):
            logger.info(f"  Node {i}/{len(nodes)}: {node.legal_name}")
            
            try:
                summary = await self._fetch_wikipedia_summary(node.legal_name)
                if summary:
                    node.wikipedia_summary = summary
                    enriched_count += 1
                    logger.info(f"    ✓ Enriched ({len(summary)} chars)")
                else:
                    logger.info(f"    ✗ No Wikipedia content found")
            except Exception as e:
                logger.warning(f"    ✗ Error: {e}")
        
        await self._session.commit()
        logger.info(f"Phase 2.5: Enriched {enriched_count}/{len(nodes)} nodes")
        return enriched_count
    
    async def _fetch_wikipedia_summary(self, team_name: str) -> Optional[str]:
        """
        Fetch Wikipedia history content in all languages for a team.
        
        Args:
            team_name: Name of the team to search for
            
        Returns:
            Concatenated history content from all languages, or None
        """
        # First, resolve Wikidata to get Wikipedia sitelinks
        wikidata_result = await self._wikidata.resolve(team_name)
        if not wikidata_result or not wikidata_result.sitelinks:
            return None
        
        # Collect history from all available languages
        all_history = []
        
        for lang in WIKI_LANGUAGES:
            wiki_url = wikidata_result.sitelinks.get(f"{lang}wiki")
            if not wiki_url:
                continue
            
            try:
                history_text = await self._fetch_history_section(wiki_url, lang)
                if history_text:
                    # Prefix with language for clarity
                    all_history.append(f"[{lang.upper()}]\n{history_text}")
            except Exception as e:
                logger.debug(f"    Failed to fetch {lang} Wikipedia: {e}")
        
        if all_history:
            return "\n\n---\n\n".join(all_history)
        return None
    
    async def _fetch_history_section(self, url: str, lang: str) -> Optional[str]:
        """
        Fetch and extract the History section from a Wikipedia page.
        
        Args:
            url: Wikipedia URL
            lang: Language code (for header matching)
            
        Returns:
            History section text, or None
        """
        from bs4 import BeautifulSoup
        
        try:
            html = await self._scraper.fetch(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try common History header IDs across languages
            history_headers = self._get_history_header_ids(lang)
            
            for header_id in history_headers:
                history_header = soup.find(id=header_id)
                if history_header:
                    return self._extract_section_content(history_header)
            
            return None
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None
    
    def _get_history_header_ids(self, lang: str) -> List[str]:
        """Get possible History section header IDs for a language."""
        headers = {
            "en": ["History", "Team_history"],
            "fr": ["Histoire", "Historique"],
            "de": ["Geschichte", "Teamgeschichte"],
            "nl": ["Geschiedenis"],
            "it": ["Storia"],
            "es": ["Historia"]
        }
        return headers.get(lang, ["History"])
    
    def _extract_section_content(self, header_element) -> Optional[str]:
        """Extract text content from a section until the next h2."""
        content = []
        
        # Navigate to parent h2 if header is a span
        parent = header_element.parent if header_element.name != 'h2' else header_element
        
        for sibling in parent.find_next_siblings():
            if sibling.name == 'h2':
                break
            text = sibling.get_text(strip=True)
            if text:
                content.append(text)
        
        return '\n'.join(content) if content else None
