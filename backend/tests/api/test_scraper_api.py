"""Test Scraper API endpoints."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

@pytest.fixture
def admin_auth_headers(admin_user_token):
    """Headers for admin authentication."""
    return {"Authorization": f"Bearer {admin_user_token}"}

@pytest.mark.asyncio
async def test_scraper_start_requires_admin(client: AsyncClient):
    """POST /api/admin/scraper/start requires admin role."""
    response = await client.post("/api/admin/scraper/start")
    assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_scraper_start_as_admin(
    client: AsyncClient,
    admin_auth_headers
):
    """Admin can start scraper."""
    # Note: We patch the path where it's USED, not where it's defined.
    # Since it will be imported in app.api.admin.scraper, we patch it there.
    with patch('app.api.admin.scraper.run_scraper_background') as mock:
        # mock is a sync function added to background tasks, but 
        # the response expects it to return something? 
        # Actually the provided implementation doesn't return anything from background_tasks.add_task.
        # But the test expects "task_id" in response.json().
        
        response = await client.post(
            "/api/admin/scraper/start",
            json={"phase": 1, "tier": "1"},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 202
        assert "task_id" in response.json()
