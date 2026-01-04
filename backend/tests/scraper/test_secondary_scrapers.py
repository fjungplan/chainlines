"""Test secondary/tertiary scrapers."""
import pytest
from pathlib import Path

def test_cycling_ranking_parser():
    """CyclingRankingParser should extract team data."""
    from app.scraper.sources.cycling_ranking import CyclingRankingParser
    
    html = """
    <div class=\"team-info\">
        <h1>Team Name Here</h1>
        <span class=\"founded\">Founded: 1985</span>
    </div>
    """
    
    parser = CyclingRankingParser()
    data = parser.parse_team(html)
    
    assert data.get("founded_year") == 1985

from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_wayback_scraper_gets_newest():
    """WaybackScraper should fetch newest snapshot."""
    from app.scraper.sources.wayback import WaybackScraper
    
    mock_response = {
        "archived_snapshots": {
            "closest": {
                "url": "https://web.archive.org/web/20231201/http://example.com",
                "timestamp": "20231201120000"
            }
        }
    }
    
    with patch.object(WaybackScraper, "_fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        
        scraper = WaybackScraper(min_delay=0, max_delay=0)
        snapshot = await scraper.get_newest_snapshot("http://example.com")
        
        assert "20231201" in snapshot["url"]
