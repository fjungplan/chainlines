import asyncio
from app.db.database import get_db
from app.models.team import TeamNode
from app.models.lineage import LineageEvent
from sqlalchemy import select, or_

async def find_7up_lineage():
    async for session in get_db():
        # Find 7UP/Colorado Cyclist teams
        result = await session.execute(
            select(TeamNode).where(
                or_(
                    TeamNode.name.ilike('%7UP%'),
                    TeamNode.name.ilike('%Colorado Cyclist%')
                )
            )
        )
        teams = result.scalars().all()
        
        print("=== Teams matching '7UP' or 'Colorado Cyclist' ===")
        for t in teams:
            print(f"ID: {t.node_id} | Name: {t.name} | Years: {t.founding_year}-{t.dissolution_year}")
        
        if teams:
            # Find all lineage events involving these teams
            node_ids = [t.node_id for t in teams]
            events_result = await session.execute(
                select(LineageEvent).where(
                    or_(
                        LineageEvent.source_node_id.in_(node_ids),
                        LineageEvent.target_node_id.in_(node_ids)
                    )
                )
            )
            events = events_result.scalars().all()
            
            print("\n=== Lineage Events ===")
            for e in events:
                print(f"{e.event_year}: {e.source_node_id} -> {e.target_node_id} ({e.event_type})")
        
        break

if __name__ == "__main__":
    asyncio.run(find_7up_lineage())
