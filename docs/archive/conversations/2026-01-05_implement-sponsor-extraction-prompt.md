---
id: "8d189840-b1f8-4482-87a0-8963d80889a1"
title: "Implement Sponsor Extraction Prompt"
date: "2026-01-05T15:02:01.963945400Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

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


*Listed directory [scraper](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper) *

### Planner Response

I can see there's already an existing [test_llm_prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:0:0-0:0) file and the [SponsorExtractionResult](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py:11:0-17:18) and [SponsorInfo](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py:3:0-9:5) models are already defined. Let me check the existing test file to see what's already covered:

*Viewed [test_llm_prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py) *

### Planner Response

Now I have a clear picture. The test in the spec uses `mock_llm.call()` but the actual [LLMService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/service.py:9:0-42:17) uses [generate_structured()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/service.py:20:4-42:17). Let me create the test file following the existing pattern and then implement the prompt.

*Edited relevant file*

### Planner Response

Now let me run the tests to confirm they fail (TDD approach):

*User accepted the command `pytest backend/tests/scraper/test_sponsor_prompts.py -v 2>&1 | head -50`*

*User accepted the command `pytest backend/tests/scraper/test_sponsor_prompts.py -v`*

### Planner Response

Tests fail as expected because [extract_sponsors_from_name](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:7:0-40:72) doesn't exist yet. Now let me implement the method:

*Viewed [prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py) *

### Planner Response

Now I'll add the sponsor extraction prompt and method to [prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:0:0-0:0):

*Edited relevant file*

### Planner Response

Now I need to add the SPONSOR_EXTRACTION_PROMPT constant and the method. Let me view the file again to get the correct line numbers:

*Viewed [prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py) *

*Edited relevant file*

### Planner Response

Now let's run the tests to verify the implementation:

*User accepted the command `pytest backend/tests/scraper/test_sponsor_prompts.py -v`*

### Planner Response

All 5 tests pass. Let me also run a quick sanity check to ensure the existing tests still pass:

*User accepted the command `pytest backend/tests/scraper/test_llm_prompts.py -v`*

### Planner Response

These are pre-existing test failures from a previous change where `ScrapedTeamData.sponsors` was changed from `List[str]` to `List[SponsorInfo]`. This is not related to my current changes. Let me update these tests to use the correct [SponsorInfo](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py:3:0-9:5) type:

*Viewed [test_llm_prompts.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py) *

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_sponsor_prompts.py backend/tests/scraper/test_llm_prompts.py -v`*

### Planner Response

All 8 tests pass. Now let me commit the changes as specified:

*User accepted the command `git add -A && git commit -m "feat(scraper): add LLM sponsor extraction prompt

- Add SPONSOR_EXTRACTION_PROMPT with detailed instructions
- Implement extract_sponsors_from_name() method
- Include context: team name, year, country, partial matches
- Provide cycling-specific examples in prompt
- Comprehensive tests with mocked LLM responses
- Fix pre-existing test failures in test_llm_prompts.py (SponsorInfo type)"`*

*User accepted the command `git add -A`*

*User accepted the command `git commit -m "feat(scraper): add LLM sponsor extraction prompt

- Add SPONSOR_EXTRACTION_PROMPT with detailed instructions
- Implement extract_sponsors_from_name() method
- Include context: team name, year, country, partial matches
- Provide cycling-specific examples in prompt
- Comprehensive tests with mocked LLM responses
- Fix pre-existing test failures in test_llm_prompts.py (SponsorInfo type)"`*

### Planner Response

**SLICE 3.1: Sponsor Extraction Prompt** is complete! ✅

### Summary of Changes

| File | Changes |
|------|---------|
| [[test_sponsor_prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:0:0-0:0)](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py) | **[NEW]** 5 comprehensive tests for sponsor extraction prompt |
| [[prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:0:0-0:0)](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py) | Added `SPONSOR_EXTRACTION_PROMPT` constant + [extract_sponsors_from_name()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:157:4-185:9) method |
| [[test_llm_prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:0:0-0:0)](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py) | Fixed pre-existing test failures (updated to use [SponsorInfo](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py:3:0-9:5) type) |

### Tests Verified
All 8 tests pass:
- [test_extract_sponsors_from_name](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:7:0-40:72) - Basic sponsor extraction with prompt formatting
- [test_extract_sponsors_with_partial_matches](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:43:0-72:28) - Partial DB matches included in prompt
- [test_extract_sponsors_with_parent_company](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:75:0-99:61) - Parent company extraction
- [test_extract_sponsors_unknown_country](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:102:0-127:30) - Handles unknown country code
- [test_extract_sponsors_multiple_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:130:0-160:33) - Multiple sponsors extraction
- [test_scraped_team_data_validates](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:7:0-21:49) - Data validation (fixed)
- [test_scraped_team_data_requires_name](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:24:0-29:41) - Required field validation
- [test_extract_team_data_prompt](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:32:0-62:57) - Team data prompt (fixed)

### Commit
```
feat(scraper): add LLM sponsor extraction prompt
```

### Planner Response



Shall we commit changes now and proceed to the next slice?

### Planner Response

SLICE 3.1 is complete! Here's a summary:

### ✅ Completed

