"""
Selective database reset - clears scraper data while preserving users and scraper_runs.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def reset_selective():
    # Use localhost since we're running outside Docker
    db_url = "postgresql+asyncpg://cycling:cycling@localhost:5432/cycling_lineage"
    print(f"Connecting to {db_url}")
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        print("Clearing scraper data tables (keeping users, scraper_runs, alembic_version)...")
        
        # Delete in order respecting foreign key constraints
        tables_to_clear = [
            "team_sponsor_link",      # References team_era and sponsor_brand
            "lineage_event",          # References team_node
            "team_era",               # References team_node
            "team_node",              # No dependencies from above
            "sponsor_brand",          # References sponsor_master
            "sponsor_master",         # No dependencies
            "edit_history",           # Audit log entries
        ]
        
        for table in tables_to_clear:
            print(f"  Truncating {table}...")
            await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
    
    print("Database selectively cleared. Preserved: users, scraper_runs, alembic_version")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_selective())
