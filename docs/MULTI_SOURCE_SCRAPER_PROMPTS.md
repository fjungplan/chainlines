# Multi-Source Scraper TDD Implementation Prompts

**Reference**: [MULTI_SOURCE_SCRAPER_BLUEPRINT.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md)  
**Reference**: [MULTI_SOURCE_SCRAPER_SPECIFICATION.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md)

---

## PHASE A: INFRASTRUCTURE FOUNDATION

### Prompt A1.1: Create CacheManager Class

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Implementation plan)
- backend/app/scraper/checkpoint.py (Reference for file persistence patterns)
- backend/app/scraper/base/scraper.py (Target for future integration)

---

SLICE A1.1: Create File-Based CacheManager

CONTEXT:
You are implementing a file-based caching system for the Smart Scraper. This cache will store HTTP responses and LLM results to enable resume capability. The cache uses URL/prompt hashing for keys and stores data as files on disk.

STEP 1 - CREATE TESTS FIRST:
Create `backend/tests/scraper/test_cache.py` with these tests:

1. test_cache_miss_returns_none: When key doesn't exist, get() returns None
2. test_cache_set_and_get: After set(key, data), get(key) returns the data
3. test_cache_uses_hash_for_filename: Verify long URLs are hashed to safe filenames
4. test_cache_respects_domain_subdirectory: URLs from different domains go to different subdirs
5. test_force_refresh_bypasses_cache: When force_refresh=True, cache is ignored

STEP 2 - IMPLEMENT:
Create `backend/app/scraper/utils/cache.py`:

class CacheManager:
    def __init__(self, cache_dir: Path = Path("./cache")):
        ...
    
    def _hash_key(self, key: str) -> str:
        """Create filesystem-safe hash of key."""
        ...
    
    def _get_path(self, key: str, domain: str = "default") -> Path:
        """Get cache file path for key."""
        ...
    
    def get(self, key: str, domain: str = "default") -> Optional[str]:
        """Retrieve cached content, or None if not cached."""
        ...
    
    def set(self, key: str, content: str, domain: str = "default") -> None:
        """Store content in cache."""
        ...

Use hashlib.sha256 for hashing. Store files as .txt or .html based on content.

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_cache.py -v
All 5 tests must pass.

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add CacheManager for HTTP/LLM result caching"
````

---

### Prompt A1.2: Integrate Cache into BaseScraper

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Implementation plan)
- backend/app/scraper/base/scraper.py (Target file)
- backend/app/scraper/utils/cache.py (Just created in A1.1)

---

SLICE A1.2: Integrate CacheManager into BaseScraper

CONTEXT:
The BaseScraper class has a fetch(url) method that makes HTTP requests. We need to wrap this with caching so repeated requests return cached content.

STEP 1 - UPDATE TESTS:
Add to `backend/tests/scraper/test_cache.py`:

1. test_base_scraper_fetch_caches_response: First fetch hits network, second fetch returns cached
2. test_base_scraper_fetch_force_refresh: With force_refresh=True, always hits network

Use unittest.mock.patch to mock aiohttp.ClientSession.get.

STEP 2 - IMPLEMENT:
Modify `backend/app/scraper/base/scraper.py`:

1. Add CacheManager as constructor parameter (optional, with default)
2. Wrap fetch() to check cache before making request
3. Store response in cache after successful fetch
4. Add force_refresh parameter to fetch()

Example:
async def fetch(self, url: str, force_refresh: bool = False) -> str:
    if not force_refresh and self._cache:
        cached = self._cache.get(url, domain=self._get_domain(url))
        if cached:
            return cached
    
    # ... existing fetch logic ...
    
    if self._cache:
        self._cache.set(url, content, domain=self._get_domain(url))
    
    return content

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_cache.py -v
All tests must pass.

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): integrate CacheManager into BaseScraper.fetch()"
````

---

### Prompt A2.1: Create FirstCycling Scraper

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Implementation plan)
- backend/app/scraper/sources/cyclingflash.py (Reference for scraper pattern)
- backend/app/scraper/base/scraper.py (Base class)

---

SLICE A2.1: Create FirstCycling Scraper with Rate Limiting

CONTEXT:
FirstCycling.com has a strict 10-second crawl delay. We need a scraper that respects this limit. The scraper will fetch Grand Tour start lists for the relevance filter.

GT Start List URL Pattern:
- Giro: https://firstcycling.com/race.php?r=13&y={year}&k=8
- Tour: https://firstcycling.com/race.php?r=17&y={year}&k=8
- Vuelta: https://firstcycling.com/race.php?r=23&y={year}&k=8

