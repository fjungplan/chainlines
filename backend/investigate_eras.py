"""Investigate why only 28 eras were created instead of 36."""
import asyncio
from app.db.database import async_session_maker
from sqlalchemy import select, func
from app.models.team import TeamNode, TeamEra

async def investigate_era_count():
    async with async_session_maker() as session:
        # Count eras by year
        print("\n=== ERA COUNT BY YEAR ===")
        for year in [2026, 2025]:
            result = await session.execute(
                select(func.count(TeamEra.era_id)).where(TeamEra.season_year == year)
            )
            count = result.scalar()
            print(f"{year}: {count} eras")
        
        # Get all eras with their node info
        result = await session.execute(
            select(TeamEra, TeamNode)
            .join(TeamNode, TeamEra.node_id == TeamNode.node_id)
            .order_by(TeamEra.season_year.desc(), TeamNode.legal_name)
        )
        eras_with_nodes = result.all()
        
        print(f"\n=== ALL ERAS ({len(eras_with_nodes)} total) ===")
        
        # Group by year
        by_year = {2026: [], 2025: []}
        for era, node in eras_with_nodes:
            if era.season_year in by_year:
                by_year[era.season_year].append((era.registered_name, node.legal_name, node.external_ids))
        
        for year in [2026, 2025]:
            print(f"\n{year} ({len(by_year[year])} eras):")
            for reg_name, legal_name, ext_ids in by_year[year]:
                identity = ext_ids.get('cyclingflash_identity') if ext_ids else None
                print(f"  - {reg_name} (node: {legal_name}, id: {identity})")
        
        # Check for teams that should have 2 eras but only have 1
        print(f"\n=== NODES BY ERA COUNT ===")
        result = await session.execute(select(TeamNode))
        nodes = result.scalars().all()
        
        nodes_with_counts = []
        for node in nodes:
            era_result = await session.execute(
                select(func.count(TeamEra.era_id)).where(TeamEra.node_id == node.node_id)
            )
            era_count = era_result.scalar()
            nodes_with_counts.append((node.legal_name, era_count, node.external_ids))
        
        # Sort by era count
        nodes_with_counts.sort(key=lambda x: x[1])
        
        print(f"\nNodes with 1 era ({sum(1 for _, c, _ in nodes_with_counts if c == 1)}):")
        for name, count, ext_ids in nodes_with_counts:
            if count == 1:
                identity = ext_ids.get('cyclingflash_identity') if ext_ids else None
                print(f"  - {name} (id: {identity})")
        
        print(f"\nNodes with 2+ eras ({sum(1 for _, c, _ in nodes_with_counts if c >= 2)}):")
        for name, count, ext_ids in nodes_with_counts:
            if count >= 2:
                identity = ext_ids.get('cyclingflash_identity') if ext_ids else None
                print(f"  - {name}: {count} eras (id: {identity})")

if __name__ == "__main__":
    asyncio.run(investigate_era_count())
