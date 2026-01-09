"""Smart Scraper CLI interface."""
import argparse
import asyncio
import logging
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Smart Scraper - Cycling team data ingestion"
    )
    
    parser.add_argument(
        "--phase",
        type=int,
        choices=[0, 1, 2, 3],
        default=1,
        help="Phase to run (0=All, 1=Discovery, 2=Assembly, 3=Lineage)"
    )

    parser.add_argument(
        "--tier",
        type=str,
        choices=["1", "2", "3", "all"],
        default="1",
        help="Team tier level to process (1=WorldTour/GS1, 2=ProTeam/GS2, 3=Continental/GS3)"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without writing to database"
    )

    parser.add_argument(
        "--start-year",
        type=int,
        default=2025,
        help="Start year for scraping (default: current year)"
    )

    parser.add_argument(
        "--end-year",
        type=int,
        default=1990,
        help="End year for scraping (default: 1990)"
    )

    parser.add_argument(
        "--log-file",
        type=str,
        nargs='?',
        const="auto",
        help="Path to save log output. Defaults to scraper_{timestamp}.log if flag is present but no path provided"
    )

    return parser.parse_args(args)


from pathlib import Path
from app.scraper.checkpoint import CheckpointManager
from app.scraper.monitor import ScraperStatusMonitor
import uuid