STEP 1 - CREATE TESTS:
Create `backend/tests/scraper/test_firstcycling.py`:

1. test_firstcycling_scraper_respects_rate_limit: Verify 10s delay between requests
2. test_get_gt_url_giro: Verify correct URL generation for Giro
3. test_get_gt_url_tour: Verify correct URL generation for Tour
4. test_get_gt_url_vuelta: Verify correct URL generation for Vuelta

STEP 2 - IMPLEMENT:
Create `backend/app/scraper/sources/firstcycling.py`:

class FirstCyclingScraper(BaseScraper):
    BASE_URL = "https://firstcycling.com"
    RATE_LIMIT_SECONDS = 10.0
    
    GT_RACE_IDS = {
        "giro": 13,
        "tour": 17,
        "vuelta": 23
    }
    
    def __init__(self, **kwargs):
        super().__init__(rate_limit=self.RATE_LIMIT_SECONDS, **kwargs)
    
    def get_gt_start_list_url(self, race: str, year: int) -> str:
        race_id = self.GT_RACE_IDS[race.lower()]
        return f"{self.BASE_URL}/race.php?r={race_id}&y={year}&k=8"
    
    async def fetch_gt_start_list(self, race: str, year: int) -> str:
        url = self.get_gt_start_list_url(race, year)
        return await self.fetch(url)

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_firstcycling.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add FirstCyclingScraper with 10s rate limit"
````

---

### Prompt A2.2: Implement GT Start List Parser

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Implementation plan)
- backend/app/scraper/sources/firstcycling.py (Target file)

---

SLICE A2.2: Implement FirstCycling GT Start List Parser

CONTEXT:
The GT start list page contains team names in a table. We need to extract these team names to build the relevance index.

STEP 1 - CREATE TEST FIXTURE:
Create `backend/tests/scraper/fixtures/firstcycling_gt_sample.html` with sample HTML from a GT start list page.

STEP 2 - CREATE TESTS:
Add to `backend/tests/scraper/test_firstcycling.py`:

1. test_parse_gt_start_list_extracts_team_names: Given sample HTML, returns list of team names
2. test_parse_gt_start_list_handles_empty_page: Returns empty list for invalid/empty HTML
3. test_parse_gt_start_list_normalizes_names: Team names are stripped and normalized

STEP 3 - IMPLEMENT:
Add to `backend/app/scraper/sources/firstcycling.py`:

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

STEP 4 - VERIFY:
Run: pytest backend/tests/scraper/test_firstcycling.py -v

STEP 5 - COMMIT:
git add -A && git commit -m "feat(scraper): add FirstCycling GT start list parser"
````

---

### Prompt A2.3: Implement GTRelevanceIndex

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Implementation plan)
- backend/app/scraper/sources/firstcycling.py (Source of team data)
- backend/app/scraper/utils/cache.py (For understanding caching patterns)

---

SLICE A2.3: Implement GTRelevanceIndex Class

CONTEXT:
The GTRelevanceIndex manages a JSON file containing all team names that participated in Grand Tours (1900-1998). This is used to filter irrelevant pre-1991 teams.

JSON structure:
{
  "1990": ["Peugeot", "Panasonic", "Z", ...],
  "1989": ["Panasonic", "PDM", ...],
  ...
}

STEP 1 - CREATE TESTS:
Add to `backend/tests/scraper/test_firstcycling.py`:

1. test_gt_index_is_relevant_exact_match: "Peugeot" in 1985 returns True
2. test_gt_index_is_relevant_fuzzy_match: "Peugeot-Shell" matches "Peugeot" (80% similarity)
3. test_gt_index_is_relevant_no_match: "Unknown Team" returns False
4. test_gt_index_load_from_json: Loads existing JSON file correctly
5. test_gt_index_save_to_json: Saves index to JSON file

STEP 2 - IMPLEMENT:
Create `backend/app/scraper/services/gt_relevance.py`:

from pathlib import Path
import json
from rapidfuzz import fuzz

class GTRelevanceIndex:
    SIMILARITY_THRESHOLD = 80
    
    def __init__(self, index_path: Path = Path("./cache/gt_relevance_index.json")):
        self._path = index_path
        self._index: dict[str, list[str]] = {}
        self._load()
    
    def _load(self):
        if self._path.exists():
            self._index = json.loads(self._path.read_text())
    
    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._index, indent=2))
    
    def add_year(self, year: int, teams: list[str]):
        self._index[str(year)] = teams
    
    def is_relevant(self, team_name: str, year: int) -> bool:
        year_teams = self._index.get(str(year), [])
        for gt_team in year_teams:
            if fuzz.ratio(team_name.lower(), gt_team.lower()) >= self.SIMILARITY_THRESHOLD:
                return True
        return False

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_firstcycling.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add GTRelevanceIndex for pre-1991 team filtering"
````

