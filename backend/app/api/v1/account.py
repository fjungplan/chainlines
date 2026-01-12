from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.user_deletion_service import UserDeletionService

router = APIRouter()

@router.delete("/account", status_code=200)
async def delete_my_account(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete the current user's account and anonymize all their contributions.
    """
    try:
        await UserDeletionService.delete_user_account(session, current_user.user_id, current_user)
        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        # TODO: Log actual error
        raise HTTPException(status_code=500, detail="Internal server error during account deletion")
