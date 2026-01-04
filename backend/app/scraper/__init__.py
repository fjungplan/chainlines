"""Scraper package - infrastructure for scraping cycling data."""
from .rate_limiter import RateLimiter
from .scheduler import ScraperScheduler
from .parsers import PCScraper
from .checkpoint import CheckpointManager, CheckpointData

__all__ = [
    "RateLimiter",
    "ScraperScheduler",
    "PCScraper",
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
    scrapers = [
        PCScraper(),
    ]
    return ScraperScheduler(scrapers=scrapers)
