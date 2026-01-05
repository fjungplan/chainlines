# Progressive Sponsor Extraction - TDD Implementation Prompts

**Context**: Smart Scraper project implementing LLM-based sponsor extraction  
**Specification**: `docs/PROGRESSIVE_SPONSOR_EXTRACTION.md`  
**Blueprint**: `docs/PROGRESSIVE_SPONSOR_EXTRACTION_BLUEPRINT.md`  
**Branch**: `feat/scraper-refinement-llm`

**Critical Rules:**
- ALWAYS write tests FIRST (TDD)
- NEVER skip integration/wiring
- ALWAYS commit after each slice
- Follow existing code patterns

---

## SLICE 1.1: Create LLM Response Models

### Context

You are implementing the foundation for LLM-based sponsor extraction. This slice creates the Pydantic models that will structure LLM responses and brand matching results.

### Background

The Smart Scraper currently uses simple string lists for sponsors. We're upgrading to structured data that includes parent company information and confidence scores. These models will be used throughout the extraction pipeline.

### Task

**Step 1: Write Tests First**

Create `backend/tests/scraper/test_llm_models.py` with tests for:

1. `SponsorInfo` model validation:
   - Valid brand_name (required string)
   - Optional parent_company
   - Rejects empty brand_name
   - Serialization/deserialization

2. `SponsorExtractionResult` model validation:
   - List of SponsorInfo objects
   - team_descriptors and filler_words lists (optional)
   - confidence (float, 0.0-1.0 range)
   - reasoning (required string)
   - Rejects invalid confidence values

3. `BrandMatchResult` model validation:
   - known_brands and unmatched_words lists
   - needs_llm boolean
   - All fields with proper types

**Step 2: Implement Models**

Create `backend/app/scraper/llm/models.py`:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class SponsorInfo(BaseModel):
    """Detailed sponsor/brand information."""
    brand_name: str = Field(description="Brand name (e.g., 'Ineos Grenadier')")
    parent_company: Optional[str] = Field(
        default=None,
        description="Parent company (e.g., 'INEOS Group')"
    )

class SponsorExtractionResult(BaseModel):
    """LLM response for sponsor extraction."""
    sponsors: List[SponsorInfo]
    team_descriptors: List[str] = Field(default_factory=list)
    filler_words: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class BrandMatchResult(BaseModel):
    """Brand matching analysis result."""
    known_brands: List[str]
    unmatched_words: List[str]
    needs_llm: bool
```

**Step 3: Wire Integration**

Update `backend/app/scraper/llm/__init__.py`:
```python
from .models import SponsorInfo, SponsorExtractionResult, BrandMatchResult

__all__ = [
    "SponsorInfo",
    "SponsorExtractionResult",
    "BrandMatchResult",
]
```

**Step 4: Verify**

Run tests:
```bash
pytest backend/tests/scraper/test_llm_models.py -v
```

All tests should pass.

**Step 5: Commit**

```bash
git add backend/app/scraper/llm/models.py backend/app/scraper/llm/__init__.py backend/tests/scraper/test_llm_models.py
git commit -m "feat(scraper): add LLM response Pydantic models for sponsor extraction

- Add SponsorInfo with brand_name and parent_company
- Add SponsorExtractionResult for LLM responses
- Add BrandMatchResult for brand matching analysis
- Comprehensive validation tests for all models"
```

---

## SLICE 1.2: Update ScrapedTeamData Model

### Context

Now that we have `SponsorInfo`, we need to update `ScrapedTeamData` to use it instead of simple strings. This is a breaking change that requires updating the parser and all related tests.

### Background

Currently `ScrapedTeamData.sponsors` is `List[str]`. We're changing it to `List[SponsorInfo]` to carry richer sponsor information from Phase 1 to Phase 2.

### Task

**Step 1: Update Tests First**

Update `backend/tests/scraper/test_cyclingflash.py`:

1. Import `SponsorInfo` from `app.scraper.llm.models`
2. Update `test_parse_team_detail_extracts_data`:
   - Assert sponsors is `List[SponsorInfo]`
   - Check `.brand_name` attribute
   - Verify parent_company is None (not set by parser yet)

3. Update any test fixtures that create `ScrapedTeamData`

**Step 2: Update Model**

Modify `backend/app/scraper/sources/cyclingflash.py`:

```python
from app.scraper.llm.models import SponsorInfo

class ScrapedTeamData(BaseModel):
    """Data scraped from a team's detail page."""
    name: str
    uci_code: Optional[str] = None
    tier_level: Optional[int] = None
    country_code: Optional[str] = Field(default=None, description="3-letter IOC/UCI code")
    sponsors: List[SponsorInfo] = Field(default_factory=list)  # CHANGED
    previous_season_url: Optional[str] = None
    season_year: int
    extraction_confidence: Optional[float] = Field(  # NEW
        default=None,
        description="Confidence of sponsor extraction (if LLM was used)"
    )
```

**Step 3: Update Parser**

In same file, update `CyclingFlashParser.parse_team_detail()`:

```python
# Extract EQUIPMENT sponsors from brand links
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

**Step 4: Update Phase 2 (Temporary Fix)**

Update `backend/app/scraper/orchestration/phase2.py` to handle `SponsorInfo`:

```python
# In _create_sponsor_links or similar method:
for sponsor_info in data.sponsors:
    brand_name = sponsor_info.brand_name  # Extract string from SponsorInfo
    # ... rest of logic
```

**Step 5: Verify**

```bash
pytest backend/tests/scraper/test_cyclingflash.py -v
pytest backend/tests/scraper/test_phase2.py -v  # Ensure Phase 2 still works
```

**Step 6: Commit**

```bash
git add -A
git commit -m "refactor(scraper): update ScrapedTeamData to use SponsorInfo

- Change sponsors field from List[str] to List[SponsorInfo]
- Add extraction_confidence field
- Update parser to create SponsorInfo objects
- Update Phase 2 to extract brand_name from SponsorInfo
- Fix all related tests

BREAKING CHANGE: ScrapedTeamData.sponsors is now List[SponsorInfo]"
```

---

## SLICE 2.1: Team Name Cache (DB Lookup)

### Context

Implement the first level of caching: checking if we've seen this exact team name before by querying the `TeamEra` table.

### Background

To minimize LLM calls, we first check if this team name already exists in our database. If it does, we can reuse the sponsors we already extracted.

### Task

**Step 1: Write Tests First**

Create `backend/tests/scraper/test_brand_matcher.py`:

