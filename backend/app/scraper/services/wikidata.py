from typing import Optional, Dict
import httpx
from pydantic import BaseModel
from app.scraper.utils.cache import CacheManager

class WikidataResult(BaseModel):
    qid: str
    label: str
    sitelinks: Dict[str, str]  # {"en": "https://en.wikipedia.org/...", ...}

class WikidataResolver:
    SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
    
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
        cache_key = f"wikidata:{team_name.lower()}"
        cached = self._cache.get(cache_key, domain="wikidata")
        if cached:
            return WikidataResult.model_validate_json(cached)
        
        query = self._build_query(team_name)
        result = await self._execute_query(query)
        
        if result:
            self._cache.set(cache_key, result.model_dump_json(), domain="wikidata")
        
        return result
    
    def _build_query(self, team_name: str) -> str:
        # P31: instance of
        # P279: subclass of
        # Q20658729: cycling team
        # We search for items that are instances of cycling team (or subclasses)
        # And filter by label containing the team name
        return f'''
        SELECT ?item ?itemLabel ?sitelink WHERE {{
          ?item wdt:P31/wdt:P279* wd:Q20658729 .
          ?item rdfs:label ?label .
          FILTER(CONTAINS(LCASE(?label), "{team_name.lower()}"))
          OPTIONAL {{ ?sitelink schema:about ?item }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de,nl,it,es". }}
        }}
        LIMIT 20
        '''
        
    async def _execute_query(self, query: str) -> Optional[WikidataResult]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    self.SPARQL_ENDPOINT,
                    params={"query": query, "format": "json"},
                    headers={"User-Agent": "ChainlinesScraper/1.0 (bot@chainlines.com)"}
                )
                response.raise_for_status()
                data = response.json()
                
                bindings = data.get("results", {}).get("bindings", [])
                if not bindings:
                    return None
                
                # Logic to pick the best match or aggregate sitelinks
                # For now, we take the first item and aggregate all its sitelinks found in the result set
                # The SPARQL query returns one row per sitelink if we are not careful OR one row per item if we don't request sitelinks in a specific way.
                # The current query: OPTIONAL { ?sitelink schema:about ?item } will cause cartesian product if multiple sitelinks exist?
                # Actually, ?sitelink is the URL. schema:about points to the item.
                # A better way might be to group by item, but simple parsing is fine for now.
                
                # We'll group by item QID first
                candidates = {}
                
                for row in bindings:
                    item_uri = row["item"]["value"]
                    qid = item_uri.split("/")[-1]
                    label = row["itemLabel"]["value"]
                    sitelink = row.get("sitelink", {}).get("value")
                    
                    if qid not in candidates:
                        candidates[qid] = {
                            "qid": qid,
                            "label": label,
                            "sitelinks": {}
                        }
                    
                    if sitelink:
                        # Extract language code from wikimedia URL
                        # e.g. https://en.wikipedia.org/wiki/... -> en
                        # e.g. https://commons.wikimedia.org/wiki/... -> commons (we skip non-wikipedia usually but keep for now)
                        try:
                            # Rudimentary parsing, can be improved
                            import re
                            match = re.search(r'https://(\w+)\.wikipedia\.org', sitelink)
                            if match:
                                code = match.group(1)
                                candidates[qid]["sitelinks"][code] = sitelink
                        except Exception:
                            pass
                
                if not candidates:
                    return None
                
                # Return the candidate with the most sitelinks? Or just the first one?
                # For this slice, simple assumption: first unique QID found is the match.
                # (Ideally we'd do fuzzy matching on the label vs input)
                
                first_match = list(candidates.values())[0]
                
                return WikidataResult(
                    qid=first_match["qid"],
                    label=first_match["label"],
                    sitelinks=first_match["sitelinks"]
                )
                
            except httpx.HTTPError:
                # Log error in real app
                return None
            except Exception:
                return None
