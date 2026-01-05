"""Wayback Machine (Archive.org) scraper."""
from typing import Dict, Any, Optional
import httpx
from app.scraper.base import BaseScraper


class WaybackScraper(BaseScraper):
    """Scraper for Archive.org Wayback Machine."""

    API_URL = "https://archive.org/wayback/available"

    def __init__(self, min_delay: float = 5.0, max_delay: float = 10.0, **kwargs):
        super().__init__(min_delay=min_delay, max_delay=max_delay, **kwargs)

    async def _fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON from URL."""
        await self._rate_limiter.wait()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            return response.json()

    async def get_newest_snapshot(self, target_url: str) -> Optional[Dict[str, Any]]:
        """Get the newest available snapshot."""
        api_url = f"{self.API_URL}?url={target_url}"
        data = await self._fetch_json(api_url)
        snapshots = data.get("archived_snapshots", {})
        closest = snapshots.get("closest")
        return closest

    async def fetch_archived_page(self, snapshot_url: str) -> str:
        """Fetch the actual archived HTML."""
        return await self.fetch(snapshot_url)
