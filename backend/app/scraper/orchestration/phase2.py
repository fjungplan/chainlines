"""Phase 2: Team Node Assembly."""
import asyncio
import logging
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.models.team import TeamNode, TeamEra
from app.models.user import User
from app.scraper.sources.cyclingflash import ScrapedTeamData
from app.scraper.llm.models import SponsorInfo
from app.services.audit_log_service import AuditLogService
from app.services.edit_service import EditService
from app.schemas.edits import SponsorMasterEditRequest, SponsorBrandEditRequest
from app.models.enums import EditAction, EditStatus
from app.scraper.orchestration.workers import SourceWorker, SourceData
from app.scraper.services.wikidata import WikidataResolver, WikidataResult
from app.scraper.services.arbiter import ConflictArbiter, ArbitrationDecision, ArbitrationResult

from app.scraper.utils.sse import sse_manager
from app.scraper.utils.sponsor_normalizer import normalize_sponsor_name

if TYPE_CHECKING:
    from app.scraper.services.enrichment import TeamEnrichmentService

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.90


class EnrichedTeamData(BaseModel):
    """Enriched team data from multiple sources."""
    base_data: ScrapedTeamData
    wikidata_result: Optional[WikidataResult] = None
    wikipedia_data: Optional[SourceData] = None
    cycling_ranking_data: Optional[SourceData] = None
    memoire_data: Optional[SourceData] = None


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
        system_user_id: UUID,
        system_user: Optional[User] = None  # User object for EditService
    ):
        self._audit = audit_service
        self._session = session
        self._user_id = system_user_id
        self._system_user = system_user  # For EditService calls
    
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
        
        # Extract brand names for prominence calculation (ONLY TITLE sponsors)
        # Assuming sponsors without 'type' are TITLE (backward capability)
        title_sponsors = [
            s for s in data.sponsors 
            if getattr(s, "type", "TITLE") == "TITLE"
        ]
        title_names = [s.brand_name for s in title_sponsors]
        
        # Calculate prominence only for title sponsors
        title_prominence = ProminenceCalculator.calculate(title_names)
        
        # Build full prominence map
        # Title sponsors get their calculated share
        # Equipment sponsors get 0
        prominence_map = {}
        for s, p in zip(title_sponsors, title_prominence):
            prominence_map[s.brand_name] = p
            
        new_data = {
            "registered_name": data.name,
            "season_year": data.season_year,
            "uci_code": data.uci_code,
            "country_code": data.country_code,
            "tier_level": data.tier_level,
            "valid_from": f"{data.season_year}-01-01",
            "team_identity_id": data.team_identity_id,  # For node matching across name changes
            "sponsors": [
                {
                    "name": s_info.brand_name, 
                    "prominence": prominence_map.get(s_info.brand_name, 0),
                    "parent_company": s_info.parent_company,
                    "brand_color": s_info.brand_color,
                    "industry_sector": s_info.industry_sector,
                    "source_url": s_info.source_url
                }
                for s_info in data.sponsors
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
        legal_name: str,
        industry_sector: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> SponsorMaster:
        """Get or create sponsor master (parent company) via EditService.
        
        Creates an audit log entry for each new master.
        """
        stmt = select(SponsorMaster).where(SponsorMaster.legal_name == legal_name)
        result = await self._session.execute(stmt)
        master = result.scalar_one_or_none()
        
        if master:
            return master
        
        # Create via EditService if we have a user
        if self._system_user:
            logger.info(f"Creating SponsorMaster via EditService: {legal_name}")
            request = SponsorMasterEditRequest(
                legal_name=legal_name,
                industry_sector=industry_sector,
                source_url=source_url,
                reason="Created by Smart Scraper during team extraction"
            )
            await EditService.create_sponsor_master_edit(
                session=self._session,
                user=self._system_user,
                request=request
            )
            # Re-fetch the created master
            result = await self._session.execute(stmt)
            master = result.scalar_one_or_none()
            return master
        
        # Fallback: Direct creation (legacy path, no audit)
        logger.info(f"Creating new SponsorMaster (direct): {legal_name}")
        master = SponsorMaster(legal_name=legal_name)
        self._session.add(master)
        await self._session.flush()
        return master
    
    async def _get_or_create_brand(
        self,
        sponsor_info: SponsorInfo,
        country_code: Optional[str] = None
    ) -> SponsorBrand:
        """Get or create sponsor brand with parent company via EditService.
        
        Creates audit log entries for both master and brand.
        
        Args:
            sponsor_info: Sponsor information from LLM extraction
            country_code: Optional country code for abbreviation normalization (BEL, ITA, etc.)
        """
        # Handle parent company first
        master = None
        if sponsor_info.parent_company:
            master = await self._get_or_create_sponsor_master(
                legal_name=sponsor_info.parent_company,
                industry_sector=sponsor_info.industry_sector,
                source_url=sponsor_info.source_url
            )
        
        # Check if brand exists
        stmt = select(SponsorBrand).where(
            SponsorBrand.brand_name == sponsor_info.brand_name
        )
        if master:
            stmt = stmt.where(SponsorBrand.master_id == master.master_id)
        
        result = await self._session.execute(stmt)
        brand = result.scalar_one_or_none()
        
        if brand:
            return brand
        
        # Need a master for the brand
        if not master:
            # Apply sponsor normalization to get correct parent company
            # e.g., "FDJ United" -> parent: "Française des Jeux"
            # e.g., "Lotto" with country_code="BEL" -> parent: "Nationale Loterij"
            normalized_master_name, _ = normalize_sponsor_name(
                sponsor_info.brand_name, country_code
            )
            
            logger.info(f"Creating master for brand '{sponsor_info.brand_name}' -> '{normalized_master_name}'")
            master = await self._get_or_create_sponsor_master(
                legal_name=normalized_master_name,
                industry_sector=sponsor_info.industry_sector,
                source_url=sponsor_info.source_url
            )

        # Create brand via EditService if we have a user
        if self._system_user:
            logger.info(f"Creating SponsorBrand via EditService: {sponsor_info.brand_name}")
            request = SponsorBrandEditRequest(
                master_id=str(master.master_id),
                brand_name=sponsor_info.brand_name,
                default_hex_color=sponsor_info.brand_color or "#000000",
                source_url=sponsor_info.source_url,
                reason="Created by Smart Scraper during team extraction"
            )
            await EditService.create_sponsor_brand_edit(
                session=self._session,
                user=self._system_user,
                request=request
            )
            # Re-fetch the created brand
            stmt = select(SponsorBrand).where(
                SponsorBrand.brand_name == sponsor_info.brand_name,
                SponsorBrand.master_id == master.master_id
            )
            result = await self._session.execute(stmt)
            brand = result.scalar_one_or_none()
            return brand
        
        # Fallback: Direct creation (legacy path, no audit)
        logger.info(f"Creating SponsorBrand (direct): {sponsor_info.brand_name}")
        brand = SponsorBrand(
            brand_name=sponsor_info.brand_name,
            master=master,
            default_hex_color=sponsor_info.brand_color or "#000000",
        )
        self._session.add(brand)
        await self._session.flush()
        return brand
    
    async def _create_sponsor_links(
        self,
        team_era: TeamEra,
        sponsors: List[SponsorInfo],
        country_code: Optional[str] = None
    ):
        """Create sponsor links for team era."""
        for idx, sponsor_info in enumerate(sponsors):
            brand = await self._get_or_create_brand(sponsor_info, country_code)
            
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
        """Assemble team era from scraped data.
        
        Node matching priority:
        1. Match by team_identity_id (stable across name changes)
        2. Fall back to legal_name match
        3. Create new node if not found
        """
        node = None
        
        # Step 1: Try to find existing node by team_identity_id
        if data.team_identity_id:
            stmt = select(TeamNode).where(
                TeamNode.external_ids.op('->>')('cyclingflash_identity') == data.team_identity_id
            )
            result = await self._session.execute(stmt)
            node = result.scalar_one_or_none()
        
        # Step 2: Fall back to legal_name match (for teams without identity)
        if not node:
            stmt = select(TeamNode).where(TeamNode.legal_name == data.name)
            result = await self._session.execute(stmt)
            node = result.scalar_one_or_none()
        
        # Step 3: Create new node if not found
        if not node:
            external_ids = {}
            if data.team_identity_id:
                external_ids["cyclingflash_identity"] = data.team_identity_id
            
            node = TeamNode(
                legal_name=data.name,
                founding_year=data.season_year,
                external_ids=external_ids if external_ids else None
            )
            self._session.add(node)
            await self._session.flush()  # Get node_id assigned

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

        await self._create_sponsor_links(era, data.sponsors, data.country_code)
        return era

    async def assemble_team_enriched(self, enriched: "EnrichedTeamData") -> TeamEra:
        """Assemble team era from enriched data, including Wikipedia history.
        
        Args:
            enriched: EnrichedTeamData containing base_data and optional wikipedia_data
            
        Returns:
            Created TeamEra with Wikipedia history stored
        """
        data = enriched.base_data
        node = None
        
        # Step 1: Try to find existing node by team_identity_id
        if data.team_identity_id:
            stmt = select(TeamNode).where(
                TeamNode.external_ids.op('->>')('cyclingflash_identity') == data.team_identity_id
            )
            result = await self._session.execute(stmt)
            node = result.scalar_one_or_none()
        
        # Step 2: Fall back to legal_name match
        if not node:
            stmt = select(TeamNode).where(TeamNode.legal_name == data.name)
            result = await self._session.execute(stmt)
            node = result.scalar_one_or_none()
        
        # Step 3: Create new node if not found
        if not node:
            external_ids = {}
            if data.team_identity_id:
                external_ids["cyclingflash_identity"] = data.team_identity_id
            
            node = TeamNode(
                legal_name=data.name,
                founding_year=data.season_year,
                external_ids=external_ids if external_ids else None
            )
            self._session.add(node)
            await self._session.flush()

        # Extract Wikipedia history if available
        wiki_history = None
        if enriched.wikipedia_data:
            wiki_history = enriched.wikipedia_data.history_text

        era = TeamEra(
            node=node,
            season_year=data.season_year,
            valid_from=date(data.season_year, 1, 1),
            registered_name=data.name,
            uci_code=data.uci_code,
            country_code=data.country_code,
            tier_level=data.tier_level,
            wikipedia_history_content=wiki_history  # Store Wikipedia history
        )
        self._session.add(era)

        await self._create_sponsor_links(era, data.sponsors, data.country_code)
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
        session: AsyncSession,
        monitor: Optional[ScraperStatusMonitor] = None,
        enricher: Optional["TeamEnrichmentService"] = None,
        wikidata_resolver: Optional[WikidataResolver] = None,
        workers: Optional[list[SourceWorker]] = None,
        arbiter: Optional[ConflictArbiter] = None,
    ):
        self._service = service
        self._scraper = scraper
        self._checkpoint = checkpoint_manager
        self._session = session
        self._monitor = monitor
        self._enricher = enricher
        self._resolver = wikidata_resolver
        self._workers = workers or []
        self._arbiter = arbiter
        self._run_id = str(monitor.run_id) if monitor else None

    async def _emit_progress(self, current: int, total: int):
        """Emit progress event via SSE."""
        if not self._run_id:
            return
        await sse_manager.emit(self._run_id, "progress", {
            "phase": 2,
            "current": current,
            "total": total,
            "percent": round(current / total * 100, 1)
        })

    async def _emit_decision(self, team_name: str, decision: ArbitrationResult):
        """Emit arbitration decision event via SSE."""
        if not self._run_id:
            return
        await sse_manager.emit(self._run_id, "decision", {
            "type": "CONFLICT_RESOLUTION",
            "subject": team_name,
            "outcome": decision.decision.value,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning
        })

    def _has_date_conflict(self, base_data: ScrapedTeamData, cr_data: SourceData) -> bool:
        """Check for significant date conflicts."""
        if not cr_data or not cr_data.dissolved_year:
            return False
        
        # Conflict if dissolved year is more than 1 year away from season year
        # e.g. Scraped 2024, but CR says dissolved 2020 -> Conflict
        if abs(base_data.season_year - cr_data.dissolved_year) > 1:
            return True
            
        return False

    async def _create_pending_edit(self, enriched: EnrichedTeamData, decision: ArbitrationResult):
        """Create a PENDING edit for human review."""
        logger.warning(f"Creating PENDING edit for {enriched.base_data.name}: {decision.reasoning}")
        
        # Use existing service to create edit but force PENDING status via low confidence
        await self._service.create_team_era(enriched.base_data, confidence=decision.confidence)

    async def _handle_split(self, enriched: EnrichedTeamData, decision: ArbitrationResult):
        """Handle strict split decision."""
        logger.info(f"Split detected for {enriched.base_data.name}: {decision.suggested_lineage_type}")
        # TODO: Implement full split logic (creating new Node/LineageEvent)
        # For now, we Log and do NOT assemble the era on the old node.
        pass

    async def _process_team(self, enriched: EnrichedTeamData):
        """Process a single enriched team, handling conflicts."""
        cr_data = enriched.cycling_ranking_data
        
        if self._arbiter and cr_data and self._has_date_conflict(enriched.base_data, cr_data):
            logger.info(f"Conflict detected for {enriched.base_data.name}. Invoking arbiter...")
            
            history_text = enriched.wikipedia_data.history_text if enriched.wikipedia_data else None
            decision = await self._arbiter.decide(
                enriched.base_data,
                cr_data,
                history_text
            )
            
            logger.info(f"Arbiter decision: {decision.decision.value} (Confidence: {decision.confidence})")
            
            # Hook for monitoring/testing if needed
            if self._monitor and hasattr(self._monitor, 'emit_decision'):
                 await self._monitor.emit_decision(decision)
            
            # Emit SSE event
            await self._emit_decision(enriched.base_data.name, decision)
            
            if decision.decision == ArbitrationDecision.PENDING:
                await self._create_pending_edit(enriched, decision)
                return
            
            if decision.decision == ArbitrationDecision.SPLIT:
                await self._handle_split(enriched, decision)
                return
                
        # MERGE or No Conflict -> Proceed to assembly with enriched data
        await self._service.assemble_team_enriched(enriched)

    def _get_url_for_worker(
        self, 
        source_name: str, 
        wd_result: Optional[WikidataResult]
    ) -> Optional[str]:
        """Extract appropriate URL for a worker from Wikidata result.
        
        Args:
            source_name: Name of the source worker
            wd_result: WikidataResult containing sitelinks
            
        Returns:
            URL string if available, None otherwise
        """
        if not wd_result:
            return None
        
        # Map worker source names to Wikidata sitelink codes
        if source_name == "wikipedia":
            return wd_result.sitelinks.get("en")  # EN Wikipedia
        elif source_name == "cyclingranking":
            # CyclingRanking URL resolution needs more logic
            # For now, returning None as it requires QID->URL mapping
            return None
        elif source_name == "memoire":
            # Memoire URLs would come from sitelinks if available
            return wd_result.sitelinks.get("fr")  # FR Wikipedia as proxy
        
        return None
    
    async def _enrich_team(
        self, 
        base_data: ScrapedTeamData
    ) -> EnrichedTeamData:
        """Enrich team data by calling Wikidata and fanning out to workers.
        
        Args:
            base_data: Base scraped team data from CyclingFlash
            
        Returns:
            EnrichedTeamData with results from all sources
        """
        
        # Step 1: Resolve via Wikidata
        wd_result = None
        if self._resolver:
            wd_result = await self._resolver.resolve(base_data.name)
        
        # Step 2: Fan out to workers in parallel
        tasks = []
        worker_map = {}  # Track which task corresponds to which worker
        
        for worker in self._workers:
            url = self._get_url_for_worker(worker.source_name, wd_result)
            if url:
                task = worker.fetch(url)
                tasks.append(task)
                worker_map[len(tasks) - 1] = worker.source_name
        
        # Execute all worker fetches in parallel
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Step 3: Collect results into EnrichedTeamData
        enriched = EnrichedTeamData(
            base_data=base_data,
            wikidata_result=wd_result
        )
        
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Worker {worker_map.get(idx)} failed: {result}")
                continue
            
            source_name = worker_map.get(idx)
            if source_name == "wikipedia":
                enriched.wikipedia_data = result
            elif source_name == "cyclingranking":
                enriched.cycling_ranking_data = result
            elif source_name == "memoire":
                enriched.memoire_data = result
        
        return enriched


    async def run(self, years: List[int]) -> None:
        """Process the team queue for specified years."""
        checkpoint = self._checkpoint.load()
        if not checkpoint or not checkpoint.team_queue:
            logger.warning("Phase 2: No teams in queue to process. Run Phase 1 first.")
            return

        queue = checkpoint.team_queue
        logger.info(f"Phase 2: Starting Assembly for {len(queue)} team-year pairs")
        
        for i, (url, year) in enumerate(queue, 1):  # Unpack (URL, year) tuples
            if self._monitor:
                await self._monitor.check_status()
            
            await self._emit_progress(i, len(queue))
            
            # Each queue item is now a (url, year) tuple from Phase 1
            # so we process each URL for its specific year
            
            logger.info(f"Team {i}/{len(queue)}: Assembling '{url}' for {year}")
            try:
                # Step 1: Scrape base data from CyclingFlash
                base_data = await self._scraper.get_team(url, year)
                
                # Step 2: Enrich with multi-source data (Wikidata, Wikipedia, etc.)
                enriched = await self._enrich_team(base_data)
                
                # Step 3: Apply sponsor enrichment (if available)
                if self._enricher:
                    enriched.base_data = await self._enricher.enrich_team_data(enriched.base_data)
                
                # Step 4: Process (handles conflicts, arbiter, assembly)
                await self._process_team(enriched)
                
                # Commit transaction for this team
                await self._session.commit()
            except Exception as e:
                logger.error(f"    - Failed to assemble {url}: {e}")
                # Rollback the session to clear error state and allow next team to process
                await self._session.rollback()
                continue

        logger.info("Phase 2: Assembly complete.")
