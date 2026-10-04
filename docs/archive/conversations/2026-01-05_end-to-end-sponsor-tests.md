---
id: "c1d400c7-31c9-4e85-b18b-e99d2b8ce5b9"
title: "End-to-End Sponsor Tests"
date: "2026-01-05T17:29:43.855260600Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

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


*User accepted the command `dir backend\app\scraper\orchestration backend\app\scraper\sources backend\tests\integration`*

*Viewed [phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py) *

*Grep searched codebase*

*Searched filesystem*

*Grep searched codebase*

*Viewed [test_cyclingflash.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_cyclingflash.py) *

*Viewed [conftest.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/conftest.py) *

*Viewed [team_detail_2024.html](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/fixtures/cyclingflash/team_detail_2024.html) *

*Viewed [phase2.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase2.py) *

*Viewed [cyclingflash.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/sources/cyclingflash.py) *

*Edited relevant file*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v`*

*Checked command status*

*Viewed [models.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py) *

*Edited relevant file*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v`*

*Checked command status*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py --collect-only -p no:warnings`*

*Viewed [brand_matcher.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services/brand_matcher.py) *

*Checked command status*

*Edited relevant file*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v`*

*Checked command status*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py::test_full_sponsor_extraction_pipeline -vv`*

*Checked command status*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py::test_full_sponsor_extraction_pipeline --tb=long`*

*Checked command status*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py::test_full_sponsor_extraction_pipeline --tb=long > test_output.txt 2>&1`*

*Checked command status*

*User accepted the command `type test_output.txt`*

*Viewed [prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py) *

*Edited relevant file*

*Viewed [test_sponsor_extraction_e2e.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/integration/test_sponsor_extraction_e2e.py) *

*Edited relevant file*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v`*

*Checked command status*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py::test_full_sponsor_extraction_pipeline --tb=short`*

*Checked command status*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py::test_full_sponsor_extraction_pipeline --tb=short > error.txt 2>&1`*

*User accepted the command `type error.txt`*

*Edited relevant file*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v`*

*Checked command status*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py::test_sponsor_extraction_with_cache_hit --tb=short`*

*Checked command status*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py::test_sponsor_extraction_with_cache_hit --tb=short > cache_error.txt 2>&1`*

*User accepted the command `type cache_error.txt`*

*Checked command status*

*Checked command status*

*User accepted the command `type cache_error.txt`*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v`*

*Checked command status*

*User accepted the command `del test_output.txt error.txt cache_error.txt`*

*User accepted the command `git add backend/tests/integration/test_sponsor_extraction_e2e.py`*

*User accepted the command `git commit -m "test(scraper): add end-to-end sponsor extraction integration tests

- Test full pipeline: scrape → extract → assemble → DB
- Test cache hit scenario with existing team data
- Test LLM fallback creates low confidence records
- Verify parent company relationships in DB
- Verify sponsor links created correctly"`*

*User accepted the command `del test_output.txt
del error.txt
del cache_error.txt`*