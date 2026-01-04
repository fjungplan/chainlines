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