**Files Changed:**
- **[NEW]** [backend/tests/scraper/test_sponsor_prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:0:0-0:0) - 5 comprehensive tests
- **[MODIFIED]** [backend/app/scraper/llm/prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:0:0-0:0) - Added `SPONSOR_EXTRACTION_PROMPT` and [extract_sponsors_from_name()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:157:4-185:9) method
- **[FIXED]** [backend/tests/scraper/test_llm_prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:0:0-0:0) - Updated to use [SponsorInfo](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py:3:0-9:5) type

**Tests:** All 8 passing ✅

**Commit:** `feat(scraper): add LLM sponsor extraction prompt` on branch `feat/scraper-refinement-llm`

Ready for the next slice when you are!

### User Input

Continue

*Viewed [PROGRESSIVE_SPONSOR_EXTRACTION_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/PROGRESSIVE_SPONSOR_EXTRACTION_PROMPTS.md) *

### Planner Response

Good, I can see the next slice is **SLICE 4.1: Update DiscoveryService Constructor**. Let me start implementing it:

*Viewed [phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py) *

*Viewed [test_phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py) *

### Planner Response

Now I understand the current structure. Let me first check if the `BrandMatcherService` exists:

### Planner Response

The [BrandMatcherService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services/brand_matcher.py:13:0-100:9) already exists. Now let me update the test file first (TDD approach), then update [DiscoveryService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:36:0-121:10) to accept the new parameters:

*Edited relevant file*

### Planner Response

Now let's run the tests to verify they fail (TDD red phase):

*User accepted the command `pytest backend/tests/scraper/test_phase1.py::test_discovery_service_with_llm_dependencies backend/tests/scraper/test_phase1.py::test_discovery_service_logs_llm_availability -v`*

### Planner Response

Tests fail as expected. Now let's implement the changes to [DiscoveryService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:36:0-121:10):

*Edited relevant file*

### Planner Response

Now let's run the tests to verify they pass:

*User accepted the command `pytest backend/tests/scraper/test_phase1.py -v`*

### Planner Response

All 5 tests pass. Now I need to check the CLI to see where [DiscoveryService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:41:0-140:10) is instantiated and update it if needed:

### Planner Response

I can see the CLI at line ~97-103 creates [DiscoveryService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:41:0-140:10). The spec says to update the CLI but pass `session=None` and `llm_prompts=None` for now. Since the parameters are optional with defaults of `None`, this should work without any changes. Let me verify by running the existing tests:

*User accepted the command `pytest backend/tests/scraper/test_cli.py -v`*

### Planner Response

All tests pass. The CLI doesn't need changes since the new parameters are optional. Now let's commit:

*User rejected the command `git add -A`*

### User Input

Before committing, please check if slice 3.1 is fully impleented and if the tests pass, as I'm not sure you finished the task. If all tests from 3.1 and 4.1 pass you can commit all at once!

*User accepted the command `pytest backend/tests/scraper/test_sponsor_prompts.py backend/tests/scraper/test_llm_prompts.py backend/tests/scraper/test_phase1.py backend/tests/scraper/test_cli.py -v`*

### Planner Response

All **18 tests pass** ✅

Let me summarize what was implemented for both slices:

### SLICE 3.1: Sponsor Extraction Prompt ✅
| File | Changes |
|------|---------|
| [test_sponsor_prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_sponsor_prompts.py:0:0-0:0) | **[NEW]** 5 tests for sponsor extraction |
| [prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:0:0-0:0) | Added `SPONSOR_EXTRACTION_PROMPT` + [extract_sponsors_from_name()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:157:4-185:9) |
| [test_llm_prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_llm_prompts.py:0:0-0:0) | Fixed pre-existing failures (SponsorInfo type) |

### SLICE 4.1: Update DiscoveryService Constructor ✅
| File | Changes |
|------|---------|
| [test_phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0) | Added 2 tests for new constructor parameters |
| [phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0) | Added `session` and `llm_prompts` parameters, initializes [BrandMatcherService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services/brand_matcher.py:13:0-100:9) |

Now let's commit both slices together:

*User accepted the command `git add -A`*

*User accepted the command `git commit -m "feat(scraper): add LLM sponsor extraction and DiscoveryService LLM integration

SLICE 3.1 - Sponsor Extraction Prompt:
- Add SPONSOR_EXTRACTION_PROMPT with detailed cycling-domain instructions
- Implement extract_sponsors_from_name() method in ScraperPrompts
- Include context: team name, year, country, partial matches
- Provide cycling-specific examples in prompt
- 5 comprehensive tests with mocked LLM responses
- Fix SponsorInfo type in test_llm_prompts.py

SLICE 4.1 - DiscoveryService Constructor:
- Add optional session and llm_prompts constructor parameters
- Initialize BrandMatcherService when session is provided
- Add logging for LLM/brand matching availability
- Maintain backward compatibility (both params optional)
- 2 new tests for LLM dependency injection"`*

### Planner Response

Both slices committed! ✅

### Summary

**Commit:** `feat(scraper): add LLM sponsor extraction and DiscoveryService LLM integration`

| Slice | Status | Tests |
|-------|--------|-------|
| **SLICE 3.1** - Sponsor Extraction Prompt | ✅ Complete | 5 tests |
| **SLICE 4.1** - DiscoveryService Constructor | ✅ Complete | 2 tests |

**Total:** 18 tests passing (including related tests)

Ready for the next slice (4.2: Sponsor Extraction Method) when you are!