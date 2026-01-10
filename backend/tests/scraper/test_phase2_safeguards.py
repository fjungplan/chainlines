import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.exc import MultipleResultsFound
from app.scraper.orchestration.phase2 import AssemblyOrchestrator, TeamAssemblyService
from app.models.team import TeamNode

@pytest.fixture
def mock_session():
    m = AsyncMock()
    # session.add is synchronous
    m.add = MagicMock()
    return m

import uuid
from app.services.audit_log_service import AuditLogService

@pytest.fixture
def mock_audit_service():
    return MagicMock(spec=AuditLogService)

@pytest.fixture
def service(mock_session, mock_audit_service):
    return TeamAssemblyService(
        audit_service=mock_audit_service,
        session=mock_session,
        system_user_id=uuid.uuid4()
    )

@pytest.mark.asyncio
async def test_assemble_team_handles_duplicates_gracefully(service, mock_session):
    """
    Test that finding multiple nodes for the same identity does not crash the scraper.
    """
    # Mock data
    team_identity_id = "test-identity-123"
    
    # Setup mock result to simulate duplicate nodes
    # We want session.execute() to return a result that behaves like it has 2 rows
    # when .scalar_one_or_none() is called.
    
    # Mocking sqlalchemy result is tricky. 
    # Option A: Mock the result object and make scalar_one_or_none raise MultipleResultsFound
    # Option B: Mock the result to return a list of 2 items when scalars().all() is called
    
    # Let's try to verify the method CALLS scalars().first() instead of scalar_one_or_none()
    # But strictly TDD means we want to see it fail first.
    
    mock_result = MagicMock()
    
    # Configure mock:
    # 1. scalar_one_or_none RAISES error (to prove we don't use it or if we did, it would fail)
    mock_result.scalar_one_or_none.side_effect = MultipleResultsFound("Multiple rows found - Should not be called")
    
    # 2. scalars().first() returns a valid node (The fix)
    mock_node = TeamNode(
        node_id=uuid.uuid4(), 
        legal_name="Existing Node",
        founding_year=1990
    )
    mock_result.scalars.return_value.first.return_value = mock_node
    
    # Initialize the session execute return value
    mock_session.execute.return_value = mock_result
    
    # Prepare input data
    mock_data = MagicMock()
    mock_data.team_identity_id = team_identity_id
    mock_data.name = "Test Team"
    mock_data.season_year = 2024
    mock_data.dissolution_year = None
    mock_data.sponsors = []
    mock_data.uci_code = "TST"
    mock_data.country_code = "TST"
    mock_data.tier_level = 1
    
    # Run - Should now SUCCEED without raising MultipleResultsFound
    result_era = await service.assemble_team(mock_data)
    
    # Assert
    assert result_era is not None
    assert result_era.node.legal_name == "Existing Node"  # Should pick the existing one
    
    # Verify we called execute
    assert mock_session.execute.called

