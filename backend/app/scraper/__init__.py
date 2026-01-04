"""Scraper package - infrastructure for scraping cycling data."""
from .rate_limiter import RateLimiter
from .scheduler import ScraperScheduler
from .checkpoint import CheckpointManager, CheckpointData

__all__ = [
    "RateLimiter",
    "ScraperScheduler",
    "create_scheduler",
    "CheckpointManager",
    "CheckpointData",
]


def create_scheduler() -> ScraperScheduler:
    """
    Factory function to create a ScraperScheduler with all available scrapers.
    
    Returns:
        Configured ScraperScheduler instance
    """
    scrapers = []
    return ScraperScheduler(scrapers=scrapers)
