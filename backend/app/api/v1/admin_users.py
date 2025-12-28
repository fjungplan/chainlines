from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.dependencies import require_admin, get_db

from app.services.user_service import UserService
from app.schemas.user import UserListResponse, UserUpdateAdmin, UserAdminRead
from app.models.user import User
import uuid

router = APIRouter(prefix="/users", tags=["admin-users"])

@router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    # Ensure only admins can access
    dependencies=[Depends(require_admin)]
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List users with pagination and search.
    Requires Admin privileges.
    """
    users, total = await UserService.get_users(
        session=db,
        skip=skip,
        limit=limit,
        search_query=search
    )
    
    return UserListResponse(items=users, total=total)

@router.patch(
    "/{user_id}",
    response_model=UserAdminRead,
    status_code=status.HTTP_200_OK,
    # Ensure only admins can access
    dependencies=[Depends(require_admin)]
)
async def update_user(
    user_id: uuid.UUID,
    update_request: UserUpdateAdmin,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user's role or ban status.
    Requires Admin privileges.
    """
    # UUID validation handled by FastAPI type hint
    
    user = await UserService.update_user(
        session=db,
        user_id=user_id,
        update_data=update_request.model_dump(exclude_unset=True)
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user
