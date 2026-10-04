---
id: "28f3edac-3a18-4849-bb54-915548542dd2"
title: "Implementing Scraper Base Infrastructure"
date: "2026-01-04T15:50:36.052271400Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

# SLICE 3: Scraper Base Infrastructure

## Context
Now we build the reusable scraper foundation: rate limiting, retries, and User-Agent rotation.

**Dependencies:** SLICE 1 must be complete.

**Relevant Existing Files:**
- `backend/app/scraper/` - Existing scraper directory

## Prompt

You are implementing SLICE 3 of the Smart Scraper project. Follow TDD strictly.

### TASK 3.1: Rate Limiter (Test: Delays Respected)

**Test First:**
Create `backend/tests/scraper/test_base_scraper.py`:
```python
"""Test base scraper infrastructure."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import time

@pytest.mark.asyncio
async def test_rate_limiter_enforces_delay():
    """RateLimiter should enforce minimum delay between calls."""
    from app.scraper.base.rate_limiter import RateLimiter
    
    limiter = RateLimiter(min_delay=0.1, max_delay=0.1)  # Fixed 100ms
    
    start = time.monotonic()
    await limiter.wait()
    await limiter.wait()
    elapsed = time.monotonic() - start
    
    # Second call should have waited ~100ms
    assert elapsed >= 0.09  # Allow small timing variance

@pytest.mark.asyncio
async def test_rate_limiter_randomizes_delay():
    """RateLimiter should randomize delays within range."""
    from app.scraper.base.rate_limiter import RateLimiter
    
    limiter = RateLimiter(min_delay=0.05, max_delay=0.15)
    delays = []
    
    for _ in range(5):
        start = time.monotonic()
        await limiter.wait()
        delays.append(time.monotonic() - start)
    
    # At least some variance (not all identical)
    # First call has no delay, so check from second onwards
    assert len(set(round(d, 2) for d in delays[1:])) > 1 or len(delays) < 3
```

**Implementation:**
Create `backend/app/scraper/base/__init__.py` (empty).
Create `backend/app/scraper/base/rate_limiter.py`:
```python
"""Rate limiter for respectful scraping."""
import asyncio
import random
import time

class RateLimiter:
    """Enforces delays between requests with randomization."""
    
    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._last_request: float = 0
    
    async def wait(self) -> None:
        """Wait appropriate time before next request."""
        now = time.monotonic()
        elapsed = now - self._last_request
        
        if self._last_request > 0:  # Not first request
            delay = random.uniform(self.min_delay, self.max_delay)
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
        
        self._last_request = time.monotonic()
```

**Verify:** Run `pytest backend/tests/scraper/test_base_scraper.py -v`

---

### TASK 3.2: Retry with Backoff (Test: Retries and Backs Off)

**Test First:**
Add to `backend/tests/scraper/test_base_scraper.py`:
```python
@pytest.mark.asyncio
async def test_retry_succeeds_after_failures():
    """Retry decorator should retry on failure and succeed."""
    from app.scraper.base.retry import with_retry
    
    call_count = 0
    
    @with_retry(max_attempts=3, base_delay=0.01)
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary failure")
        return "success"
    
    result = await flaky_function()
    assert result == "success"
    assert call_count == 3

@pytest.mark.asyncio
async def test_retry_raises_after_max_attempts():
    """Retry decorator should raise after max attempts exceeded."""
    from app.scraper.base.retry import with_retry
    
    @with_retry(max_attempts=2, base_delay=0.01)
    async def always_fails():
        raise ConnectionError("Always fails")
    
    with pytest.raises(ConnectionError):
        await always_fails()
```

**Implementation:**
Create `backend/app/scraper/base/retry.py`:
```python
"""Retry decorator with exponential backoff."""
import asyncio
import functools
import logging
from typing import TypeVar, Callable, Any

logger = logging.getLogger(__name__)
F = TypeVar('F', bound=Callable[..., Any])

def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """Decorator for async functions with exponential backoff retry."""
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator
```

**Verify:** Run `pytest backend/tests/scraper/test_base_scraper.py -v`

---

### TASK 3.3: User-Agent Rotation (Test: Headers Rotate)

