
import asyncio
import os
import logging
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select, func
from dotenv import load_dotenv

# App imports - Moved to main() to allow env var patching before config load

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
MODEL_NAME = "gemini-2.5-pro" # 2026 Update: Pro model needed for deep historical context ("Sky" vs "Team Sky")

class BrandColorResponse(BaseModel):
    """LLM Response model for brand color identification."""
    hex_color: str = Field(..., description="The definitive corporate identity hex color code (e.g. #FF0000).")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0.")
    reasoning: str = Field(..., description="Brief reason for the color choice.")

async def analyze_brand(client: "GeminiClient", brand_name: str) -> Optional[BrandColorResponse]:
    """
    Ask LLM for the brand color using enhanced prompt.
    Returns BrandColorResponse object or None if error.
    """
    prompt = f"""You are analyzing a sponsor/brand from the professional road cycling industry.

Brand name: "{brand_name}"

CRITICAL: This brand appears in the context of professional road cycling team sponsorships (UCI WorldTour, ProTeams, Continental teams). Many brand names are generic (e.g., "Cube" is a German bicycle manufacturer, not a storage company; "Giant" is a Taiwanese bike brand, not a general retailer; "Sky" refers to the British broadcaster's cycling team, not general telecommunications).

Task: Identify the single most iconic corporate identity color for THIS SPECIFIC cycling-related brand.

Search and identification guidelines:
1. First, identify which company this brand refers to in cycling context:
   - For bike manufacturers: Specialized, Trek, Canyon, Pinarello, Colnago, Giant, Cube, BMC, etc.
   - For cycling apparel/components: Shimano, Campagnolo, Castelli, Santini, etc.
   - For team sponsors: Rabobank (Dutch bank), Sky (British broadcaster), Telekom (German telecom), Mapei (Italian construction), etc.
   - For nutrition/sports brands: PowerBar, SIS, Maurten, etc.

2. Verify you have the CYCLING-SPECIFIC brand:
   - Search for "{brand_name} professional cycling" or "{brand_name} cycling team"
   - Confirm historical team associations (e.g., Rabobank sponsored a WorldTour team 1996-2012)
   - Look for team jerseys, logos, and official team colors

3. Color selection criteria:
   - Use the color from their CYCLING TEAM JERSEYS or official team branding
   - Historical examples: Rabobank = Orange #FF6600, Team Telekom = Magenta #E20074, Mapei = Multi-color but purple/pink dominant
   - If multiple team sponsorships exist, use the most prominent/memorable cycling team colors
   - For bike/component brands without team sponsorship, use their corporate brand color

Response requirements:
- hex_color: Exact hex code (e.g., #FF6600) of the PRIMARY brand color IN CYCLING CONTEXT
- confidence: Score between 0.0-1.0 where:
  * 0.9-1.0 = Universally recognized single cycling team/brand color, well-documented
  * 0.7-0.89 = Strong cycling association but some ambiguity (multiple teams, era changes)
  * 0.0-0.69 = Weak/unclear cycling connection OR multiple equally-weighted colors
- reasoning: Explain which cycling entity you identified and why you chose this color

If you cannot find a clear cycling-specific match for "{brand_name}", indicate LOW confidence (<0.7)."""

    try:
        response = await client.generate_structured(
            prompt=prompt,
            response_model=BrandColorResponse,
            temperature=0.1
        )
        
        logger.info(f"Analyzed {brand_name}: {response.hex_color} (Conf: {response.confidence})")
        return response
            
    except Exception as e:
        logger.error(f"Error analyzing {brand_name}: {e}")
        return None