---

### Prompt A2.4: Build GT Index Cache Script

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- backend/app/scraper/sources/firstcycling.py (Scraper to use)
- backend/app/scraper/services/gt_relevance.py (Index to populate)

---

SLICE A2.4: Create Script to Build GT Relevance Index

CONTEXT:
This is a one-time script to fetch all GT start lists (1900-1998) and build the relevance index JSON. At 10s per request with ~300 pages, this takes ~50 minutes. The script must be resumable.

STEP 1 - IMPLEMENT:
Create `backend/scripts/build_gt_index.py`:

import asyncio
import json
from pathlib import Path
from app.scraper.sources.firstcycling import FirstCyclingScraper, FirstCyclingParser
from app.scraper.services.gt_relevance import GTRelevanceIndex

PROGRESS_FILE = Path("./cache/gt_index_progress.json")

async def build_gt_index():
    scraper = FirstCyclingScraper()
    parser = FirstCyclingParser()
    index = GTRelevanceIndex()
    
    completed_years = set()
    if PROGRESS_FILE.exists():
        completed_years = set(json.loads(PROGRESS_FILE.read_text()))
    
    races = ["giro", "tour", "vuelta"]
    
    for year in range(1998, 1899, -1):
        if year in completed_years:
            print(f"Skipping {year} (already done)")
            continue
        
        all_teams = set()
        for race in races:
            try:
                html = await scraper.fetch_gt_start_list(race, year)
                teams = parser.parse_gt_start_list(html)
                all_teams.update(teams)
                print(f"  {race.upper()} {year}: {len(teams)} teams")
            except Exception as e:
                print(f"  {race.upper()} {year}: FAILED - {e}")
        
        index.add_year(year, list(all_teams))
        index.save()
        
        completed_years.add(year)
        PROGRESS_FILE.write_text(json.dumps(list(completed_years)))
        print(f"Year {year} done: {len(all_teams)} unique teams")

if __name__ == "__main__":
    asyncio.run(build_gt_index())

STEP 2 - TEST LOCALLY (small range):
Modify script temporarily to test years 1997-1998 only:
python -m backend.scripts.build_gt_index

STEP 3 - COMMIT:
git add -A && git commit -m "feat(scraper): add script to build GT relevance index from FirstCycling"
````

---

### Prompt A3.1: Update DiscoveryService for Dual Seeding

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture - see Phase 1 filtering rules)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Implementation plan)
- backend/app/scraper/orchestration/phase1.py (Target file)
- backend/app/scraper/services/gt_relevance.py (Relevance index)

---

SLICE A3.1: Update DiscoveryService for Dual Seeding and Relevance Filtering

CONTEXT:
The current DiscoveryService processes year-by-year. We need to update it to:
1. Accept a year range (1900-2026)
2. Implement the tier-based filtering logic
3. Integrate GTRelevanceIndex for pre-1991 filtering

Relevance Rules:
- Post-1999: Keep Tier 1 and 2 only
- 1991-1998: Keep Tier 1, keep Tier 2 ONLY if in GT index
- Pre-1991: Keep ONLY if in GT index

STEP 1 - UPDATE TESTS:
Add to `backend/tests/scraper/test_phase1.py`:

1. test_discovery_filters_tier3_post_1999: Tier 3 teams in 2020 are excluded
2. test_discovery_keeps_tier1_pre_1991_if_relevant: Tier 1 in 1985 kept if in GT index
3. test_discovery_filters_tier1_pre_1991_if_irrelevant: Tier 1 in 1985 dropped if not in GT index
4. test_discovery_filters_tier2_1995_if_not_in_gt: Tier 2 in 1995 dropped if not in GT index

STEP 2 - IMPLEMENT:
Modify `backend/app/scraper/orchestration/phase1.py`:

class DiscoveryService:
    def __init__(
        self,
        scraper: CyclingFlashScraper,
        gt_index: Optional[GTRelevanceIndex] = None,
        ...
    ):
        self._gt_index = gt_index or GTRelevanceIndex()
        ...
    
    def _is_relevant(self, team_name: str, tier: int, year: int) -> bool:
        """Apply relevance filtering rules."""
        if year >= 1999:
            return tier in (1, 2)
        elif year >= 1991:
            if tier == 1:
                return True
            elif tier == 2:
                return self._gt_index.is_relevant(team_name, year)
            return False
        else:  # Pre-1991
            return self._gt_index.is_relevant(team_name, year)

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_phase1.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add tier-based relevance filtering to DiscoveryService"
````