**Test First:**
Add to `backend/tests/scraper/test_base_scraper.py`:
```python
def test_user_agent_rotator_returns_different_agents():
    """UserAgentRotator should return varying user agents."""
    from app.scraper.base.user_agent import UserAgentRotator
    
    rotator = UserAgentRotator()
    agents = [rotator.get() for _ in range(10)]
    
    # Should have at least 2 different agents in 10 calls
    assert len(set(agents)) >= 2

def test_user_agent_rotator_all_valid():
    """All user agents should be valid strings."""
    from app.scraper.base.user_agent import UserAgentRotator
    
    rotator = UserAgentRotator()
    for _ in range(10):
        agent = rotator.get()
        assert isinstance(agent, str)
        assert len(agent) > 20  # Reasonable UA length
        assert "Mozilla" in agent or "ChainlinesBot" in agent
```

**Implementation:**
Create `backend/app/scraper/base/user_agent.py`:
```python
"""User-Agent rotation for scraping."""
import random

# Common browser user agents
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "ChainlinesBot/1.0 (https://chainlines.app; contact@chainlines.app)",
]

class UserAgentRotator:
    """Rotates through user agents for requests."""
    
    def __init__(self, agents: list[str] | None = None):
        self._agents = agents or _USER_AGENTS
    
    def get(self) -> str:
        """Get a random user agent."""
        return random.choice(self._agents)
```

**Verify:** Run `pytest backend/tests/scraper/test_base_scraper.py -v`

---

### TASK 3.4: Base Scraper Class (Test: Fetches with Rate Limiting)

**Test First:**
Add to `backend/tests/scraper/test_base_scraper.py`:
```python
@pytest.mark.asyncio
async def test_base_scraper_fetches_with_rate_limit():
    """BaseScraper should fetch URLs respecting rate limits."""
    from app.scraper.base.scraper import BaseScraper
    
    class TestScraper(BaseScraper):
        pass
    
    scraper = TestScraper(min_delay=0.01, max_delay=0.01)
    
    # Mock httpx
    with patch('app.scraper.base.scraper.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.text = "<html>test</html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = lambda: None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client
        
        html = await scraper.fetch("https://example.com")
        assert html == "<html>test</html>"
```

**Implementation:**
Create `backend/app/scraper/base/scraper.py`:
```python
"""Base scraper with rate limiting and retries."""
import httpx
from app.scraper.base.rate_limiter import RateLimiter
from app.scraper.base.retry import with_retry
from app.scraper.base.user_agent import UserAgentRotator

class BaseScraper:
    """Base class for all scrapers."""
    
    def __init__(
        self,
        min_delay: float = 3.0,
        max_delay: float = 6.0,
        timeout: float = 30.0
    ):
        self._rate_limiter = RateLimiter(min_delay, max_delay)
        self._user_agent = UserAgentRotator()
        self._timeout = timeout
    
    @with_retry(max_attempts=3, base_delay=2.0, exceptions=(httpx.HTTPError,))
    async def fetch(self, url: str) -> str:
        """Fetch a URL with rate limiting and retries."""
        await self._rate_limiter.wait()
        
        headers = {"User-Agent": self._user_agent.get()}
        
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
```

**Verify:** Run `pytest backend/tests/scraper/test_base_scraper.py -v`

---

### WIRING: Export base scraper components

Update `backend/app/scraper/base/__init__.py`:
```python
from app.scraper.base.scraper import BaseScraper
from app.scraper.base.rate_limiter import RateLimiter
from app.scraper.base.retry import with_retry
from app.scraper.base.user_agent import UserAgentRotator

__all__ = ["BaseScraper", "RateLimiter", "with_retry", "UserAgentRotator"]
```

---

## Finalize Slice 3

**Step 1: Update Task Checklist**

Edit `docs/SMART_SCRAPER_TASKS.md` and mark the following as complete:
```markdown
- [x] 3.1 Create `BaseScraper` abstract class
- [x] 3.2 Implement rate limiting with configurable delays
- [x] 3.3 Implement retry with exponential backoff
- [x] 3.4 Implement User-Agent rotation
- [x] **SLICE 3 COMMITTED**
```

**Step 2: Commit (execute now)**
```bash
git add -A && git commit -m "feat(scraper): add base scraper infrastructure

- Add RateLimiter with configurable random delays
- Add retry decorator with exponential backoff
- Add UserAgentRotator for header rotation
- Add BaseScraper class combining all features"
```

---

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `mkdir -p backend/app/scraper/base`*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_base_scraper.py -v`*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_base_scraper.py -v`*

*Viewed [scheduler.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/scheduler.py) *

