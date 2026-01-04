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

async def run_scraper(
    phase: int,
    tier: str,
    resume: bool,
    dry_run: bool,
    start_year: int = 2025,
    end_year: int = 1990
) -> None:
    """Run the scraper for specified phase."""
    logger.info(f"Starting Phase {phase} for tier {tier}")
    
    if dry_run:
        logger.info("DRY RUN - no database writes")
    
    checkpoint_path = Path("./scraper_checkpoint.json")
    checkpoint_manager = CheckpointManager(checkpoint_path)
    
    if not resume:
        checkpoint_manager.clear()
    
    if phase == 1:
        from app.scraper.sources.cyclingflash import CyclingFlashScraper
        from app.scraper.orchestration.phase1 import DiscoveryService
        
        scraper = CyclingFlashScraper()
        service = DiscoveryService(
            scraper=scraper,
            checkpoint_manager=checkpoint_manager
        )
        
        # Convert string tier to level if not "all"
        target_tier = int(tier) if tier != "all" else None
        
        result = await service.discover_teams(
            start_year=start_year,
            end_year=end_year,
            tier_level=target_tier
        )
        
        logger.info(f"Discovered {len(result.team_urls)} teams")
        logger.info(f"Collected {len(result.sponsor_names)} unique sponsors")
    
    elif phase == 2:
        logger.info("Phase 2: Team Assembly - Not yet implemented")
    
    elif phase == 3:
        logger.info("Phase 3: Lineage Connection - Not yet implemented")


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
