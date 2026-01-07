"""Diagnostic script to analyze node/era creation issues."""
import asyncio
from app.db.database import async_session_maker
from sqlalchemy import select, func
from app.models.team import TeamNode, TeamEra

async def diagnose():
    async with async_session_maker() as session:
        # Count total nodes and eras
        node_count = await session.execute(select(func.count(TeamNode.node_id)))
        era_count = await session.execute(select(func.count(TeamEra.era_id)))
        
        print(f"\n=== SUMMARY ===")
        print(f"Total TeamNodes: {node_count.scalar()}")
        print(f"Total TeamEras: {era_count.scalar()}")
        
        # Get all nodes with their era counts
        result = await session.execute(
            select(TeamNode)
        )
        nodes = result.scalars().all()
        
        print(f"\n=== NODES BY ERA COUNT ===")
        nodes_by_era_count = {}
        for node in nodes:
            era_result = await session.execute(
                select(TeamEra).where(TeamEra.node_id == node.node_id)
            )
            eras = era_result.scalars().all()
            era_count = len(eras)
            
            if era_count not in nodes_by_era_count:
                nodes_by_era_count[era_count] = []
            nodes_by_era_count[era_count].append((node.legal_name, node.external_ids))
        
        for count in sorted(nodes_by_era_count.keys()):
            print(f"\nNodes with {count} era(s): {len(nodes_by_era_count[count])}")
            for name, ext_ids in nodes_by_era_count[count][:5]:  # Show first 5
                identity = ext_ids.get('cyclingflash_identity') if ext_ids else None
                print(f"  - {name} (identity: {identity})")
        
        # Check for duplicate team names
        print(f"\n=== POTENTIAL DUPLICATES ===")
        team_names = {}
        for node in nodes:
            base_name = node.legal_name.split(' - ')[0] if ' - ' in node.legal_name else node.legal_name
            if base_name not in team_names:
                team_names[base_name] = []
            team_names[base_name].append((node.legal_name, node.node_id, node.external_ids))
        
        for base_name, node_list in team_names.items():
            if len(node_list) > 1:
                print(f"\n{base_name}: {len(node_list)} nodes")
                for name, node_id, ext_ids in node_list:
                    identity = ext_ids.get('cyclingflash_identity') if ext_ids else None
                    print(f"  - {name}")
                    print(f"    Node ID: {node_id}")
                    print(f"    Identity: {identity}")
        
        # Check eras by year
        print(f"\n=== ERAS BY YEAR ===")
        for year in [2026, 2025]:
            result = await session.execute(
                select(TeamEra).where(TeamEra.season_year == year)
            )
            eras = result.scalars().all()
            print(f"{year}: {len(eras)} eras")

if __name__ == "__main__":
    asyncio.run(diagnose())