```python
import pytest
from app.scraper.services.brand_matcher import BrandMatcherService
from app.models.team import TeamEra
from app.models.sponsor import SponsorBrand, SponsorMaster
from app.models.link import TeamSponsorLink

@pytest.mark.asyncio
async def test_team_name_cache_hit(db_session):
    """Test team name cache returns existing sponsors when found."""
    # Setup: Create team era with sponsors in DB
    master = SponsorMaster(legal_name="Test Master", ...)
    brand1 = SponsorBrand(master=master, brand_name="Lotto", ...)
    brand2 = SponsorBrand(master=master, brand_name="Jumbo", ...)
    team_era = TeamEra(registered_name="Lotto Jumbo Team", ...)
    link1 = TeamSponsorLink(team_era=team_era, brand=brand1, ...)
    link2 = TeamSponsorLink(team_era=team_era, brand=brand2, ...)
    db_session.add_all([master, brand1, brand2, team_era, link1, link2])
    await db_session.commit()
    
    # Test
    matcher = BrandMatcherService(db_session)
    result = await matcher.check_team_name("Lotto Jumbo Team")
    
    # Assert
    assert result is not None
    assert len(result) == 2
    assert result[0].brand_name == "Lotto"
    assert result[1].brand_name == "Jumbo"

@pytest.mark.asyncio
async def test_team_name_cache_miss(db_session):
    """Test returns None when team name not found."""
    matcher = BrandMatcherService(db_session)
    result = await matcher.check_team_name("Unknown Team")
    assert result is None

@pytest.mark.asyncio
async def test_team_name_cache_in_memory(db_session):
    """Test in-memory cache works across multiple calls."""
    # Setup DB
    # ...
    matcher = BrandMatcherService(db_session)
    
    # First call: DB query
    result1 = await matcher.check_team_name("Lotto Jumbo Team")
    
    # Second call: in-memory cache (no DB query)
    result2 = await matcher.check_team_name("Lotto Jumbo Team")
    
    assert result1 == result2
```

**Step 2: Implement Service**

Create `backend/app/scraper/services/brand_matcher.py`:

```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.team import TeamEra
from app.scraper.llm.models import SponsorInfo
import logging

logger = logging.getLogger(__name__)

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
            logger.debug(f"Team name cache HIT (in-memory): {team_name}")
            return self._team_name_cache[team_name]
        
        # 2. Query TeamEra table
        stmt = (
            select(TeamEra)
            .where(TeamEra.registered_name == team_name)
            .options(selectinload(TeamEra.sponsor_links).selectinload(TeamSponsorLink.brand).selectinload(SponsorBrand.master))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        team_era = result.scalar_one_or_none()
        
        if team_era and team_era.sponsor_links:
            logger.debug(f"Team name cache HIT (DB): {team_name}")
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
        
        logger.debug(f"Team name cache MISS: {team_name}")
        return None
```

**Step 3: Wire Integration**

Update `backend/app/scraper/services/__init__.py`:
```python
from .brand_matcher import BrandMatcherService

__all__ = [
    "BrandMatcherService",
    # ... existing exports
]
```

**Step 4: Verify**

```bash
pytest backend/tests/scraper/test_brand_matcher.py::test_team_name_cache_* -v
```

**Step 5: Commit**

```bash
git add backend/app/scraper/services/brand_matcher.py backend/app/scraper/services/__init__.py backend/tests/scraper/test_brand_matcher.py
git commit -m "feat(scraper): add BrandMatcher team name caching

- Implement check_team_name() with two-level cache
- In-memory cache for session-level performance
- DB lookup via TeamEra.registered_name for persistence
- Load existing sponsors from TeamSponsorLink
- Comprehensive tests for cache hit/miss scenarios"
```

---

## SLICE 2.2: Word-Level Brand Matching

### Context

Add word-level brand matching to determine if all words in a team name match known brands in the database.

### Background

If we haven't seen this exact team name before, we check if all individual words (brands) are already known. If yes, we can skip the LLM call.

### Task

**Step 1: Write Tests First**

Add to `backend/tests/scraper/test_brand_matcher.py`:

```python
@pytest.mark.asyncio
async def test_brand_coverage_complete(db_session):
    """Test all words match existing brands - no LLM needed."""
    # Setup: Create brands "Lotto" and "Jumbo" in DB
    master = SponsorMaster(...)
    brand1 = SponsorBrand(master=master, brand_name="Lotto", ...)
    brand2 = SponsorBrand(master=master, brand_name="Jumbo", ...)
    db_session.add_all([master, brand1, brand2])
    await db_session.commit()
    
    matcher = BrandMatcherService(db_session)
    result = await matcher.analyze_words("Lotto Jumbo")
    
    assert result.needs_llm == False
    assert len(result.known_brands) == 2
    assert "Lotto" in result.known_brands
    assert "Jumbo" in result.known_brands
    assert len(result.unmatched_words) == 0

@pytest.mark.asyncio
async def test_brand_coverage_incomplete(db_session):
    """Test unknown words trigger LLM."""
    # Setup: Only create "Lotto" brand
    master = SponsorMaster(...)
    brand1 = SponsorBrand(master=master, brand_name="Lotto", ...)
    db_session.add(brand1)
    await db_session.commit()
    
    matcher = BrandMatcherService(db_session)
    result = await matcher.analyze_words("Lotto NL Jumbo")
    
    assert result.needs_llm == True
    assert "Lotto" in result.known_brands
    assert "NL" in result.unmatched_words
    assert "Jumbo" in result.unmatched_words

@pytest.mark.asyncio
async def test_brand_coverage_no_brands(db_session):
    """Test completely unknown team triggers LLM."""
    matcher = BrandMatcherService(db_session)
    result = await matcher.analyze_words("Unknown New Team")
    
    assert result.needs_llm == True
    assert len(result.known_brands) == 0
    assert len(result.unmatched_words) == 3
```

**Step 2: Implement Method**

Add to `backend/app/scraper/services/brand_matcher.py`:

```python
import re
from app.models.sponsor import SponsorBrand
from app.scraper.llm.models import BrandMatchResult

class BrandMatcherService:
    # ... existing methods ...
    
    async def analyze_words(self, team_name: str) -> BrandMatchResult:
        """
        Check if all words in team name match known brands.
        Returns analysis result indicating if LLM is needed.
        """
        # Tokenize: split on non-alphanumeric, keep words
        words = re.findall(r'\b[\w]+\b', team_name)
        
        known_brands = []
        unmatched_words = []
        
        for word in words:
            # Exact match against brand_name
            stmt = select(SponsorBrand).where(SponsorBrand.brand_name == word).limit(1)
            result = await self._session.execute(stmt)
            brand = result.scalar_one_or_none()
            
            if brand:
                known_brands.append(word)
            else:
                unmatched_words.append(word)
        
        needs_llm = len(unmatched_words) > 0
        
        logger.debug(
            f"Word analysis for '{team_name}': "
            f"{len(known_brands)} known, {len(unmatched_words)} unknown, "
            f"LLM needed: {needs_llm}"
        )
        
        return BrandMatchResult(
            known_brands=known_brands,
            unmatched_words=unmatched_words,
            needs_llm=needs_llm
        )
```

**Step 3: Verify**

```bash
pytest backend/tests/scraper/test_brand_matcher.py -v
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(scraper): add word-level brand matching to BrandMatcher

- Implement analyze_words() method
- Tokenize team names and match against SponsorBrand table
- Return BrandMatchResult with known/unknown words
- Determine if LLM extraction is needed
- Tests for complete/incomplete/no coverage scenarios"
```

---

## SLICE 3.1: Sponsor Extraction Prompt

### Context

Add the LLM prompt and method for extracting sponsors from team names.

### Background

This is the core LLM integration. The prompt must provide context, examples, and clear instructions for accurate sponsor extraction.

### Task

**Step 1: Write Tests First**

