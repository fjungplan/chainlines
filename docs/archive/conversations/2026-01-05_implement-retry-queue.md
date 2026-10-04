---
id: "dd379baa-dc31-4761-9f85-62808870a146"
title: "Implement Retry Queue"
date: "2026-01-05T16:49:25.276851800Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

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


### Planner Response

I'll implement SLICE 6.1: Implement Retry Queue following TDD principles. Let me start by checking the current branch and reviewing the relevant files.

*User accepted the command `git branch --show-current`*

*Viewed [test_phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py) *

*Viewed [phase1.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py) *

### Planner Response

Good! I'm on the `feat/scraper-refinement-llm` branch. Now I'll implement SLICE 6.1 following strict TDD. Let me first add the tests to the test file:

*Edited relevant file*

### Planner Response

Good! Now let me verify that the tests fail as expected (TDD step 2):

*User accepted the command `pytest backend/tests/scraper/test_phase1.py::test_retry_queue_adds_failed_teams -v`*

*User accepted the command `pytest backend/tests/scraper/test_phase1.py::test_process_retry_queue -v`*

### Planner Response

Perfect! The tests fail as expected because [_retry_queue](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:325:0-362:60) doesn't exist yet. Now let me implement the retry queue logic in [phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0):

*Edited relevant file*

### Planner Response

Excellent! Now let me verify that both tests pass:

*User accepted the command `pytest backend/tests/scraper/test_phase1.py::test_retry_queue_adds_failed_teams backend/tests/scraper/test_phase1.py::test_process_retry_queue -v`*

### Planner Response

Perfect! Both tests pass. Now let me run all the Phase 1 tests to ensure we haven't broken anything:

*User accepted the command `pytest backend/tests/scraper/test_phase1.py -v`*

### Planner Response

Excellent! All 12 tests pass, including the 2 new retry queue tests. Let me now check if there's a task tracking file I should update:

*Searched filesystem*

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

### Planner Response

I see the tasks file doesn't have a specific entry for Slice 6.1. Let me check if there's a more detailed prompts document that I should look at:

*Grep searched codebase*

### Planner Response

Great! Let me check that document to see if there's a task list I should update:

*Viewed [PROGRESSIVE_SPONSOR_EXTRACTION_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/PROGRESSIVE_SPONSOR_EXTRACTION_PROMPTS.md) *

### Planner Response

Perfect! I can see SLICE 6.1 is documented in the prompts file. Since all tests are passing, let me now prepare for commit. Let me create a summary of the changes:

## Summary of Implementation

I've successfully implemented **SLICE 6.1: Implement Retry Queue** following strict TDD principles:

### Changes Made:

1. **Tests Added** ([test_phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0)):
   - [test_retry_queue_adds_failed_teams](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:297:0-323:71): Verifies failed LLM extractions are added to retry queue
   - [test_process_retry_queue](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:325:0-362:60): Verifies retry queue is processed at end of year

2. **Implementation** ([phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0)):
   - Initialize `_retry_queue: List[Tuple[str, dict]]` in `DiscoveryService.__init__`
   - Added logic in [_extract_sponsors](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:173:4-236:76) to queue teams when LLM extraction fails
   - Implemented [_process_retry_queue()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:238:4-270:72) method with:
     - Empty queue check
     - Copy and clear mechanism
     - 1-second delay between retries to avoid rate limits
     - Confidence logging
     - Exception handling
   - Called [_process_retry_queue()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:238:4-270:72) at end of [discover_teams()](cci:1://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:70:4-164:9)

### Test Results:
✅ All 12 tests in [test_phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0) pass (including 2 new retry queue tests)

**Shall we commit these changes now?**

### User Input

yes please

*User accepted the command `git add -A`*

*User accepted the command `git commit -m "feat(scraper): add retry queue for failed LLM extractions

- Add _retry_queue list to DiscoveryService
- Queue teams when LLM extraction fails
- Implement _process_retry_queue() method
- Retry queued items at end of year processing
- Add delay between retries to avoid rate limits
- Tests for queue addition and processing"`*

### Planner Response

Perfect! ✅ **SLICE 6.1 has been successfully committed**!

## Commit Summary

**Commit Hash:** `7e059ad`  
**Branch:** `feat/scraper-refinement-llm`

### Changes:
- 2 files changed
- 117 insertions

### Files Modified:
1. [backend/tests/scraper/test_phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0) - Added 2 new tests for retry queue functionality
2. [backend/app/scraper/orchestration/phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/orchestration/phase1.py:0:0-0:0) - Implemented retry queue logic

### Implementation Details:
✅ **TDD Approach Followed:**
1. ✅ Tests written first (and failed as expected)
2. ✅ Implementation added to make tests pass
3. ✅ All 12 tests in [test_phase1.py](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_phase1.py:0:0-0:0) passing
4. ✅ Atomic commit with descriptive message

### What's Next?
The retry queue is now integrated into Phase 1 Discovery. When LLM extraction fails (both Gemini and Deepseek after retries), teams are:
1. Added to the retry queue with context preserved
2. Processed at the end of year discovery with 1-second delays between attempts
3. Given another chance for successful extraction before final fallback

Ready for the next slice! 🚀