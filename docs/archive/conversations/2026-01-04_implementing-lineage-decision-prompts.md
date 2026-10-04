---
id: "fbd9b965-0616-4b0c-bb72-0d95e87aa050"
title: "Implementing Lineage Decision Prompts"
date: "2026-01-04T17:13:02.392700Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

# SLICE 9: LLM Prompts - Lineage Decision

## Context
We need the LLM to determine lineage relationships between teams (transfers, merges, splits, spiritual succession).

**Dependencies:** SLICE 2 must be complete.

## Prompt

You are implementing SLICE 9 of the Smart Scraper project. Follow TDD strictly.

### TASK 9.1: LineageDecision Model (Test: All Event Types)

**Test First:**
Create `backend/tests/scraper/test_lineage_prompt.py`:
```python
"""Test Lineage Decision LLM prompts."""
import pytest
from uuid import uuid4

def test_lineage_decision_validates():
    """LineageDecision should validate correctly."""
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    decision = LineageDecision(
        event_type=LineageEventType.LEGAL_TRANSFER,
        confidence=0.95,
        reasoning="Same UCI code, continuous license",
        predecessor_ids=[uuid4()],
        successor_ids=[uuid4()]
    )
    
    assert decision.event_type == LineageEventType.LEGAL_TRANSFER
    assert decision.confidence >= 0.9

def test_lineage_decision_merge_has_multiple_predecessors():
    """MERGE should allow multiple predecessors."""
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    decision = LineageDecision(
        event_type=LineageEventType.MERGE,
        confidence=0.85,
        reasoning="Two teams combined",
        predecessor_ids=[uuid4(), uuid4()],
        successor_ids=[uuid4()]
    )
    
    assert len(decision.predecessor_ids) == 2
    assert len(decision.successor_ids) == 1

def test_lineage_decision_split_has_multiple_successors():
    """SPLIT should allow multiple successors."""
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    decision = LineageDecision(
        event_type=LineageEventType.SPLIT,
        confidence=0.80,
        reasoning="Team dissolved into two",
        predecessor_ids=[uuid4()],
        successor_ids=[uuid4(), uuid4()]
    )
    
    assert len(decision.predecessor_ids) == 1
    assert len(decision.successor_ids) == 2
```

**Implementation:**
Create `backend/app/scraper/llm/lineage.py`:
```python
"""Lineage decision models and prompts."""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.models.enums import LineageEventType

class LineageDecision(BaseModel):
    """LLM decision about team lineage."""
    event_type: LineageEventType
    confidence: float
    reasoning: str
    predecessor_ids: List[UUID]
    successor_ids: List[UUID]
    notes: Optional[str] = None
```

**Verify:** Run `pytest backend/tests/scraper/test_lineage_prompt.py -v`

---

### TASK 9.2: Lineage Decision Prompt

**Test First:**
Add to `backend/tests/scraper/test_lineage_prompt.py`:
```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_decide_lineage_prompt():
    """ScraperPrompts.decide_lineage should return decision."""
    from app.scraper.llm.prompts import ScraperPrompts
    from app.scraper.llm.lineage import LineageDecision
    from app.models.enums import LineageEventType
    
    mock_service = AsyncMock()
    mock_service.generate_structured = AsyncMock(
        return_value=LineageDecision(
            event_type=LineageEventType.LEGAL_TRANSFER,
            confidence=0.92,
            reasoning="Continuation of same team",
            predecessor_ids=[uuid4()],
            successor_ids=[uuid4()]
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_service)
    
    result = await prompts.decide_lineage(
        predecessor_info="Team A ended 2023, UCI code TJV",
        successor_info="Team B started 2024, UCI code TJV"
    )
    
    assert result.event_type == LineageEventType.LEGAL_TRANSFER
    mock_service.generate_structured.assert_called_once()
```

**Implementation:**
Add to `backend/app/scraper/llm/prompts.py`:
```python
from app.scraper.llm.lineage import LineageDecision

DECIDE_LINEAGE_PROMPT = """
Analyze the relationship between these two cycling teams and determine the lineage type.

PREDECESSOR TEAM (ended):
{predecessor_info}

SUCCESSOR TEAM (started):
{successor_info}

Determine the relationship type:
- LEGAL_TRANSFER: Same legal entity, continuous UCI license
- SPIRITUAL_SUCCESSION: No legal link, but cultural/personnel continuity
- MERGE: Multiple predecessors combined into one successor
- SPLIT: One predecessor split into multiple successors

Consider:
- UCI codes (same = likely legal transfer)
- Staff continuity (>50% = strong connection)
- Sponsor continuity
- Time gap (>2 years = weaker connection)

Return your decision with confidence score (0.0 to 1.0).
"""

# Add to ScraperPrompts class:
async def decide_lineage(
    self,
    predecessor_info: str,
    successor_info: str
) -> LineageDecision:
    """Decide lineage relationship between teams."""
    prompt = DECIDE_LINEAGE_PROMPT.format(
        predecessor_info=predecessor_info,
        successor_info=successor_info
    )
    
    return await self._llm.generate_structured(
        prompt=prompt,
        response_model=LineageDecision
    )
```

**Verify:** Run `pytest backend/tests/scraper/test_lineage_prompt.py -v`

---

### WIRING: Export lineage components

