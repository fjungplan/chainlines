"""LLM prompts for scraper operations."""
from typing import TYPE_CHECKING
from app.scraper.sources.cyclingflash import ScrapedTeamData

if TYPE_CHECKING:
    from app.scraper.llm.service import LLMService

EXTRACT_TEAM_DATA_PROMPT = """
Analyze the following HTML from a cycling team page and extract structured data.

HTML Content:
{html}

Season Year: {season_year}

Extract the following information:
- Team name (without year suffix)
- UCI code (3-letter code if present)
- Tier level (WorldTour, ProTeam, Continental, or null)
- Country code (2-letter ISO code if determinable)
- List of sponsor names (in order of appearance/prominence)
- Previous season URL (if there's a link to previous year's page)

Return the data in the specified JSON format.
"""


class ScraperPrompts:
    """Collection of LLM prompts for scraper operations."""
    
    def __init__(self, llm_service: "LLMService"):
        """Initialize with LLM service.
        
        Args:
            llm_service: The LLM service to use for generating structured output.
        """
        self._llm = llm_service
    
    async def extract_team_data(
        self,
        html: str,
        season_year: int
    ) -> ScrapedTeamData:
        """Extract structured team data from HTML using LLM.
        
        Args:
            html: Raw HTML content from team page.
            season_year: The season year for context.
            
        Returns:
            ScrapedTeamData with extracted information.
        """
        prompt = EXTRACT_TEAM_DATA_PROMPT.format(
            html=html[:10000],  # Limit HTML size
            season_year=season_year
        )
        
        return await self._llm.generate_structured(
            prompt=prompt,
            response_model=ScrapedTeamData
        )
