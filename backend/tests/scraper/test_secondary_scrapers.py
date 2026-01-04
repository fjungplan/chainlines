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

from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_wikidata_scraper_parses_result():
    """WikidataScraper should parse mocked SPARQL response."""
    from app.scraper.sources.wikidata import WikidataScraper
    mock_response = {
        "results": {
            "bindings": [{
                "teamLabel": {"type": "literal", "value": "Team Example"},
                "foundedYear": {"type": "literal", "value": "1990"},
                "countryCode": {"type": "literal", "value": "FRA"},
                "uciCode": {"type": "literal", "value": "EXM"},
            }]
        }
    }
    with patch.object(WikidataScraper, "_run_query", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        scraper = WikidataScraper(min_delay=0, max_delay=0)
        data = await scraper.get_team("Q12345")
        assert data["team_name"] == "Team Example"
        assert data["founded_year"] == 1990
        assert data["country_code"] == "FRA"
        assert data["uci_code"] == "EXM"

def test_wikipedia_scraper_parser():
    """WikipediaScraper should extract founded year for multiple languages."""
    from app.scraper.sources.wikipedia import WikipediaParser
    
    parser = WikipediaParser()
    
    # English
    html_en = """<table class="infobox"><tr><th scope="row">Founded</th><td>1980</td></tr></table>"""
    assert parser.parse_team(html_en, "en")["founded_year"] == 1980
    
    # French
    html_fr = """<table class="infobox"><tr><th scope="row">Fondation</th><td>1995</td></tr></table>"""
    assert parser.parse_team(html_fr, "fr")["founded_year"] == 1995
    
    # German
    html_de = """<table class="infobox"><tr><th scope="row">Gründung</th><td>2001</td></tr></table>"""
    assert parser.parse_team(html_de, "de")["founded_year"] == 2001

def test_memoire_scraper_parser():
    """MemoireScraper should extract data."""
    from app.scraper.sources.memoire import MemoireParser
    
    html = """
    <div class="content">
        <h1>Team Historical</h1>
        <p><b>Année d'existence:</b> 1975 - 1980</p>
    </div>
    """
    
    parser = MemoireParser()
    data = parser.parse_team(html)
    assert data["founded_year"] == 1975

@pytest.mark.asyncio
async def test_memoire_scraper_uses_wayback():
    """MemoireScraper should use WaybackScraper to fetch content."""
    from app.scraper.sources.memoire import MemoireScraper
    from app.scraper.sources.wayback import WaybackScraper

    # Mock WaybackScraper methods
    with patch.object(WaybackScraper, "get_newest_snapshot", new_callable=AsyncMock) as mock_snap, \
         patch.object(WaybackScraper, "fetch_archived_page", new_callable=AsyncMock) as mock_fetch:
        
        # Setup mocks
        mock_snap.return_value = {"url": "http://archive.org/snapshot"}
        mock_fetch.return_value = """
        <div class="content"><p>Année d'existence: 1975</p></div>
        """
        
        scraper = MemoireScraper(min_delay=0, max_delay=0)
        data = await scraper.get_team("algo")
        
        assert data["founded_year"] == 1975
        mock_snap.assert_called_once()
        mock_fetch.assert_called_once_with("http://archive.org/snapshot")
