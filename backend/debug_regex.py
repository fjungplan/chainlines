"""Debug the regex pattern."""
import asyncio
import re
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from bs4 import BeautifulSoup

async def debug_regex():
    scraper = CyclingFlashScraper()
    
    url = "/team/cofidis-2026"
    full_url = f"{scraper.BASE_URL}{url}"
    html = await scraper.fetch(full_url)
    
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    for script in scripts:
        script_text = script.string
        if script_text and '"editions"' in script_text:
            print("Found 'editions' in script")
            
            # Show snippet
            idx = script_text.find('"editions"')
            snippet = script_text[idx:idx+200]
            print(f"\nSnippet:\n{snippet}\n")
            
            # Try regex
            pattern = r'"editions":\{([^}]+)\}'
            match = re.search(pattern, script_text)
            if match:
                print(f"✅ Regex matched!")
                print(f"Group 1: {match.group(1)[:100]}...")
            else:
                print("❌ Regex did NOT match")
                
                # Try simpler patterns
                if re.search(r'"editions":', script_text):
                    print("  - Pattern 'editions:' found")
                if re.search(r'"editions":\{', script_text):
                    print("  - Pattern 'editions:{' found")
                else:
                    print("  - Pattern 'editions:{' NOT found")
                    # Check actual chars
                    print(f"  - Chars at idx: {repr(script_text[idx:idx+20])}")
            
            break

if __name__ == "__main__":
    asyncio.run(debug_regex())