---

## PHASE B: ENTITY RESOLUTION

### Prompt B1.1: Create WikidataResolver

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture - see Rosetta Stone pattern)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Implementation plan)
- backend/app/scraper/utils/cache.py (For caching SPARQL results)

---

SLICE B1.1: Create WikidataResolver with SPARQL Query

CONTEXT:
The WikidataResolver maps team names to Wikidata entities. Wikidata returns Q-IDs and sitelinks (Wikipedia URLs in multiple languages).

SPARQL Endpoint: https://query.wikidata.org/sparql

STEP 1 - CREATE TESTS:
Create `backend/tests/scraper/test_wikidata.py`:

1. test_resolve_known_team: "Peugeot cycling team" returns Q-ID and sitelinks
2. test_resolve_unknown_team: "XYZ Unknown Team" returns None
3. test_extracts_wikipedia_urls: Sitelinks include EN, FR, NL URLs
4. test_respects_cache: Second call uses cached result

Use unittest.mock.patch to mock HTTP requests.

STEP 2 - IMPLEMENT:
Create `backend/app/scraper/services/wikidata.py`:

import httpx
from pydantic import BaseModel
from app.scraper.utils.cache import CacheManager

class WikidataResult(BaseModel):
    qid: str
    label: str
    sitelinks: dict[str, str]  # {"en": "https://en.wikipedia.org/...", ...}

class WikidataResolver:
    SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
    
    def __init__(self, cache: Optional[CacheManager] = None):
        self._cache = cache or CacheManager()
    
    async def resolve(self, team_name: str) -> Optional[WikidataResult]:
        cache_key = f"wikidata:{team_name}"
        cached = self._cache.get(cache_key, domain="wikidata")
        if cached:
            return WikidataResult.model_validate_json(cached)
        
        query = self._build_query(team_name)
        result = await self._execute_query(query)
        
        if result:
            self._cache.set(cache_key, result.model_dump_json(), domain="wikidata")
        
        return result
    
    def _build_query(self, team_name: str) -> str:
        return f'''
        SELECT ?item ?itemLabel ?sitelink WHERE {{
          ?item wdt:P31/wdt:P279* wd:Q20658729 .
          ?item rdfs:label ?label .
          FILTER(CONTAINS(LCASE(?label), "{team_name.lower()}"))
          OPTIONAL {{ ?sitelink schema:about ?item }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de,nl,it,es". }}
        }}
        LIMIT 10
        '''

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_wikidata.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add WikidataResolver for entity resolution"
````

---

### Prompt B2.1: Add Data Model Columns

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference - see new columns)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- docs/final_schema_doc.md (Full database schema)
- backend/app/models/team.py (Target file)

---

SLICE B2.1: Add external_ids and wikipedia_history_content Columns

CONTEXT:
We need to store Wikidata IDs and Wikipedia history text for Phase 3 lineage decisions.

STEP 1 - UPDATE MODELS:
Modify `backend/app/models/team.py`:

from sqlalchemy.dialects.postgresql import JSONB

class TeamNode(Base):
    # ... existing fields ...
    external_ids = Column(JSONB, nullable=True, comment="External source IDs: {wikidata: Q123, ...}")

class TeamEra(Base):
    # ... existing fields ...
    wikipedia_history_content = Column(Text, nullable=True, comment="Cached Wikipedia History section text")

STEP 2 - CREATE MIGRATION:
cd backend
alembic revision --autogenerate -m "Add external_ids and wikipedia_history_content"

Review the generated migration file, then apply:
alembic upgrade head

STEP 3 - UPDATE PYDANTIC SCHEMAS:
Update `backend/app/schemas/team.py` to include the new fields.

STEP 4 - COMMIT:
git add -A && git commit -m "feat(models): add external_ids and wikipedia_history_content columns"
````

---

## PHASE C: PARALLEL WORKERS

### Prompt C1.1: Create SourceWorker Base Class

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Implementation plan)
- backend/app/scraper/base/scraper.py (Base scraper pattern)

---

SLICE C1.1: Create Abstract SourceWorker Base Class

CONTEXT:
All secondary source workers (Wikipedia, CyclingRanking, Memoire) share a common pattern. We define an abstract base class for consistency.

STEP 1 - CREATE TESTS FIRST:
Create `backend/tests/scraper/test_workers.py`:

1. test_source_data_model_validates: SourceData model accepts valid data
2. test_source_worker_is_abstract: Cannot instantiate SourceWorker directly