Create `backend/tests/scraper/test_sponsor_prompts.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.scraper.llm.prompts import ScraperPrompts
from app.scraper.llm.models import SponsorExtractionResult, SponsorInfo

@pytest.mark.asyncio
async def test_extract_sponsors_from_name():
    """Test sponsor extraction prompt formatting and call."""
    mock_llm = AsyncMock()
    mock_llm.call.return_value = SponsorExtractionResult(
        sponsors=[SponsorInfo(brand_name="Bahrain")],
        team_descriptors=["Victorious"],
        filler_words=[],
        confidence=0.95,
        reasoning="Bahrain is the sponsor, Victorious is a descriptor"
    )
    
    prompts = ScraperPrompts(llm=mock_llm)
    
    result = await prompts.extract_sponsors_from_name(
        team_name="Bahrain Victorious",
        season_year=2024,
        country_code="BHR",
        partial_matches=[]
    )
    
    assert len(result.sponsors) == 1
    assert result.sponsors[0].brand_name == "Bahrain"
    assert "Victorious" in result.team_descriptors
    assert result.confidence == 0.95
    
    # Verify LLM was called with formatted prompt
    mock_llm.call.assert_called_once()
    call_args = mock_llm.call.call_args
    assert "Bahrain Victorious" in call_args.kwargs["prompt"]
    assert "2024" in call_args.kwargs["prompt"]

@pytest.mark.asyncio
async def test_extract_sponsors_with_partial_matches():
    """Test prompt includes partial matches from DB."""
    mock_llm = AsyncMock()
    mock_llm.call.return_value = SponsorExtractionResult(...)
    
    prompts = ScraperPrompts(llm=mock_llm)
    await prompts.extract_sponsors_from_name(
        team_name="Lotto NL Jumbo",
        season_year=2016,
        country_code="NED",
        partial_matches=["Lotto", "Jumbo"]
    )
    
    call_args = mock_llm.call.call_args
    assert "Lotto, Jumbo" in call_args.kwargs["prompt"]
```

**Step 2: Implement Prompt**

Add to `backend/app/scraper/llm/prompts.py`:

```python
from app.scraper.llm.models import SponsorExtractionResult
from typing import List, Optional

class ScraperPrompts:
    # ... existing code ...
    
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

**Step 3: Verify**

```bash
pytest backend/tests/scraper/test_sponsor_prompts.py -v
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(scraper): add LLM sponsor extraction prompt

- Add SPONSOR_EXTRACTION_PROMPT with detailed instructions
- Implement extract_sponsors_from_name() method
- Include context: team name, year, country, partial matches
- Provide cycling-specific examples in prompt
- Comprehensive tests with mocked LLM responses"
```

---

## SLICE 4.1: Update DiscoveryService Constructor

### Context

Update Phase 1's `DiscoveryService` to accept database session and LLM prompts for sponsor extraction.

### Background

`DiscoveryService` currently doesn't have database access or LLM integration. We need to add these dependencies while maintaining backward compatibility.

### Task

**Step 1: Update Tests First**

Update `backend/tests/scraper/test_phase1.py`:

```python
from app.scraper.services.brand_matcher import BrandMatcherService
from app.scraper.llm.prompts import ScraperPrompts

@pytest.fixture
async def llm_prompts(mock_llm_service):
    """Provide ScraperPrompts instance for tests."""
    return ScraperPrompts(llm=mock_llm_service)

@pytest.fixture
async def discovery_service(
    cycling_flash_scraper,
    sponsor_collector,
    checkpoint_manager,
    run_monitor,
    db_session,  # NEW
    llm_prompts  # NEW
):
    """Create DiscoveryService with all dependencies."""
    return DiscoveryService(
        scraper=cycling_flash_scraper,
        sponsor_collector=sponsor_collector,
        checkpoint=checkpoint_manager,
        monitor=run_monitor,
        session=db_session,  # NEW
        llm_prompts=llm_prompts  # NEW
    )

# Update existing tests to use new fixture
```

**Step 2: Update Constructor**

Modify `backend/app/scraper/orchestration/phase1.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.services.brand_matcher import BrandMatcherService
from app.scraper.llm.prompts import ScraperPrompts
from typing import Optional

class DiscoveryService:
    """Phase 1: Discover teams and collect sponsor names."""
    
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
        
        logger.info(
            f"DiscoveryService initialized with "
            f"LLM extraction: {llm_prompts is not None}, "
            f"Brand matching: {self._brand_matcher is not None}"
        )
```

**Step 3: Update CLI/Main (Temporary - No LLM Yet)**

Update `backend/app/scraper/cli.py` or wherever `DiscoveryService` is instantiated:

```python
# Add session and llm_prompts as None for now
discovery_service = DiscoveryService(
    scraper=scraper,
    sponsor_collector=collector,
    checkpoint=checkpoint,
    monitor=monitor,
    session=None,  # Will be provided when LLM integration is ready
    llm_prompts=None  # Will be provided when LLM integration is ready
)
```

**Step 4: Verify**

```bash
pytest backend/tests/scraper/test_phase1.py -v
```

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor(scraper): add session and LLM prompts to DiscoveryService

- Add optional session and llm_prompts constructor parameters
- Initialize BrandMatcherService when session is provided
- Update tests to provide new dependencies
- Maintain backward compatibility (both params optional)
- Add logging for LLM/brand matching availability"
```

---

## SLICE 4.2: Sponsor Extraction Method

### Context

Implement the core sponsor extraction method with two-level caching and LLM integration.

### Background

This method orchestrates the entire extraction flow: team name cache → brand coverage → LLM call → fallback.

### Task

**Step 1: Write Tests First**

Add to `backend/tests/scraper/test_phase1.py`:

```python
@pytest.mark.asyncio
async def test_extract_sponsors_cache_hit(discovery_service_with_llm, db_session):
    """Test extraction uses cached sponsors when team name found."""
    # Setup: Create team in DB with sponsors
    # ...
    
    sponsors, confidence = await discovery_service._extract_sponsors(
        team_name="Lotto Jumbo Team",
        country_code="NED",
        season_year=2024
    )
    
    assert len(sponsors) == 2
    assert confidence == 1.0  # Cache hit = full confidence

@pytest.mark.asyncio
async def test_extract_sponsors_all_known_brands(discovery_service_with_llm, db_session):
    """Test extraction skips LLM when all words are known brands."""
    # Setup: Create brands in DB
    # ...
    
    sponsors, confidence = await discovery_service._extract_sponsors(
        team_name="Lotto Jumbo",
        country_code="NED",
        season_year=2024
    )
    
    assert len(sponsors) == 2
    assert confidence == 1.0  # All known = full confidence
    # Verify LLM was NOT called

@pytest.mark.asyncio
async def test_extract_sponsors_llm_call(discovery_service_with_llm, mock_llm):
    """Test extraction calls LLM for unknown words."""
    mock_llm.call.return_value = SponsorExtractionResult(
        sponsors=[SponsorInfo(brand_name="Lotto NL"), SponsorInfo(brand_name="Jumbo")],
        confidence=0.95,
        reasoning="..."
    )
    
    sponsors, confidence = await discovery_service._extract_sponsors(
        team_name="Lotto NL Jumbo",
        country_code="NED",
        season_year=2016
    )
    
    assert len(sponsors) == 2
    assert sponsors[0].brand_name == "Lotto NL"
    assert confidence == 0.95
    # Verify LLM WAS called

@pytest.mark.asyncio
async def test_extract_sponsors_fallback(discovery_service_no_llm):
    """Test extraction falls back to pattern matching without LLM."""
    sponsors, confidence = await discovery_service._extract_sponsors(
        team_name="Lotto Jumbo Team",
        country_code="NED",
        season_year=2024
    )
    
    # Should use simple pattern extraction
    assert len(sponsors) > 0
    assert confidence < 1.0  # Fallback has lower confidence
```

