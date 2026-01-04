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
