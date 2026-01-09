"""Debug the JSON extraction logic."""
import asyncio
from app.scraper.sources.cyclingflash import CyclingFlashScraper
from bs4 import BeautifulSoup
import json

async def debug_json_parsing():
    scraper = CyclingFlashScraper()
    
    url = "/team/cofidis-2026"
    year = 2026
    
    print(f"\nFetching: {url}")
    full_url = f"{scraper.BASE_URL}{url}"
    html = await scraper.fetch(full_url)
    
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    for script in scripts:
        script_text = script.string
        if script_text and '"editions":{' in script_text:
            print("\n✅ Found editions in script!")
            
            # Try to extract
            editions_start = script_text.find('"editions":{')
            print(f"editions_start index: {editions_start}")
            
            if editions_start != -1:
                # Show snippet around it
                snippet = script_text[editions_start:editions_start+300]
                print(f"\nSnippet:\n{snippet}\n")
                
                # Try brace counting
                brace_count = 1  # Start with 1 for the opening brace
                editions_end = editions_start + len('"editions":{')
                
                for i in range(editions_end, min(editions_end + 1000, len(script_text))):
                    if script_text[i] == '{':
                        brace_count += 1
                    elif script_text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            editions_end = i
                            print(f"Found closing brace at index: {i}")
                            break
                
                # Extract
                editions_json = script_text[editions_start:editions_end+1]
                editions_json = '{' + editions_json + '}'
                
                print(f"\nExtracted JSON (first 200 chars):\n{editions_json[:200]}\n")
                
                # Try to parse
                try:
                    editions_data = json.loads(editions_json)
                    slugs = list(editions_data.get('editions', {}).keys())
                    print(f"✅ Parsed successfully! Found {len(slugs)} slugs")
                    print(f"First 5 slugs: {slugs[:5]}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"Error at position: {e.pos}")
                    if e.pos:
                        print(f"Context: {editions_json[max(0, e.pos-50):e.pos+50]}")
            
            break

if __name__ == "__main__":
    asyncio.run(debug_json_parsing())