**Step 2: Implement Method**

Add to `backend/app/scraper/orchestration/phase1.py`:

```python
from typing import Tuple
from app.scraper.llm.models import SponsorInfo

class DiscoveryService:
    # ... existing code ...
    
    async def _extract_sponsors(
        self,
        team_name: str,
        country_code: Optional[str],
        season_year: int
    ) -> Tuple[List[SponsorInfo], float]:
        """
        Extract sponsors from team name with multi-tier caching.
        Returns (sponsors, confidence).
        """
        # Fallback if no LLM/DB available
        if not self._brand_matcher or not self._llm_prompts:
            logger.warning(f"No LLM/BrandMatcher available, using pattern fallback for '{team_name}'")
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.5
        
        # Level 1: Check team name cache (exact match)
        cached = await self._brand_matcher.check_team_name(team_name)
        if cached:
            logger.info(f"Using cached sponsors for '{team_name}'")
            return cached, 1.0
        
        # Level 2: Check brand coverage (word-level matching)
        match_result = await self._brand_matcher.analyze_words(team_name)
        
        if not match_result.needs_llm:
            # All words are known brands - no LLM needed
            logger.info(f"All brands known for '{team_name}', skipping LLM")
            sponsors = [SponsorInfo(brand_name=b) for b in match_result.known_brands]
            return sponsors, 1.0
        
        # Level 3: Call LLM for unknown words
        try:
            logger.info(f"Calling LLM for '{team_name}' (unknown: {match_result.unmatched_words})")
            llm_result = await self._llm_prompts.extract_sponsors_from_name(
                team_name=team_name,
                season_year=season_year,
                country_code=country_code,
                partial_matches=match_result.known_brands
            )
            
            logger.debug(
                f"LLM extraction complete for '{team_name}': "
                f"{len(llm_result.sponsors)} sponsors, confidence={llm_result.confidence}"
            )
            return llm_result.sponsors, llm_result.confidence
            
        except Exception as e:
            logger.exception(f"LLM extraction failed for '{team_name}': {e}")
            # Fallback: simple pattern extraction
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.3
```

**Step 3: Verify**

```bash
pytest backend/tests/scraper/test_phase1.py::test_extract_sponsors_* -v
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(scraper): implement two-level sponsor extraction method

- Add _extract_sponsors() with team cache and brand matching
- Level 1: TeamEra cache (exact team name match)
- Level 2: Brand coverage check (all words known)
- Level 3: LLM extraction for unknown words
- Fallback: Pattern extraction if LLM unavailable/fails
- Comprehensive tests for all extraction paths"
```

---
---

## SLICE 4.3a: Integrate Equipment Sponsors into Discovery

### Context

Integrate the `_extract_sponsors()` method into the discovery loop to extract sponsors from equipment brands (currently collected from HTML links).

### Background

The parser already collects equipment sponsors from brand links in the HTML. Now we need to ensure these go through LLM extraction as well for consistency.

### Task

**Step 1: Write Tests First**

Add to `backend/tests/scraper/test_phase1.py`:

```python
@pytest.mark.asyncio
async def test_discover_teams_extracts_sponsors(discovery_service_with_llm, mock_scraper, db_session):
    """Test discovery loop extracts sponsors via LLM."""
    # Setup: Mock scraper to return team data
    mock_team_data = ScrapedTeamData(
        name="Lotto Jumbo Team",
        uci_code="LOT",
        tier_level=1,
        country_code="NED",
        sponsors=[SponsorInfo(brand_name="Shimano")],  # Equipment sponsor from parser
        season_year=2024
    )
    mock_scraper.scrape_team.return_value = mock_team_data
    
    # Mock LLM to add title sponsors
    mock_llm.call.return_value = SponsorExtractionResult(
        sponsors=[
            SponsorInfo(brand_name="Lotto"),
            SponsorInfo(brand_name="Jumbo")
        ],
        confidence=0.95,
        reasoning="..."
    )
    
    # Run discovery
    await discovery_service.discover_year(tier=1, year=2024)
    
    # Verify sponsors were extracted from team name
    assert mock_llm.call.called
    # Verify equipment + title sponsors combined
```

**Step 2: Update Discovery Loop**

Modify `backend/app/scraper/orchestration/phase1.py`:

```python
async <br>_discover_teams_for_tier(self, tier: int, year: int):
    """Discover all teams for a specific tier and year."""
    # ... existing code to get team URLs ...
    
    for team_url in team_urls:
        try:
            # Parse team detail page (gets equipment sponsors)
            team_data = await self._scraper.scrape_team(team_url, year)
            
            # NEW: Extract title sponsors from team name
            if self._llm_prompts and self._brand_matcher:
                title_sponsors, confidence = await self._extract_sponsors(
                    team_name=team_data.name,
                    country_code=team_data.country_code,
                    season_year=year
                )
                
                # Merge title sponsors with equipment sponsors from parser
                # Title sponsors go first (more prominent)
                all_sponsors = title_sponsors.copy()
                for eq_sponsor in team_data.sponsors:
                    # Avoid duplicates
                    if not any(s.brand_name == eq_sponsor.brand_name for s in all_sponsors):
                        all_sponsors.append(eq_sponsor)
                
                # Update team data with merged sponsors
                team_data = team_data.model_copy(update={
                    "sponsors": all_sponsors,
                    "extraction_confidence": confidence
                })
                
                logger.debug(
                    f"Merged sponsors for '{team_data.name}': "
                    f"{len(title_sponsors)} title + {len(team_data.sponsors)} equipment"
                )
            
            # Collect for Phase 2
            await self._collector.add_team(team_data)
            
        except Exception as e:
            logger.exception(f"Failed to process team {team_url}: {e}")
            continue
```

**Step 3: Verify**

```bash
pytest backend/tests/scraper/test_phase1.py -v
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(scraper): integrate sponsor extraction into discovery loop

- Call _extract_sponsors() for each team during discovery
- Extract title sponsors from team name via LLM
- Merge title + equipment sponsors (title first)
- Set extraction_confidence on ScrapedTeamData
- Avoid duplicate sponsors in merged list
- Tests verify LLM extraction in discovery flow"
```

---

## SLICE 4.3b: Add CLI Integration for LLM Extraction

### Context

Wire the database session and LLM prompts into the CLI so the discovery service can actually use LLM extraction in production.

### Background

Currently, `DiscoveryService` receives `session=None` and `llm_prompts=None` from the CLI. We need to pass actual instances.

### Task

**Step 1: Update Tests (if needed)**