STEP 2 - IMPLEMENT:
Create `backend/app/scraper/orchestration/workers.py`:

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class SourceData(BaseModel):
    """Data returned by a source worker."""
    source: str
    raw_content: Optional[str] = None
    founded_year: Optional[int] = None
    dissolved_year: Optional[int] = None
    history_text: Optional[str] = None
    extra: dict = {}

class SourceWorker(ABC):
    """Abstract base for source-specific workers."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source."""
        ...
    
    @abstractmethod
    async def fetch(self, url: str) -> Optional[SourceData]:
        """Fetch and parse data from this source."""
        ...

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_workers.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add SourceWorker abstract base class and SourceData model"
````

---

### Prompt C1.2: Implement WikipediaWorker

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- backend/app/scraper/orchestration/workers.py (Base class)
- backend/app/scraper/sources/wikipedia.py (If exists, for reference)

---

SLICE C1.2: Implement WikipediaWorker

CONTEXT:
The WikipediaWorker fetches a Wikipedia page and extracts the "History" section. This text is critical for Phase 3 lineage decisions.

STEP 1 - CREATE TESTS:
Add to `backend/tests/scraper/test_workers.py`:

1. test_wikipedia_worker_extracts_history: Given sample HTML, extracts History section
2. test_wikipedia_worker_handles_no_history: Returns None if no History section
3. test_wikipedia_worker_extracts_founded_year: Extracts year from infobox

STEP 2 - IMPLEMENT:
Add to `backend/app/scraper/orchestration/workers.py`:

class WikipediaWorker(SourceWorker):
    source_name = "wikipedia"
    
    def __init__(self, scraper: BaseScraper):
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
        history_header = soup.find(id="History")
        if history_header:
            content = []
            for sibling in history_header.parent.find_next_siblings():
                if sibling.name == 'h2':
                    break
                content.append(sibling.get_text())
            history_text = '\n'.join(content)
        
        founded_year = self._extract_founded_year(soup)
        
        return SourceData(
            source=self.source_name,
            history_text=history_text,
            founded_year=founded_year
        )

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_workers.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add WikipediaWorker for history extraction"
````

---

### Prompt C1.3: Implement CyclingRankingWorker

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- backend/app/scraper/orchestration/workers.py (Base class)
- backend/app/scraper/sources/cycling_ranking.py (If exists)

---

SLICE C1.3: Implement CyclingRankingWorker

CONTEXT:
CyclingRanking provides authoritative founded/dissolved years for teams. This is critical for conflict detection.

STEP 1 - CREATE TESTS:
Add to `backend/tests/scraper/test_workers.py`:

1. test_cycling_ranking_worker_extracts_years: Extracts founded and dissolved years
2. test_cycling_ranking_worker_handles_active_team: No dissolved year for active teams

STEP 2 - IMPLEMENT:
Add to `backend/app/scraper/orchestration/workers.py`:

class CyclingRankingWorker(SourceWorker):
    source_name = "cyclingranking"
    
    def __init__(self, scraper: BaseScraper):
        self._scraper = scraper
    
    async def fetch(self, url: str) -> Optional[SourceData]:
        try:
            html = await self._scraper.fetch(url)
            return self._parse(html)
        except Exception as e:
            logger.warning(f"CyclingRanking fetch failed: {e}")
            return None
    
    def _parse(self, html: str) -> SourceData:
        # Parse years from page content
        ...

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_workers.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add CyclingRankingWorker"
````

---

### Prompt C1.4: Implement MemoireWorker

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- backend/app/scraper/orchestration/workers.py (Base class)

---

SLICE C1.4: Implement MemoireWorker with Wayback Machine

CONTEXT:
Mémoire du Cyclisme is no longer live but archived on Wayback Machine. We use the Wayback CDX API to find archived snapshots.

Wayback API: https://web.archive.org/web/{timestamp}/{url}

STEP 1 - CREATE TESTS:
Add to `backend/tests/scraper/test_workers.py`:

1. test_memoire_worker_uses_wayback: Fetches via archive.org URL
2. test_memoire_worker_handles_no_archive: Returns None if no snapshot found

STEP 2 - IMPLEMENT:
Add to `backend/app/scraper/orchestration/workers.py`:

class MemoireWorker(SourceWorker):
    source_name = "memoire"
    WAYBACK_PREFIX = "https://web.archive.org/web/2020/"
    
    def __init__(self, scraper: BaseScraper):
        self._scraper = scraper
    
    async def fetch(self, original_url: str) -> Optional[SourceData]:
        wayback_url = f"{self.WAYBACK_PREFIX}{original_url}"
        try:
            html = await self._scraper.fetch(wayback_url)
            return self._parse(html)
        except Exception as e:
            logger.warning(f"Memoire fetch failed: {e}")
            return None

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_workers.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add MemoireWorker with Wayback support"
````

