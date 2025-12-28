import pytest
from httpx import AsyncClient
from app.models.enums import UserRole
from app.models.user import User
from main import app

@pytest.mark.asyncio
async def test_list_users_admin_success(
    test_client: AsyncClient,
    test_user_admin: User,  # From fixtures list: test_user_admin
    test_user: User
):
    """
    Test that an admin can list users.
    """
    # Authenticate as Admin
    # Assuming test_client is not auto-authenticated, or we need to override.
    # Checking existing patterns would be ideal, but for now I'll use test_user_admin
    # and assume there's a way to use it.
    # WAIT: test_client is usually an AsyncClient.
    # If the app uses dependency injection for current_user, we can override it.
    
    # Let's inspect conftest.py or test_users.py to see how auth is handled if we get 401/403.
    # But first fixing the fixture name.
    
    response = await test_client.get("/api/v1/admin/users?limit=10")
    
    # If 401, we know we need to mock auth. But 404 is expected for now (endpoint missing).
    # If 404, the test failed for the "Right" reason (endpoint missing), but we want 200.
    # So "Red" phase is accomplished if it returns 404.
    
    # However, to be robust, we need to pass headers or override dependency.
    # I'll rely on the app's likely `get_current_user` override pattern.
    pass
    
    # Retrying the file content with the correct fixture
    
    response = await test_client.get("/api/v1/admin/users?limit=10")
    # We expect 404 now.
    assert response.status_code == 404

# Wait, I shouldn't just assert 404, I should write the test respecting the end goal (200).
# The failure will be 404, which is correct.

@pytest.mark.asyncio
@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_list_users_admin_success(
    test_client: AsyncClient,
    test_user_admin: User,
    test_user_new: User
):
    # Override auth dependency to force admin
    from app.api.dependencies import get_current_user, require_admin
    
    app.dependency_overrides[get_current_user] = lambda: test_user_admin
    app.dependency_overrides[require_admin] = lambda: test_user_admin

    response = await test_client.get("/api/v1/admin/users?limit=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1

@pytest.mark.asyncio
async def test_list_users_non_admin_forbidden(
    test_client: AsyncClient,
    test_user_new: User
):
    from app.api.dependencies import get_current_user
    
    app.dependency_overrides = {}
    app.dependency_overrides[get_current_user] = lambda: test_user_new
    
    response = await test_client.get("/api/v1/admin/users")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_list_users_search(
    test_client: AsyncClient,
    test_user_admin: User,
    test_user_new: User
):
    from app.api.dependencies import get_current_user, require_admin
    
    app.dependency_overrides[get_current_user] = lambda: test_user_admin
    app.dependency_overrides[require_admin] = lambda: test_user_admin
    
    search_term = test_user_new.email.split('@')[0]
    response = await test_client.get(f"/api/v1/admin/users?search={search_term}")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["items"]) >= 1
    # Check if any item matches ID
    ids = [item["user_id"] for item in data["items"]]
    assert str(test_user_new.user_id) in ids

@pytest.mark.asyncio
async def test_update_user_role(
    test_client: AsyncClient,
    test_user_admin: User,
    test_user_new: User
):
    from app.api.dependencies import get_current_user, require_admin
    from main import app
    
    app.dependency_overrides[get_current_user] = lambda: test_user_admin
    app.dependency_overrides[require_admin] = lambda: test_user_admin
    
    # Update Role
    payload = {"role": UserRole.MODERATOR}
    response = await test_client.patch(f"/api/v1/admin/users/{test_user_new.user_id}", json=payload)
    # Expect 404 or 405 initially as endpoint doesn't exist
    # But for TDD Red phase, failure is good.
    # However, since I'm running all tests, and I want to see the update fail specifically.
    
    # If endpoint doesn't exist, it returns 405 Method Not Allowed if GET exists but PATCH doesn't?
    # Or 404 if I use a different path?
    # Path is /users/{id}. GET /users exists. 
    # So POST/PATCH /users/{id} should return 404 or 405.
    
    # I'll just assert 200 and expect failure.
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == UserRole.MODERATOR
    assert data["user_id"] == str(test_user_new.user_id)

@pytest.mark.asyncio
async def test_update_user_ban(
    test_client: AsyncClient,
    test_user_admin: User,
    test_user_new: User
):
    from app.api.dependencies import get_current_user, require_admin
    from main import app
    
    app.dependency_overrides[get_current_user] = lambda: test_user_admin
    app.dependency_overrides[require_admin] = lambda: test_user_admin
    
    payload = {"is_banned": True, "banned_reason": "Violation of rules"}
    response = await test_client.patch(f"/api/v1/admin/users/{test_user_new.user_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_banned"] is True
    assert data["banned_reason"] == "Violation of rules"

@pytest.mark.asyncio
async def test_update_user_forbidden(
    test_client: AsyncClient,
    test_user_new: User
):
    from app.api.dependencies import get_current_user
    from main import app
    
    app.dependency_overrides = {}
    app.dependency_overrides[get_current_user] = lambda: test_user_new
    
    # Try to update self or other
    payload = {"role": UserRole.ADMIN}
    response = await test_client.patch(f"/api/v1/admin/users/{test_user_new.user_id}", json=payload)
    assert response.status_code == 403