async def main():
    load_dotenv()
    
    # --- PROVISION LOCAL DB CONNECTION ---
    # The .env likely contains "postgres" as host (for Docker), but we are running locally.
    # We detect and patch this before the app configuration loads.
    db_url = os.getenv("DATABASE_URL", "")
    if "@postgres" in db_url:
        new_url = db_url.replace("@postgres", "@localhost")
        os.environ["DATABASE_URL"] = new_url
        logger.info(f"Local execution detected: Patched DATABASE_URL host from 'postgres' to 'localhost'")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found.")
        return

    # --- LAZY IMPORTS ---
    # Imported here so they pick up the patched os.environ["DATABASE_URL"]
    from app.db.database import async_session_maker
    from app.models.sponsor import SponsorBrand
    from app.models.enums import EditAction, EditStatus
    from app.scraper.llm.gemini import GeminiClient
    from app.services.audit_log_service import AuditLogService

    client = GeminiClient(api_key=api_key, model=MODEL_NAME)
    logger.info(f"Initialized Gemini Client ({MODEL_NAME})")

    async with async_session_maker() as session:
        # Fetch Candidates: updated_at approx created_at (within 1s)
        stmt = select(SponsorBrand).where(
            func.abs(func.extract('epoch', SponsorBrand.updated_at) - func.extract('epoch', SponsorBrand.created_at)) < 1
        )
        
        result = await session.execute(stmt)
        brands = result.scalars().all()
        
        total_brands = len(brands)
        logger.info(f"Found {total_brands} brands to analyze.")
        
        stats = {"updated": 0, "audit": 0, "fallback": 0, "error": 0}
        
        for i, brand in enumerate(brands, 1):
            logger.info(f"[{i}/{total_brands}] Processing '{brand.brand_name}'...")
            
            result = await analyze_brand(client, brand.brand_name)
            
            if not result:
                stats["error"] += 1
                continue

            if result.confidence >= 0.9:
                # 1. High Confidence: Direct Save
                brand.default_hex_color = result.hex_color
                brand.updated_at = datetime.utcnow()
                brand.last_modified_by = SYSTEM_USER_ID
                stats["updated"] += 1
                logger.info(f"-> DIRECT UPDATE: {result.hex_color}")
                
            elif result.confidence < 0.7:
                # 2. Low Confidence: Save Fallback
                brand.default_hex_color = "#000001" # Differentiate from true black
                brand.updated_at = datetime.utcnow()
                brand.last_modified_by = SYSTEM_USER_ID
                stats["fallback"] += 1
                logger.info(f"-> FALLBACK UPDATE: #000001 (Confidence {result.confidence} too low)")
                
            else:
                # 3. Medium Confidence (0.7 - 0.9): Audit Log
                # Create PENDING edit for manual review
                old_data = {
                    "brand_name": brand.brand_name,
                    "default_hex_color": brand.default_hex_color
                }
                new_data = {
                    "brand_name": brand.brand_name,
                    "default_hex_color": result.hex_color,
                    "reasoning": result.reasoning # Store reasoning in new_data or separate field if possible? 
                    # EditHistory structure is strict snapshot. We can parse it from source_url or snapshot extras?
                    # The prompt asked to "incorporate a short note... to explain its reasoning".
                    # We'll append it to source_url or handle it via a note field if create_edit allows.
                    # create_edit takes source_url. We can use that for metadata.
                }

                # Construct a "source" string with the reasoning
                # Truncate to 490 chars to fit in source_url (varchar(500))
                source_note = f"LLM Suggestion (Conf: {result.confidence}): {result.reasoning}"
                if len(source_note) > 490:
                    source_note = source_note[:487] + "..."
                
                await AuditLogService.create_edit(
                    session=session,
                    user_id=SYSTEM_USER_ID,
                    entity_type="SponsorBrand",
                    entity_id=brand.brand_id,
                    action=EditAction.UPDATE,
                    old_data=old_data,
                    new_data=new_data,
                    status=EditStatus.PENDING,
                    source_url=source_note # Hacking source_url to store reasoning for reviewer
                )
                
                # Mark as touched so we don't re-process, BUT do not change the color yet.
                # Just update timestamp? No, if we update timestamp it won't be picked up again, 
                # but the color remains old. That's what we want (pending review).
                brand.updated_at = datetime.utcnow() 
                brand.last_modified_by = SYSTEM_USER_ID
                
                stats["audit"] += 1
                logger.info(f"-> AUDIT LOG: {result.hex_color} (Reason: {result.reasoning})")

            # Commit per row
            try:
                await session.commit()
            except Exception as db_e:
                logger.error(f"DB Commit Error: {db_e}")
                await session.rollback()
            
            await asyncio.sleep(0.5) # Rate limit

        logger.info(f"Done. Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
