import asyncio
import json
import os
from pathlib import Path
from app.scraper.sources.firstcycling import FirstCyclingScraper, FirstCyclingParser
from app.scraper.services.gt_relevance import GTRelevanceIndex

# Ensure we are running from the root or backend directory correctly
# If run with 'python -m backend.scripts.build_gt_index', CWD is project root.
PROGRESS_FILE = Path("./cache/gt_index_progress.json")

async def build_gt_index(start_year: int = 1998, end_year: int = 1900):
    """
    Fetch all GT start lists and build the relevance index JSON.
    """
    # Ensure cache directory exists
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    scraper = FirstCyclingScraper()
    parser = FirstCyclingParser()
    index = GTRelevanceIndex()
    
    completed_years = set()
    if PROGRESS_FILE.exists():
        try:
            completed_years = set(json.loads(PROGRESS_FILE.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"Warning: Could not load progress file: {e}")
    
    races = ["giro", "tour", "vuelta"]
    
    print(f"Starting GT Index build from {start_year} down to {end_year}...")
    
    for year in range(start_year, end_year - 1, -1):
        if year in completed_years:
            print(f"Skipping {year} (already done)")
            continue
        
        all_teams = set()
        for race in races:
            try:
                print(f"Fetching {race} {year}...")
                html = await scraper.fetch_gt_start_list(race, year)
                teams = parser.parse_gt_start_list(html)
                all_teams.update(teams)
                print(f"  {race.upper()} {year}: {len(teams)} teams")
            except Exception as e:
                print(f"  {race.upper()} {year}: FAILED - {e}")
        
        if all_teams:
            index.add_year(year, sorted(list(all_teams)))
            index.save()
            
            completed_years.add(year)
            PROGRESS_FILE.write_text(json.dumps(sorted(list(completed_years))), encoding="utf-8")
            print(f"Year {year} done: {len(all_teams)} unique teams")
        else:
            print(f"Year {year}: No teams found, skipping save for this year.")

if __name__ == "__main__":
    # For testing, we can use environment variables or just change here
    start = int(os.getenv("GT_START_YEAR", 1998))
    end = int(os.getenv("GT_END_YEAR", 1900))
    asyncio.run(build_gt_index(start, end))
