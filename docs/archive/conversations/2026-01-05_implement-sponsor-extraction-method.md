---
id: "b546e3fa-0f70-467d-8128-c5c7a2fda1fb"
title: "Implement Sponsor Extraction Method"
date: "2026-01-05T15:17:40.305188500Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

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


*Viewed [test_phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py) *

*Viewed [phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py) *

*Viewed [models.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_phase1.py -k "extract_sponsors" -v`*

*Searched filesystem*

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

*Viewed [PROGRESSIVE_SPONSOR_EXTRACTION_BLUEPRINT.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/PROGRESSIVE_SPONSOR_EXTRACTION_BLUEPRINT.md) *

*User accepted the command `git add -A`*

*User accepted the command `git commit -m "feat(scraper): implement two-level sponsor extraction method

- Add _extract_sponsors() with team cache and brand matching
- Level 1: TeamEra cache (exact team name match)
- Level 2: Brand coverage check (all words known)
- Level 3: LLM extraction for unknown words
- Fallback: Pattern extraction if LLM unavailable/fails
- Comprehensive tests for all extraction paths"`*