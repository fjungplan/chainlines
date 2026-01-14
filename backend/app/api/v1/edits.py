from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.dependencies import get_current_user, require_editor
from app.models.user import User
from app.schemas.edits import (
    EditMetadataRequest, EditMetadataResponse, MergeEventRequest, 
    SplitEventRequest, CreateTeamRequest, CreateEraEditRequest, UpdateEraEditRequest,
    UpdateNodeRequest, LineageEditRequest,
    SponsorMasterEditRequest, SponsorBrandEditRequest
)
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


@router.put("/era/{era_id}", response_model=EditMetadataResponse)
async def update_era(
    era_id: str,
    request: UpdateEraEditRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Update an existing team era.
    
    This endpoint allows updating era fields including node_id for transfers.
    - NEW_USER: Update goes to moderation queue (PENDING status)
    - TRUSTED_USER/ADMIN: Update is auto-approved immediately
    """
    try:
        if request.era_id and request.era_id != era_id:
            raise ValueError("Era ID in path does not match body")
        request.era_id = era_id
        
        result = await EditService.update_era_edit(
            session,
            current_user,
            request
        )
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


@router.post("/lineage", response_model=EditMetadataResponse)
async def create_lineage(
    request: LineageEditRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create a new lineage connection (event).
    
    - NEW_USER: Goes to moderation queue (PENDING)
    - TRUSTED/ADMIN: Auto-approved
    """
    try:
        result = await EditService.create_lineage_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/lineage/{event_id}", response_model=EditMetadataResponse)
async def update_lineage(
    event_id: str,
    request: LineageEditRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Update an existing lineage event.
    
    - NEW_USER: Goes to moderation queue (PENDING)
    - TRUSTED/ADMIN: Auto-approved (unless protected & not mod)
    """
    try:
        if request.event_id and request.event_id != event_id:
             raise ValueError("Event ID in path does not match body")
        request.event_id = event_id # Ensure it's set
        
        result = await EditService.update_lineage_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sponsor-master", response_model=EditMetadataResponse)
async def create_sponsor_master(
    request: SponsorMasterEditRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create a new sponsor master.
    
    - NEW_USER: Goes to moderation queue (PENDING)
    - TRUSTED/ADMIN: Auto-approved
    """
    try:
        # Check permissions managed by service
        result = await EditService.create_sponsor_master_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sponsor-master/{master_id}", response_model=EditMetadataResponse)
async def update_sponsor_master(
    master_id: str,
    request: SponsorMasterEditRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Update an existing sponsor master.
    
    - NEW_USER: Goes to moderation queue (PENDING)
    - TRUSTED/ADMIN: Auto-approved (unless protected & not mod)
    """
    try:
        request.master_id = master_id
        result = await EditService.update_sponsor_master_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sponsor-brand", response_model=EditMetadataResponse)
async def create_sponsor_brand(
    request: SponsorBrandEditRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create a new sponsor brand.
    
    - NEW_USER: Goes to moderation queue (PENDING)
    - TRUSTED/ADMIN: Auto-approved
    """
    try:
        result = await EditService.create_sponsor_brand_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sponsor-brand/{brand_id}", response_model=EditMetadataResponse)
async def update_sponsor_brand(
    brand_id: str,
    request: SponsorBrandEditRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Update an existing sponsor brand.
    
    - NEW_USER: Goes to moderation queue (PENDING)
    - TRUSTED/ADMIN: Auto-approved (unless protected & not mod)
    """
    try:
        request.brand_id = brand_id
        result = await EditService.update_sponsor_brand_edit(
            session,
            current_user,
            request
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
