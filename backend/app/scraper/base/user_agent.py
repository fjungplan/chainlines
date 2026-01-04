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