Update `backend/app/scraper/llm/__init__.py`:
```python
from app.scraper.llm.lineage import LineageDecision
# ... existing exports ...

__all__ = [
    "BaseLLMClient", "GeminiClient", "DeepseekClient", 
    "LLMService", "ScraperPrompts", "LineageDecision"
]
```

---

## Finalize Slice 9

**Step 1: Update Task Checklist**

Edit `docs/SMART_SCRAPER_TASKS.md` and mark the following as complete:
```markdown
- [x] 9.1 Define `LineageDecision` Pydantic model
- [x] 9.2 Write `decide_lineage` prompt
- [x] 9.3 Test all event types
- [x] 9.4 Test confidence scoring
- [x] **SLICE 9 COMMITTED**
```

**Step 2: Commit (execute now)**
```bash
git add -A && git commit -m "feat(scraper): add lineage decision LLM prompt

- Add LineageDecision Pydantic model
- Add decide_lineage prompt for all event types
- Support LEGAL_TRANSFER, MERGE, SPLIT, SPIRITUAL_SUCCESSION"
```

---

*Viewed [prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py) *

*Viewed [enums.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/enums.py) *

*Viewed [__init__.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/__init__.py) *

### Planner Response

Good, I have the context I need. The [LineageEventType](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/enums.py:19:0-24:19) enum already exists in [enums.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/enums.py:0:0-0:0). Now let me create the test file and implementation following TDD.

*Edited relevant file*

*Edited relevant file*

### Planner Response

Now let me add the [decide_lineage](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_lineage_prompt.py:57:0-83:57) method to the [ScraperPrompts](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:27:0-60:9) class and run the tests:

*Edited relevant file*

*Edited relevant file*

### Planner Response

Now let me update the exports and run the tests:

*Edited relevant file*

*User accepted the command `cd backend && python -m pytest tests/scraper/test_lineage_prompt.py -v`*

### Planner Response

PowerShell requires a different command separator. Let me fix that:

*User accepted the command `python -m pytest tests/scraper/test_lineage_prompt.py -v`*

### Planner Response

All 4 tests passed. Now let me update the task checklist and commit:

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

*Edited relevant file*

*User accepted the command `git add -A; git commit -m "feat(scraper): add lineage decision LLM prompt

- Add LineageDecision Pydantic model
- Add decide_lineage prompt for all event types
- Support LEGAL_TRANSFER, MERGE, SPLIT, SPIRITUAL_SUCCESSION"`*

### Planner Response

SLICE 9 is complete. Let me notify you of the completion:

### User Input

@[backend/app/scraper/llm/prompts.py] about this (and anywhere else we go into lineage events: mergers and splits are ALSO joins into an already existing team or split-offs from a still existing team! Cultural succession can best be found in Wikipedia articles in the "History" section. And there shouldn't be time gaps - lineage events have a single date, so I can't really imagine any time gaps (maybe if a team folded mid-season it only "comes back" as a successor for the start of the following season, but that's about how far I would go...) WHen adjusting, please also check that this is correct in all other files we`re already worked on on this branch (slices 1-8) and if we need to adjust any of the smart-scraper docs regarding the next steps (slices 10-15).

*Grep searched codebase*

*Grep searched codebase*

### Planner Response

The grep didn't find results - possibly due to encoding. Let me search specifically for these terms:

*Grep searched codebase*

*Grep searched codebase*

*Viewed [SMART_SCRAPER_SPECIFICATION.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_SPECIFICATION.md) *

*Viewed [SMART_SCRAPER_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_PROMPTS.md) *

### Planner Response

Let me now view the specific lineage sections in the prompts document and spec to understand what needs to be corrected:

*Viewed [SMART_SCRAPER_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_PROMPTS.md) *

*Viewed [prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py) *

### Planner Response

Now I have a clear picture. Let me update the lineage prompt in [prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:0:0-0:0) with the corrected definitions based on the user's feedback, and also check the specification document for related updates:

*Edited relevant file*

### Planner Response

Now let me update the SMART_SCRAPER_SPECIFICATION.md and SMART_SCRAPER_PROMPTS.md with the corrected lineage definitions, and check for any other files that need updating:

*Edited relevant file*

*Viewed [SMART_SCRAPER_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_PROMPTS.md) *

### Planner Response

I see the lint warnings are pre-existing issues in the docs. Now let me update the SMART_SCRAPER_PROMPTS.md with corrected lineage definitions and check the Phase 3 slice for time gap references that need correction:

*Edited relevant file*

### Planner Response

The lint warnings are all pre-existing issues in the documentation files and are not related to my changes. Now let me verify the tests still pass and then commit:

*User accepted the command `python -m pytest tests/scraper/test_lineage_prompt.py -v`*

### Planner Response

All tests pass. Now let me commit the changes:

*User accepted the command `git add -A; git commit -m "docs(scraper): clarify lineage event definitions

- MERGE includes joins into an already-existing team
- SPLIT includes spin-offs where the original team continues
- SPIRITUAL_SUCCESSION: added Wikipedia 'History' section hint
- Time gaps: lineage events have single dates, gaps should be minimal
- Updated prompts.py, SMART_SCRAPER_SPECIFICATION.md, SMART_SCRAPER_PROMPTS.md"`*