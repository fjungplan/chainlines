import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User, UserRole


async def promote(email: str):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User not found: {email}")
            return
        user.role = UserRole.ADMIN
        await session.commit()
        print(f"Promoted {email} to ADMIN")
    await engine.dispose()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.promote_user <email>")
        raise SystemExit(1)
    asyncio.run(promote(sys.argv[1]))
