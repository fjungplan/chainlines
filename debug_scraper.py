import asyncio
import logging
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from app.scraper.utils.cache import CacheManager

logging.basicConfig(level=logging.INFO)

async def debug():
    cache = CacheManager()
    scraper = CyclingFlashScraper(cache=cache)
    
    year = 2026
    print(f"Fetching {year}...")
    url = f"https://cyclingflash.com/teams/{year}"
    html = await scraper.fetch(url, force_refresh=True)
    
    print(f"HTML Length: {len(html)}")
    try:
        # print("First 500 chars:")
        # print(html[:500].encode('cp1252', errors='replace').decode('cp1252'))
        pass
    except Exception:
        pass
    
    # Test parser
    urls = scraper._parser.parse_team_list(html)
    print(f"Found {len(urls)} total team URLs")
    for u in urls[:5]:
        print(f" - {u}")

    print("\nTesting Tier Parsing:")
    tier_results = scraper._parser.parse_team_list_by_tier(html)
    for tier, t_urls in tier_results.items():
        print(f"Tier {tier}: {len(t_urls)} teams")
        if t_urls:
            print(f" - Example: {t_urls[0]}")

    # Check for specific link patterns
    if "href" in html:
        print("Checking for header-like elements...")
        # Dump some A tags to see what they look like
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        print(f"Total links found: {len(links)}")
        count = 0
        for link in links:
            href = link.get('href')
            if 'team' in href:
                print(f"Link with 'team': {href}")
                count += 1
                if count > 10: break

if __name__ == "__main__":
    asyncio.run(debug())
