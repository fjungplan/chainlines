---
id: "ad4ed210-ec3a-4c26-a7bb-65f5b6984d03"
title: "Implementing Multi-Tier Resilience"
date: "2026-01-05T17:13:24.655765600Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

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


### Planner Response

I'll implement SLICE 6.2: Multi-Tier Resilience Strategy following TDD principles. Let me start by examining the current state of the files and then write the tests first.

*Viewed [test_phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py) *

### Planner Response

Now let me view the specific [_extract_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76) method to understand its current implementation:

*Viewed code item*

### Planner Response

Good! Now let me check the LLM service structure to understand how to work with it:

*Searched filesystem*

### Planner Response

Let me check the LLM service and prompts to understand the architecture:

### Planner Response

Perfect! I can see that [LLMService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/service.py:9:0-42:17) already has built-in Gemini → Deepseek fallback logic in its [generate_structured](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/service.py:20:4-42:17) method. Now let me check the [prompts.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/prompts.py:0:0-0:0) to see how it's used:

*Grep searched codebase*

### Planner Response

Let me view the prompts file to understand its structure:

### Planner Response

Perfect! Now I understand the architecture. The `ScraperPrompts.extract_sponsors_from_name` method already uses `self._llm.generate_structured`, which has the Gemini → Deepseek fallback built-in. I need to add exponential backoff retry logic on top of this.

Let me start implementing according to the TDD workflow:

**Step 1: Write Tests First**

*Edited relevant file*

### Planner Response

Good! Now let's verify the tests fail as expected (Step 2 of TDD). Let me run them:

*User accepted the command `pytest backend/tests/scraper/test_phase1.py::test_resilience_gemini_fallback_to_deepseek backend/tests/scraper/test_phase1.py::test_resilience_exponential_backoff -v`*

### Planner Response

Good! The first test passed (because [_extract_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76) already exists), but the second test failed because:
1. The `mocker` fixture is not available (we need to install `pytest-mock`)
2. The `_extract_with_resilience` method doesn't exist yet

Let me install pytest-mock first:

*User accepted the command `pip install pytest-mock`*

### Planner Response

Great! Now let's run the tests again to confirm they fail properly (because `_extract_with_resilience` doesn't exist yet):

*User accepted the command `pytest backend/tests/scraper/test_phase1.py::test_resilience_exponential_backoff -v`*

### Planner Response

Perfect! The test fails as expected because `_extract_with_resilience` doesn't exist yet. Now let's implement it.

**Step 2: Implement the `_extract_with_resilience` method**

*Viewed [phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py) *

### Planner Response

Now I'll add the `_extract_with_resilience` method and update [_extract_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76) to use it. I need to place it before [_extract_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76):

*Edited relevant file*

### Planner Response

Perfect! Now I need to update the [_extract_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76) method to usethis new [_extract_with_resilience](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-227:25) method. Let me view the current implementation of [_extract_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76) again:

*Viewed [phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py) *

### Planner Response

Now I'll update the [_extract_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:229:4-292:76) method to use [_extract_with_resilience](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-227:25):

*Edited relevant file*

### Planner Response

Oh, there's a syntax error! It looks like I have an escaped double quote in the f-string. Let me fix this:

*Viewed [phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py) *

### Planner Response

I see the issue - there are escaped backslashes before the quotes on lines 274 and 283. Let me fix this:

*Edited relevant file*

### Planner Response

Great! Now let's run the tests to verify the implementation:

*User accepted the command `pytest backend/tests/scraper/test_phase1.py::test_resilience_gemini_fallback_to_deepseek backend/tests/scraper/test_phase1.py::test_resilience_exponential_backoff -v`*

### Planner Response

Excellent! Both tests pass! Now let's run all the Phase 1 tests to make sure we didn't break anything:

*User accepted the command `pytest backend/tests/scraper/test_phase1.py -v`*

*Checked command status*

### Planner Response

Perfect! All 14 tests pass! Now let's commit the changes as specified in the task:

*User accepted the command `git add -A`*

*User accepted the command `git commit -m "feat(scraper): implement multi-tier resilience strategy

- Add _extract_with_resilience() method
- Exponential backoff retries (1s, 2s, 4s)
- Leverage LLMService Gemini → Deepseek fallback
- Queue failed extractions after all retries exhausted
- Lower confidence on final fallback
- Comprehensive resilience tests"`*

### Planner Response

Perfect! The implementation is complete and committed. Let me now create a summary of what was accomplished:

