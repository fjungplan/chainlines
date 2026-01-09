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
            wiki_url = wikidata_result.sitelinks.get(lang)
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
            
            # First try exact ID match
            for header_id in history_headers:
                history_header = soup.find(id=header_id)
                if history_header:
                    content = self._extract_section_content(history_header)
                    if content:
                        return content
            
            # Fallback: Search for partial ID matches (e.g., "Histoire_de_l'équipe")
            for h2 in soup.find_all('h2'):
                # Check the h2 itself
                h2_id = h2.get('id', '')
                
                # Also check span children
                for span in h2.find_all('span'):
                    span_id = span.get('id', '')
                    for header_pattern in history_headers:
                        if header_pattern.lower() in h2_id.lower() or header_pattern.lower() in span_id.lower():
                            content = self._extract_section_content(h2)
                            if content:
                                return content
            
            # Final fallback: Extract lead section (intro paragraphs before first h2)
            # This often contains key information about the team
            lead_content = self._extract_lead_section(soup)
            if lead_content:
                return lead_content
            
            return None
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None
    
    def _get_history_header_ids(self, lang: str) -> List[str]:
        """Get possible History section header IDs for a language."""
        # Expanded list with common variations found on Wikipedia
        headers = {
            "en": ["History", "Team_history", "History_of_the_team"],
            "fr": ["Histoire", "Historique", "Histoire_de_l'équipe", "Histoire_de_l"],
            "de": ["Geschichte", "Teamgeschichte", "Organisation_und_Geschichte"],
            "nl": ["Geschiedenis", "Teamgeschiedenis"],
            "it": ["Storia", "Cronistoria"],
            "es": ["Historia", "Historia_del_equipo"]
        }
        return headers.get(lang, ["History"])
    
    def _extract_section_content(self, header_element) -> Optional[str]:
        """Extract text content from a section until the next h2.
        
        Wikipedia now wraps h2 headers in <div class="mw-heading mw-heading2">.
        We need to find that wrapper and iterate its siblings, not the h2's siblings.
        """
        content = []
        
        # Navigate to h2 if header is a span
        element = header_element
        while element and element.name != 'h2':
            element = element.parent
        
        if not element:
            return None
        
        # Check if h2 is wrapped in mw-heading div (new Wikipedia structure)
        parent = element.parent
        if parent and parent.name == 'div' and 'mw-heading' in parent.get('class', []):
            # New structure: iterate siblings of the wrapper div
            for sibling in parent.find_next_siblings():
                # Stop at next heading div or h2
                if sibling.name == 'h2':
                    break
                if sibling.name == 'div' and 'mw-heading' in sibling.get('class', []):
                    break
                
                # Skip edit sections and navigation elements
                if sibling.name in ['span', 'style', 'script']:
                    continue
                
                # Get text from paragraphs and other content elements
                text = sibling.get_text(strip=True)
                if text and len(text) > 10:  # Skip very short fragments like "[edit]"
                    content.append(text)
        else:
            # Old structure: iterate siblings of h2 directly
            for sibling in element.find_next_siblings():
                if sibling.name == 'h2':
                    break
                text = sibling.get_text(strip=True)
                if text and len(text) > 10:
                    content.append(text)
        
        return '\n'.join(content) if content else None

    def _extract_lead_section(self, soup) -> Optional[str]:
        """Extract the lead/intro section (content before first h2).
        
        This is useful for pages without a dedicated History section,
        as the intro often contains key information about team origins,
        mergers, and lineage.
        """
        content = []
        
        # Find the main content area
        # Wikipedia uses different IDs: mw-content-text, bodyContent, etc.
        main_content = soup.find(id='mw-content-text')
        if not main_content:
            main_content = soup.find(id='bodyContent')
        if not main_content:
            main_content = soup.body
        
        if not main_content:
            return None
        
        # Find first mw-parser-output div (actual article content)
        parser_output = main_content.find(class_='mw-parser-output')
        if parser_output:
            main_content = parser_output
        
        # Iterate direct children until we hit the first heading
        for child in main_content.children:
            # Stop at first h2 or heading div
            if hasattr(child, 'name'):
                if child.name == 'h2':
                    break
                if child.name == 'div' and 'mw-heading' in child.get('class', []):
                    break
                
                # Skip navigation, tables of contents, infoboxes, etc.
                if child.name in ['table', 'style', 'script', 'meta', 'link']:
                    continue
                classes = child.get('class', []) if hasattr(child, 'get') else []
                if any(c in classes for c in ['toc', 'infobox', 'navbox', 'sidebar', 'thumb', 'mw-empty-elt']):
                    continue
                
                # Extract text from paragraphs and other content
                if child.name == 'p':
                    text = child.get_text(strip=True)
                    if text and len(text) > 20:  # Skip short fragments
                        content.append(text)
        
        return '\n'.join(content) if content else None
