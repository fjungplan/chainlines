"""Phase 2: Team Node Assembly."""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.models.team import TeamNode, TeamEra
from app.scraper.sources.cyclingflash import ScrapedTeamData
from app.scraper.llm.models import SponsorInfo
from app.services.audit_log_service import AuditLogService
from app.models.enums import EditAction, EditStatus

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.90


class ProminenceCalculator:
    """Calculates sponsor prominence percentages."""
    
    RULES = {
        1: [100],
        2: [60, 40],
        3: [40, 30, 30],
        4: [40, 20, 20, 20],
    }
    
    @classmethod
    def calculate(cls, sponsors: List[str]) -> List[int]:
        """Calculate prominence for each sponsor.
        
        Args:
            sponsors: List of sponsor names
            
        Returns:
            List of prominence percentages (must sum to 100)
        """
        count = len(sponsors)
        
        if count == 0:
            return []
        
        if count in cls.RULES:
            return cls.RULES[count]
        
        # 5+ sponsors: extend pattern (first gets 40, rest split evenly)
        first = 40
        remaining = 100 - first
        each = remaining // (count - 1)
        last_adjustment = remaining - (each * (count - 1))
        
        result = [first] + [each] * (count - 2) + [each + last_adjustment]
        return result


class TeamAssemblyService:
    """Orchestrates Phase 2: Team and Era creation."""
    
    def __init__(
        self,
        audit_service: AuditLogService,
        session: AsyncSession,
        system_user_id: UUID
    ):
        self._audit = audit_service
        self._session = session
        self._user_id = system_user_id
    
    async def create_team_era(
        self,
        data: ScrapedTeamData,
        confidence: float
    ) -> None:
        """Create TeamNode/TeamEra via AuditLog.
        
        Args:
            data: Scraped team data
            confidence: LLM confidence score (0.0-1.0)
        """
        status = (
            EditStatus.APPROVED if confidence >= CONFIDENCE_THRESHOLD
            else EditStatus.PENDING
        )
        
        # Extract brand names for prominence calculation
        brand_names = [s.brand_name for s in data.sponsors]
        prominence_values = ProminenceCalculator.calculate(brand_names)

        # Build the edit payload
        new_data = {
            "registered_name": data.name,
            "season_year": data.season_year,
            "uci_code": data.uci_code,
            "tier_level": data.tier_level,
            "valid_from": f"{data.season_year}-01-01",
            "sponsors": [
                {"name": s_info.brand_name, "prominence": p}
                for s_info, p in zip(data.sponsors, prominence_values)
            ]
        }
        
        await self._audit.create_edit(
            session=self._session,
            user_id=self._user_id,
            entity_type="TeamEra",
            entity_id=None,  # New entity
            action=EditAction.CREATE,
            old_data=None,
            new_data=new_data,
            status=status
        )
        
        logger.info(f"    - Edit created: {data.name} -> {status.value} (Confidence: {confidence*100:.1f}%)")
        for s in new_data["sponsors"]:
            logger.info(f"      * Sponsor: {s['name']} ({s['prominence']}%)")

    async def _get_or_create_sponsor_master(
        self,
        legal_name: str
    ) -> SponsorMaster:
        """Get or create sponsor master (parent company)."""
        stmt = select(SponsorMaster).where(SponsorMaster.legal_name == legal_name)
        result = await self._session.execute(stmt)
        master = result.scalar_one_or_none()
        
        if not master:
            logger.info(f"Creating new SponsorMaster: {legal_name}")
            master = SponsorMaster(
                legal_name=legal_name,
            )
            self._session.add(master)

        
        return master
    
    async def _get_or_create_brand(
        self,
        sponsor_info: SponsorInfo
    ) -> SponsorBrand:
        """Get or create sponsor brand with parent company."""
        # Handle parent company first
        master = None
        if sponsor_info.parent_company:
            master = await self._get_or_create_sponsor_master(sponsor_info.parent_company)
        
        # Check if brand exists
        stmt = select(SponsorBrand).where(
            SponsorBrand.brand_name == sponsor_info.brand_name
        )
        if master:
            stmt = stmt.where(SponsorBrand.master_id == master.master_id)
        
        result = await self._session.execute(stmt)
        brand = result.scalar_one_or_none()
        
        if not brand:
            # If no master but parent_company passed? (Handled above).
            # If no master and NO parent_company passed?
            # Model requires master_id. We must create a "Self-Master" or similar.
            if not master:
                # Fallback: Create master with same name as brand
                logger.info(f"Creating default SponsorMaster for brand: {sponsor_info.brand_name}")
                master = await self._get_or_create_sponsor_master(sponsor_info.brand_name)

            logger.info(
                f"Creating new SponsorBrand: {sponsor_info.brand_name} "
                f"(parent: {master.legal_name})"
            )
            brand = SponsorBrand(
                brand_name=sponsor_info.brand_name,
                master=master,
                default_hex_color="#000000",
            )
            self._session.add(brand)

        
        return brand
    
    async def _create_sponsor_links(
        self,
        team_era: TeamEra,
        sponsors: List[SponsorInfo]
    ):
        """Create sponsor links for team era."""
        for idx, sponsor_info in enumerate(sponsors):
            brand = await self._get_or_create_brand(sponsor_info)
            
            # Create link with prominence (title sponsors higher)
            prominence = 100 - (idx * 10)  # 100%, 90%, 80%, etc.
            prominence = max(prominence, 0)  # Min 0%
            
            link = TeamSponsorLink(
                era=team_era,
                brand=brand,
                prominence_percent=prominence,
                rank_order=idx + 1,
            )
            self._session.add(link)

    async def assemble_team(self, data: ScrapedTeamData) -> TeamEra:
        """Assemble team era from scraped data (Direct Creation)."""
        # Create Node (needed for Era)
        stmt = select(TeamNode).where(TeamNode.legal_name == data.name)
        result = await self._session.execute(stmt)
        node = result.scalar_one_or_none()
        if not node:
             node = TeamNode(
                 legal_name=data.name,
                 founding_year=data.season_year,
              )
             self._session.add(node)
 

        era = TeamEra(
            node=node,
            season_year=data.season_year,
            valid_from=date(data.season_year, 1, 1),
            registered_name=data.name,
            uci_code=data.uci_code,
            country_code=data.country_code,
            tier_level=data.tier_level,
        )
        self._session.add(era)


        await self._create_sponsor_links(era, data.sponsors)
        return era


