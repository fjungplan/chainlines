import asyncio
import sys
import os
from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.config import settings
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType

async def cleanup_duplicates():
    db_url = settings.DATABASE_URL
    if "postgres" in db_url:
        db_url = db_url.replace("@postgres", "@localhost")
    
    engine = create_async_engine(db_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # DBG: Print all links
        all_q = await session.execute(select(LineageEvent))
        all_links = all_q.scalars().all()
        print(f"Total links in DB: {len(all_links)}")
        for l in all_links:
             if "1f410b0b-fe6f-447c-9405-ca088b86b73f" in str(l.predecessor_node_id):
                 print(f" DEBUG: {l.predecessor_node_id} -> {l.successor_node_id} ({l.event_year}) Type: {l.event_type}")

        # 1. Find duplicate groups
        stmt = (
            select(
                LineageEvent.predecessor_node_id,
                LineageEvent.successor_node_id,
                LineageEvent.event_year,
                func.count().label("count")
            )
            .group_by(
                LineageEvent.predecessor_node_id,
                LineageEvent.successor_node_id,
                LineageEvent.event_year
            )
            .having(func.count() > 1)
        )
        
        result = await session.execute(stmt)
        duplicates = result.all()
        
        if not duplicates:
            print("No duplicates found.")
            return

        print(f"Found {len(duplicates)} groups with duplicate links.")
        
        total_deleted = 0
        for dup in duplicates:
            p_id, s_id, year, count = dup
            
            # Fetch all events in this group
            event_stmt = select(LineageEvent).where(
                LineageEvent.predecessor_node_id == p_id,
                LineageEvent.successor_node_id == s_id,
                LineageEvent.event_year == year
            )
            ev_res = await session.execute(event_stmt)
            events = ev_res.scalars().all()
            
            print(f"Processing group: {p_id} -> {s_id} ({year}) | Count: {len(events)}")
            
            # Decision: Keep LEGAL_TRANSFER, otherwise keep the first one
            to_keep = None
            for ev in events:
                if ev.event_type == LineageEventType.LEGAL_TRANSFER:
                    to_keep = ev
                    break
            
            if not to_keep:
                to_keep = events[0]
            
            keep_id = to_keep.event_id
            print(f"  Keeping event: {keep_id} (Type: {to_keep.event_type})")
            
            # Delete others
            delete_ids = [ev.event_id for ev in events if ev.event_id != keep_id]
            if delete_ids:
                del_stmt = delete(LineageEvent).where(LineageEvent.event_id.in_(delete_ids))
                await session.execute(del_stmt)
                total_deleted += len(delete_ids)
                print(f"  Deleted {len(delete_ids)} duplicate events.")

        await session.commit()
        print(f"\nCleanup complete. Total duplicate events deleted: {total_deleted}")

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
