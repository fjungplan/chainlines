---
id: "8261b120-bc25-4bc6-b7b4-a433b4530fd9"
title: "Implement Team Name Cache"
date: "2026-01-05T14:46:19.540606Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

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


*Listed directory [models](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models) *

*Listed directory [scraper](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper) *

*Listed directory [services](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services) *

*Viewed [team.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/team.py) *

*Viewed [sponsor.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/sponsor.py) *

*Viewed [models.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py) *

*Viewed [conftest.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/conftest.py) *

*Edited relevant file*

*Edited relevant file*

### User Input

go

*Edited relevant file*

*Edited relevant file*

*User accepted the command `mkdir -p backend/app/scraper/services`*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_brand_matcher.py::test_team_name_cache_* -v`*

*User accepted the command `pytest backend/tests/scraper/test_brand_matcher.py -v`*

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

*Viewed [PROGRESSIVE_SPONSOR_EXTRACTION.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/PROGRESSIVE_SPONSOR_EXTRACTION.md) *

*Viewed [PROGRESSIVE_SPONSOR_EXTRACTION_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/PROGRESSIVE_SPONSOR_EXTRACTION_PROMPTS.md) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `git add backend/app/scraper/services/brand_matcher.py backend/app/scraper/services/__init__.py backend/tests/scraper/test_brand_matcher.py
git commit -m "feat(scraper): add BrandMatcher team name caching

- Implement check_team_name() with two-level cache
- In-memory cache for session-level performance
- DB lookup via TeamEra.registered_name for persistence
- Load existing sponsors from TeamSponsorLink
- Comprehensive tests for cache hit/miss scenarios"`*

---

## Session Artifacts & Documentation

### Artifact: `task.md`

# Task: SLICE 2.1: Team Name Cache (DB Lookup)

- [x] Create Implementation Plan [x]
- [x] Write Tests First `backend/tests/scraper/test_brand_matcher.py` [x]
    - [x] `test_team_name_cache_hit` [x]
    - [x] `test_team_name_cache_miss` [x]
    - [x] `test_team_name_cache_in_memory` [x]
- [x] Implement Service `backend/app/scraper/services/brand_matcher.py` [x]
- [x] Wire Integration `backend/app/scraper/services/__init__.py` [x]
- [x] Verify with Pytest [x]
- [ ] Update `docs/SMART_SCRAPER_TASKS.md` [ ]
- [x] Commit Changes [x]

### Artifact: `walkthrough.md`

# Walkthrough - SLICE 2.1: Team Name Cache (DB Lookup)

I have implemented the first level of caching for sponsor extraction: checking if we've seen an exact team name before by querying the `TeamEra` table.

## Changes Made

### Scraper Services

#### [NEW] [brand_matcher.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services/brand_matcher.py)
Implemented `BrandMatcherService` with a two-level cache:
1.  **In-memory cache**: A dictionary to store results within the same session.
2.  **Database cache**: Queries `TeamEra.registered_name` to find existing records and reuse their linked sponsors.

#### [NEW] [__init__.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services/__init__.py)
Exported `BrandMatcherService`.

### Tests

#### [NEW] [test_brand_matcher.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_brand_matcher.py)
Created unit tests covering:
-   **Cache HIT (DB)**: Successfully loads sponsors from existing `TeamEra` and `TeamSponsorLink` records.
-   **Cache MISS**: Returns `None` when a team name is unknown.
-   **In-Memory Cache**: Verifies that subsequent calls for the same team name hit the in-memory cache and return the same object.

## Verification Results

### Automated Tests
Ran `pytest backend/tests/scraper/test_brand_matcher.py -v`:
```text
backend\tests\scraper\test_brand_matcher.py::test_team_name_cache_hit PASSED [ 33%]
backend\tests\scraper\test_brand_matcher.py::test_team_name_cache_miss PASSED [ 66%]
backend\tests\scraper\test_brand_matcher.py::test_team_name_cache_in_memory PASSED [100%]
```

## Next Steps

1.  **SLICE 2.2**: Implement word-level brand matching to skip LLM calls when all words in a team name are known brands.

### Artifact: `implementation_plan.md`

# Implementation Plan - SLICE 2.1: Team Name Cache (DB Lookup)

Implement the first level of caching: checking if we've seen this exact team name before by querying the `TeamEra` table.

## Proposed Changes

### Scraper Services

#### [NEW] [brand_matcher.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services/brand_matcher.py)
- Implement `BrandMatcherService` with `check_team_name` method.
- Use a two-level cache:
    1. In-memory `dict` for session-level caching.
    2. DB lookup via `TeamEra.registered_name` for persistence across sessions.
- Load existing sponsors from `TeamSponsorLink` and return as `List[SponsorInfo]`.

#### [MODIFY] [__init__.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services/__init__.py)
- Export `BrandMatcherService` for use in other components.

### Tests

#### [NEW] [test_brand_matcher.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_brand_matcher.py)
- Test suite for `BrandMatcherService`.
- Scenario: Cache HIT (DB) - ensure sponsors are correctly loaded.
- Scenario: Cache MISS - ensure `None` is returned for unknown teams.
- Scenario: Cache HIT (In-Memory) - ensure subsequent calls return from memory without hitting the DB.

## Verification Plan

### Automated Tests
- Run specific tests:
  ```bash
  pytest backend/tests/scraper/test_brand_matcher.py::test_team_name_cache_* -v
  ```

### Manual Verification
- None required for this slice beyond automated tests.