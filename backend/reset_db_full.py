
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def reset_db():
    print(f"Connecting to {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        print("Dropping all tables and types...")
        # Drop everything
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        # Note: 'public' role usually exists, 'postgres' might not
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
    
    print("Database wiped cleanly.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_db())
