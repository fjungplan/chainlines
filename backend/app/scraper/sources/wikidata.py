"""Wikidata scraper implementation."""
from typing import Dict, Any
import httpx
from app.scraper.base import BaseScraper


class WikidataScraper(BaseScraper):
    """Scraper for Wikidata using SPARQL queries."""

    SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

    def __init__(self, min_delay: float = 5.0, max_delay: float = 10.0, **kwargs):
        # Allow overriding delays via kwargs without duplication.
        super().__init__(min_delay=min_delay, max_delay=max_delay, **kwargs)

    async def _run_query(self, query: str) -> Dict[str, Any]:
        """Execute a SPARQL query and return the JSON result."""
        await self._rate_limiter.wait()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.SPARQL_ENDPOINT,
                params={"query": query, "format": "json"},
            )
            response.raise_for_status()
            return response.json()

    def _build_query_by_qid(self, qid: str) -> str:
        """Return a SPARQL query string for a given Wikidata Q‑ID.
        Extracts team label, founded year, country ISO‑3 code, and UCI code (if present).
        """
        return f"""
        SELECT ?teamLabel ?foundedYear ?countryCode ?uciCode WHERE {{
          wd:{qid} rdfs:label ?teamLabel FILTER (lang(?teamLabel) = \"en\").
          OPTIONAL {{ wd:{qid} wdt:P571 ?founded . BIND(YEAR(?founded) AS ?foundedYear) }}
          OPTIONAL {{ wd:{qid} wdt:P17 ?country . ?country wdt:P298 ?countryCode }}
          OPTIONAL {{ wd:{qid} wdt:PXXXX ?uciCode }}  # replace PXXXX with actual property if known
        }}
        """

    def _parse_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten the SPARQL JSON result into a simple dict."""
        results = data.get("results", {}).get("bindings", [])
        if not results:
            return {}
        row = results[0]
        def get_val(key: str) -> Any:
            return row.get(key, {}).get("value")
        founded = get_val("foundedYear")
        return {
            "team_name": get_val("teamLabel"),
            "founded_year": int(founded) if founded else None,
            "country_code": get_val("countryCode"),
            "uci_code": get_val("uciCode"),
        }

    async def get_team(self, identifier: str) -> Dict[str, Any]:
        """Fetch team data from Wikidata.
        `identifier` can be a Q‑ID (e.g., "Q12345") or a plain team name.
        """
        if identifier.upper().startswith("Q"):
            query = self._build_query_by_qid(identifier)
        else:
            # Simple name search – fallback to a generic query.
            query = f"""
            SELECT ?team WHERE {{
              ?team rdfs:label \"{identifier}\"@en .
            }} LIMIT 1
            """
        raw = await self._run_query(query)
        return self._parse_result(raw)
