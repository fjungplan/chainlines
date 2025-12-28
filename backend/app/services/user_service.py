from typing import List, Optional, Tuple
import uuid
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class UserService:
    @staticmethod
    async def get_users(
        session: AsyncSession, 
        skip: int = 0, 
        limit: int = 50, 
        search_query: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """
        Get paginated users with optional search.
        Returns (users, total_count).
        """
        query = select(User)
        
        if search_query:
            term = f"%{search_query}%"
            query = query.where(
                or_(
                    User.display_name.ilike(term),
                    User.email.ilike(term),
                    User.google_id.ilike(term)
                )
            )
            
        # Total count query
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)
        
        # Pagination
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        return list(users), (total or 0)

    @staticmethod
    async def update_user(
        session: AsyncSession, 
        user_id: uuid.UUID, 
        update_data: dict
    ) -> Optional[User]:
        """
        Update a user by ID.
        """
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
            
        for key, value in update_data.items():
            if value is not None:
                setattr(user, key, value)
            
        await session.commit()
        await session.refresh(user)
        return user
