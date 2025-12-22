import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch
from app.models.enums import UserRole, EditStatus
from app.models.user import User
from app.models.team import TeamEra, TeamNode
from app.services.edit_service import EditService
from app.schemas.edits import CreateEraEditRequest

# Mock schemas/data structures for testing
class MockEraRequest:
    def __init__(self, season_year, registered_name, reason=None):
        self.season_year = season_year
        self.registered_name = registered_name
        self.reason = reason
        self.valid_from = "2024-01-01"
        self.node_id = str(uuid.uuid4())
        self.uci_code = "TES"
        self.country_code = "BEL"
        self.tier_level = 1

# We need to test the logic branch: "If Editor -> Pending, If Trusted -> Approved"
# We also need to test "If Protected -> Check Role"

@pytest.mark.asyncio
async def test_create_era_edit_as_editor(db_session):
    """Test that a standard editor creates a PENDING edit request."""
    user = User(
        user_id=uuid.uuid4(), 
        google_id="123", 
        email="ed@test.com", 
        display_name="Editor",
        role=UserRole.EDITOR, 
        approved_edits_count=0
    )
    db_session.add(user)
    await db_session.commit() # Ensure user exists for FK

    request = MockEraRequest(2025, "New Era", "Reason")
    
    # We patch the class where it is DEFINED, because EditService imports it locally
    with patch("app.services.team_service.TeamService.get_node_with_eras", new_callable=AsyncMock) as mock_get_node:
        mock_get_node.return_value = TeamNode(node_id=uuid.UUID(request.node_id))
        
        # ACT
        # We expect a method `create_era_edit` to exist on EditService
        if not hasattr(EditService, "create_era_edit"):
             pytest.fail("EditService.create_era_edit not implemented yet (TDD)")
             
        response = await EditService.create_era_edit(db_session, user, request)
        
        # ASSERT
        assert response.status == EditStatus.PENDING
        assert "submitted for moderation" in response.message

@pytest.mark.asyncio
async def test_create_era_edit_as_trusted(db_session):
    """Test that a trusted editor creates an APPROVED edit and applies it."""
    user = User(
        user_id=uuid.uuid4(), 
        google_id="456", 
        email="trusted@test.com", 
        display_name="Trusted",
        role=UserRole.TRUSTED_EDITOR, 
        approved_edits_count=10
    )
    db_session.add(user)
    await db_session.commit()

    request = MockEraRequest(2025, "Trusted Era", "Reason")
    
    with patch("app.services.team_service.TeamService.get_node_with_eras", new_callable=AsyncMock) as mock_get_node:
        mock_get_node.return_value = TeamNode(node_id=uuid.UUID(request.node_id))
        
        # We also need to mock the actual creation call to TeamService.create_era if auto-approved
        with patch("app.services.team_service.TeamService.create_era", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = TeamEra(
                era_id=uuid.uuid4(),
                registered_name="Trusted Era",
                season_year=2025
            )
            
            response = await EditService.create_era_edit(db_session, user, request)
            
            assert response.status == EditStatus.APPROVED
            assert "created" in response.message.lower()
            mock_create.assert_called_once()
