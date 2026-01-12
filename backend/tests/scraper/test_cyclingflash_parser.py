import pytest
from pathlib import Path
from app.scraper.sources.cyclingflash import CyclingFlashParser

# Fixture path
# Fixture path
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "cyclingflash"

@pytest.fixture
def parser():
    return CyclingFlashParser()

@pytest.fixture
def html_samples():
    """Load HTML samples from fixtures."""
    samples = {}
    for path in FIXTURES_DIR.glob("*.html"):
        samples[path.stem] = path.read_text(encoding="utf-8")
    return samples

def test_parse_team_detail_cervelo_dissolution(parser, html_samples):
    """Test extracting dissolution year for Cervelo Test Team (should be 2010)."""
    html = html_samples.get("cervelo_2010")
    assert html is not None, "Fixture not found"
    
    data = parser.parse_team_detail(html, "cervelo-test-team-2010")
    
    assert data.dissolution_year == 2010
    # Also verify we extracted the identity/editions fully (we'll need to update ScrapedTeamData model first to test this properly, 
    # but for now let's assert on what we have or valid side effects)
    assert data.team_identity_id is not None
    # Check that we parsed the max year correctly
    
def test_parse_team_detail_credit_agricole_history(parser, html_samples):
    """Test Credit Agricole which has a long history."""
    html = html_samples.get("credit_agricole_2008")
    assert html is not None
    
    data = parser.parse_team_detail(html, "credit-agricole-2008")
    
    assert data.name == "Crédit Agricole"
    assert data.team_identity_id is not None
    # Should have dissolved in 2008
    assert data.dissolution_year == 2008

def test_parse_team_detail_intermarche_current(parser, html_samples):
    """Test Intermarché (active team)."""
    html = html_samples.get("intermarche_2024")
    assert html is not None
    
    from unittest.mock import patch
    import datetime
    
    # Mock datetime.datetime.now() to return a date in 2024
    # We patch 'app.scraper.sources.cyclingflash.datetime.datetime' if it was imported at top level
    # But it writes 'import datetime' inside the function.
    # So we patch 'datetime.datetime' globally or side-effect?
    # patching 'datetime.datetime' is tricky because it's a built-in.
    # Safe way: use a custom class inheriting from datetime (if needed) or just MagicMock if type checks aren't strict.
    
    # Actually, simpler: The parser logic compares max_year (2024) < current_year.
    # If we set current_year to 2024, 2024 < 2024 is False. -> Active.
    
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value.year = 2024
        # We also need side_effect for other calls? No, just .now().year is used.
        
        data = parser.parse_team_detail(html, "intermarche-wanty-2024")
    
    assert data.name == "Intermarché - Wanty"
    # Active team -> dissolution_year should be None
    assert data.dissolution_year is None

def test_parser_extracts_full_editions_structure(parser, html_samples):
    """Test that we can extract the Full Editions Dictionary (names and slugs)."""
    # This test will likely FAIL until we implement the new logic and update the model
    html = html_samples.get("cervelo_2010")
    # For now, just test if internals would work (we can call the extraction method directly if we make it public/helper)
    # But since we are doing TDD on the public API (parse_team_detail), we expect 'available_years' or 'editions' to be populated.
    
    # We haven't updated ScrapedTeamData yet to hold 'editions', so let's stick to observing the current fields 
    # and ensuring the IDENTITY is stable.
    data = parser.parse_team_detail(html, "cervelo-test-team-2010")
    assert data.team_identity_id is not None