---

### Prompt C2.1: Wire Workers into Phase 2

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- backend/app/scraper/orchestration/phase2.py (Target file)
- backend/app/scraper/orchestration/workers.py (Workers to integrate)
- backend/app/scraper/services/wikidata.py (Resolver)

---

SLICE C2.1: Wire Workers into AssemblyOrchestrator

CONTEXT:
The AssemblyOrchestrator now needs to:
1. Call WikidataResolver to get external URLs
2. Fan-out to workers in parallel
3. Collect results into EnrichedTeamData

STEP 1 - CREATE TESTS:
Add to `backend/tests/scraper/test_phase2.py`:

1. test_orchestrator_calls_wikidata_resolver: Verify resolver is called
2. test_orchestrator_fans_out_to_workers: All workers called in parallel
3. test_orchestrator_collects_enriched_data: Results merged correctly

STEP 2 - IMPLEMENT:
Modify `backend/app/scraper/orchestration/phase2.py`:

class EnrichedTeamData(BaseModel):
    base_data: ScrapedTeamData
    wikidata_result: Optional[WikidataResult] = None
    wikipedia_data: Optional[SourceData] = None
    cycling_ranking_data: Optional[SourceData] = None
    memoire_data: Optional[SourceData] = None

class AssemblyOrchestrator:
    def __init__(
        self,
        ...,
        wikidata_resolver: Optional[WikidataResolver] = None,
        workers: Optional[list[SourceWorker]] = None,
    ):
        self._resolver = wikidata_resolver
        self._workers = workers or []
    
    async def _enrich_team(self, base_data: ScrapedTeamData) -> EnrichedTeamData:
        wd_result = await self._resolver.resolve(base_data.name)
        
        tasks = []
        for worker in self._workers:
            url = self._get_url_for_worker(worker.source_name, wd_result)
            if url:
                tasks.append(worker.fetch(url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return EnrichedTeamData(
            base_data=base_data,
            wikidata_result=wd_result,
            ...
        )

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_phase2.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): wire workers into AssemblyOrchestrator for parallel enrichment"
````

---

## PHASE D: CONFLICT ARBITRATION

### Prompt D1.1: Create ConflictArbiter

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture - see conflict arbitration rules)
- backend/app/scraper/llm/prompts.py (Prompt patterns)
- backend/app/scraper/llm/service.py (LLM service)

---

SLICE D1.1: Create ConflictArbiter with Deepseek Reasoner

CONTEXT:
When CyclingFlash says "Peugeot 1912-2008" and CyclingRanking says "Peugeot 1912-1986", we need an LLM to decide if this is ONE team or a SPLIT.

STEP 1 - CREATE TESTS:
Create `backend/tests/scraper/test_arbiter.py`:

1. test_arbiter_detects_no_conflict: Same dates = no conflict
2. test_arbiter_decides_split: Different end years = SPLIT decision
3. test_arbiter_respects_confidence_threshold: Low confidence returns PENDING

STEP 2 - IMPLEMENT:
Create `backend/app/scraper/services/arbiter.py`:

from enum import Enum
from pydantic import BaseModel

class ArbitrationDecision(Enum):
    MERGE = "merge"
    SPLIT = "split"
    PENDING = "pending"

class ArbitrationResult(BaseModel):
    decision: ArbitrationDecision
    confidence: float
    reasoning: str
    suggested_lineage_type: Optional[str] = None

class ConflictArbiter:
    CONFIDENCE_THRESHOLD = 0.90
    
    def __init__(self, llm_service: LLMService):
        self._llm = llm_service
    
    async def decide(
        self,
        cf_data: ScrapedTeamData,
        cr_data: Optional[SourceData],
        wp_history: Optional[str]
    ) -> ArbitrationResult:
        if not self._has_conflict(cf_data, cr_data):
            return ArbitrationResult(
                decision=ArbitrationDecision.MERGE,
                confidence=1.0,
                reasoning="No conflict detected"
            )
        
        prompt = self._build_prompt(cf_data, cr_data, wp_history)
        result = await self._llm.complete(prompt, model="deepseek-reasoner")
        
        if result.confidence < self.CONFIDENCE_THRESHOLD:
            return ArbitrationResult(decision=ArbitrationDecision.PENDING, ...)
        
        return result

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_arbiter.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add ConflictArbiter for multi-source resolution"
````

---

### Prompt D2.1: Integrate Arbiter into Phase 2

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- backend/app/scraper/orchestration/phase2.py (Target file)
- backend/app/scraper/services/arbiter.py (Arbiter service)