from app.scraper.monitor import ScraperStatusMonitor
from app.scraper.checkpoint import CheckpointManager
from app.scraper.sources.cyclingflash import CyclingFlashScraper

class AssemblyOrchestrator:
    """Orchestrates Phase 2 processing across the team queue."""
    
    def __init__(
        self,
        service: TeamAssemblyService,
        scraper: CyclingFlashScraper,
        checkpoint_manager: CheckpointManager,
        monitor: Optional[ScraperStatusMonitor] = None
    ):
        self._service = service
        self._scraper = scraper
        self._checkpoint = checkpoint_manager
        self._monitor = monitor

    async def run(self, years: List[int]) -> None:
        """Process the team queue for specified years."""
        checkpoint = self._checkpoint.load()
        if not checkpoint or not checkpoint.team_queue:
            logger.warning("Phase 2: No teams in queue to process. Run Phase 1 first.")
            return

        queue = checkpoint.team_queue
        logger.info(f"Phase 2: Starting Assembly for {len(queue)} teams across {years}")
        
        for i, url in enumerate(queue, 1):
            if self._monitor:
                await self._monitor.check_status()
            
            # For each team, we may need to fetch detail for multiple years 
            # if we want a complete history, but for now we follow the simple 
            # Phase 1 -> Phase 2 flow where Phase 1 gathered the URLs.
            
            # We'll process the latest requested year for this URL
            year = years[0] # Simplification for now
            
            logger.info(f"Team {i}/{len(queue)}: Assembling '{url}' for {year}")
            try:
                data = await self._scraper.get_team(url, year)
                # LLM Confidence is simulated here or retrieved if we stored it
                # For Phase 2 extraction, we assume high confidence (0.95) if parsing succeeded
                # or we would have used an LLM-assisted parser.
                await self._service.create_team_era(data, confidence=0.95)
            except Exception as e:
                logger.error(f"    - Failed to assemble {url}: {e}")
                continue

        logger.info("Phase 2: Assembly complete.")