async def run_scraper(
    phase: int,
    tier: str,
    resume: bool,
    dry_run: bool,
    start_year: int = 2025,
    end_year: int = 1990,
    run_id: Optional[uuid.UUID] = None
) -> None:
    """Run the scraper for specified phase."""
    logger.info(f"Starting Scraper (Phase: {phase}, Tier: {tier}, Range: {start_year}-{end_year})")

    if dry_run:
        logger.info("DRY RUN - no database writes")

    checkpoint_path = Path("./scraper_checkpoint.json")
    checkpoint_manager = CheckpointManager(checkpoint_path)

    # Static system user ID
    SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

    # Initialize monitor if run_id provided
    monitor = ScraperStatusMonitor(run_id) if run_id else None

    if not resume:
        checkpoint_manager.clear()
        logger.info("Fresh run - cleared checkpoint")
    else:
        logger.info("Resuming from last checkpoint")

    # Unified imports for core services
    from app.scraper.llm.service import LLMService
    from app.scraper.llm.gemini import GeminiClient
    from app.scraper.llm.deepseek import DeepseekClient
    from app.scraper.llm.prompts import ScraperPrompts
    from app.db.database import async_session_maker
    from app.scraper.utils.cache import CacheManager
    from app.scraper.services.gt_relevance import GTRelevanceIndex
    from app.scraper.services.wikidata import WikidataResolver
    from app.scraper.base.scraper import BaseScraper
    from app.scraper.orchestration.workers import WikipediaWorker, CyclingRankingWorker, MemoireWorker
    from app.scraper.services.arbiter import ConflictArbiter
    from dotenv import load_dotenv
    import os

    # Load environment variables (for local execution)
    load_dotenv()

    # Initialize Cache
    cache = CacheManager()

    # Initialize GT Index
    gt_index = GTRelevanceIndex()

    # Initialize Wikidata Resolver
    wikidata_resolver = WikidataResolver(cache=cache)

    # Initialize Workers
    base_scraper = BaseScraper(cache=cache)
    workers = [
        WikipediaWorker(base_scraper),
        CyclingRankingWorker(base_scraper),
        # MemoireWorker(base_scraper), # Disable until logic is fixed
    ]

    # Initialize LLM infrastructure (Shared across phases)
    gemini_key = os.getenv("GEMINI_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    clients = {}

    if gemini_key:
        clients["gemini-2.5-flash"] = GeminiClient(api_key=gemini_key, model="gemini-2.5-flash")
        clients["gemini-2.5-pro"] = GeminiClient(api_key=gemini_key, model="gemini-2.5-pro")

    if deepseek_key:
        clients["deepseek-chat"] = DeepseekClient(api_key=deepseek_key, model="deepseek-chat")
        clients["deepseek-reasoner"] = DeepseekClient(api_key=deepseek_key, model="deepseek-reasoner")

    llm_service = None
    llm_prompts = None

    if clients:
        # Initialize service with all available clients
        llm_service = LLMService(clients=clients)
        llm_prompts = ScraperPrompts(llm_service=llm_service)
        logger.info(f"LLM Service initialized with models: {', '.join(clients.keys())}")
    else:
        logger.warning("No LLM API keys found (GEMINI_API_KEY or DEEPSEEK_API_KEY). LLM-based operations will be disabled.")

    # Initialize Arbiter
    arbiter = ConflictArbiter(llm_service) if llm_service else None

    async with async_session_maker() as session:
        # Phase 1: Discovery
        if phase in (0, 1):
            from app.scraper.sources.cyclingflash import CyclingFlashScraper
            from app.scraper.orchestration.phase1 import DiscoveryService

            logger.info("--- Starting Phase 1: Discovery ---")
            scraper = CyclingFlashScraper(cache=cache)
            service = DiscoveryService(
                scraper=scraper,
                gt_index=gt_index,
                checkpoint_manager=checkpoint_manager,
                monitor=monitor,
                session=session,
                llm_prompts=llm_prompts
            )

            # Convert string tier to level if not "all"
            target_tier = int(tier) if tier != "all" else None

            result = await service.discover_teams(
                start_year=start_year,
                end_year=end_year,
                tier_level=target_tier
            )

            logger.info(f"Phase 1 Complete: Discovered {len(result.team_urls)} teams")
            logger.info(f"Collected {len(result.sponsor_names)} unique sponsors for resolution")

        # Phase 2: Assembly
        if phase in (0, 2):
            from app.scraper.orchestration.phase2 import TeamAssemblyService, AssemblyOrchestrator
            from app.services.audit_log_service import AuditLogService
            from app.scraper.sources.cyclingflash import CyclingFlashScraper
            from app.models.user import User

            from app.scraper.services.enrichment import TeamEnrichmentService

            logger.info("--- Starting Phase 2: Team Assembly ---")
            
            # Fetch the scraper User object for EditService calls
            system_user = await session.get(User, SYSTEM_USER_ID)
            if not system_user:
                logger.warning("Scraper user not found, sponsor edits will not create audit entries")
            else:
                # Refresh to ensure all columns are loaded (prevents MissingGreenlet in EditService)
                await session.refresh(system_user)

            enricher = None
            if llm_prompts:
                enricher = TeamEnrichmentService(session, llm_prompts)

            service = TeamAssemblyService(
                audit_service=AuditLogService(),
                session=session,
                system_user_id=SYSTEM_USER_ID,
                system_user=system_user  # Pass User object for EditService
            )
            orchestrator = AssemblyOrchestrator(
                service=service,
                scraper=CyclingFlashScraper(cache=cache),
                checkpoint_manager=checkpoint_manager,
                session=session,
                wikidata_resolver=wikidata_resolver,
                workers=workers,
                arbiter=arbiter,
                monitor=monitor,
                enricher=enricher
            )
            
            # Process the year range
            years = list(range(start_year, end_year - 1, -1))
            await orchestrator.run(years=years)

        # Phase 3: Lineage (now includes Phase 2.5 Wikipedia enrichment)
        if phase in (0, 3):
            from app.scraper.orchestration.enrichment import NodeEnrichmentService
            from app.scraper.orchestration.phase3 import (
                BoundaryNodeDetector, LineageExtractor, LineageOrchestrator
            )
            from app.services.audit_log_service import AuditLogService

            logger.info("--- Starting Phase 2.5: Wikipedia Enrichment ---")
            
            # Phase 2.5: Enrich nodes with Wikipedia content
            enrichment_service = NodeEnrichmentService(
                session=session,
                scraper=base_scraper,
                wikidata_resolver=wikidata_resolver
            )
            enriched_count = await enrichment_service.enrich_all_nodes()
            logger.info(f"Phase 2.5 complete: enriched {enriched_count} nodes")

            logger.info("--- Starting Phase 3: Lineage Detection ---")

            if not llm_prompts:
                logger.error("LLM prompts not initialized (missing API key). Lineage analysis aborted.")
                return

            # Initialize new Phase 3 components
            detector = BoundaryNodeDetector(session=session)
            extractor = LineageExtractor(
                prompts=llm_prompts,
                audit_service=AuditLogService(),
                session=session,
                system_user_id=SYSTEM_USER_ID
            )
            orchestrator = LineageOrchestrator(
                detector=detector,
                extractor=extractor,
                session=session,
                monitor=monitor
            )

            # Analyze each year transition
            years = list(range(start_year, end_year - 1, -1))
            for i in range(len(years) - 1):
                transition_year = years[i + 1]  # e.g., 2025 for 2025->2026 transition
                await orchestrator.run(transition_year=transition_year)


def main() -> None:
    """CLI entry point."""
    args = parse_args()

    log_file = args.log_file
    if log_file:
        from pathlib import Path
        if log_file == "auto":
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = str(log_dir / f"scraper_{timestamp}.log")
        else:
            # Ensure the directory for custom path exists
            log_path = Path(log_file)
            if log_path.parent:
                log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    
    asyncio.run(run_scraper(
        phase=args.phase,
        tier=args.tier,
        resume=args.resume,
        dry_run=args.dry_run,
        start_year=args.start_year,
        end_year=args.end_year
    ))


if __name__ == "__main__":
    main()
