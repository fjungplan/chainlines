"""
CLI script for discovering and registering complex families.

This is the "initial discovery" operation that scans the entire database
and registers all families that meet the complexity threshold.

Usage:
    python -m backend.scripts.discover_families [--threshold N]
"""
import asyncio
import argparse
import logging
from app.db.database import async_session_maker
from app.services.family_discovery import FamilyDiscoveryService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main(threshold: int = 20):
    """
    Discover all complex families in the database.
    
    Args:
        threshold: Minimum number of nodes to consider a family complex
    """
    logger.info(f"Starting family discovery (threshold: {threshold} nodes)...")
    
    async with async_session_maker() as session:
        service = FamilyDiscoveryService(session, complexity_threshold=threshold)
        results = await service.discover_all_families()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Discovery Summary:")
    logger.info(f"{'='*60}")
    logger.info(f"Total families registered: {len(results)}")
    
    if results:
        logger.info(f"\nRegistered families:")
        for i, family in enumerate(results, 1):
            status_icon = "✓" if family["status"] == "registered" else "↻"
            logger.info(
                f"  {status_icon} Family {i}: {family['family_hash'][:16]}... "
                f"({family['node_count']} nodes, {family['link_count']} links)"
            )
    else:
        logger.info("No complex families found.")
    
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Discover and register complex families for optimization"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=20,
        help="Minimum number of nodes to consider a family complex (default: 20)"
    )
    
    args = parser.parse_args()
    asyncio.run(main(threshold=args.threshold))
