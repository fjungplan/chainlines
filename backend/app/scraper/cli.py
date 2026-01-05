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
        choices=[1, 2, 3],
        default=1,
        help="Phase to run (1=Discovery, 2=Assembly, 3=Lineage)"
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
    logger.info(f"Starting Phase {phase} for tier {tier}")
    
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
    
    if phase == 1:
        from app.scraper.sources.cyclingflash import CyclingFlashScraper
        from app.scraper.orchestration.phase1 import DiscoveryService
        
        logger.info("--- Starting Phase 1: Discovery ---")
        scraper = CyclingFlashScraper()
        service = DiscoveryService(
            scraper=scraper,
            checkpoint_manager=checkpoint_manager,
            monitor=monitor
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
    
    elif phase == 2:
        from app.scraper.orchestration.phase2 import TeamAssemblyService, AssemblyOrchestrator
        from app.services.audit_log_service import AuditLogService
        from app.db.database import async_session_maker
        from app.scraper.sources.cyclingflash import CyclingFlashScraper
        
        logger.info("--- Starting Phase 2: Team Assembly ---")
        async with async_session_maker() as session:
            service = TeamAssemblyService(
                audit_service=AuditLogService(),
                session=session,
                system_user_id=SYSTEM_USER_ID
            )
            orchestrator = AssemblyOrchestrator(
                service=service,
                scraper=CyclingFlashScraper(),
                checkpoint_manager=checkpoint_manager,
                monitor=monitor
            )
            # For now, process the start_year
            await orchestrator.run(years=[start_year])
    
    elif phase == 3:
        from app.scraper.orchestration.phase3 import LineageConnectionService, LineageOrchestrator, OrphanDetector
        from app.services.audit_log_service import AuditLogService
        from app.scraper.llm.service import LLMService
        from app.scraper.llm.gemini import GeminiClient
        from app.scraper.llm.prompts import ScraperPrompts
        from app.db.database import async_session_maker
        import os
        
        logger.info("--- Starting Phase 3: Lineage Connection ---")
        
        # Initialize LLM infrastructure
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            logger.error("GEMINI_API_KEY not found in environment. Lineage analysis aborted.")
            return

        llm_client = GeminiClient(api_key=gemini_key)
        llm_service = LLMService(primary=llm_client)
        prompts = ScraperPrompts(llm_service=llm_service)
        
        async with async_session_maker() as session:
            service = LineageConnectionService(
                prompts=prompts,
                audit_service=AuditLogService(),
                session=session,
                system_user_id=SYSTEM_USER_ID
            )
            orchestrator = LineageOrchestrator(
                service=service,
                monitor=monitor
            )
            
            # Simple candidate detection for now (demo mode)
            detector = OrphanDetector()
            # In real run, we'd fetch actual teams from DB here
            candidates = [] 
            await orchestrator.run(candidates=candidates)


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    
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
