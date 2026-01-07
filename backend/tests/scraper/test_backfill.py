"""Tests for team history backfill functionality."""
import pytest
from app.scraper.orchestration.phase1 import DiscoveryService


class TestClosesGap:
    """Unit tests for _closes_gap helper method."""
    
    @pytest.fixture
    def discovery_service(self, mocker):
        """Create a minimal DiscoveryService for testing."""
        mock_scraper = mocker.MagicMock()
        mock_checkpoint = mocker.MagicMock()
        mock_checkpoint.load.return_value = None
        return DiscoveryService(mock_scraper, mock_checkpoint)
    
    def test_closes_gap_year_between_scraped(self, discovery_service):
        """Year between min and max scraped years closes a gap."""
        scraped = {2020, 2022, 2024}
        
        # 2021 and 2023 are between 2020 and 2024
        assert discovery_service._closes_gap(2021, scraped) is True
        assert discovery_service._closes_gap(2023, scraped) is True
    
    def test_closes_gap_year_outside_not_closes(self, discovery_service):
        """Year outside min/max range doesn't close a gap."""
        scraped = {2020, 2022, 2024}
        
        # 2019 and 2025 are outside the range
        assert discovery_service._closes_gap(2019, scraped) is False
        assert discovery_service._closes_gap(2025, scraped) is False
    
    def test_closes_gap_empty_scraped_returns_false(self, discovery_service):
        """Empty scraped years returns False."""
        assert discovery_service._closes_gap(2022, set()) is False
    
    def test_closes_gap_single_year_returns_false(self, discovery_service):
        """Single scraped year returns False (no gap possible)."""
        assert discovery_service._closes_gap(2022, {2020}) is False
