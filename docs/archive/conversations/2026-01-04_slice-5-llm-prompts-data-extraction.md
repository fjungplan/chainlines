---
id: "9c296659-eaff-499e-959f-0881255690ac"
title: "# SLICE 5: LLM Prompts - Data Extraction"
date: "2026-01-04T16:08:39.762142Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

# SLICE 5: LLM Prompts - Data Extraction

## Context
Now we connect the LLM layer to the scraper layer, enabling structured data extraction from HTML.

**Dependencies:** SLICE 2 and SLICE 4 must be complete.

## Prompt

You are implementing SLICE 5 of the Smart Scraper project. Follow TDD strictly.

### TASK 5.1: Enhance ScrapedTeamData Model

**Test First:**
Create `backend/tests/scraper/test_llm_prompts.py`:
```python
"""Test LLM prompts for data extraction."""
import pytest
from pydantic import ValidationError

def test_scraped_team_data_validates():
    """ScrapedTeamData should validate correctly."""
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    data = ScrapedTeamData(
        name="Team Visma",
        season_year=2024,
        sponsors=["Visma", "Lease a Bike"]
    )
    assert data.name == "Team Visma"
    assert len(data.sponsors) == 2

def test_scraped_team_data_requires_name():
    """ScrapedTeamData should require name field."""
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    with pytest.raises(ValidationError):
        ScrapedTeamData(season_year=2024)
```

**Verify:** Run `pytest backend/tests/scraper/test_llm_prompts.py -v`

---

### TASK 5.2: Team Data Extraction Prompt

**Test First:**
Add to `backend/tests/scraper/test_llm_prompts.py`:
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_extract_team_data_prompt():
    """LLMService.extract_team_data should return structured data."""
    from app.scraper.llm.prompts import ScraperPrompts
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    mock_service = AsyncMock()
    mock_service.generate_structured = AsyncMock(
        return_value=ScrapedTeamData(
            name="UAE Team Emirates",
            uci_code="UAD",
            tier="WorldTour",
            country_code="AE",
            sponsors=["Emirates", "Colnago"],
            season_year=2024
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_service)
    
    result = await prompts.extract_team_data(
        html="<html>...</html>",
        season_year=2024
    )
    
    assert result.name == "UAE Team Emirates"
    assert result.uci_code == "UAD"
    mock_service.generate_structured.assert_called_once()
```

**Implementation:**
Create `backend/app/scraper/llm/prompts.py`:
```python
"""LLM prompts for scraper operations."""
from typing import TYPE_CHECKING
from app.scraper.sources.cyclingflash import ScrapedTeamData

if TYPE_CHECKING:
    from app.scraper.llm.service import LLMService

EXTRACT_TEAM_DATA_PROMPT = """
Analyze the following HTML from a cycling team page and extract structured data.

HTML Content:
{html}

Season Year: {season_year}

Extract the following information:
- Team name (without year suffix)
- UCI code (3-letter code if present)
- Tier level (WorldTour, ProTeam, Continental, or null)
- Country code (2-letter ISO code if determinable)
- List of sponsor names (in order of appearance/prominence)
- Previous season URL (if there's a link to previous year's page)

Return the data in the specified JSON format.
"""

class ScraperPrompts:
    """Collection of LLM prompts for scraper operations."""
    
    def __init__(self, llm_service: "LLMService"):
        self._llm = llm_service
    
    async def extract_team_data(
        self,
        html: str,
        season_year: int
    ) -> ScrapedTeamData:
        """Extract structured team data from HTML using LLM."""
        prompt = EXTRACT_TEAM_DATA_PROMPT.format(
            html=html[:10000],  # Limit HTML size
            season_year=season_year
        )
        
        return await self._llm.generate_structured(
            prompt=prompt,
            response_model=ScrapedTeamData
        )
```

**Verify:** Run `pytest backend/tests/scraper/test_llm_prompts.py -v`

---

### WIRING: Export prompts

Update `backend/app/scraper/llm/__init__.py`:
```python
from app.scraper.llm.base import BaseLLMClient
from app.scraper.llm.gemini import GeminiClient
from app.scraper.llm.deepseek import DeepseekClient
from app.scraper.llm.service import LLMService
from app.scraper.llm.prompts import ScraperPrompts

__all__ = [
    "BaseLLMClient", "GeminiClient", "DeepseekClient", 
    "LLMService", "ScraperPrompts"
]
```

---

## Finalize Slice 5

**Step 1: Update Task Checklist**

Edit `docs/SMART_SCRAPER_TASKS.md` and mark the following as complete:
```markdown
- [x] 5.1 Define `ScrapedTeamData` Pydantic model
- [x] 5.2 Write `extract_team_data` prompt
- [x] 5.3 Integrate prompt into `LLMService`
- [x] 5.4 Test with CyclingFlash fixture HTML
- [x] **SLICE 5 COMMITTED**
```

**Step 2: Commit (execute now)**
```bash
git add -A && git commit -m "feat(scraper): add team data extraction LLM prompt

- Add ScraperPrompts class for LLM prompt management
- Implement extract_team_data prompt with structured output
- Wire ScraperPrompts to LLMService"
```

---

*Viewed [cyclingflash.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/sources/cyclingflash.py) *

*Viewed [__init__.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/__init__.py) *

*Listed directory [scraper](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper) *

### Planner Response

Good, I can see the [ScrapedTeamData](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/sources/cyclingflash.py:7:0-15:20) model already exists in [cyclingflash.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_cyclingflash.py:0:0-0:0) with `name` as a required field. Now I'll create the test file first following TDD.

*Edited relevant file*

### Planner Response

Now let me run the tests to verify they fail first (since [prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:0:0-0:0) doesn't exist yet):

*User accepted the command `cd backend && python -m pytest tests/scraper/test_llm_prompts.py -v`*

### Planner Response

PowerShell doesn't use `&&`. Let me fix the command:

*User accepted the command `python -m pytest tests/scraper/test_llm_prompts.py -v`*

### Planner Response

The TDD cycle is working correctly:
- ✅ First two tests pass (ScrapedTeamData already exists and validates correctly)
- ❌ Third test fails because [prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:0:0-0:0) doesn't exist yet

Now I'll create the implementation file:

*Edited relevant file*

### Planner Response

Now let me run the tests to verify:

*User accepted the command `python -m pytest tests/scraper/test_llm_prompts.py -v`*

### Planner Response

All 3 tests pass. Now I need to update the [__init__.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/__init__.py:0:0-0:0) to export [ScraperPrompts](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:27:0-60:9), then update the task checklist and commit:

*Edited relevant file*

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

### Planner Response

Now I need to update the SMART_SCRAPER_TASKS.md to mark SLICE 5 as complete, then commit:

*Edited relevant file*

### Planner Response

Now let me commit the changes:

*User accepted the command `git add -A; git commit -m "feat(scraper): add team data extraction LLM prompt

- Add ScraperPrompts class for LLM prompt management
- Implement extract_team_data prompt with structured output
- Wire ScraperPrompts to LLMService"`*

### Planner Response

Excellent! SLICE 5 is complete. Let me notify the user with the summary: