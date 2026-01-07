"""LLM prompts for scraper operations."""
from typing import TYPE_CHECKING, List, Optional
from app.scraper.sources.cyclingflash import ScrapedTeamData
from app.scraper.llm.lineage import LineageDecision
from app.scraper.llm.models import SponsorExtractionResult
from app.scraper.llm.model_config import PromptType

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
{predecessor_history}

SUCCESSOR TEAM:
{successor_info}
{successor_history}

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

TASK: Extract ONLY title/naming sponsor brands from a professional cycling team name.

TEAM INFORMATION:
- Team Name: {team_name}
- Season Year: {season_year}
- Country: {country_code}
- Partial DB Matches: {partial_matches}

CRITICAL INSTRUCTIONS:

1. **Extract ONLY Title/Naming Sponsors:**
   - Title sponsors are companies whose names appear IN THE TEAM NAME ITSELF
   - DO NOT extract equipment sponsors (bikes, wheels, clothing, nutrition, etc.)
   - Equipment sponsors will be handled separately by the scraper
   - Example: "Alpecin - Premier Tech" → Title sponsors: ["Alpecin", "Premier Tech"]
   - Example: "Bahrain Victorious" → Title sponsor: ["Bahrain"] ("Victorious" is a descriptor)

2. **Be Self-Critical and Conservative:**
   - If you're uncertain whether a word is a sponsor or descriptor, mark confidence lower
   - Don't guess - if the team name is ambiguous, reduce confidence to <85%
   - Example uncertainties that should reduce confidence:
     * Unclear brand boundaries ("Modern Adventure" vs "Modern" + "Adventure"?)
     * Potential descriptors ("Pro", "Cycling", "Team", "Racing")
     * Regional variants ("Lotto NL" vs "Lotto")
   - Better to have a human review an 80% confidence case than auto-approve a wrong extraction

3. **Verify Partial Matches:**
   - The partial matches from DB may be incorrect or incomplete
   - Re-verify ALL parts independently
   - Example: If DB matched "Lotto" but team is "Lotto NL Jumbo", "Lotto" alone is wrong

4. **Handle Compound Brands Correctly:**
   - DO NOT split compound brands (e.g., "Uno-X Mobility" is ONE brand)
   - DO NOT include the full team name as a sponsor (e.g., "XDS Astana Team" → ["XDS", "Astana"], NOT the full name)
   - Handle multi-word brand names (e.g., "Ineos Grenadier" not just "Ineos")

5. **Examples of TITLE Sponsors (what TO extract):**
   - "Bahrain Victorious" → ["Bahrain"]
   - "Ineos Grenadiers" → ["Ineos Grenadier"] (brand of INEOS Group)
   - "Uno-X Mobility" → ["Uno-X Mobility"]
   - "XDS Astana Team" → ["XDS", "Astana"]
   - "UAE Team Emirates XRG" → ["UAE", "Emirates", "XRG"]
   - "Alpecin - Premier Tech" → ["Alpecin", "Premier Tech"]
   - "Soudal - Quick Step" → ["Soudal", "Quick Step"]
   - "Modern Adventure Pro Cycling" → ["Modern Adventure"] (if certain it's a brand; otherwise confidence <85%)

6. **Examples of NON-title words (what NOT to extract):**
   - Team descriptors: "Victorious", "Grenadiers", "United", "Development"
   - Generic terms: "Team", "Pro", "Cycling", "Racing"
   - Equipment brands appearing outside the team name (handled by scraper)

7. **Parent Companies:**
   - Include parent company ONLY if you're certain (e.g., "Ineos Grenadier" → INEOS Group)
   - If uncertain, leave as null
   - Don't guess at corporate structures

8. **Brand Colors:**
   - Extract the primary brand color as a hex code if you know it (e.g., "#FF0000" for Coca-Cola red)
   - Only include if you're confident about the brand's official color
   - Common examples: Bahrain (#DD2A4C pink), INEOS (#1A1F5F navy), Alpecin (#009DE0 blue)
   - If uncertain or brand uses multiple colors, leave as null

9. **Confidence Scoring:**
   - 0.95-1.0: Extremely clear, well-known brands ("Bahrain Victorious", "UAE Emirates")
   - 0.90-0.94: Clear brands, minor ambiguity ("Alpecin - Premier Tech")
   - 0.85-0.89: Some uncertainty in brand boundaries or recognition
   - <0.85: Significant uncertainty - prefer human review

Provide your analysis with honest confidence assessment and clear reasoning.
If you're not certain, SAY SO in your reasoning and lower the confidence.
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
            response_model=ScrapedTeamData,
            prompt_type=PromptType.EXTRACT_TEAM_DATA
        )

    async def decide_lineage(
        self,
        predecessor_info: str,
        successor_info: str,
        predecessor_history: Optional[str] = None,
        successor_history: Optional[str] = None
    ) -> LineageDecision:
        """Decide lineage relationship between teams.
        
        Uses LLM to analyze predecessor and successor team information
        and determine the type of lineage relationship.
        
        Args:
            predecessor_info: Description of the predecessor team.
            successor_info: Description of the successor team.
            predecessor_history: Wikipedia history content for predecessor.
            successor_history: Wikipedia history content for successor.
            
        Returns:
            LineageDecision with event type, confidence, and reasoning.
        """
        # Format history sections if content exists
        pred_hist_block = f"TEAM A HISTORY:\n{predecessor_history}" if predecessor_history else ""
        succ_hist_block = f"TEAM B HISTORY:\n{successor_history}" if successor_history else ""
        
        prompt = DECIDE_LINEAGE_PROMPT.format(
            predecessor_info=predecessor_info,
            predecessor_history=pred_hist_block,
            successor_info=successor_info,
            successor_history=succ_hist_block
        )
        
        return await self._llm.generate_structured(
            prompt=prompt,
            response_model=LineageDecision,
            prompt_type=PromptType.DECIDE_LINEAGE
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
            response_model=SponsorExtractionResult,
            prompt_type=PromptType.SPONSOR_EXTRACTION
        )
