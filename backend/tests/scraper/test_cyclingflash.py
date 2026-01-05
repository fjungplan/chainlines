"""Test CyclingFlash scraper."""
import pytest
from pathlib import Path
from app.scraper.llm.models import SponsorInfo

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "cyclingflash"

def test_parse_team_list_extracts_urls():
    """Parser should extract team URLs from list page."""
    from app.scraper.sources.cyclingflash import CyclingFlashParser
    
    html = (FIXTURE_DIR / "team_list_2024.html").read_text()
    parser = CyclingFlashParser()
    
    urls = parser.parse_team_list(html)
    
    assert len(urls) == 3
    assert "/team/uae-team-emirates-2024" in urls
    assert "/team/team-visma-lease-a-bike-2024" in urls

def test_parse_team_detail_extracts_data():
    """Parser should extract full team data from detail page."""
    from app.scraper.sources.cyclingflash import CyclingFlashParser
    
    html = (FIXTURE_DIR / "team_detail_2024.html").read_text()
    parser = CyclingFlashParser()
    
    data = parser.parse_team_detail(html, season_year=2024)
    
    assert data.name == "Team Visma | Lease a Bike"
    assert data.uci_code == "TJV"
    assert data.tier_level == 1
    assert data.country_code == "NED"
    # Title sponsors (Visma, Lease a Bike) + Equipment sponsors (Visma, Lease a Bike, Cervelo) -> Deduplicated
    assert isinstance(data.sponsors[0], SponsorInfo)
    assert [s.brand_name for s in data.sponsors] == ["Visma", "Lease a Bike", "Cervelo"]
    assert data.sponsors[0].parent_company is None
    assert data.previous_season_url == "/team/team-jumbo-visma-2023"
    assert data.season_year == 2024

from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_cyclingflash_scraper_gets_team():
    """CyclingFlashScraper should fetch and parse team data."""
    from app.scraper.sources.cyclingflash import CyclingFlashScraper
    
    html = (FIXTURE_DIR / "team_detail_2024.html").read_text()
    
    with patch.object(CyclingFlashScraper, 'fetch', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = html
        
        scraper = CyclingFlashScraper(min_delay=0, max_delay=0)
        data = await scraper.get_team("/team/test-2024", season_year=2024)
        
        assert data.name == "Team Visma | Lease a Bike"
        mock_fetch.assert_called_once()
