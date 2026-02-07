import asyncio
import uuid
import sys
import os

# Add backend to path so we can import app
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlalchemy import select, or_
from app.db.database import async_session_maker
from app.models.team import TeamNode, TeamEra
from app.models.lineage import LineageEvent

async def debug_utensilnord():
    # Recreate engine for local connection
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.core.config import settings
    
    db_url = settings.DATABASE_URL
    if "postgres" in db_url:
        db_url = db_url.replace("@postgres", "@localhost")
    
    engine = create_async_engine(db_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Search for nodes
        stmt = select(TeamNode).where(
            or_(
                TeamNode.legal_name.ilike("%Utensilnord%"),
                TeamNode.legal_name.ilike("%LPR Brakes%"),
                TeamNode.node_id == uuid.UUID("7c299fe0-5b3a-4eaa-961d-615b2033f005"),
                TeamNode.node_id == uuid.UUID("b1c3f113-2928-4a14-bbfd-4e3c9caebf4c")
            )
        )
        result = await session.execute(stmt)
        nodes = result.scalars().all()
        
        print(f"Found {len(nodes)} nodes:")
        node_ids = []
        for n in nodes:
            print(f" - {n.legal_name} (ID: {n.node_id}, Start: {n.founding_year}, End: {n.dissolution_year})")
            node_ids.append(n.node_id)
        
        if not nodes:
            print("No nodes found.")
            return

        # Get all links involving these nodes
        links_stmt = select(LineageEvent).where(
            or_(
                LineageEvent.predecessor_node_id.in_(node_ids),
                LineageEvent.successor_node_id.in_(node_ids)
            )
        )
        links_result = await session.execute(links_stmt)
        links = links_result.scalars().all()
        
        print(f"\nFound {len(links)} links:")
        for l in links:
            p_name = next((n.legal_name for n in nodes if n.node_id == l.predecessor_node_id), str(l.predecessor_node_id))
            s_name = next((n.legal_name for n in nodes if n.node_id == l.successor_node_id), str(l.successor_node_id))
            print(f" - {p_name} -> {s_name} (Year: {l.event_year}, Type: {l.event_type})")

        # Get all eras for these nodes
        eras_stmt = select(TeamEra).where(TeamEra.node_id.in_(node_ids)).order_by(TeamEra.season_year)
        eras_result = await session.execute(eras_stmt)
        eras = eras_result.scalars().all()
        
        print("\nEras:")
        for e in eras:
            n_name = next((n.legal_name for n in nodes if n.node_id == e.node_id), str(e.node_id))
            print(f" - {n_name}: {e.season_year} ({e.registered_name})")

if __name__ == "__main__":
    asyncio.run(debug_utensilnord())
