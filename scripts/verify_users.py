
import asyncio
import os
import sys

# Add backend directory to sys.path
# Using absolute path based on known workspace structure
BACKEND_DIR = r"C:\Users\fjung\Documents\DEV\chainlines\backend"
sys.path.append(BACKEND_DIR)

# Force localhost DB connection for this script
os.environ["DATABASE_URL"] = "postgresql+asyncpg://cycling:cycling@localhost:5432/cycling_lineage"

from app.db.database import async_session_maker
from app.services.user_service import UserService
from app.schemas.user import UserAdminRead

async def verify_users():
    async with async_session_maker() as session:
        print("Fetching all users...")
        users, total = await UserService.get_users(session, limit=1000)
        print(f"Found {total} users.")
        
        for user in users:
            try:
                # Try to validate against the schema
                UserAdminRead.model_validate(user)
                print(f"User {user.display_name} ({user.user_id}): OK")
            except Exception as e:
                print(f"User {user.display_name} ({user.user_id}): FAIL - {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_users())