Ensure CLI tests pass database session and LLM service:

```python
# In backend/tests/scraper/test_cli.py or similar
async def test_cli_scraper_with_llm(db_session, llm_service):
    """Test CLI wires LLM extraction correctly."""
    # Verify DiscoveryService receives session and prompts
```

**Step 2: Update CLI**

Modify `backend/app/scraper/cli.py`:

```python
from app.scraper.llm.service import LLMService
from app.scraper.llm.prompts import ScraperPrompts
from app.db.session import get_async_session

async def run_scraper(
    phase: int,
    tier: str,
    dry_run: bool = False,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
):
    """Run scraper with all phases."""
    
    # Initialize LLM service
    llm_service = LLMService()  # Uses Gemini primary, Deepseek fallback
    llm_prompts = ScraperPrompts(llm=llm_service)
    
    # Get database session
    async with get_async_session() as session:
        # Initialize scraper components
        scraper = CyclingFlashScraper()
        collector = SponsorCollector()
        checkpoint = CheckpointManager(...)
        monitor = RunMonitor(...)
        
        # Create discovery service WITH database and LLM
        discovery_service = DiscoveryService(
            scraper=scraper,
            sponsor_collector=collector,
            checkpoint=checkpoint,
            monitor=monitor,
            session=session,  # NOW PROVIDED
            llm_prompts=llm_prompts  # NOW PROVIDED
        )
        
        # Run Phase 1
        if phase == 1:
            await discovery_service.discover_year(tier=int(tier), year=start_year)
        
        # ... rest of CLI logic
```

**Step 3: Update Main Entry Point**

If there's a separate `main.py` or FastAPI endpoint, update similarly.

**Step 4: Verify**

```bash
# Test with dry run
python -m app.scraper.cli --phase 1 --tier 1 --dry-run --start-year 2024
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat(scraper): wire LLM extraction into CLI

- Initialize LLMService and ScraperPrompts in CLI
- Pass database session to DiscoveryService
- Enable LLM-based sponsor extraction in production
- Update CLI tests to verify LLM integration"
```

---

## SLICE 5.1: Update Phase 2 for SponsorInfo

### Context

Update `TeamAssemblyService` in Phase 2 to properly handle `SponsorInfo` objects and create/link sponsor brands with parent companies.

### Background

Phase 2 currently expects `List[str]` for sponsors. Now it receives `List[SponsorInfo]` with potential parent company information.

### Task

**Step 1: Write Tests First**

Update `backend/tests/scraper/test_phase2.py`:

```python
@pytest.mark.asyncio
async def test_assembly_creates_sponsor_with_parent(db_session, audit_log_service):
    """Test Phase 2 creates sponsor brand with parent company."""
    team_data = ScrapedTeamData(
        name="Ineos Grenadiers",
        sponsors=[
            SponsorInfo(
                brand_name="Ineos Grenadier",
                parent_company="INEOS Group"
            )
        ],
        tier_level=1,
        country_code="GBR",
        season_year=2024
    )
    
    assembly_service = TeamAssemblyService(session=db_session, audit=audit_log_service)
    team_era = await assembly_service.assemble_team(team_data)
    
    # Verify sponsor brand created
    assert len(team_era.sponsor_links) == 1
    assert team_era.sponsor_links[0].brand.brand_name == "Ineos Grenadier"
    
    # Verify parent company created/linked
    assert team_era.sponsor_links[0].brand.master is not None
    assert team_era.sponsor_links[0].brand.master.legal_name == "INEOS Group"

@pytest.mark.asyncio
async def test_assembly_handles_sponsor_without_parent(db_session, audit_log_service):
    """Test Phase 2 handles sponsors without parent company."""
    team_data = ScrapedTeamData(
        name="Bahrain Victorious",
        sponsors=[
            SponsorInfo(brand_name="Bahrain", parent_company=None)
        ],
        tier_level=1,
        country_code="BHR",
        season_year=2024
    )
    
    assembly_service = TeamAssemblyService(session=db_session, audit=audit_log_service)
    team_era = await assembly_service.assemble_team(team_data)
    
    # Verify sponsor created without parent
    assert len(team_era.sponsor_links) == 1
    assert team_era.sponsor_links[0].brand.brand_name == "Bahrain"
    assert team_era.sponsor_links[0].brand.master is None
```

**Step 2: Update Assembly Service**

Modify `backend/app/scraper/orchestration/phase2.py`:

```python
from app.scraper.llm.models import SponsorInfo

class TeamAssemblyService:
    # ... existing code ...
    
    async def _get_or_create_sponsor_master(
        self,
        legal_name: str
    ) -> SponsorMaster:
        """Get or create sponsor master (parent company)."""
        stmt = select(SponsorMaster).where(SponsorMaster.legal_name == legal_name)
        result = await self._session.execute(stmt)
        master = result.scalar_one_or_none()
        
        if not master:
            logger.info(f"Creating new SponsorMaster: {legal_name}")
            master = SponsorMaster(
                legal_name=legal_name,
                created_by=SMART_SCRAPER_USER_ID
            )
            self._session.add(master)
            await self._session.flush()
        
        return master
    
    async def _get_or_create_brand(
        self,
        sponsor_info: SponsorInfo
    ) -> SponsorBrand:
        """Get or create sponsor brand with parent company."""
        # Handle parent company first
        master = None
        if sponsor_info.parent_company:
            master = await self._get_or_create_sponsor_master(sponsor_info.parent_company)
        
        # Check if brand exists
        stmt = select(SponsorBrand).where(
            SponsorBrand.brand_name == sponsor_info.brand_name
        )
        if master:
            stmt = stmt.where(SponsorBrand.master_id == master.master_id)
        
        result = await self._session.execute(stmt)
        brand = result.scalar_one_or_none()
        
        if not brand:
            logger.info(
                f"Creating new SponsorBrand: {sponsor_info.brand_name} "
                f"(parent: {sponsor_info.parent_company or 'None'})"
            )
            brand = SponsorBrand(
                brand_name=sponsor_info.brand_name,
                master=master,
                default_hex_color="#000000",  # Default color
                created_by=SMART_SCRAPER_USER_ID
            )
            self._session.add(brand)
            await self._session.flush()
        
        return brand
    
    async def _create_sponsor_links(
        self,
        team_era: TeamEra,
        sponsors: List[SponsorInfo]
    ):
        """Create sponsor links for team era."""
        for idx, sponsor_info in enumerate(sponsors):
            brand = await self._get_or_create_brand(sponsor_info)
            
            # Create link with prominence (title sponsors higher)
            prominence = 100 - (idx * 10)  # 100%, 90%, 80%, etc.
            prominence = max(prominence, 0)  # Min 0%
            
            link = TeamSponsorLink(
                team_era=team_era,
                brand=brand,
                prominence_percentage=prominence,
                sponsor_type="TITLE" if idx == 0 else "SECONDARY",
                created_by=SMART_SCRAPER_USER_ID
            )
            self._session.add(link)
```

**Step 3: Verify**