---

SLICE D2.1: Integrate ConflictArbiter into Phase 2 Flow

CONTEXT:
After enriching a team, we check for conflicts. If conflicts exist, we invoke the arbiter. Based on the decision:
- MERGE: Proceed normally
- SPLIT: Create additional TeamNode and LineageEvent
- PENDING: Create PENDING edit in AuditLog

STEP 1 - UPDATE TESTS:
Add to `backend/tests/scraper/test_phase2.py`:

1. test_phase2_invokes_arbiter_on_conflict: Arbiter called when dates mismatch
2. test_phase2_creates_pending_edit_on_low_confidence: PENDING edit created
3. test_phase2_emits_decision_event: SSE decision event emitted

STEP 2 - IMPLEMENT:
Modify `backend/app/scraper/orchestration/phase2.py`:

async def _process_team(self, enriched: EnrichedTeamData):
    cr_data = enriched.cycling_ranking_data
    if cr_data and self._has_date_conflict(enriched.base_data, cr_data):
        decision = await self._arbiter.decide(
            enriched.base_data,
            cr_data,
            enriched.wikipedia_data.history_text if enriched.wikipedia_data else None
        )
        
        if decision.decision == ArbitrationDecision.PENDING:
            await self._create_pending_edit(enriched, decision)
            return
        
        if decision.decision == ArbitrationDecision.SPLIT:
            await self._handle_split(enriched, decision)
            return
    
    await self._assemble_team(enriched)

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_phase2.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): integrate ConflictArbiter into Phase 2"
````

---

## PHASE E: LINEAGE ENHANCEMENT

### Prompt E1.1: Add Wikipedia Context to Phase 3

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- backend/app/scraper/orchestration/phase3.py (Target file)
- backend/app/scraper/llm/prompts.py (Prompt definitions)

---

SLICE E1.1: Enhance Phase 3 with Wikipedia History Context

CONTEXT:
Phase 3's OrphanDetector proposes lineage connections. The LLM prompt now receives the Wikipedia History text stored during Phase 2.

STEP 1 - UPDATE TESTS:
Add to `backend/tests/scraper/test_phase3.py`:

1. test_lineage_prompt_includes_wiki_history: Prompt contains history text
2. test_lineage_decision_uses_context: Decision references history content

STEP 2 - IMPLEMENT:
Modify `backend/app/scraper/orchestration/phase3.py`:

async def _decide_lineage(self, team_a: TeamEra, team_b: TeamEra):
    history_a = team_a.wikipedia_history_content
    history_b = team_b.wikipedia_history_content
    
    prompt = self._build_lineage_prompt(team_a, team_b, history_a, history_b)
    decision = await self._llm.decide_lineage(prompt)
    
    return decision

Update DECIDE_LINEAGE_PROMPT in prompts.py to include history context:
"""
TEAM A HISTORY:
{history_a}

TEAM B HISTORY:
{history_b}
"""

STEP 3 - VERIFY:
Run: pytest backend/tests/scraper/test_phase3.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(scraper): add Wikipedia history context to Phase 3 lineage decisions"
````

---

## PHASE F: MONITORING

### Prompt F1.1: Create SSE Stream Endpoint

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture - see UI & Monitoring)
- backend/app/api/admin/scraper.py (Target file)

---

SLICE F1.1: Create SSE Stream Endpoint for Live Monitoring

CONTEXT:
The Admin UI needs real-time updates. We use Server-Sent Events (SSE) to stream log, progress, and decision events.

STEP 1 - CREATE TESTS:
Add to `backend/tests/api/test_scraper_admin.py`:

1. test_sse_stream_endpoint_returns_event_stream: Content-Type is text/event-stream
2. test_sse_stream_sends_progress_events: Progress events are formatted correctly

STEP 2 - IMPLEMENT:
Create `backend/app/scraper/utils/sse.py`:

import asyncio
from typing import AsyncGenerator

