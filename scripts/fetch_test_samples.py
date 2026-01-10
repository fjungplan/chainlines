import asyncio
import httpx
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target teams for test corpus
TARGETS = [
    {
        "name": "cervelo_2010",
        "url": "https://cyclingflash.com/team/cervelo-test-team-2010",
        "desc": "Missing dissolution date case"
    },
    {
        "name": "credit_agricole_2008",
        "url": "https://cyclingflash.com/team/credit-agricole-2008",
        "desc": "Complex long history"
    },
    {
        "name": "intermarche_2024",
        "url": "https://cyclingflash.com/team/intermarche-wanty-2024",
        "desc": "Tier 3 history case"
    },
    {
        "name": "metec_2024",
        "url": "https://cyclingflash.com/team/metec-solarwatt-pb-mantel-2024",
        "desc": "Standard Tier 3 team"
    }
]

OUTPUT_DIR = Path("backend/tests/fixtures/cyclingflash")

async def fetch_samples():
    """Fetch HTML samples and save to fixtures directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for target in TARGETS:
            logger.info(f"Fetching {target['name']} ({target['desc']})...")
            
            try:
                response = await client.get(target['url'])
                response.raise_for_status()
                
                # Save to file
                file_path = OUTPUT_DIR / f"{target['name']}.html"
                file_path.write_text(response.text, encoding="utf-8")
                
                logger.info(f"Saved to {file_path}")
                
                # Be nice to the server
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to fetch {target['name']}: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_samples())
