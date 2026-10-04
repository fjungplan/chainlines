---
id: "95b31e5e-6f75-4ff4-b0ab-06e7f51356dc"
title: "Implementing Phase 3 Lineage Connection"
date: "2026-01-04T17:29:04.134657100Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

# SLICE 10: Phase 3 Orchestration - Lineage Connection

## Context
Phase 3 detects orphan nodes and connects them via LineageEvents.

**Dependencies:** SLICES 8 and 9 must be complete.

## Prompt

You are implementing SLICE 10 of the Smart Scraper project. Follow TDD strictly.

### TASK 10.1: Orphan Detector (Test: Finds Gaps)

**Test First:**
Create `backend/tests/scraper/test_phase3.py`:
```python
"""Test Phase 3 Lineage Connection orchestration."""
import pytest
from datetime import date

def test_orphan_detector_finds_gaps():
    """OrphanDetector should find teams with year gaps."""
    from app.scraper.orchestration.phase3 import OrphanDetector
    
    teams = [
        {"node_id": "a", "name": "Team A", "end_year": 2022},
        {"node_id": "b", "name": "Team B", "start_year": 2023},
        {"node_id": "c", "name": "Team C", "end_year": 2020},
    ]
    
    detector = OrphanDetector()
    candidates = detector.find_candidates(teams)
    
    # Should match Team A (ended 2022) with Team B (started 2023)
    assert len(candidates) >= 1
    assert any(c["predecessor"]["name"] == "Team A" for c in candidates)

def test_orphan_detector_ignores_large_gaps():
    """OrphanDetector should ignore gaps > 2 years."""
    from app.scraper.orchestration.phase3 import OrphanDetector
    
    teams = [
        {"node_id": "a", "name": "Team A", "end_year": 2018},
        {"node_id": "b", "name": "Team B", "start_year": 2023},
    ]
    
    detector = OrphanDetector(max_gap_years=2)
    candidates = detector.find_candidates(teams)
    
    assert len(candidates) == 0
```

**Implementation:**
Create `backend/app/scraper/orchestration/phase3.py`:
```python
"""Phase 3: Lineage Connection."""
from typing import List, Dict, Any

class OrphanDetector:
    """Detects orphan nodes that may need lineage connections."""
    
    def __init__(self, max_gap_years: int = 2):
        self._max_gap = max_gap_years
    
    def find_candidates(
        self,
        teams: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find teams that ended near when another started."""
        candidates = []
        
        ended_teams = [t for t in teams if "end_year" in t]
        started_teams = [t for t in teams if "start_year" in t]
        
        for ended in ended_teams:
            for started in started_teams:
                gap = started["start_year"] - ended["end_year"]
                if 0 < gap <= self._max_gap:
                    candidates.append({
                        "predecessor": ended,
                        "successor": started,
                        "gap_years": gap
                    })
        
        return candidates
```

**Verify:** Run `pytest backend/tests/scraper/test_phase3.py -v`

---

### TASK 10.2: Lineage Connection Service

**Test First:**
Add to `backend/tests/scraper/test_phase3.py`:
```python
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

@pytest.mark.asyncio
async def test_lineage_service_creates_event():
    """LineageConnectionService should create lineage events."""
    from app.scraper.orchestration.phase3 import LineageConnectionService
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    mock_prompts = AsyncMock()
    mock_prompts.decide_lineage = AsyncMock(
        return_value=LineageDecision(
            event_type=LineageEventType.LEGAL_TRANSFER,
            confidence=0.95,
            reasoning="Same team",
            predecessor_ids=[uuid4()],
            successor_ids=[uuid4()]
        )
    )
    
    mock_audit = AsyncMock()
    mock_session = AsyncMock()
    
    service = LineageConnectionService(
        prompts=mock_prompts,
        audit_service=mock_audit,
        session=mock_session,
        system_user_id=uuid4()
    )
    
    await service.connect(
        predecessor_info="Team A 2022",
        successor_info="Team B 2023"
    )
    
    mock_prompts.decide_lineage.assert_called_once()
```