class SSEManager:
    def __init__(self):
        self._subscribers: dict[str, asyncio.Queue] = {}
    
    def subscribe(self, run_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._subscribers[run_id] = queue
        return queue
    
    async def emit(self, run_id: str, event_type: str, data: dict):
        if run_id in self._subscribers:
            await self._subscribers[run_id].put({
                "event": event_type,
                "data": data
            })

sse_manager = SSEManager()

Add to `backend/app/api/admin/scraper.py`:

from fastapi.responses import StreamingResponse

@router.get("/runs/{run_id}/stream")
async def stream_run_events(run_id: uuid.UUID):
    async def event_generator():
        queue = sse_manager.subscribe(str(run_id))
        while True:
            event = await queue.get()
            yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

STEP 3 - VERIFY:
Run: pytest backend/tests/api/test_scraper_admin.py -v

STEP 4 - COMMIT:
git add -A && git commit -m "feat(api): add SSE stream endpoint for live scraper monitoring"
````

---

### Prompt F1.2: Emit Events from Phase 2/3

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- backend/app/scraper/orchestration/phase2.py (Target file)
- backend/app/scraper/orchestration/phase3.py (Target file)
- backend/app/scraper/utils/sse.py (SSE manager)

---

SLICE F1.2: Emit SSE Events from Scraper Phases

CONTEXT:
Now that we have the SSE infrastructure, we emit events from Phase 2 and Phase 3 for real-time UI updates.

STEP 1 - IMPLEMENT:
Modify `backend/app/scraper/orchestration/phase2.py`:

from app.scraper.utils.sse import sse_manager

class AssemblyOrchestrator:
    async def _emit_progress(self, current: int, total: int):
        await sse_manager.emit(str(self._run_id), "progress", {
            "phase": 2,
            "current": current,
            "total": total,
            "percent": round(current / total * 100, 1)
        })
    
    async def _emit_decision(self, team_name: str, decision: ArbitrationResult):
        await sse_manager.emit(str(self._run_id), "decision", {
            "type": "CONFLICT_RESOLUTION",
            "subject": team_name,
            "outcome": decision.decision.value,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning
        })

STEP 2 - VERIFY:
Run full Phase 2 with SSE client connected and verify events are received.

STEP 3 - COMMIT:
git add -A && git commit -m "feat(scraper): emit SSE events from Phase 2 and Phase 3"
````

---

## FINAL INTEGRATION

### Prompt FINAL: Wire Everything in CLI

````text
REFERENCE FILES TO LOAD:
- GEMINI.md (Project conventions, TDD protocol)
- model.md (Data model reference)
- docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md (Architecture)
- docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md (Dependency graph)
- backend/app/scraper/cli.py (Target file)

---

SLICE FINAL: Wire All Components in CLI

CONTEXT:
All components are implemented. Now we wire them together in cli.py so run_scraper initializes and uses everything.

STEP 1 - IMPLEMENT:
Modify `backend/app/scraper/cli.py`:

async def run_scraper(...):
    # Initialize Cache
    cache = CacheManager()
    
    # Initialize GT Index
    gt_index = GTRelevanceIndex()
    
    # Initialize Wikidata Resolver
    wikidata_resolver = WikidataResolver(cache=cache)
    
    # Initialize Workers
    base_scraper = BaseScraper(cache=cache)
    workers = [
        WikipediaWorker(base_scraper),
        CyclingRankingWorker(base_scraper),
        MemoireWorker(base_scraper),
    ]
    
    # Initialize Arbiter
    arbiter = ConflictArbiter(llm_service)
    
    # Phase 1
    if phase in (0, 1):
        discovery_service = DiscoveryService(
            scraper=CyclingFlashScraper(cache=cache),
            gt_index=gt_index,
            ...
        )
        await discovery_service.run(start_year, end_year)
    
    # Phase 2
    if phase in (0, 2):
        orchestrator = AssemblyOrchestrator(
            wikidata_resolver=wikidata_resolver,
            workers=workers,
            arbiter=arbiter,
            ...
        )
        await orchestrator.run()
    
    # Phase 3
    if phase in (0, 3):
        lineage_orchestrator = LineageOrchestrator(...)
        await lineage_orchestrator.run()

STEP 2 - VERIFY:
Run full scraper:
python -m backend.app.scraper.cli --phase 0 --start-year 2025 --end-year 2020

STEP 3 - COMMIT:
git add -A && git commit -m "feat(scraper): wire all multi-source components in CLI"
````

---

## Summary

| Prompt | Est. Time |
|--------|-----------|
| A1.1 | 15 min |
| A1.2 | 10 min |
| A2.1 | 15 min |
| A2.2 | 20 min |
| A2.3 | 15 min |
| A2.4 | 10 min |
| A3.1 | 20 min |
| B1.1 | 25 min |
| B2.1 | 10 min |
| C1.1 | 10 min |
| C1.2 | 20 min |
| C1.3 | 15 min |
| C1.4 | 15 min |
| C2.1 | 25 min |
| D1.1 | 25 min |
| D2.1 | 20 min |
| E1.1 | 15 min |
| F1.1 | 20 min |
| F1.2 | 10 min |
| FINAL | 15 min |

**Total: ~6-7 hours of focused implementation**
