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

def test_parse_team_list_ignores_sidebar_links():
    """Parser should ignore team links in list items (li), which are usually sidebar/nav."""
    from app.scraper.sources.cyclingflash import CyclingFlashParser
    
    html = """
    <div class="container">
        <!-- Tier 1 Header -->
        <h3>UCI WorldTeam</h3>
        <div class="grid">
            <!-- Valid Div Team -->
            <div><a href="/team/valid-team-1">Valid Team 1</a></div>
        </div>
        
        <!-- Tier 2 Header -->
        <h3>UCI ProTeam</h3>
        <table>
            <!-- Valid Table Team -->
            <tr><td><a href="/team/valid-team-2">Valid Team 2</a></td></tr>
        </table>
        
        <!-- Sidebar / Random List -->
        <div class="sidebar">
            <h3>Latest Transfers</h3>
            <ul>
                <li><a href="/team/invalid-sidebar-team">Invalid Team</a></li>
            </ul>
        </div>
    </div>
    """
    
    parser = CyclingFlashParser()
    urls = parser.parse_team_list(html)
    
    assert "/team/valid-team-1" in urls
    assert "/team/valid-team-2" in urls
    assert "/team/invalid-sidebar-team" not in urls



def test_parse_team_detail_generates_team_identity_id():
    """Parser should generate stable team identity ID from Next.js data."""
    from app.scraper.sources.cyclingflash import CyclingFlashParser
    
    # Base HTML
    html = (FIXTURE_DIR / "team_detail_2024.html").read_text()
    
    # Append Next.js script with editions data
    # simulating escaped JSON inside a script string
    script_content = r'self.__next_f.push([1,"editions:{\"team-2025\":\"Team 2025\",\"team-2024\":\"Team 2024\",\"team-2023\":\"Team 2023\"}"])'
    # The parser looks for \"editions\":{...}
    # We construct it to match the regex: \\"editions\\":\{([^}]+)\}
    # Regex expects double backslashes for quotes in the source string
    
    # Let's verify the regex in python:
    # r'\\"editions\\":\{([^}]+)\}' matches '...\"editions\":{\"slug\":\"Name\"}...'
    
    # We'll stick to a simple injection that satisfies the regex
    injected_html = html + """
    <script>
    self.__next_f.push([1,"...\\\"editions\\\":{\\\"team-2025\\\":\\\"Team 2025\\\",\\\"team-2024\\\":\\\"Team 2024\\\"}..."])
    </script>
    """
    
    parser = CyclingFlashParser()
    data = parser.parse_team_detail(injected_html, season_year=2024)
    
    # Should have a team identity ID
    assert hasattr(data, 'team_identity_id')
    assert data.team_identity_id is not None
    
    # Identity should be stable (derived from team-2024 and team-2025)
    data2 = parser.parse_team_detail(injected_html, season_year=2024)
    assert data.team_identity_id == data2.team_identity_id


