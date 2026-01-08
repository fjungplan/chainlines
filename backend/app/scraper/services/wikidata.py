from typing import Optional, Dict
import httpx
from pydantic import BaseModel
from app.scraper.utils.cache import CacheManager

class WikidataResult(BaseModel):
    qid: str
    label: str
    sitelinks: Dict[str, str]  # {"en": "https://en.wikipedia.org/...", ...}

class WikidataResolver:
    API_ENDPOINT = "https://www.wikidata.org/w/api.php"
    
    def __init__(self, cache: Optional[CacheManager] = None):
        self._cache = cache or CacheManager()
    
    async def resolve(self, team_name: str) -> Optional[WikidataResult]:
        """
        Resolve a team name to a Wikidata entity.
        
        Args:
            team_name: The name of the team to resolve.
            
        Returns:
            A WikidataResult object if found, otherwise None.
        """
        # Patch known encoding issues from scraper
        if "ArkAca" in team_name:
            team_name = team_name.replace("ArkAca", "Arkéa")
            
        cache_key = f"wikidata_api_v2:{team_name.lower()}"
        cached = self._cache.get(cache_key, domain="wikidata")
        if cached:
            return WikidataResult.model_validate_json(cached)
        
        # 1. Search for the entity
        qid = await self._search_entity(team_name)
        if not qid:
            # Try cleaning name? e.g. remove "Team" prefix if it fails?
            # For now, simplistic.
            return None
            
        # 2. Get sitelinks for the QID
        result = await self._get_entity_details(qid, team_name)
        
        if result:
            self._cache.set(cache_key, result.model_dump_json(), domain="wikidata")
        
        return result
    
    async def _search_entity(self, original_query: str) -> Optional[str]:
        """Search for a cycling team item and return its QID."""
        
        # Generates list of queries to try
        queries = [original_query]
        if " - " in original_query:
            queries.append(original_query.replace(" - ", "-"))
            queries.append(original_query.split(" - ")[0])
            
        # Try each query until we find a match
        for query in queries:
            qid = await self._execute_search_request(query, original_query)
            if qid:
                return qid
        return None

    async def _execute_search_request(self, query: str, context_query: str) -> Optional[str]:
        """Execute a single search request and apply heuristics."""
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "format": "json",
            "type": "item",
            "limit": 50
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.API_ENDPOINT,
                    params=params, 
                    headers={"User-Agent": "ChainlinesBot/1.0 (dev@chainlines.com)"}
                )
                response.raise_for_status()
                data = response.json()
                
                best_match = None
                
                for item in data.get("search", []):
                    label = item.get("label", "")
                    desc = item.get("description", "").lower()
                    
                    # Heuristic 1: Skip Season Items (start with Year)
                    import re
                    if re.match(r'^\d{4}\s', label):
                        continue
                        
                    # Heuristic 2: Skip Development/Women teams if not asked for
                    keywords = ["development", "women", "dames", "femmes", "u23", "junio"]
                    
                    # Check against the ORIGINAL query context to decide if keywords are unwanted
                    query_lower = context_query.lower()
                    label_lower = label.lower()
                    
                    has_unwanted_keyword = False
                    for kw in keywords:
                        if kw in label_lower and kw not in query_lower:
                            has_unwanted_keyword = True
                            break
                    
                    if has_unwanted_keyword:
                        continue
                        
                    # Heuristic 3: Prefer items with "cycling team" in description
                    if "cycling" in desc or "cycliste" in desc:
                         return item["id"]
                    
                    if not best_match:
                        best_match = item["id"]
                
                return best_match
        except Exception:
            return None

    async def _get_entity_details(self, qid: str, original_label: str) -> Optional[WikidataResult]:
        """Fetch sitelinks for a specific QID."""
        params = {
            "action": "wbgetentities",
            "ids": qid,
            "props": "sitelinks|labels",
            "sitefilter": "enwiki|frwiki|dewiki|nlwiki|itwiki|eswiki",
            "format": "json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.API_ENDPOINT, 
                    params=params,
                    headers={"User-Agent": "ChainlinesBot/1.0 (dev@chainlines.com)"}
                )
                response.raise_for_status()
                data = response.json()
                
                entity = data.get("entities", {}).get(qid)
                if not entity:
                    return None
                    
                sitelinks_raw = entity.get("sitelinks", {})
                sitelinks = {}
                
                for site_key, info in sitelinks_raw.items():
                    # site_key e.g. "enwiki"
                    lang = site_key.replace("wiki", "")
                    url = f"https://{lang}.wikipedia.org/wiki/{info['title'].replace(' ', '_')}"
                    sitelinks[lang] = url
                
                # Get label in English
                label = entity.get("labels", {}).get("en", {}).get("value", original_label)
                
                return WikidataResult(
                    qid=qid,
                    label=label,
                    sitelinks=sitelinks
                )
        except Exception:
            return None