## ✅ SLICE 6.2: Multi-Tier Resilience Strategy - Complete

I've successfully implemented the full multi-tier resilience strategy for the Smart Scraper following TDD principles:

### What Was Implemented

**1. Tests First (TDD)**
- ✅ Added [test_resilience_gemini_fallback_to_deepseek](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:366:0-394:29) - verifies the LLM service's built-in Gemini → Deepseek fallback works
- ✅ Added [test_resilience_exponential_backoff](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:396:0-439:29) - verifies exponential backoff retry logic (1s, 2s, 4s delays)
- Required installation of `pytest-mock` for mocking `asyncio.sleep`

**2. Implementation**
- ✅ Created [_extract_with_resilience()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-227:25) method in [DiscoveryService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:41:0-270:72):
  - Implements exponential backoff retries (max 3 attempts)
  - Waits 2^attempt seconds between retries (1s, 2s, 4s)
  - Leverages the existing [LLMService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/service.py:9:0-42:17) Gemini → Deepseek fallback
  - Comprehensive logging at each retry attempt
  - Raises exception after all retries exhausted

- ✅ Updated [_extract_sponsors()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76) to use the new resilience layer:
  - Calls [_extract_with_resilience()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-227:25) instead of directly calling LLM
  - Maintains existing multi-tier caching architecture
  - On final failure: adds to retry queue, falls back to simple extraction with confidence 0.2

**3. Multi-Tier Resilience Architecture**
The complete resilience strategy now includes:
1. **Tier 1**: Gemini LLM (primary via [LLMService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/service.py:9:0-42:17))
2. **Tier 2**: Deepseek LLM (automatic fallback in [LLMService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/service.py:9:0-42:17))
3. **Tier 3**: Exponential backoff retries (1s, 2s, 4s)
4. **Tier 4**: Retry queue (for end-of-year reprocessing)
5. **Tier 5**: Simple pattern fallback (confidence 0.2)

**4. Verification**
- ✅ All 14 Phase 1 tests pass
- ✅ New resilience tests verify the exponential backoff behavior
- ✅ Existing tests confirm no regressions

**5. Commit**
- ✅ Changes committed with the specified commit message
- ✅ Following atomic commit practice from the Fire-and-Forget workflow

The implementation is production-ready and provides robust handling of transient LLM failures while maintaining high extraction quality through intelligent fallback strategies.

### Planner Response

I've successfully completed **SLICE 6.2: Multi-Tier Resilience Strategy**! 🎉

## Summary

Following strict TDD principles, I implemented a comprehensive multi-tier resilience system for LLM sponsor extraction:

### ✅ What Was Done

1. **Tests First** - Added two new tests to [test_phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0):
   - [test_resilience_gemini_fallback_to_deepseek](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:366:0-394:29) - Verifies the system handles LLM failures gracefully
   - [test_resilience_exponential_backoff](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:396:0-439:29) - Validates exponential backoff retry logic (1s, 2s, 4s)

2. **Implementation** - Created [_extract_with_resilience()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-227:25) method:
   - 3 retry attempts with exponential backoff (2^attempt seconds)
   - Leverages existing [LLMService](cci:2://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/service.py:9:0-42:17) Gemini → Deepseek fallback
   - Comprehensive logging at each attempt
   - Raises exception only after all retries exhausted

3. **Integration** - Updated [_extract_sponsors()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76):
   - Now calls [_extract_with_resilience()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-227:25) for LLM extraction
   - Maintains all existing caching layers
   - Final fallback has confidence 0.2 (lower than before)

4. **Verification** - All 14 Phase 1 tests passing ✅

5. **Committed** - Changes committed with the exact message specified in the prompt

### The Complete Resilience Stack
- **Tier 1**: Gemini (primary)
- **Tier 2**: Deepseek (automatic fallback) 
- **Tier 3**: Exponential backoff (3 retries)
- **Tier 4**: Retry queue (end-of-year processing)
- **Tier 5**: Simple pattern extraction (0.2 confidence)

Ready for the next slice! 🚀

### User Input

Please commit

### Planner Response

Let me check the current git status to see if there are any uncommitted changes:

*User accepted the command `git status`*

### Planner Response

Good news! Everything is already committed. The working tree is clean, which means the implementation from SLICE 6.2 was successfully committed earlier (commit `0dce789`).

Your branch is ahead of origin by 14 commits. Would you like me to push these commits to the remote repository?