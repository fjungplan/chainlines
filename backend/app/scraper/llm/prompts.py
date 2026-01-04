"""LLM prompts for scraper operations."""
from typing import TYPE_CHECKING
from app.scraper.sources.cyclingflash import ScrapedTeamData
from app.scraper.llm.lineage import LineageDecision

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
- Country code (3-letter IOC/UCI code, e.g., NED, GER, FRA, if determinable)
- List of sponsor names (in order of appearance/prominence)
- Previous season URL (if there's a link to previous year's page)

Return the data in the specified JSON format.
"""

DECIDE_LINEAGE_PROMPT = """
Analyze the relationship between these cycling teams and determine the lineage type.

PREDECESSOR TEAM:
{predecessor_info}

SUCCESSOR TEAM:
{successor_info}

Determine the relationship type:
- LEGAL_TRANSFER: Same legal entity, continuous UCI license (the standard season-to-season continuation)
- SPIRITUAL_SUCCESSION: No legal link, but cultural/personnel continuity (often documented in Wikipedia "History" sections)
- MERGE: Multiple predecessors combined into one successor (includes joins into an already-existing team)
- SPLIT: One predecessor split into multiple successors (includes spin-offs where the original team continues)

Key considerations:
- UCI codes: Same code = likely legal transfer
- Staff continuity: >50% retained staff = strong connection
- Sponsor continuity: Same major sponsors suggest legal transfer
- Wikipedia "History" sections are the best source for spiritual succession evidence

IMPORTANT: Lineage events occur on a single date (typically season start). Time gaps should be minimal
(e.g., a team folding mid-season may have a successor starting the following season).

Return your decision with confidence score (0.0 to 1.0).
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

    async def decide_lineage(
        self,
        predecessor_info: str,
        successor_info: str
    ) -> LineageDecision:
        """Decide lineage relationship between teams.
        
        Uses LLM to analyze predecessor and successor team information
        and determine the type of lineage relationship.
        
        Args:
            predecessor_info: Description of the predecessor team.
            successor_info: Description of the successor team.
            
        Returns:
            LineageDecision with event type, confidence, and reasoning.
        """
        prompt = DECIDE_LINEAGE_PROMPT.format(
            predecessor_info=predecessor_info,
            successor_info=successor_info
        )
        
        return await self._llm.generate_structured(
            prompt=prompt,
            response_model=LineageDecision
        )
