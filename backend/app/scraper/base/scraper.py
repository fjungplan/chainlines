"""Base scraper with rate limiting and retries."""
import httpx
from typing import Optional
from app.scraper.base.rate_limiter import RateLimiter
from app.scraper.base.retry import with_retry
from app.scraper.base.user_agent import UserAgentRotator
from app.scraper.utils.cache import CacheManager

class BaseScraper:
    """Base class for all scrapers."""
    
    def __init__(
        self,
        min_delay: float = 3.0,
        max_delay: float = 6.0,
        timeout: float = 30.0,
        cache: Optional[CacheManager] = None,
        rate_limit: Optional[float] = None
    ):
        if rate_limit is not None:
            min_delay = rate_limit
            max_delay = rate_limit + 1.0  # Add small jitter range
            
        self._rate_limiter = RateLimiter(min_delay, max_delay)
        self._user_agent = UserAgentRotator()
        self._timeout = timeout
        self._cache = cache
    
    @with_retry(max_attempts=3, base_delay=2.0, exceptions=(httpx.HTTPError,))
    async def fetch(self, url: str, force_refresh: bool = False) -> str:
        """Fetch a URL with rate limiting and retries."""
        # Check cache first
        if not force_refresh and self._cache:
            domain = self._get_domain(url)
            cached = self._cache.get(url, domain=domain)
            if cached:
                return cached

        await self._rate_limiter.wait()
        
        headers = {"User-Agent": self._user_agent.get()}
        
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            content = response.text
            
            # Save to cache if successful
            if self._cache:
                domain = self._get_domain(url)
                self._cache.set(url, content, domain=domain)
                
            return content

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL for cache organization."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or "default"
