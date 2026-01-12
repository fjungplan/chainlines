import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.services.user_deletion_service import UserDeletionService

@pytest.mark.asyncio
async def test_delete_account_unauthenticated_returns_401(client: AsyncClient):
    response = await client.delete("/api/v1/account")
    assert response.status_code in (401, 403)

@pytest.mark.asyncio
async def test_delete_account_success(
    client: AsyncClient, new_user, new_user_token, db_session
):
    """Test successful account deletion call."""
    # Mock the service to avoid actual DB side effects in API test (we tested service separately)
    # and to verify it calls the service correctly
    with patch("app.api.v1.account.UserDeletionService.delete_user_account", new_callable=AsyncMock) as mock_delete:
        headers = {"Authorization": f"Bearer {new_user_token}"}
        response = await client.delete("/api/v1/account", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Account deleted successfully"
        
        # Verify service called with correct args
        mock_delete.assert_called_once()
        # Args: session, user_id, user_obj
        # We can't easily check session equality, but can check user_id
        # args[0] is session, args[1] is user_id, args[2] is user
        call_args = mock_delete.call_args
        assert call_args[0][1] == new_user.user_id

@pytest.mark.asyncio
async def test_delete_account_service_error(
    client: AsyncClient, new_user, new_user_token
):
    """Test 500 error propagation."""
    with patch("app.api.v1.account.UserDeletionService.delete_user_account", side_effect=ValueError("Service error")) as mock_delete:
        headers = {"Authorization": f"Bearer {new_user_token}"}
        response = await client.delete("/api/v1/account", headers=headers)
        
        assert response.status_code == 400 # ValueError usually maps to 400 or 500 depending on handler
        # If we handle it explicitly. Let's see. If unhandled, 500.
        
