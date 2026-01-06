# Progressive Sponsor Extraction - Specification (DRAFT)

**Status**: In Development  
**Created**: 2026-01-05  
**Owner**: fjungplan

---

## Overview

Replace the current pattern-based sponsor extraction with an intelligent, progressive learning system that:
1. Runs scraper phases per-year to build knowledge incrementally
2. Uses database lookups to check for known sponsors before calling LLM
3. Only invokes LLM for unknown/ambiguous sponsor names

## Goals

- Accurately extract sponsor names from team names (e.g., "Bahrain" from "Bahrain Victorious", not both)
- Minimize LLM API costs through progressive learning
- Handle complex cases (multi-word sponsors, parent companies, regional variants)


## Questions & Decisions

### Question 1: Orchestration Granularity

**Current Behavior:**

- Phase 1 collects `previous_season_url` but doesn't follow it
- Scrapes year-by-year: 2025 → 2024 → 2023...
- Each year: get team list, scrape all teams, move to next year

**Option A: Per-Year Iteration**

```text
Year 2025: Phase 1 (discover all teams) → Phase 2 (process all) → Phase 3 (link all)
Year 2024: Phase 1 (discover all teams) → Phase 2 (process all) → Phase 3 (link all)
...
```

✅ Simpler implementation  
✅ Builds brand knowledge year-by-year  
✅ Checkpoint system stays similar  
❌ Doesn't follow natural team lineage chains

**Option B: Per-Team Traversal**

```text
Get 2025 team list (entry points)
For each team:
  - Follow previous_season_url chain backward (2025 → 2024 → ... → first season)
  - Phase 2: Process this team's complete history
  - Phase 3: Link lineage within this team's history
Move to next team
```

✅ Follows CyclingFlash's natural structure (dropdown chains)  
✅ Progressive learning within each team lineage  
✅ More efficient for sponsor learning (Peugeot → Crédit Agricole sponsors evolve together)  
❌ Need to track processed teams to avoid duplicates (when chains overlap)  
❌ Checkpoint system needs refactoring  
❌ Phases 2 & 3 need to handle "within-team" vs "between-team" processing

**User Decision:** **Per-year** (simpler, more robust, easier to maintain)

### Question 2: Brand Matching Strategy

**The Problem:**

If DB has "Lotto" and we scrape "Lotto NL Jumbo":
- Simple match: "Lotto" found → skip LLM ❌ WRONG (missed "NL")

**User Solution: "Two-Level Caching"**

**Level 1: Team Name Cache (Exact Match)**
```text
Team name: "Lotto Jumbo Team"
Check: Have we processed this EXACT string before?
- YES → Use cached sponsors, skip LLM
- NO → Proceed to Level 2
```

**Level 2: Brand Coverage Check**
```text
Split team name: ["Lotto", "Jumbo", "Team"]
Check each word against DB:
- "Lotto" ✓ (known brand)
- "Jumbo" ✓ (known brand)
- "Team" ✗ (NOT in DB)

Result: Unknown word exists → CALL LLM
(Even if "Team" looks like filler, don't auto-skip)
```

**Important:** NO auto-skip for "filler-like" words
- "Team", "Cycling", etc. might be part of actual brand names
- These are **hints to LLM** in prompt, not auto-ignore

**User Decision:**
- Skip LLM only if: (1) exact team name seen before, OR (2) all words match known brands
- Never auto-skip words based on filler list

### Question 3: LLM Prompt Context

**Decision:** Full context with re-verification requirement.

**Prompt should include:**

1. **Team name**: "Lotto NL Jumbo Team"
2. **Season year**: 2016
3. **Country**: Netherlands
4. **Partial matches from DB**: "Lotto", "Jumbo" (if any)
5. **Critical instruction**: "These partial matches may be incorrect - verify all parts independently"

**Rationale:**

- Year/country help with regional variants (e.g., "Lotto NL" = Dutch Lotto, 2014-2016)
- Partial matches provide hints but **must be re-verified**
- Example: "Lotto" alone is wrong if team is actually "Lotto NL"

**User Decision:** Full context (Option C) + explicit re-verification instruction

### Question 4: LLM Response Data Model

