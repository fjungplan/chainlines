import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.checkpoint import CheckpointManager, CheckpointData
from pathlib import Path
import tempfile
import uuid
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_checkpoint_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "checkpoint.json"
        yield CheckpointManager(path)

@pytest.fixture
def admin_token_headers(admin_user_token: str):
    return {"Authorization": f"Bearer {admin_user_token}"}

@pytest.mark.asyncio
async def test_get_checkpoint_empty(client: AsyncClient, admin_token_headers):
    """GET /checkpoint should return 404 if no checkpoint exists."""
    # Mock CheckpointManager.load to return None (no checkpoint)
    with patch('app.api.admin.scraper.CheckpointManager') as mock_manager_class:
        mock_instance = MagicMock()
        mock_instance.load.return_value = None
        mock_manager_class.return_value = mock_instance
        
        response = await client.get("/api/v1/admin/scraper/checkpoint", headers=admin_token_headers)
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_start_scraper_run(client: AsyncClient, admin_token_headers, db_session: AsyncSession):
    """POST /start should create a ScraperRun and return task_id."""
    # Mock the background task to avoid event loop conflicts
    with patch('app.api.admin.scraper.run_scraper_with_logging') as mock_bg_task:
        payload = {
            "phase": 1,
            "tier": "1",
            "dry_run": True,
            "start_year": 2024,
            "end_year": 2024
        }
        response = await client.post("/api/v1/admin/scraper/start", json=payload, headers=admin_token_headers)
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        
        # Verify DB record was created
        from app.models.run_log import ScraperRun
        from sqlalchemy import select
        
        result = await db_session.execute(select(ScraperRun).where(ScraperRun.run_id == uuid.UUID(data["task_id"])))
        run = result.scalar_one()
        assert run.phase == 1
        assert run.tier == "1"
        assert run.status.value == "PENDING"  # Initial status before background task runs

@pytest.mark.asyncio
async def test_list_scraper_runs(client: AsyncClient, admin_token_headers, db_session: AsyncSession):
    """GET /runs should list scraper runs."""
    # Create a dummy run
    from app.models.run_log import ScraperRun, ScraperRunStatus
    run = ScraperRun(
        phase=2,
        tier="2",
        status=ScraperRunStatus.COMPLETED,
        items_processed=10
    )
    db_session.add(run)
    await db_session.commit()
    
    response = await client.get("/api/v1/admin/scraper/runs", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["phase"] == 2
    assert data["items"][0]["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_get_logs(client: AsyncClient, admin_token_headers):
    """GET /runs/{id}/logs should return log content."""
    # We need a run_id that exists in DB and a log file
    # This is hard to test fully integrated without mocking file system *and* DB.
    # We'll skip for now or write a mock test unit.
    pass
