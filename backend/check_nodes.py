import asyncio
from app.db.database import async_session_maker
from sqlalchemy import select
from app.models.team import TeamNode, TeamEra

async def check_alpecin():
    async with async_session_maker() as session:
        # Get all Alpecin nodes
        result = await session.execute(
            select(TeamNode).where(TeamNode.legal_name.like('%Alpecin%'))
        )
        nodes = result.scalars().all()
        
        print(f"\n=== Found {len(nodes)} Alpecin TeamNode(s) ===\n")
        
        for node in nodes:
            print(f"Node: {node.legal_name}")
            print(f"  ID: {node.node_id}")
            print(f"  external_ids: {node.external_ids}")
            print(f"  founding_year: {node.founding_year}")
            
            # Get eras for this node
            era_result = await session.execute(
                select(TeamEra).where(TeamEra.node_id == node.node_id)
            )
            eras = era_result.scalars().all()
            print(f"  Eras ({len(eras)}):")
            for era in eras:
                print(f"    - {era.season_year}: {era.registered_name}")
            print()

if __name__ == "__main__":
    asyncio.run(check_alpecin())