**Requirement:** Granular extraction beyond just sponsor names.

**Examples:**

- "Bahrain Victorious"
  - Sponsor: "Bahrain"
  - Team descriptor: "Victorious"

- "Ineos Grenadiers"
  - Sponsor: "Ineos Grenadier" (brand of INEOS group)
  - Team descriptor: "s" (suffix)

- "NSN Cycling Team"
  - Sponsor: "NSN" (brand of Intl Commercialization of Sports Rights Spain)
  - Filler: "Cycling Team"

**Proposed Response Model:**

```python
class SponsorExtractionResult(BaseModel):
    sponsors: List[str]           # Actual brand/company names
    team_descriptors: List[str]   # Naming additions (e.g., "Victorious")
    filler_words: List[str]       # Generic parts (e.g., "Team", "Cycling")
    confidence: float             # 0.0 - 1.0
    reasoning: str                # Explanation of extraction
```


**My question:** Does this data model capture what you need, or should we add/remove fields?

**Additional considerations:**

- Should we track **parent companies**?
  - Example: "Ineos Grenadier" → parent_company: "INEOS Group"
  - Or: "NSN" → parent_company: "Intl Commercialization of Sports Rights Spain"

- Should we track **regional variants**?
  - Example: "Lotto NL" → base_brand: "Lotto", region: "Netherlands"
  - Or: "Lotto Dstny" → base_brand: "Lotto", region: "Belgium"

- Or is the simple `sponsors: List[str]` sufficient?