**Implementation:**
Add to `backend/app/scraper/orchestration/phase3.py`:
```python
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.llm.prompts import ScraperPrompts
from app.services.audit_log_service import AuditLogService
from app.models.enums import EditAction, EditStatus

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.90

class LineageConnectionService:
    """Orchestrates Phase 3: Creating lineage connections."""
    
    def __init__(
        self,
        prompts: ScraperPrompts,
        audit_service: AuditLogService,
        session: AsyncSession,
        system_user_id: UUID
    ):
        self._prompts = prompts
        self._audit = audit_service
        self._session = session
        self._user_id = system_user_id
    
    async def connect(
        self,
        predecessor_info: str,
        successor_info: str
    ) -> None:
        """Analyze and create lineage connection."""
        decision = await self._prompts.decide_lineage(
            predecessor_info=predecessor_info,
            successor_info=successor_info
        )
        
        status = (
            EditStatus.APPROVED if decision.confidence >= CONFIDENCE_THRESHOLD
            else EditStatus.PENDING
        )
        
        await self._audit.create_edit(
            session=self._session,
            user_id=self._user_id,
            entity_type="LineageEvent",
            entity_id=None,
            action=EditAction.CREATE,
            old_data=None,
            new_data={
                "event_type": decision.event_type.value,
                "predecessor_ids": [str(id) for id in decision.predecessor_ids],
                "successor_ids": [str(id) for id in decision.successor_ids],
                "reasoning": decision.reasoning
            },
            status=status
        )
        
        logger.info(f"Created lineage {decision.event_type.value} ({status.value})")
```

**Verify:** Run `pytest backend/tests/scraper/test_phase3.py -v`

---

### WIRING: Export Phase 3 components

Update `backend/app/scraper/orchestration/__init__.py`:
```python
from app.scraper.orchestration.phase3 import (
    OrphanDetector, LineageConnectionService
)
# ... existing exports ...
```

---

## Finalize Slice 10

**Step 1: Update Task Checklist**

Edit `docs/SMART_SCRAPER_TASKS.md` and mark the following as complete:
```markdown
- [x] 10.1 Implement orphan node detector
- [x] 10.2 Implement lineage decision pipeline
- [x] 10.3 Integrate with AuditLogService for LineageEvent
- [x] 10.4 Wire Phase 3 into `SmartScraperService`
- [x] **SLICE 10 COMMITTED**
```

**Step 2: Commit (execute now)**
```bash
git add -A && git commit -m "feat(scraper): add Phase 3 lineage connection orchestration

- Add OrphanDetector to find candidate connections
- Add LineageConnectionService with LLM integration
- Create LineageEvents via AuditLogService"
```

---

*Edited relevant file*

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

*Edited relevant file*

### User Input

just to be sure: a team _can_ simply fold and cease to exist without having any kind of successor! Is this guaranteed? We should't force the scraper system, and especially the LLM, to search for a connection that just isn't there... LLMs will most likely just hallucinate stuff if we ask them to find a connection that isn't there and they don't know that they can jsut tell us that there simply isn't any. While checking please also double-check everything that's already been implemented so far on this branch (slices 1-9) and what's yet to be implemented in the current and future prompts (also review adn update other smart-scraper documentation files and the prompt plan!)

*Listed directory [scraper](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper) *

*Viewed [enums.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/enums.py) *

*Viewed [SMART_SCRAPER_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_PROMPTS.md) *

*Edited relevant file*

*Viewed content chunk*

*Viewed [SMART_SCRAPER_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_PROMPTS.md) *

*Viewed [SMART_SCRAPER_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_PROMPTS.md) *

*Edited relevant file*

*Edited relevant file*

*Viewed [prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py) *

*Viewed [lineage.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/lineage.py) *

*Edited relevant file*

*Edited relevant file*

### User Input

GO!

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_phase3.py -v`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_phase3.py -v`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*Viewed [__init__.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/__init__.py) *

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_phase3.py -v`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `git add -A && git commit -m "feat(scraper): add Phase 3 lineage connection orchestration

