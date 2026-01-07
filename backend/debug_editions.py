"""Debug script to inspect the actual HTML structure and find the editions data."""
import asyncio
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from bs4 import BeautifulSoup

async def debug_editions_extraction():
    scraper = CyclingFlashScraper()
    
    url = "/team/cofidis-2026"
    year = 2026
    
    print(f"\nFetching: {url}")
    full_url = f"{scraper.BASE_URL}{url}"
    html = await scraper.fetch(full_url)
    
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    print(f"\nTotal script tags: {len(scripts)}")
    
    # Find scripts with __next_f
    next_f_scripts = []
    for i, script in enumerate(scripts):
        if script.string and '__next_f.push' in script.string:
            next_f_scripts.append((i, script.string))
    
    print(f"Scripts with __next_f.push: {len(next_f_scripts)}")
    
    # Check for editions
    for i, script_text in next_f_scripts:
        if '"editions"' in script_text:
            print(f"\nFound 'editions' in script {i}")
            # Show a snippet
            editions_idx = script_text.find('"editions"')
            snippet = script_text[max(0, editions_idx-50):min(len(script_text), editions_idx+500)]
            print(f"Snippet: {snippet[:300]}...")
            break
    else:
        print("\n❌ No 'editions' found in any __next_f.push script!")
        print("\nSearching for 'editions' in ALL scripts...")
        for i, script in enumerate(scripts):
            if script.string and 'editions' in script.string.lower():
                print(f"Found 'editions' in script {i} (not __next_f)")
                snippet_idx = script.string.lower().find('editions')
                snippet = script.string[max(0, snippet_idx-50):min(len(script.string), snippet_idx+200)]
                print(f"Snippet: {snippet}")

if __name__ == "__main__":
    asyncio.run(debug_editions_extraction())
