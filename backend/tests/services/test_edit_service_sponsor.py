
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch
from app.models.enums import UserRole, EditStatus
from app.models.user import User
from app.models.sponsor import SponsorMaster, SponsorBrand
from app.services.edit_service import EditService
from app.schemas.edits import SponsorMasterEditRequest, SponsorBrandEditRequest
from app.core.exceptions import ValidationException

# Mock implementations or fixtures
@pytest.fixture
def admin_user():
    return User(
        user_id=uuid.uuid4(),
        google_id="admin",
        email="admin@test.com",
        display_name="Admin",
        role=UserRole.ADMIN,
        approved_edits_count=100
    )

@pytest.fixture
def editor_user():
    return User(
        user_id=uuid.uuid4(),
        google_id="editor",
        email="editor@test.com",
        display_name="Editor",
        role=UserRole.EDITOR,
        approved_edits_count=0
    )

@pytest.fixture
def moderator_user():
    return User(
        user_id=uuid.uuid4(),
        google_id="mod",
        email="mod@test.com",
        display_name="Moderator",
        role=UserRole.MODERATOR,
        approved_edits_count=50
    )

@pytest.mark.asyncio
async def test_create_sponsor_master_as_editor(db_session, editor_user):
    """Test that an editor creates a PENDING request for a new sponsor master."""
    db_session.add(editor_user)
    await db_session.commit()

    request = SponsorMasterEditRequest(
        legal_name="New Sponsor",
        display_name="New Sponsor Display",
        industry_sector="Tech",
        source_url="http://test.com",
        source_notes="Testing",
        reason="Adding new sponsor"
    )

    # We expect create_sponsor_master_edit to be implemented
    if not hasattr(EditService, "create_sponsor_master_edit"):
        pytest.fail("EditService.create_sponsor_master_edit not implemented")

    response = await EditService.create_sponsor_master_edit(db_session, editor_user, request)

    assert response.status == EditStatus.PENDING
    assert "submitted for moderation" in response.message

@pytest.mark.asyncio
async def test_create_sponsor_master_as_trusted(db_session, admin_user):
    """Test that an admin/trusted user creates an APPROVED sponsor master immediately."""
    db_session.add(admin_user)
    await db_session.commit()

    request = SponsorMasterEditRequest(
        legal_name="Trusted Sponsor",
        display_name="Trusted Sponsor Display",
        industry_sector="Finance",
        reason="Adding trusted sponsor"
    )

    with patch("app.services.sponsor_service.SponsorService.create_master", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = SponsorMaster(
            master_id=uuid.uuid4(),
            legal_name="Trusted Sponsor",
            display_name="Trusted Sponsor Display"
        )

        response = await EditService.create_sponsor_master_edit(db_session, admin_user, request)

        assert response.status == EditStatus.APPROVED
        assert "created" in response.message.lower()
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_update_sponsor_master_protected_failure(db_session, editor_user):
    """Test that an editor cannot update a protected sponsor master."""
    db_session.add(editor_user)
    await db_session.commit()

    master = SponsorMaster(
        master_id=uuid.uuid4(),
        legal_name="Protected Sponsor",
        is_protected=True
    )
    
    # Mock finding the master
    with patch("app.services.sponsor_service.SponsorService.get_master_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = master

        request = SponsorMasterEditRequest(
            master_id=str(master.master_id),
            legal_name="Hacked Name",
            reason="Malicious edit"
        )
        
        if not hasattr(EditService, "update_sponsor_master_edit"):
             pytest.fail("EditService.update_sponsor_master_edit not implemented")

        with pytest.raises(ValueError, match="protected"):
            await EditService.update_sponsor_master_edit(db_session, editor_user, request)

@pytest.mark.asyncio
async def test_update_sponsor_master_as_moderator(db_session, moderator_user):
    """Test that a moderator CAN update a protected sponsor master."""
    db_session.add(moderator_user)
    await db_session.commit()

    master = SponsorMaster(
        master_id=uuid.uuid4(),
        legal_name="Protected Sponsor",
        is_protected=True
    )

    with patch("app.services.sponsor_service.SponsorService.get_master_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = master
        
        with patch("app.services.sponsor_service.SponsorService.update_master", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = master # simplified

            request = SponsorMasterEditRequest(
                master_id=str(master.master_id),
                legal_name="Updated Name",
                reason="Legitimate update"
            )

            response = await EditService.update_sponsor_master_edit(db_session, moderator_user, request)
            
            assert response.status == EditStatus.APPROVED
            mock_update.assert_called_once()

@pytest.mark.asyncio
async def test_create_sponsor_brand_as_editor(db_session, editor_user):
    """Test that an editor creates a PENDING request for a new brand."""
    db_session.add(editor_user)
    await db_session.commit()

    master_id = uuid.uuid4()
    request = SponsorBrandEditRequest(
        master_id=str(master_id),
        brand_name="New Brand",
        default_hex_color="#FFFFFF",
        reason="New brand request"
    )

    if not hasattr(EditService, "create_sponsor_brand_edit"):
        pytest.fail("EditService.create_sponsor_brand_edit not implemented")

    # Mock finding master (needed for validation)
    with patch("app.services.sponsor_service.SponsorService.get_master_by_id", new_callable=AsyncMock) as mock_get_master:
        mock_get_master.return_value = SponsorMaster(master_id=master_id)

        response = await EditService.create_sponsor_brand_edit(db_session, editor_user, request)

        assert response.status == EditStatus.PENDING
        assert "submitted for moderation" in response.message

