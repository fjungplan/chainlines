import pytest
import uuid
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.scraper.monitor import ScraperStatusMonitor, ScraperAbortedError, ScraperRunStatus, ScraperRun

@pytest.fixture
def mock_session_maker():
    with patch("app.scraper.monitor.async_session_maker") as mock:
        yield mock

@pytest.mark.asyncio
async def test_monitor_running(mock_session_maker):
    """Test that monitor returns immediately if status is RUNNING."""
    run_id = uuid.uuid4()
    monitor = ScraperStatusMonitor(run_id)
    
    # Mock DB session and result
    mock_session = AsyncMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = ScraperRunStatus.RUNNING
    mock_session.execute.return_value = mock_result
    
    # Should not raise or block
    await monitor.check_status()
    
    # Verify query
    assert mock_session.execute.called

@pytest.mark.asyncio
async def test_monitor_aborted(mock_session_maker):
    """Test that monitor raises exception if status is ABORTED."""
    run_id = uuid.uuid4()
    monitor = ScraperStatusMonitor(run_id)
    
    # Mock DB session and result
    mock_session = AsyncMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = ScraperRunStatus.ABORTED
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(ScraperAbortedError):
        await monitor.check_status()

@pytest.mark.asyncio
async def test_monitor_paused_then_resumed(mock_session_maker):
    """Test that monitor waits when PAUSED and proceeds when RUNNING."""
    run_id = uuid.uuid4()
    monitor = ScraperStatusMonitor(run_id)
    
    # Mock DB session and result
    mock_session = AsyncMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session
    
    # First call returns PAUSED, Second call returns RUNNING
    mock_result_paused = MagicMock()
    mock_result_paused.scalar_one_or_none.return_value = ScraperRunStatus.PAUSED
    
    mock_result_running = MagicMock()
    mock_result_running.scalar_one_or_none.return_value = ScraperRunStatus.RUNNING
    
    # Side effect for execute: first PAUSED, then RUNNING
    mock_session.execute.side_effect = [mock_result_paused, mock_result_running]
    
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await monitor.check_status()
        
        # Should have slept once
        assert mock_sleep.called
        assert mock_session.execute.call_count == 2
