"""LLM prompts for scraper operations."""
from typing import TYPE_CHECKING, List, Optional
from app.scraper.sources.cyclingflash import ScrapedTeamData
from app.scraper.llm.lineage import LineageDecision
from app.scraper.llm.models import SponsorExtractionResult

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

If the teams are unrelated (predecessor folded without a successor, and the "successor" is a new, unrelated entity), return null for event_type.

Key considerations:
- UCI codes: Same code = likely legal transfer
- Staff continuity: >50% retained staff = strong connection
- Sponsor continuity: Same major sponsors suggest legal transfer
- Wikipedia "History" sections are the best source for spiritual succession evidence

IMPORTANT: Lineage events occur on a single date (typically season start). Time gaps should be minimal
(e.g., a team folding mid-season may have a successor starting the following season).

Return your decision with confidence score (0.0 to 1.0). If returning null for event_type, confidence should still be provided (confidence that there is NO connection).
"""

SPONSOR_EXTRACTION_PROMPT = """You are an expert in professional cycling team sponsorship and brand identification.

TASK: Extract sponsor/brand information from a professional cycling team name.

TEAM INFORMATION:
- Team Name: {team_name}
- Season Year: {season_year}
- Country: {country_code}
- Partial DB Matches: {partial_matches}

IMPORTANT INSTRUCTIONS:
1. **Re-verify ALL parts independently** - The partial matches may be incorrect
   Example: If DB matched "Lotto" but team is "Lotto NL Jumbo", "Lotto" alone is wrong

2. **Extract sponsors accurately:**
   - Return ONLY actual sponsor/brand names (companies, organizations)
   - Distinguish sponsors from team descriptors (e.g., "Victorious", "Grenadiers")
   - Handle multi-word brand names correctly (e.g., "Ineos Grenadier" not "Ineos")
   - Identify parent companies when possible

3. **Examples:**
   - "Bahrain Victorious" → sponsor: "Bahrain", descriptor: "Victorious"
   - "Ineos Grenadiers" → sponsor: "Ineos Grenadier" (brand of INEOS Group), descriptor: "s"
   - "NSN Cycling Team" → sponsor: "NSN", filler: "Cycling Team"
   - "UAE Team Emirates XRG" → sponsors: ["UAE", "Emirates", "XRG"]
   - "Lotto NL Jumbo Team" → sponsors: ["Lotto NL", "Jumbo"], filler: "Team"

4. **Parent Companies:**
   - If you know the parent company, include it (e.g., "Ineos Grenadier" → INEOS Group)
   - If uncertain, leave as null

5. **Regional Note:**
   - "Lotto NL" and "Lotto Belgium" are SEPARATE companies, not variants

Provide your analysis with high confidence and clear reasoning.
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

    async def extract_sponsors_from_name(
        self,
        team_name: str,
        season_year: int,
        country_code: Optional[str],
        partial_matches: List[str]
    ) -> SponsorExtractionResult:
        """Extract sponsor information from team name using LLM.
        
        Args:
            team_name: The full team name to analyze.
            season_year: The season year for context.
            country_code: 3-letter IOC/UCI country code (or None if unknown).
            partial_matches: List of potential brand matches from DB lookup.
            
        Returns:
            SponsorExtractionResult with sponsors, descriptors, and confidence.
        """
        prompt = SPONSOR_EXTRACTION_PROMPT.format(
            team_name=team_name,
            season_year=season_year,
            country_code=country_code or "Unknown",
            partial_matches=", ".join(partial_matches) if partial_matches else "None"
        )
        
        return await self._llm.generate_structured(
            prompt=prompt,
            response_model=SponsorExtractionResult
        )
