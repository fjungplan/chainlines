"""Test Lotto Intermarché editions history."""
import asyncio
import re
import json
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from bs4 import BeautifulSoup

async def test_lotto_history():
    scraper = CyclingFlashScraper()
    
    print("\n" + "="*80)
    print("Lotto Intermarché (2026) - Name History")
    print("="*80)
    
    url = "/team/lotto-intermarche-2026"
    full_url = f"{scraper.BASE_URL}{url}"
    html = await scraper.fetch(full_url)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get identiy from scraper
    data = await scraper.get_team(url, 2026)
    print(f"\nCurrent Name: {data.name}")
    print(f"Identity ID: {data.team_identity_id}")
    
    # Extract and show full editions history
    scripts = soup.find_all('script')
    for script in scripts:
        script_text = script.string
        if script_text and '\\"editions\\"' in script_text:
            match = re.search(r'\\"editions\\":\{([^}]+)\}', script_text)
            if match:
                editions_content = match.group(1)
                editions_content = editions_content.replace('\\"', '"')
                editions_json = '{"editions":{' + editions_content + '}}'
                editions_data = json.loads(editions_json)
                
                editions = editions_data.get('editions', {})
                
                print(f"\n📅 Complete Name History ({len(editions)} editions):")
                print("-" * 60)
                
                # Sort by year (extract from slug)
                sorted_editions = sorted(
                    editions.items(),
                    key=lambda x: int(x[0].split('-')[-1]) if x[0].split('-')[-1].isdigit() else 0,
                    reverse=True
                )
                
                for slug, name in sorted_editions:
                    print(f"  {name}")
                
                break

if __name__ == "__main__":
    asyncio.run(test_lotto_history())
