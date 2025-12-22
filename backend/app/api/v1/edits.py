from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.dependencies import get_current_user, require_editor
from app.models.user import User
from app.schemas.edits import EditMetadataRequest, EditMetadataResponse, MergeEventRequest, SplitEventRequest, CreateTeamRequest, CreateEraEditRequest, UpdateNodeRequest
from app.services.edit_service import EditService

router = APIRouter(prefix="/api/v1/edits", tags=["edits"])


@router.post("/metadata", response_model=EditMetadataResponse)
async def edit_metadata(
    request: EditMetadataRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Edit team era metadata.
    
    This endpoint allows authenticated users to submit edits to team metadata.
    - NEW_USER: Edits go to moderation queue (PENDING status)
    - TRUSTED_USER/ADMIN: Edits are auto-approved and applied immediately
    """
    try:
        result = await EditService.create_metadata_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/merge", response_model=EditMetadataResponse)
async def create_merge(
    request: MergeEventRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create a team merge event.
    
    This endpoint allows authenticated users to merge multiple teams into a new team.
    - NEW_USER: Merge goes to moderation queue (PENDING status)
    - TRUSTED_USER/ADMIN: Merge is auto-approved and applied immediately
    """
    try:
        result = await EditService.create_merge_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/split", response_model=EditMetadataResponse)
async def create_split(
    request: SplitEventRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create a team split event.
    
    This endpoint allows authenticated users to split a team into multiple teams.
    - NEW_USER: Split goes to moderation queue (PENDING status)
    - TRUSTED_USER/ADMIN: Split is auto-approved and applied immediately
    """
    try:
        result = await EditService.create_split_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-team", response_model=EditMetadataResponse)
async def create_team(
    request: CreateTeamRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create a new team from scratch.
    
    This endpoint allows authenticated users to create a new team node.
    - NEW_USER: Team creation goes to moderation queue (PENDING status)
    - TRUSTED_USER/ADMIN: Team is auto-created immediately
    """
    try:
        result = await EditService.create_team_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/era", response_model=EditMetadataResponse)
async def create_era(
    request: CreateEraEditRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create a new team era (season).
    
    This endpoint allows authenticated users to create a new season for a team.
    - NEW_USER: Creation goes to moderation queue (PENDING status)
    - TRUSTED_USER/ADMIN: Era is auto-created immediately
    """
    try:
        result = await EditService.create_era_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/node", response_model=EditMetadataResponse)
async def edit_node(
    request: UpdateNodeRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Edit team node details.
    
    This endpoint allows authenticated users to edit team node details.
    - NEW_USER: Edit goes to moderation queue (PENDING status)
    - TRUSTED_USER/ADMIN: Edit is auto-approved
    """
    try:
        result = await EditService.create_node_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