```bash
pytest backend/tests/scraper/test_phase2.py -v
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(scraper): update Phase 2 to handle SponsorInfo with parent companies

- Add _get_or_create_sponsor_master() method
- Update _get_or_create_brand() to accept SponsorInfo
- Create parent company (SponsorMaster) when provided
- Link brand to parent via master_id
- Calculate prominence based on sponsor order
- Tests for sponsors with/without parent companies"
```

---

## SLICE 6.1: Implement Retry Queue

### Context

Add a retry queue to handle teams where LLM extraction failed temporarily, allowing them to be retried at the end of year processing.

### Background

Per the multi-tier resilience strategy, when both Gemini and Deepseek fail after retries, we should queue the team for later retry before falling back to pattern extraction.

### Task

**Step 1: Write Tests First**

Add to `backend/tests/scraper/test_phase1.py`:

```python
@pytest.mark.asyncio
async def test_retry_queue_adds_failed_teams(discovery_service_with_llm, mock_llm):
    """Test failed LLM extractions are added to retry queue."""
    # Mock LLM to fail
    mock_llm.call.side_effect = Exception("LLM service unavailable")
    
    sponsors, confidence = await discovery_service._extract_sponsors(
        team_name="Test Team",
        country_code="USA",
        season_year=2024
    )
    
    # Should fallback to pattern extraction
    assert len(sponsors) > 0
    assert confidence < 1.0
    
    # Should be in retry queue
    assert len(discovery_service._retry_queue) == 1
    assert discovery_service._retry_queue[0][0] == "Test Team"

@pytest.mark.asyncio
async def test_process_retry_queue(discovery_service_with_llm, mock_llm):
    """Test retry queue is processed at end of year."""
    # Add items to retry queue
    discovery_service._retry_queue.append(("Team 1", {...}))
    discovery_service._retry_queue.append(("Team 2", {...}))
    
    # Mock LLM to succeed on retry
    mock_llm.call.return_value = SponsorExtractionResult(...)
    
    # Process retry queue
    await discovery_service._process_retry_queue()
    
    # Verify LLM was called for each queued item
    assert mock_llm.call.call_count == 2
    
    # Verify queue is cleared
    assert len(discovery_service._retry_queue) == 0
```

**Step 2: Add Retry Queue Logic**

Update `backend/app/scraper/orchestration/phase1.py`:

```python
from typing import List, Tuple
import asyncio

class DiscoveryService:
    def __init__(self, ...):
        # ... existing init ...
        self._retry_queue: List[Tuple[str, dict]] = []  # (team_name, context)
    
    async def _extract_sponsors(
        self,
        team_name: str,
        country_code: Optional[str],
        season_year: int
    ) -> Tuple[List[SponsorInfo], float]:
        """Extract sponsors with retry queue support."""
        # ... existing cache/brand matching logic ...
        
        # Level 3: Call LLM with retry logic
        try:
            # ... existing LLM call ...
            return llm_result.sponsors, llm_result.confidence
            
        except Exception as e:
            logger.exception(f"LLM extraction failed for '{team_name}': {e}")
            
            # Add to retry queue
            self._retry_queue.append((team_name, {
                "country_code": country_code,
                "season_year": season_year,
                "partial_matches": match_result.known_brands if match_result else []
            }))
            
            logger.info(f"Added '{team_name}' to retry queue ({len(self._retry_queue)} items)")
            
            # Fallback: simple pattern extraction
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.3
    
    async def _process_retry_queue(self):
        """Process all items in retry queue at end of year."""
        if not self._retry_queue:
            logger.info("Retry queue is empty, skipping")
            return
        
        logger.info(f"Processing retry queue: {len(self._retry_queue)} items")
        
        retry_items = self._retry_queue.copy()
        self._retry_queue.clear()
        
        for team_name, context in retry_items:
            try:
                logger.info(f"Retrying sponsor extraction for '{team_name}'")
                
                # Wait a bit between retries to avoid rate limits
                await asyncio.sleep(1)
                
                sponsors, confidence = await self._extract_sponsors(
                    team_name=team_name,
                    country_code=context["country_code"],
                    season_year=context["season_year"]
                )
                
                if confidence > 0.5:
                    logger.info(f"Retry successful for '{team_name}': {len(sponsors)} sponsors")
                else:
                    logger.warning(f"Retry fallback for '{team_name}': low confidence {confidence}")
                    
            except Exception as e:
                logger.exception(f"Retry failed for '{team_name}': {e}")
    
    async def discover_year(self, tier: int, year: int):
        """Discover all teams for a year."""
        # ... existing discovery logic ...
        
        # NEW: Process retry queue at end
        await self._process_retry_queue()
```

**Step 3: Verify**

```bash
pytest backend/tests/scraper/test_phase1.py::test_retry_* -v
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(scraper): add retry queue for failed LLM extractions

- Add _retry_queue list to DiscoveryService
- Queue teams when LLM extraction fails
- Implement _process_retry_queue() method
- Retry queued items at end of year processing
- Add delay between retries to avoid rate limits
- Tests for queue addition and processing"
```

---

## SLICE 6.2: Multi-Tier Resilience Strategy

### Context

Implement the full multi-tier resilience strategy: Gemini → Deepseek → exponential backoff → queue → fallback.

### Background

Currently we have basic try/catch. We need to leverage the dual-LLM architecture (Gemini + Deepseek) and add exponential backoff retries.

### Task

**Step 1: Write Tests First**

Add to `backend/tests/scraper/test_phase1.py`:

```python
@pytest.mark.asyncio
async def test_resilience_gemini_fallback_to_deepseek(discovery_service, llm_service):
    """Test falls back to Deepseek when Gemini fails."""
    # Mock Gemini to fail, Deepseek to succeed
    llm_service.call_gemini.side_effect = Exception("Gemini down")
    llm_service.call_deepseek.return_value = SponsorExtractionResult(...)
    
    sponsors, confidence = await discovery_service._extract_sponsors(...)
    
    # Verify Deepseek was used
    assert llm_service.call_deepseek.called

@pytest.mark.asyncio
async def test_resilience_exponential_backoff(discovery_service, llm_service, mocker):
    """Test exponential backoff on transient failures."""
    # Mock to fail twice, succeed third time
    llm_service.call.side_effect = [
        Exception("Transient error"),
        Exception("Transient error"),
        SponsorExtractionResult(...)
    ]
    
    # Mock sleep to avoid actual delays in tests
    mock_sleep = mocker.patch('asyncio.sleep')
    
    sponsors, confidence = await discovery_service._extract_with_resilience(...)
    
    # Verify retries happened
    assert llm_service.call.call_count == 3
    
    # Verify exponential backoff (1s, 2s, 4s)
    assert mock_sleep.call_count >= 2
```

**Step 2: Implement Resilience Method**

Add to `backend/app/scraper/orchestration/phase1.py`:

```python
import asyncio

class DiscoveryService:
    async def _extract_with_resilience(
        self,
        team_name: str,
        country_code: Optional[str],
        season_year: int,
        partial_matches: List[str]
    ) -> Tuple[List[SponsorInfo], float]:
        """
        Extract sponsors with full multi-tier resilience.
        Tier 1: Gemini → Tier 2: Deepseek → Tier 3: Exponential backoff
        """
        # This method is already built into LLMService with Gemini → Deepseek fallback
        # We just need to add exponential backoff retries
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                llm_result = await self._llm_prompts.extract_sponsors_from_name(
                    team_name=team_name,
                    season_year=season_year,
                    country_code=country_code,
                    partial_matches=partial_matches
                )
                
                logger.info(
                    f"LLM extraction successful for '{team_name}' "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                return llm_result.sponsors, llm_result.confidence
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"LLM extraction failed for '{team_name}' "
                        f"(attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # All retries exhausted
                    logger.error(
                        f"LLM extraction failed for '{team_name}' after {max_retries} attempts: {e}"
                    )
                    raise
    
    async def _extract_sponsors(
        self,
        team_name: str,
        country_code: Optional[str],
        season_year: int
    ) -> Tuple[List[SponsorInfo], float]:
        """Extract sponsors with multi-tier caching and resilience."""
        # ... existing cache/brand matching logic ...
        
        # Level 3: Call LLM with full resilience
        try:
            return await self._extract_with_resilience(
                team_name=team_name,
                country_code=country_code,
                season_year=season_year,
                partial_matches=match_result.known_brands
            )
        except Exception as e:
            # Final fallback after all resilience measures
            logger.exception(f"All extraction attempts failed for '{team_name}': {e}")
            
            # Add to retry queue
            self._retry_queue.append((team_name, {...}))
            
            # Fallback
            from app.scraper.utils.sponsor_extractor import extract_title_sponsors
            simple_sponsors = extract_title_sponsors(team_name)
            return [SponsorInfo(brand_name=s) for s in simple_sponsors], 0.2
```

**Step 3: Verify**

```bash
pytest backend/tests/scraper/test_phase1.py::test_resilience_* -v
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(scraper): implement multi-tier resilience strategy

- Add _extract_with_resilience() method
- Exponential backoff retries (1s, 2s, 4s)
- Leverage LLMService Gemini → Deepseek fallback
- Queue failed extractions after all retries exhausted
- Lower confidence on final fallback
- Comprehensive resilience tests"
```

---

## SLICE 7.1: End-to-End Integration Tests

### Context

Create comprehensive end-to-end tests that verify the entire sponsor extraction flow from scraping to database storage.

### Background

We've tested individual components. Now we need integration tests that verify the complete pipeline works together.

### Task

**Step 1: Create Integration Tests**

Create `backend/tests/integration/test_sponsor_extraction_e2e.py`:

```python
import pytest
from app.scraper.orchestration.phase1 import DiscoveryService
from app.scraper.orchestration.phase2 import TeamAssemblyService
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from app.models.team import TeamEra
from app.models.sponsor import SponsorBrand, SponsorMaster
from sqlalchemy import select

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_sponsor_extraction_pipeline(
    db_session,
    llm_service,
    real_html_fixture
):
    """Test complete flow: scrape → extract → assemble → verify DB."""
    # Setup: Initialize services
    scraper = CyclingFlashScraper()
    discovery = DiscoveryService(
        scraper=scraper,
        session=db_session,
        llm_prompts=ScraperPrompts(llm=llm_service),
        ...
    )
    assembly = TeamAssemblyService(session=db_session, ...)
    
    # Phase 1: Scrape and extract
    team_data = scraper.parse_team_detail(real_html_fixture, season_year=2024)
    sponsors, confidence = await discovery._extract_sponsors(
        team_name=team_data.name,
        country_code=team_data.country_code,
        season_year=2024
    )
    
    # Update team data with extracted sponsors
    team_data = team_data.model_copy(update={"sponsors": sponsors})
    
    # Phase 2: Assemble and store
    team_era = await assembly.assemble_team(team_data)
    await db_session.commit()
    
    # Verify: Check database state
    stmt = select(TeamEra).where(TeamEra.registered_name == team_data.name)
    result = await db_session.execute(stmt)
    stored_era = result.scalar_one()
    
    assert stored_era is not None
    assert len(stored_era.sponsor_links) > 0
    
    # Verify sponsors were created
    for link in stored_era.sponsor_links:
        assert link.brand is not None
        assert link.brand.brand_name in [s.brand_name for s in sponsors]
        
        # Verify parent companies if provided
        if link.brand.master:
            assert link.brand.master.legal_name is not None

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sponsor_extraction_with_cache_hit(db_session, llm_service):
    """Test extraction uses cached sponsors from previous run."""
    # Setup: Create team with sponsors in DB
    master = SponsorMaster(legal_name="Test Master", ...)
    brand = SponsorBrand(master=master, brand_name="Test Brand", ...)
    team_era = TeamEra(registered_name="Test Brand Team", ...)
    link = TeamSponsorLink(team_era=team_era, brand=brand, ...)
    db_session.add_all([master, brand, team_era, link])
    await db_session.commit()
    
    # Run extraction
    discovery = DiscoveryService(
        session=db_session,
        llm_prompts=ScraperPrompts(llm=llm_service),
        ...
    )
    
    sponsors, confidence = await discovery._extract_sponsors(
        team_name="Test Brand Team",
        country_code="USA",
        season_year=2025
    )
    
    # Verify cache was used
    assert confidence == 1.0
    assert len(sponsors) == 1
    assert sponsors[0].brand_name == "Test Brand"
    assert sponsors[0].parent_company == "Test Master"
    
    # Verify LLM was NOT called (cache hit)
    assert llm_service.call.call_count == 0

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sponsor_extraction_llm_fallback_creates_low_confidence(
    db_session,
    failing_llm_service
):
    """Test fallback to pattern extraction creates low confidence record."""
    discovery = DiscoveryService(
        session=db_session,
        llm_prompts=ScraperPrompts(llm=failing_llm_service),
        ...
    )
    
    sponsors, confidence = await discovery._extract_sponsors(
        team_name="Unknown New Sponsor Team",
        country_code="USA",
        season_year=2024
    )
    
    # Verify fallback was used
    assert sponsors is not None
    assert len(sponsors) > 0
    assert confidence < 0.5  # Low confidence from pattern fallback
```

**Step 2: Verify**

```bash
pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v -m integration
```

**Step 3: Commit**

```bash
git add backend/tests/integration/test_sponsor_extraction_e2e.py
git commit -m "test(scraper): add end-to-end sponsor extraction integration tests

- Test full pipeline: scrape → extract → assemble → DB
- Test cache hit scenario with existing team data
- Test LLM fallback creates low confidence records
- Verify parent company relationships in DB
- Verify sponsor links created correctly"
```

---

## SLICE 7.2: Manual Verification & Documentation

### Context

Create manual verification guide and update documentation with the new sponsor extraction system.

### Background

Final step: document how to test manually, update README, and create a verification checklist.

### Task

**Step 1: Create Manual Verification Guide**

Create `docs/SPONSOR_EXTRACTION_MANUAL_VERIFICATION.md`:

```markdown
# Sponsor Extraction - Manual Verification Guide

## Prerequisites

- Database with test data
- LLM API keys configured (Gemini & Deepseek)
- Scraper CLI working

## Test 1: Single Team Extraction

**Objective**: Verify sponsor extraction for a known team

```bash
python -m app.scraper.cli \
  --phase 1 \
  --tier 1 \
  --start-year 2024 \
  --end-year 2024 \
  --dry-run