*Listed directory [scraper](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_base_scraper.py -v`*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_base_scraper.py -v`*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_base_scraper.py -v`*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_base_scraper.py -v`*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_base_scraper.py -v`*

*User accepted the command `pytest backend/tests/scraper/test_base_scraper.py -v`*

*Edited relevant file*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `git add -A && git commit -m "feat(scraper): add base scraper infrastructure

- Add RateLimiter with configurable random delays
- Add retry decorator with exponential backoff
- Add UserAgentRotator for header rotation
- Add BaseScraper class combining all features"`*

---

## Session Artifacts & Documentation

### Artifact: `task.md`

# Task: Implement Scraper Base Infrastructure (Slice 3)

- [x] Rate Limiter
    - [x] Create tests for RateLimiter <!-- id: 0 -->
    - [x] Implement RateLimiter <!-- id: 1 -->
    - [x] Verify RateLimiter <!-- id: 2 -->
- [x] Retry with Backoff
    - [x] Create tests for Retry decorator <!-- id: 3 -->
    - [x] Implement Retry decorator <!-- id: 4 -->
    - [x] Verify Retry decorator <!-- id: 5 -->
- [x] User-Agent Rotation
    - [x] Create tests for UserAgentRotator <!-- id: 6 -->
    - [x] Implement UserAgentRotator <!-- id: 7 -->
    - [x] Verify UserAgentRotator <!-- id: 8 -->
- [x] Base Scraper Class
    - [x] Create tests for BaseScraper <!-- id: 9 -->
    - [x] Implement BaseScraper <!-- id: 10 -->
    - [x] Wiring `__init__.py` <!-- id: 11 -->
    - [x] Verify BaseScraper <!-- id: 12 -->
- [ ] Finalize
    - [ ] Update `docs/SMART_SCRAPER_TASKS.md` <!-- id: 13 -->
    - [ ] Commit changes <!-- id: 14 -->

### Artifact: `walkthrough.md`

# Walkthrough - Scraper Base Infrastructure (Slice 3)

Implemented the reusable scraper foundation with rate limiting, retries, and User-Agent rotation.

## Changes

### New Components
- **[RateLimiter](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/rate_limiter.py)**: Enforces configurable delays with randomization.
- **[with_retry](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/retry.py)**: Async decorator for exponential backoff retries.
- **[UserAgentRotator](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/user_agent.py)**: Rotates through common browser User-Agents.
- **[BaseScraper](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/scraper.py)**: Base class integrating the above.

## Verification Results

### Automated Tests
Run `pytest backend/tests/scraper/test_base_scraper.py -v`

```
backend\tests\scraper\test_base_scraper.py::test_rate_limiter_enforces_delay PASSED [ 14%]
backend\tests\scraper\test_base_scraper.py::test_rate_limiter_randomizes_delay PASSED [ 28%]
backend\tests\scraper\test_base_scraper.py::test_retry_succeeds_after_failures PASSED [ 42%]
backend\tests\scraper\test_base_scraper.py::test_retry_raises_after_max_attempts PASSED [ 57%]
backend\tests\scraper\test_base_scraper.py::test_user_agent_rotator_returns_different_agents PASSED [ 71%]
backend\tests\scraper\test_base_scraper.py::test_user_agent_rotator_all_valid PASSED [ 85%]
backend\tests\scraper\test_base_scraper.py::test_base_scraper_fetches_with_rate_limit PASSED [100%]
```

All 7 tests passed.

### Artifact: `implementation_plan.md`

# Implementation Plan - Scraper Base Infrastructure (Slice 3)

Use TDD to build the reusable scraper foundation: rate limiting, retries, and User-Agent rotation.

## User Review Required
None.

## Proposed Changes

### Backend Scraper Base

#### [NEW] [rate_limiter.py](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/rate_limiter.py)
- Implement `RateLimiter` class with `wait()` method.
- Support min/max delay and randomization.

#### [NEW] [retry.py](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/retry.py)
- Implement `with_retry` decorator.
- Support exponential backoff and configurable exceptions.

#### [NEW] [user_agent.py](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/user_agent.py)
- Implement `UserAgentRotator` class.
- List common user agents.

#### [NEW] [scraper.py](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/scraper.py)
- Implement `BaseScraper` class.
- Integrate RateLimiter, UserAgentRotator, and retry logic.
- Use `httpx` for requests.

#### [NEW] [__init__.py](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/base/__init__.py)
- Export components.

### Tests

#### [NEW] [test_base_scraper.py](file:///c%3A/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_base_scraper.py)
- Tests for RateLimiter (delays, randomization).
- Tests for Retry (success on retry, fail after max attempts).
- Tests for UserAgentRotator (rotation, validity).
- Tests for BaseScraper (fetching, integration).

## Verification Plan

### Automated Tests
- Run `pytest backend/tests/scraper/test_base_scraper.py -v` after each step.