import asyncio
import logging
from app.db.database import async_session_maker
from app.models.precomputed_layout import PrecomputedLayout
from sqlalchemy import select
from app.api.precomputed_layouts import get_precomputed_layouts

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose():
    print("--- DIAGNOSTICS START ---")
    async with async_session_maker() as session:
        # 1. Check DB Content
        print("\n[DB CHECK]")
        stmt = select(PrecomputedLayout)
        result = await session.execute(stmt)
        layouts = result.scalars().all()
        print(f"Found {len(layouts)} layouts in DB.")
        
        for l in layouts:
            fp = l.data_fingerprint
            node_ids = fp.get("node_ids", []) if fp else []
            print(f"Layout Hash: {l.family_hash[:8]}...")
            print(f"  Fingerprint present: {bool(fp)}")
            print(f"  Node IDs count: {len(node_ids)}")
            if node_ids:
                print(f"  First 3 Node IDs: {node_ids[:3]}")
                print(f"  IDs are type: {type(node_ids[0])}")
        
        # 2. Check API Response Logic
        print("\n[API LOGIC CHECK]")
        # We can call the function logic or simulate it. 
        # Since I can't easily call the API endpoint handler without mocking Dependency,
        # I'll replicate the key generation logic exactly as I wrote it.
        
        response = {}
        for layout in layouts:
            fingerprint = layout.data_fingerprint or {}
            node_ids = fingerprint.get("node_ids", [])
            if not node_ids:
                print(f"  Skipping {layout.family_hash[:8]} (no IDs)")
                continue
                
            simple_key = ",".join(sorted(node_ids))
            print(f"  Generated Key: {simple_key[:50]}...")
            response[simple_key] = "data"
            
        print(f"\nAPI would return {len(response)} items.")

    print("--- DIAGNOSTICS END ---")

if __name__ == "__main__":
    asyncio.run(diagnose())