```

**Expected Results**:
- Logs show "Calling LLM for..." messages
- Team sponsors extracted with confidence scores
- DB contains TeamEra with SponsorBrand links

**Verification**:
```sql
SELECT 
    te.registered_name,
    sb.brand_name,
    sm.legal_name as parent_company,
    tsl.prominence_percentage
FROM team_eras te
JOIN team_sponsor_links tsl ON te.era_id = tsl.era_id
JOIN sponsor_brands sb ON tsl.brand_id = sb.brand_id
LEFT JOIN sponsor_masters sm ON sb.master_id = sm.master_id
WHERE te.season_year = 2024
ORDER BY te.registered_name, tsl.prominence_percentage DESC;
```

## Test 2: Cache Verification

**Objective**: Verify team name caching works

1. Run scraper for 2024 (first time)
2. Run scraper for 2024 again (should use cache)

**Expected Results**:
- First run: "LLM extraction complete" logs
- Second run: "Team name cache HIT" logs
- No duplicate LLM calls for same team names

## Test 3: Known Test Cases

Verify these specific extractions:

| Team Name | Expected Sponsors | Parent Company | Notes |
|-----------|------------------|----------------|-------|
| "Bahrain Victorious" | ["Bahrain"] | None | "Victorious" is descriptor |
| "Ineos Grenadiers" | ["Ineos Grenadier"] | "INEOS Group" | Multi-word brand |
| "UAE Team Emirates" | ["UAE", "Emirates"] | None | Multiple sponsors |
| "Lotto NL Jumbo" | ["Lotto NL", "Jumbo"] | None | Regional variant |

## Test 4: Fallback Behavior

**Objective**: Verify pattern fallback when LLM fails

1. Temporarily disable LLM API keys
2. Run scraper
3. Verify pattern extraction used with low confidence

**Expected Results**:
- Logs show "No LLM/BrandMatcher available, using pattern fallback"
- Sponsors extracted with confidence < 0.5
- Scraping completes without crashing

## Test 5: Performance

**Objective**: Verify LLM call optimization

Run scraper for multiple years and monitor:
- Number of LLM calls
- Cache hit rate
- Total scraping time

**Expected**:
- ~80% cache hit rate on subsequent runs
- < 1 LLM call per unique team name
```

**Step 2: Update Project Documentation**

Update `backend/app/scraper/README.md`:

```markdown
## Sponsor Extraction

The scraper uses LLM-based intelligent sponsor extraction with:

- **Two-level caching**: Team name cache + brand word matching
- **LLM integration**: Gemini (primary) + Deepseek (fallback)
- **Multi-tier resilience**: Exponential backoff + retry queue
- **Parent company tracking**: Links brands to sponsor masters

### How It Works

1. **Phase 1** (Discovery):
   - Parse team name from HTML
   - Check cache: exact team name match?
   - Check brands: all words known?
   - Call LLM if needed with context
   - Store SponsorInfo with parent companies

2. **Phase 2** (Assembly):
   - Create/update SponsorBrand records
   - Link to SponsorMaster (parent companies)
   - Create TeamSponsorLink with prominence

### Configuration

Set these environment variables:

```bash
GEMINI_API_KEY=your_gemini_key
DEEPSEEK_API_KEY=your_deepseek_key
```

### Testing

Run unit tests:
```bash
pytest backend/tests/scraper/test_brand_matcher.py -v
pytest backend/tests/scraper/test_sponsor_prompts.py -v
```

Run integration tests:
```bash
pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v -m integration
```

See `docs/SPONSOR_EXTRACTION_MANUAL_VERIFICATION.md` for manual testing guide.
```

**Step 3: Create Verification Checklist**

Create `docs/SPONSOR_EXTRACTION_VERIFICATION_CHECKLIST.md`:

```markdown
# Sponsor Extraction - Verification Checklist

✅ = Verified | ⏳ = In Progress | ❌ = Failed

## Unit Tests
- [ ] LLM models validation (1.1)
- [ ] ScrapedTeamData updates (1.2)
- [ ] BrandMatcher team cache (2.1)
- [ ] BrandMatcher word matching (2.2)
- [ ] Sponsor extraction prompt (3.1)
- [ ] DiscoveryService constructor (4.1)
- [ ] Extraction method (4.2)
- [ ] Discovery integration (4.3a, 4.3b)
- [ ] Phase 2 assembly (5.1)
- [ ] Retry queue (6.1)
- [ ] Resilience strategy (6.2)

## Integration Tests
- [ ] End-to-end pipeline
- [ ] Cache hit scenarios
- [ ] LLM fallback behavior

## Manual Verification
- [ ] Single team extraction works
- [ ] Cache verification passes
- [ ] Known test cases accurate
- [ ] Fallback behavior correct
- [ ] Performance acceptable

## Production Readiness
- [ ] LLM API keys configured
- [ ] Database migrations applied
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Error alerting setup
```

**Step 4: Final Verification**

Run all tests:
```bash
# Unit tests
pytest backend/tests/scraper/ -v

# Integration tests
pytest backend/tests/integration/ -v -m integration

# Check test coverage
pytest --cov=app.scraper --cov-report=html
```

**Step 5: Commit**

```bash
git add docs/SPONSOR_EXTRACTION_MANUAL_VERIFICATION.md docs/SPONSOR_EXTRACTION_VERIFICATION_CHECKLIST.md backend/app/scraper/README.md
git commit -m "docs(scraper): add sponsor extraction verification guides

- Create manual verification guide with test cases
- Update scraper README with LLM extraction docs
- Add verification checklist for all slices
- Document known test cases and expected results
- Include configuration and testing instructions"
```

---

## Final Implementation Summary

**All 14 Slices Complete! 🎉**

### Implementation Order
1. ✅ SLICE 1.1: LLM Models
2. ✅ SLICE 1.2: Update ScrapedTeamData
3. ✅ SLICE 2.1: Team Name Cache
4. ✅ SLICE 2.2: Word Matching
5. ✅ SLICE 3.1: LLM Prompt
6. ✅ SLICE 4.1: Constructor Update
7. ✅ SLICE 4.2: Extraction Method
8. ✅ SLICE 4.3a: Integrate Equipment Sponsors
9. ✅ SLICE 4.3b: CLI Integration
10. ✅ SLICE 5.1: Update Phase 2
11. ✅ SLICE 6.1: Retry Queue
12. ✅ SLICE 6.2: Resilience Strategy
13. ✅ SLICE 7.1: Integration Tests
14. ✅ SLICE 7.2: Manual Verification

### Key Features Implemented
- ✅ Two-level caching (team + brand)
- ✅ LLM integration with Gemini + Deepseek
- ✅ Parent company tracking
- ✅ Multi-tier resilience
- ✅ Retry queue for failures
- ✅ Comprehensive testing
- ✅ Documentation & verification

### Next Steps
1. **Execute Slices**: Follow each prompt in order
2. **Test As You Go**: Run tests after each slice
3. **Commit Often**: Atomic commits preserve progress
4. **Monitor LLM Usage**: Track API costs
5. **Iterate On Prompts**: Refine LLM prompts based on results

**Ready for implementation!** 🚀
