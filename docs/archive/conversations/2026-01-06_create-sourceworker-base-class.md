---
id: "dd764361-b257-4459-a09d-6811e109ffbd"
title: "Create SourceWorker Base Class"
date: "2026-01-06T14:30:57.152920400Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

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


*Listed directory [chainlines](file:///c:/Users/fjung/Documents/DEV/chainlines) *

*Edited relevant file*

*Viewed [GEMINI.md](file:///c:/Users/fjung/Documents/DEV/chainlines/GEMINI.md) *

*Viewed [model.md](file:///c:/Users/fjung/Documents/DEV/chainlines/model.md) *

*Viewed [MULTI_SOURCE_SCRAPER_SPECIFICATION.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md) *

*Viewed [MULTI_SOURCE_SCRAPER_BLUEPRINT.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/MULTI_SOURCE_SCRAPER_BLUEPRINT.md) *

*Viewed [scraper.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/scraper.py) *

*Listed directory [orchestration](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration) *

*Edited relevant file*

### User Input

go

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_workers.py -v`*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_workers.py -v`*

*Edited relevant file*

*User accepted the command `git add -A && git commit -m "feat(scraper): add SourceWorker abstract base class and SourceData model"`*

*User accepted the command `git add -A; git commit -m "feat(scraper): add SourceWorker abstract base class and SourceData model"`*

*User accepted the command `git show --stat --name-only HEAD`*

*Edited relevant file*

*Edited relevant file*

---

## Session Artifacts & Documentation

### Artifact: `task.md`

# Task: Implement SourceWorker Base Class

- [x] Load context and plan
- [x] Create tests for `SourceWorker`
- [x] Implement `SourceData` and `SourceWorker` in `workers.py`
- [x] Verify tests pass
- [x] Commit changes

### Artifact: `walkthrough.md`

# Walkthrough - SourceWorker Base Class Implementation

I have implemented the abstract base class `SourceWorker` and the `SourceData` Pydantic model. These provide a standardized interface for all secondary source workers (e.g., Wikipedia, CyclingRanking, Memoire) in the Multi-Source Scraper pipeline.

## Changes Made

### Scraper Orchestration
- Created [workers.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/workers.py) containing:
    - `SourceData`: A model for structured data output including `source`, `raw_content`, `founded_year`, `dissolved_year`, `history_text`, and `extra` (dict).
    - `SourceWorker`: An Abstract Base Class (ABC) requiring subclasses to implement a `source_name` property and an asynchronous `fetch(url)` method.

### Tests
- Created [test_workers.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_workers.py) to verify:
    - `SourceData` validation works as expected.
    - `SourceWorker` cannot be instantiated directly due to its abstract nature.

## Verification Results

### Automated Tests
Run `pytest` to verify the implementation:
```bash
pytest backend/tests/scraper/test_workers.py -v
```

**Results:**
```text
backend/tests/scraper/test_workers.py::test_source_data_model_validates PASSED
backend/tests/scraper/test_workers.py::test_source_worker_is_abstract PASSED
```

## Git Commit
Changes committed in `5b7c2e2`:
- `feat(scraper): add SourceWorker abstract base class and SourceData model`

### Artifact: `implementation_plan.md`

# Implement SourceWorker Base Class

This plan outlines the creation of the abstract base class `SourceWorker` and the `SourceData` Pydantic model. These will serve as the foundation for secondary source workers (Wikipedia, CyclingRanking, Memoire) in the Multi-Source Scraper.

## Proposed Changes

### [Scraper Orchestration]

#### [NEW] [workers.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/workers.py)
- Define `SourceData` Pydantic model for standardized source output.
- Define `SourceWorker` abstract base class with:
    - `source_name` abstract property.
    - `fetch(url: str)` abstract async method.

### [Tests]

#### [NEW] [test_workers.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_workers.py)
- Test `SourceData` model validation.
- Test that `SourceWorker` cannot be instantiated directly (abstract check).

## Verification Plan

### Automated Tests
Run the newly created tests to verify the base class and model:
```bash
pytest backend/tests/scraper/test_workers.py -v
```