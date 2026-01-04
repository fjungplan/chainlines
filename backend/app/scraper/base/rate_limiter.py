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
