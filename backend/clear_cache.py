import asyncio
from app.db.database import async_session_maker
from sqlalchemy import text

async def clear():
    async with async_session_maker() as session:
        print("Clearing precomputed_layouts...")
        await session.execute(text("DELETE FROM precomputed_layouts"))
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(clear())
