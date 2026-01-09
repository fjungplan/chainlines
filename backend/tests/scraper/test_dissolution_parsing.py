
import pytest
from pathlib import Path
from app.scraper.sources.cyclingflash import CyclingFlashParser

@pytest.mark.asyncio
async def test_dissolution_year_extraction():
    parser = CyclingFlashParser()
    
    # Base HTML template
    base_html = "<html><body><h1>Team Test</h1></body></html>"
    
    # Scenario 1: Team dissolves in current year (season_year == max_year)
    # Editions: 2022, 2023. Season: 2023.
    # Expected: dissolution_year = 2023
    html_dissolved = base_html + """
    <script>
    self.__next_f.push([1,"...\\\"editions\\\":{\\\"team-2022\\\":\\\"Name 2022\\\",\\\"team-2023\\\":\\\"Name 2023\\\"}..."])
    </script>
    """
    data = parser.parse_team_detail(html_dissolved, season_year=2023)
    assert data.dissolution_year == 2023, f"Expected dissolution_year 2023, got {data.dissolution_year}"

    # Scenario 2: Team continues to current year (active)
    # Editions: 2025, 2026. Current Year: 2026.
    # Expected: dissolution_year = None (Active)
    html_active = base_html + """
    <script>
    self.__next_f.push([1,"...\\\"editions\\\":{\\\"team-2025\\\":\\\"Name 2025\\\",\\\"team-2026\\\":\\\"Name 2026\\\"}..."])
    </script>
    """
    data_active = parser.parse_team_detail(html_active, season_year=2026)
    assert data_active.dissolution_year is None, f"Expected active team (None), got {data_active.dissolution_year}"

    # Scenario 3: Dissolved in recent past (2024)
    # Editions: 2023, 2024. Current Year: 2026.
    # Expected: dissolution_year = 2024
    html_recent = base_html + """
    <script>
    self.__next_f.push([1,"...\\\"editions\\\":{\\\"team-2023\\\":\\\"Name 2023\\\",\\\"team-2024\\\":\\\"Name 2024\\\"}..."])
    </script>
    """
    data_recent = parser.parse_team_detail(html_recent, season_year=2024)
    assert data_recent.dissolution_year == 2024, f"Expected dissolved 2024, got {data_recent.dissolution_year}"

    # Scenario 4: Discontinuous Eras (The "Peugeot" Case - Corrected)
    # Editions: 1912, 1957-2008. Current Scrape: 1912.
    # Expected: dissolution_year = 2008 (Max year in dropdown determines dissolution)
    # Expected: Identity ID should be derived from ALL editions, ensuring match with 2008 scrape.
    html_gap = base_html + """
    <script>
    self.__next_f.push([1,"...\\\"editions\\\":{\\\"team-1912\\\":\\\"Name 1912\\\",\\\"team-2008\\\":\\\"Name 2008\\\"}..."])
    </script>
    """
    data_gap = parser.parse_team_detail(html_gap, season_year=1912)
    assert data_gap.dissolution_year == 2008, f"Expected dissolution 2008, got {data_gap.dissolution_year}"
    assert data_gap.team_identity_id is not None
    
    # Verify ID stability: Scraping 2008 yields SAME ID
    data_gap_2008 = parser.parse_team_detail(html_gap, season_year=2008)
    assert data_gap.team_identity_id == data_gap_2008.team_identity_id, "IDs must match across gap years"

if __name__ == "__main__":
    pass
