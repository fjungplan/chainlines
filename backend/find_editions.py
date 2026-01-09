"""Simple test to find editions in any form."""
import asyncio
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from bs4 import BeautifulSoup

async def find_editions():
    scraper = CyclingFlashScraper()
    
    url = "/team/cofidis-2026"
    full_url = f"{scraper.BASE_URL}{url}"
    html = await scraper.fetch(full_url)
    
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    print(f"Total scripts: {len(scripts)}\n")
    
    for i, script in enumerate(scripts):
        if script.string and 'editions' in script.string.lower():
            print(f"Script {i} contains 'editions'")
            # Find the exact location
            idx = script.string.lower().find('editions')
            snippet = script.string[max(0, idx-20):idx+100]
            print(f"  Snippet: ...{snippet}...\n")

if __name__ == "__main__":
    asyncio.run(find_editions())
