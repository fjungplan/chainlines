import pytest
import time
from app.scraper.sources.firstcycling import FirstCyclingScraper

@pytest.mark.asyncio
async def test_firstcycling_scraper_respects_rate_limit(mocker):
    """Verify 10s delay between requests."""
    # Mocking RateLimiter.wait to avoid actual 10s sleep in tests
    mock_wait = mocker.patch("app.scraper.base.rate_limiter.RateLimiter.wait")
    
    scraper = FirstCyclingScraper()
    assert scraper.RATE_LIMIT_SECONDS == 10.0
    
    # Verify rate limiter was initialized with 10s
    assert scraper._rate_limiter.min_delay == 10.0

def test_get_gt_url_giro():
    """Verify correct URL generation for Giro."""
    scraper = FirstCyclingScraper()
    url = scraper.get_gt_start_list_url("giro", 2024)
    assert url == "https://firstcycling.com/race.php?r=13&y=2024&k=8"

def test_get_gt_url_tour():
    """Verify correct URL generation for Tour."""
    scraper = FirstCyclingScraper()
    url = scraper.get_gt_start_list_url("tour", 2024)
    assert url == "https://firstcycling.com/race.php?r=17&y=2024&k=8"

def test_get_gt_url_vuelta():
    """Verify correct URL generation for Vuelta."""
    scraper = FirstCyclingScraper()
    url = scraper.get_gt_start_list_url("vuelta", 2024)
    assert url == "https://firstcycling.com/race.php?r=23&y=2024&k=8"
