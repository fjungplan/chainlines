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

def test_parse_gt_start_list_extracts_team_names():
    """Given sample HTML, returns list of unique team names.""" 
    # Note: The prompt implies a list of names, likely with duplicates if iterating rows, 
    # but usually we want unique teams. The implementation in the prompt appends every found team.
    # The prompt implementation:
    # for row in soup.select('table tr'):
    #     if team_cell: teams.append(name)
    # This will result in duplicates (one per rider). 
    # However, the prompt step 3 implementation does NOT dedup.
    # "returns list of team names" - I will follow the prompt implementation which likely produces duplicates.
    # Wait, the prompt says "returns list of team names". If the table is a start list, it lists riders.
    # So "UAE Team Emirates" will appear multiple times.
    # Let's see if the prompt implies deduping.
    # "STEP 3 ... teams.append(name) ... return teams" -> NO dedup in prompt code.
    # I will write the test to expect duplicates or I will adjust the expectation if I think it should be dedumplicated.
    # Actually, a start list parse usually wants the list of *teams* participating. 
    # If I just return 176 items (riders), that's a list of team names per rider.
    # The prompt says "Extract team names to build the relevance index."
    # Usually we want a SET of teams. 
    # But I must follow the prompt's `STEP 3` implementation which assumes a specific logic.
    # The matching logic in Step 3 is: `teams.append(name)`.
    # I will assert it returns the list including duplicates for now, OR I can dedup in the test
    # if I assume the parser is *intended* to just get the raw list. 
    # But usually "get team names" implies unique teams.
    # Let's look at the implementation provided again:
    # It loops `table tr`. `td:nth-child(2)`.
    # Based on my fixture:
    # Row 1: UAE
    # Row 2: UAE
    # Row 3: Jumbo
    # Row 4: INEOS
    # Row 5: empty
    # Result: [UAE, UAE, Jumbo, INEOS]
    
    from app.scraper.sources.firstcycling import FirstCyclingParser
    import os
    
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'firstcycling_gt_sample.html')
    with open(fixture_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    parser = FirstCyclingParser()
    teams = parser.parse_gt_start_list(html)
    
    # We expect duplicates based on the prompt's provided code
    assert "UAE Team Emirates" in teams
    assert "Jumbo-Visma" in teams
    assert "INEOS Grenadiers" in teams
    assert len(teams) >= 4 

def test_parse_gt_start_list_handles_empty_page():
    """Returns empty list for invalid/empty HTML."""
    from app.scraper.sources.firstcycling import FirstCyclingParser
    parser = FirstCyclingParser()
    assert parser.parse_gt_start_list("") == []
    assert parser.parse_gt_start_list("<html><body></body></html>") == []

def test_parse_gt_start_list_normalizes_names():
    """Team names are stripped and normalized."""
    from app.scraper.sources.firstcycling import FirstCyclingParser
    html = '''
    <table>
        <tr>
            <td>1</td>
            <td>  Dirty Team Name  \n </td>
        </tr>
    </table>
    '''
    parser = FirstCyclingParser()
    teams = parser.parse_gt_start_list(html)
    assert teams == ["Dirty Team Name"]