- Add OrphanDetector to find candidate connections
- Add LineageConnectionService with LLM integration (supports NO_CONNECTION)
- Create LineageEvents via AuditLogService"`*

### User Input

looking at the marked text, isn't it weird and unnecessary to add a NO_CONNECTION to the LineageEventType class? wouldn't we simply _not_ create a lineage event in this case, and not an event of type NO_CONNECTION? Or is this for an intermediate/hidden step in the backend process I don't understand?

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_phase3.py -v`*

*Checked command status*

*User accepted the command `git add -A; git commit -m "feat(scraper): add Phase 3 lineage connection orchestration" -m "- Add OrphanDetector to find candidate connections" -m "- Add LineageConnectionService with LLM integration (supports NO_CONNECTION via null)" -m "- Create LineageEvents via AuditLogService"`*

---

## Session Artifacts & Documentation

### Artifact: `task.md`

# Task: Implement Slice 10 - Phase 3 Orchestration

- [x] Check `docs/SMART_SCRAPER_TASKS.md` <!-- id: 0 -->
- [x] **Task 10.1: Orphan Detector** <!-- id: 1 -->
    - [x] Create tests in `backend/tests/scraper/test_phase3.py` <!-- id: 2 -->
    - [x] Implement `OrphanDetector` in `backend/app/scraper/orchestration/phase3.py` <!-- id: 3 -->
    - [x] Verify tests pass <!-- id: 4 -->
- [x] **Task 10.2: Lineage Connection Service** <!-- id: 5 -->
    - [x] Add tests to `backend/tests/scraper/test_phase3.py` <!-- id: 6 -->
    - [x] Implement `LineageConnectionService` in `backend/app/scraper/orchestration/phase3.py` <!-- id: 7 -->
    - [x] Verify tests pass <!-- id: 8 -->
- [x] **Wiring** <!-- id: 9 -->
    - [x] Export components in `backend/app/scraper/orchestration/__init__.py` <!-- id: 10 -->
- [/] **Finalize** <!-- id: 11 -->
    - [ ] Update `docs/SMART_SCRAPER_TASKS.md` <!-- id: 12 -->
    - [ ] Commit changes <!-- id: 13 -->

### Artifact: `implementation_plan.md`

# Implementation Plan - Slice 10: Phase 3 Orchestration

## Goal
Implement Phase 3 of the Smart Scraper orchestration, which focuses on detecting orphan nodes (teams with no successor) and connecting them via LineageEvents. This involves an `OrphanDetector` to find potential gaps and a `LineageConnectionService` to use LLM decision-making to approve or reject connections.

## Proposed Changes

### Backend

#### [NEW] [test_phase3.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase3.py)
- Create strict TDD tests for:
    - `OrphanDetector` (gaps <= 2 years)
    - `LineageConnectionService` (LLM integration and Audit Log creation)

#### [MODIFY] [prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py)
- Update `DECIDE_LINEAGE_PROMPT` to include `NO_CONNECTION` option.

#### [NEW] [phase3.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase3.py)
- Implement `OrphanDetector` class:
    - Logic to find predecessor/successor candidates based on year gaps.
- Implement `LineageConnectionService` class:
    - `connect(predecessor_info, successor_info)` method.
    - Integration with `ScraperPrompts` (LLM) for decision making.
    - Integration with `AuditLogService` to create `LineageEvent` entries (Approved or Pending based on confidence).

#### [MODIFY] [__init__.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/__init__.py)
- Export `OrphanDetector` and `LineageConnectionService` to make them available to the rest of the application.

## Verification Plan

### Automated Tests
Run the newly created tests to verify the logic:
```bash
pytest backend/tests/scraper/test_phase3.py -v
```
- Verify `OrphanDetector` correctly identifies candidates and ignores large gaps.
- Verify `LineageConnectionService` correctly calls the LLM and creates Audit Log entries.
- Verify `LineageConnectionService` handles `NO_CONNECTION` (does not create a connection).