(Note: We'd only store `sponsors` in the database initially, other fields are for transparency/debugging)

**User Decision:** 

✅ **YES to parent companies** - track brand → parent company relationships  
❌ **NO to regional variants** - each sponsor is distinct:
  - "Lotto NL" and "Lotto Belgium" are SEPARATE companies (not variants)
  - "Dstny" is completely separate from "Lotto"

**Updated Data Model:**

```python
class SponsorInfo(BaseModel):
    """Information about a single sponsor/brand."""
    brand_name: str              # "Ineos Grenadier", "Lotto NL", "NSN"
    parent_company: Optional[str] # "INEOS Group", "Intl Comm... Spain", None

class SponsorExtractionResult(BaseModel):
    sponsors: List[SponsorInfo]   # Detailed sponsor info
    team_descriptors: List[str]   # "Victorious", "s"
    filler_words: List[str]       # "Team", "Cycling"
    confidence: float             # 0.0 - 1.0
    reasoning: str                # Explanation
```

**Database Storage:**

- `SponsorBrand.name`: "Ineos Grenadier", "Lotto NL", "NSN"
- `SponsorBrand.parent_company`: "INEOS Group", NULL, "Intl Comm..."

### Question 5: Integration Point - When Does LLM Extraction Happen?

**User Decision: Hybrid Approach - Extract in Phase 1, Consolidate in Phase 2**

**Phase 1 (Discovery):**

```text
For each team:
  - Parse team name
  - BrandMatcher checks against DB
  - If unknown parts exist → call LLM → get SponsorExtractionResult
  - Store detailed sponsor info in ScrapedTeamData
```

**Phase 2 (Assembly):**

```text
After collecting ALL teams:
  - Read sponsor details from ScrapedTeamData
  - LLM call: Consolidate & map ALL sponsors globally
    - Decide for each: brand, sponsor master, or BOTH
    - Determine parent company relationships (if any)
    - Deduplicate variations
  - Create SponsorBrand records with hierarchy
  - Link to TeamEra
```

**Important:** A sponsor can be:
- **Brand only**: "Ineos Grenadier" (parent: INEOS Group)
- **Sponsor master only**: "INEOS Group" (no parent)
- **BOTH brand AND sponsor master**: "Bahrain" (sponsors directly, no parent)

**Rationale:**

- Phase 1 provides **richer per-team data** (not just strings)
- Phase 2 does **global consolidation** across all teams
- Avoids duplicate LLM work while maintaining clean separation

**Required Data Model Changes:**

```python
# Phase 1 output
class SponsorInfo(BaseModel):
    brand_name: str
    parent_company: Optional[str]  # Hint from LLM, may be refined in Phase 2

class ScrapedTeamData(BaseModel):
    name: str
    sponsors: List[SponsorInfo]  # Changed from List[str]
    # ... rest
```

### Question 6: BrandMatcher Database Lookup

**Options for matching:**

**Option A: Exact match only**
- "Lotto" matches "Lotto" (brand_name = "Lotto")
- "Lotto" does NOT match "Lotto NL"

**Option B: Substring/contains match**
- "Ineos" matches "Ineos Grenadier"
- Could cause false positives

**Option C: Word-level exact match**
- Split both ways into words
- "Lotto" in "Lotto NL" → match
- "NL" in "Lotto NL" → match

**User Decision:** **Option A (exact match)** - safer, avoids false positives. Per "complete coverage" rule, if "Lotto" is in DB but we scrape "Lotto NL", we still call LLM because "NL" is unknown.

### Question 7: LLM Failure Handling

**Scenario:** LLM call fails (network error, rate limit, timeout, etc.) during Phase 1 extraction.

**Options:**

**Option A: Fallback to simple pattern extraction**
- If LLM fails → use current `sponsor_extractor.extract_title_sponsors()`
- Mark as "low confidence" for manual review
- Continue scraping

**Option B: Skip extraction entirely**
- Store empty sponsors list
- Flag for re-processing
- Continue scraping

**Option C: Retry with exponential backoff**
- Retry 2-3 times with delays
- If still fails → Option A or B
- May slow down scraping significantly

**Option D: Abort scraping**
- Stop the whole process
- Requires manual intervention

**My question:** What should happen when LLM extraction fails in Phase 1?

My recommendation: **Option C** (retry) → **Option A** (pattern fallback) - resilient but keeps progress. We can flag low-confidence extractions for manual review later.

What's your preference?

**User Decision: Multi-tier resilience strategy**

```text
1. Try Gemini (primary)
2. If fails → Try Deepseek (already built into LLMService fallback)
3. If both fail → Retry with exponential backoff (2-3 attempts)
4. If still fails → Move team to BACK of processing queue
5. Retry from queue later
6. If STILL fails → Mark as LOW CONFIDENCE, use pattern extraction fallback
```

**Rationale:**
- Leverage existing dual-LLM architecture
- Exponential backoff handles transient issues
- Queue management allows recovery from temporary outages
- Final fallback ensures scraping completes

**Implementation Note:**
Phase 1 needs a retry queue to hold failed teams for later re-processing.

### Question 8: Team Name Cache Implementation

**Goal:** Avoid calling LLM twice for the same team name.

**Options:**
- **A**: In-memory only (lost on restart)
- **B**: New database table
- **C**: Checkpoint file

**User Decision: Use existing TeamEra table**

**Cache Lookup Logic:**

```text
Team name: "Lotto Jumbo Team"

1. Check in-memory cache (current session)
   - Found → use cached sponsors

2. Query: SELECT * FROM team_eras WHERE registered_name = "Lotto Jumbo Team"
   - Found → Load sponsors from TeamSponsorLink
   - Not found → Proceed with LLM extraction
```

**Rationale:**
- Leverages existing `TeamEra.registered_name` field
- Persists across scraper runs automatically
- No new tables or complexity
- Sponsors already linked via `TeamSponsorLink`

**Implementation Note:**
BrandMatcher needs database access to query both `SponsorBrand` (for word-level matching) and `TeamEra` (for team name-level caching).

---

## Summary of Decisions

**Orchestration:** Per-year iteration (2025 → 1990)  
**Caching:** Two-level (exact team name + brand word matching)  
**LLM Context:** Full (year, country, partial matches, re-verification)  
**Data Model:** Parent company tracking (no regional variants)  
**Integration:** Hybrid (Phase 1 extracts, Phase 2 consolidates)  
**Matching:** Exact match only  
**Failure Handling:** Gemini → Deepseek → retry → queue → fallback  
**Cache Storage:** TeamEra.registered_name as persistent cache

---

## Implementation Details

### Architecture Overview

```text
Phase 1 (Discovery) - PER YEAR:
  ┌─────────────────────────────────────────┐
  │ For each team in year:                   │
  │   1. Parse team name                     │
  │   2. Check TeamName Cache (in-memory)    │
  │      └─ Hit? → Use cached sponsors       │
  │   3. Query TeamEra by registered_name    │
  │      └─ Hit? → Load sponsors from DB     │
  │   4. BrandMatcher: Check words vs DB     │
  │      └─ All known? → Use existing brands │
  │   5. Call LLM (Gemini → Deepseek)       │
  │      └─ Fail? → Retry → Queue → Fallback│
  │   6. Store in ScrapedTeamData            │
  └─────────────────────────────────────────┘

Phase 2 (Assembly) - PER YEAR:
  ┌─────────────────────────────────────────┐
  │ After collecting all teams for year:    │
  │   1. Load all SponsorInfo from scraped   │
  │   2. LLM: Global consolidation           │
  │      - Decide: brand vs master vs both   │
  │      - Determine parent relationships    │
  │      - Deduplicate variations            │
  │   3. Create/Update SponsorBrand records  │
  │   4. Link to TeamEra via TeamSponsorLink │
  └─────────────────────────────────────────┘
```

### Data Model Changes

#### New Pydantic Models

**File:** `backend/app/scraper/llm/models.py` **(NEW)**

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class SponsorInfo(BaseModel):
    """Detailed sponsor/brand information extracted from team name."""
    brand_name: str = Field(description="Brand name (e.g., 'Ineos Grenadier', 'Lotto NL')")
    parent_company: Optional[str] = Field(
        default=None,
        description="Parent company if known (e.g., 'INEOS Group'). May be refined in Phase 2."
    )

class SponsorExtractionResult(BaseModel):
    """LLM response for sponsor extraction from team name."""
    sponsors: List[SponsorInfo] = Field(description="List of sponsor/brand details")
    team_descriptors: List[str] = Field(
        default_factory=list,
        description="Team name additions (e.g., 'Victorious', 's' suffix)"
    )
    filler_words: List[str] = Field(
        default_factory=list,
        description="Generic words (e.g., 'Team', 'Cycling')"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(description="Explanation of extraction decisions")

class BrandMatchResult(BaseModel):
    """Result of brand matching analysis."""
    known_brands: List[str] = Field(description="Words matching existing brands in DB")
    unmatched_words: List[str] = Field(description="Words not in DB (excluding filler)")
    needs_llm: bool = Field(description="True if LLM extraction required")
```

#### Modified Pydantic Models

**File:** `backend/app/scraper/sources/cyclingflash.py`

```python
class ScrapedTeamData(BaseModel):
    """Data scraped from a team's detail page."""
    name: str
    uci_code: Optional[str] = None
    tier_level: Optional[int] = None
    country_code: Optional[str] = Field(default=None, description="3-letter IOC/UCI code")
    
    # CHANGED: From List[str] to List[SponsorInfo]
    sponsors: List[SponsorInfo] = Field(default_factory=list)
    
    previous_season_url: Optional[str] = None
    season_year: int
    extraction_confidence: Optional[float] = Field(
        default=None,
        description="Confidence of sponsor extraction (if LLM was used)"
    )
```

### New Services

#### BrandMatcherService

**File:** `backend/app/scraper/services/brand_matcher.py` **(NEW)**

```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.sponsor import SponsorBrand
from app.models.team import TeamEra
from app.scraper.llm.models import BrandMatchResult, SponsorInfo
import re

class BrandMatcherService:
    """Checks team names against known brands in database."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._team_name_cache: dict[str, List[SponsorInfo]] = {}
    
    async def check_team_name(self, team_name: str) -> Optional[List[SponsorInfo]]:
        """
        Check if exact team name has been processed before.
        Returns cached sponsors if found, None otherwise.
        """
        # 1. Check in-memory cache
        if team_name in self._team_name_cache:
            return self._team_name_cache[team_name]
        
        # 2. Query TeamEra table
        stmt = select(TeamEra).where(TeamEra.registered_name == team_name)
        result = await self._session.execute(stmt)
        team_era = result.scalar_one_or_none()
        
        if team_era:
            # Load sponsors from TeamSponsorLink
            sponsors = []
            for link in team_era.sponsor_links:
                sponsor_info = SponsorInfo(
                    brand_name=link.brand.brand_name,
                    parent_company=link.brand.master.legal_name if link.brand.master else None
                )
                sponsors.append(sponsor_info)
            
            # Cache for session
            self._team_name_cache[team_name] = sponsors
            return sponsors
        
        return None
    
    async def analyze_words(self, team_name: str) -> BrandMatchResult:
        """
        Check if all words in team name match known brands.
        Returns analysis result.
        """
        # Tokenize: split on spaces, hyphens, keep alphanumeric
        words = re.findall(r'\b[\w]+\b', team_name)
        
        known_brands = []
        unmatched_words = []
        
        for word in words:
            stmt = select(SponsorBrand).where(SponsorBrand.brand_name == word)
            result = await self._session.execute(stmt)
            brand = result.scalar_one_or_none()
            
            if brand:
                known_brands.append(word)
            else:
                unmatched_words.append(word)
        
        return BrandMatchResult(
            known_brands=known_brands,
            unmatched_words=unmatched_words,
            needs_llm=len(unmatched_words) > 0
        )
```

### LLM Prompts

**File:** `backend/app/scraper/llm/prompts.py`

Add this method to `ScraperPrompts` class:

```python
SPONSOR_EXTRACTION_PROMPT = """You are an expert in professional cycling team sponsorship and brand identification.

TASK: Extract sponsor/brand information from a professional cycling team name.

TEAM INFORMATION:
- Team Name: {team_name}
- Season Year: {season_year}
- Country: {country_code}
- Partial DB Matches: {partial_matches}

IMPORTANT INSTRUCTIONS:
1. **Re-verify ALL parts independently** - The partial matches may be incorrect
   Example: If DB matched "Lotto" but team is "Lotto NL Jumbo", "Lotto" alone is wrong

2. **Extract sponsors accurately:**
   - Return ONLY actual sponsor/brand names (companies, organizations)
   - Distinguish sponsors from team descriptors (e.g., "Victorious", "Grenadiers")
   - Handle multi-word brand names correctly (e.g., "Ineos Grenadier" not "Ineos")
   - Identify parent companies when possible

3. **Examples:**
   - "Bahrain Victorious" → sponsor: "Bahrain", descriptor: "Victorious"
   - "Ineos Grenadiers" → sponsor: "Ineos Grenadier" (brand of INEOS Group), descriptor: "s"
   - "NSN Cycling Team" → sponsor: "NSN", filler: "Cycling Team"
   - "UAE Team Emirates XRG" → sponsors: ["UAE", "Emirates", "XRG"]
   - "Lotto NL Jumbo Team" → sponsors: ["Lotto NL", "Jumbo"], filler: "Team"

4. **Parent Companies:**
   - If you know the parent company, include it (e.g., "Ineos Grenadier" → INEOS Group)
   - If uncertain, leave as null

5. **Regional Note:**
   - "Lotto NL" and "Lotto Belgium" are SEPARATE companies, not variants

Provide your analysis with high confidence and clear reasoning.
"""

async def extract_sponsors_from_name(
    self,
    team_name: str,
    season_year: int,
    country_code: Optional[str],
    partial_matches: List[str]
) -> SponsorExtractionResult:
    """Extract sponsor information from team name using LLM."""
    prompt = self.SPONSOR_EXTRACTION_PROMPT.format(
        team_name=team_name,
        season_year=season_year,
        country_code=country_code or "Unknown",
        partial_matches=", ".join(partial_matches) if partial_matches else "None"
    )
    
    result = await self._llm.call(
        prompt=prompt,
        response_model=SponsorExtractionResult
    )
    
    return result
```

### Modified Files

#### Phase 1 Integration

**File:** `backend/app/scraper/orchestration/phase1.py`

Key changes:
1. Add `BrandMatcherService` initialization
2. Add retry queue for failed LLM extractions
3. Update discovery loop

```python
from app.scraper.services.brand_matcher import BrandMatcherService
from app.scraper.llm.prompts import ScraperPrompts
from app.scraper.llm.models import SponsorInfo

class DiscoveryService:
    def __init__(
        self,
        scraper: CyclingFlashScraper,
        sponsor_collector: SponsorCollector,
        checkpoint: CheckpointManager,
        monitor: Optional[RunMonitor] = None,
        session: Optional[AsyncSession] = None,  # NEW
        llm_prompts: Optional[ScraperPrompts] = None  # NEW
    ):
        self._scraper = scraper
        self._collector = sponsor_collector
        self._checkpoint = checkpoint
        self._monitor = monitor
        self._session = session
        self._llm_prompts = llm_prompts
        
        # NEW: Initialize brand matcher if session available
        self._brand_matcher = BrandMatcherService(session) if session else None
        
        # NEW: Retry queue for failed LLM extractions
        self._retry_queue: List[Tuple[str, ScrapedTeamData]] = []
    
    async def _extract_sponsors(
        self,
        team_name: str,
        country_code: Optional[str],
        season_year: int
    ) -> Tuple[List[SponsorInfo], float]:
        """
        Extract sponsors from team name with multi-tier resilience.
        Returns (sponsors, confidence).
        """
        if not self._brand_matcher or not self._llm_prompts:
            # Fallback: use simple pattern extraction
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.5
        
        # Level 1: Check team name cache
        cached = await self._brand_matcher.check_team_name(team_name)
        if cached:
            return cached, 1.0
        
        # Level 2: Check brand coverage        
        match_result = await self._brand_matcher.analyze_words(team_name)
        
        if not match_result.needs_llm:
            # All words are known brands
            sponsors = [SponsorInfo(brand_name=b) for b in match_result.known_brands]
            return sponsors, 1.0
        
        # Level 3: Call LLM with retry logic
        try:
            llm_result = await self._llm_prompts.extract_sponsors_from_name(
                team_name=team_name,
                season_year=season_year,
                country_code=country_code,
                partial_matches=match_result.known_brands
            )
            
            return llm_result.sponsors, llm_result.confidence
            
        except Exception as e:
            logger.warning(f"LLM extraction failed for '{team_name}': {e}")
            # Fallback: simple pattern extraction
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.3
```

**File:** `backend/app/scraper/sources/cyclingflash.py`

Update `parse_team_detail` to return `SponsorInfo` objects:

```python
def parse_team_detail(self, html: str, season_year: int) -> ScrapedTeamData:
    """Extract team data from detail page."""
    # ... existing parsing logic ...
    
    # Extract EQUIPMENT sponsors from brand links (keep as strings for now)
    equipment_sponsors = []
    for link in soup.select('a[href*="/brands/"]'):
        sponsor_name = link.get_text(strip=True)
        if sponsor_name and sponsor_name not in equipment_sponsors:
            equipment_sponsors.append(sponsor_name)
    
    # Convert to SponsorInfo (without parent company at parse time)
    sponsors = [SponsorInfo(brand_name=s) for s in equipment_sponsors]
    
    return ScrapedTeamData(
        name=name,
        uci_code=uci_code,
        tier_level=tier_level,
        country_code=country_code,
        sponsors=sponsors,  # Now List[SponsorInfo]
        previous_season_url=prev_url,
        season_year=season_year
    )
```

Note: Title sponsor extraction now happens in Phase 1 service, not parser.

#### Phase 2 Consolidation

**File:** `backend/app/scraper/orchestration/phase2.py`

Update to handle `SponsorInfo` and perform global consolidation:

```python
async def _create_sponsor_links(...):
    """Create sponsor brand records and link to team era."""
    # Extract unique sponsors from ScrapedTeamData
    for sponsor_info in data.sponsors:
        # Check if brand exists
        brand = await self._get_or_create_brand(
            brand_name=sponsor_info.brand_name,
            parent_company_hint=sponsor_info.parent_company
        )
        
        # Create TeamSponsorLink...
```

### Error Handling Strategy

#### Multi-Tier Failure Handling

```python
async def _extract_with_resilience(self, team_name: str, ...) -> Tuple[List[SponsorInfo], float]:
    """Extract with full resilience strategy."""
    
    # Tier 1: Gemini (primary)
    try:
        return await self._call_llm("gemini", ...)
    except Exception as e1:
        logger.warning(f"Gemini failed: {e1}")
    
    # Tier 2: Deepseek (built-in fallback via LLMService)
    try:
        return await self._call_llm("deepseek", ...)
    except Exception as e2:
        logger.warning(f"Deepseek failed: {e2}")
    
    # Tier 3: Exponential backoff retry
    for attempt in range(3):
        await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
        try:
            return await self._call_llm("gemini", ...)
        except Exception as e:
            if attempt == 2:  # Last attempt
                logger.error(f"All retries failed: {e}")
    
    # Tier 4: Add to retry queue
    self._retry_queue.append((team_name, data))
    
    # Tier 5: Pattern fallback (low confidence)
    from app.scraper.utils.sponsor_extractor import extract_title_sponsors
    simple = extract_title_sponsors(team_name)
    return [SponsorInfo(brand_name=s) for s in simple], 0.2
```

### Database Changes

**NO new tables required** - leverages existing schema:

- `SponsorBrand.brand_name`: Store brand names
- `SponsorBrand.master_id`: Link to parent company (SponsorMaster)
- `SponsorMaster.legal_name`: Parent company name
- `TeamEra.registered_name`: Used as persistent cache
- `TeamSponsorLink`: Links brands to team eras

### Testing Strategy

#### Unit Tests

**File:** `backend/tests/scraper/test_brand_matcher.py` **(NEW)**

```python
@pytest.mark.asyncio
async def test_team_name_cache_hit(db_session):
    """Test team name cache returns existing sponsors."""
    # Setup: Create team era with sponsors in DB
    matcher = BrandMatcherService(db_session)
    
    result = await matcher.check_team_name("Lotto Jumbo Team")
    
    assert result is not None
    assert len(result) == 2
    assert result[0].brand_name == "Lotto"

@pytest.mark.asyncio
async def test_brand_coverage_complete(db_session):
    """Test all words match existing brands."""
    matcher = BrandMatcherService(db_session)
    
    result = await matcher.analyze_words("Lotto Jumbo")
    
    assert result.needs_llm == False
    assert len(result.known_brands) == 2

@pytest.mark.asyncio
async def test_brand_coverage_incomplete(db_session):
    """Test unknown words trigger LLM."""
    matcher = BrandMatcherService(db_session)
    
    result = await matcher.analyze_words("Lotto NL Jumbo")
    
    assert result.needs_llm == True
    assert "NL" in result.unmatched_words
```

#### Integration Tests

**File:** `backend/tests/integration/test_sponsor_extraction_flow.py` **(NEW)**

```python
@pytest.mark.asyncio
async def test_full_extraction_flow(db_session, llm_service):
    """Test complete sponsor extraction flow."""
    # Scrape team → Extract sponsors → Verify DB storage
    
@pytest.mark.asyncio
async def test_llm_failure_fallback(db_session):
    """Test fallback when LLM fails."""
    # Mock LLM failure → Verify pattern fallback used
```

#### Manual Verification

1. Run scraper on 2024 WorldTour teams
2. Verify sponsor extraction accuracy:
   - "Bahrain Victorious" → ["Bahrain"]
   - "UAE Team Emirates" → ["UAE", "Emirates"]
   - "Alpecin-Deceuninck" → ["Alpecin", "Deceuninck"]

### Performance Considerations

- **LLM Call Reduction**: Two-level caching should reduce calls by ~80% on subsequent scrapes
- **Database Queries**: Brand matching adds 1 query per unknown team name (acceptable)
- **Memory**: In-memory cache cleared per scraping session

### Migration Path

1. **Phase 1**: Implement new models and services
2. **Phase 2**: Integrate into Phase 1 (scraping)
3. **Phase 3**: Update Phase 2 (assembly)
4. **Phase 4**: Run test scrape on single year
5. **Phase 5**: Full scrape with monitoring

---

## Appendix: Common Filler Words (For LLM Prompt)

These words are **hints** for the LLM (not auto-ignored):

- Team, Pro, Professional, Elite, Development
- Cycling, Racing, Riders
- Club, Foundation, Association
- International, National, Continental
- Academy, U23, Women's
