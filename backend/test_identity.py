"""Test editions-based team_identity_id extraction on 4 teams."""
import asyncio
from app.scraper.sources.cyclingflash import CyclingFlashScraper

async def test_identity_extraction():
    scraper = CyclingFlashScraper()
    
    teams = [
        # Cofidis - same name across years
        ("/team/cofidis-2026", 2026),
        ("/team/cofidis-2025", 2025),
        # Alpecin - name changed (Premier Tech vs Deceuninck)
        ("/team/alpecin-premier-tech-2026", 2026),
        ("/team/alpecin-deceuninck-2025", 2025),
        # Decathlon - name changed (CMA CGM vs AG2R)
        ("/team/decathlon-cma-cgm-team-2026", 2026),
        # Israel Premier Tech / NSN - name changed
        ("/team/israel-premier-tech-2025", 2025),
    ]
    
    print("\n" + "="*80)
    print("Testing editions-based team_identity_id extraction")
    print("="*80)
    
    results = {}
    for url, year in teams:
        print(f"\nTesting: {url}")
        try:
            data = await scraper.get_team(url, year)
            print(f"  Name: {data.name}")
            print(f"  Year: {data.season_year}")
            print(f"  team_identity_id: {data.team_identity_id}")
            
            if data.team_identity_id:
                print(f"  ✅ Identity extracted!")
                # Group by identity
                if data.team_identity_id not in results:
                    results[data.team_identity_id] = []
                results[data.team_identity_id].append(data.name)
            else:
                print(f"  ❌ Identity is None!")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("Identity Groups (should show teams that share the same identity)")
    print("="*80)
    for identity, names in results.items():
        print(f"\n{identity}: {names}")

if __name__ == "__main__":
    asyncio.run(test_identity_extraction())
