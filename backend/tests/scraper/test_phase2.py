"""Test Phase 2 Team Assembly orchestration."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


def test_prominence_calculator_one_sponsor():
    """One sponsor should get 100%."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["Visma"])
    assert result == [100]


def test_prominence_calculator_two_sponsors():
    """Two sponsors should get 60/40."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["Visma", "Lease a Bike"])
    assert result == [60, 40]


def test_prominence_calculator_three_sponsors():
    """Three sponsors should get 40/30/30."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["A", "B", "C"])
    assert result == [40, 30, 30]


def test_prominence_calculator_four_sponsors():
    """Four sponsors should get 40/20/20/20."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["A", "B", "C", "D"])
    assert result == [40, 20, 20, 20]


def test_prominence_calculator_five_sponsors():
    """Five+ sponsors: LLM pattern extension (sum=100)."""
    from app.scraper.orchestration.phase2 import ProminenceCalculator
    
    result = ProminenceCalculator.calculate(["A", "B", "C", "D", "E"])
    assert sum(result) == 100
    assert result[0] >= result[-1]  # First should be highest


@pytest.mark.asyncio
async def test_team_assembly_creates_edit():
    """TeamAssemblyService should create edits via AuditLog."""
    from app.scraper.orchestration.phase2 import TeamAssemblyService
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    mock_audit = AsyncMock()
    mock_audit.create_edit = AsyncMock(return_value=MagicMock(edit_id=uuid4()))
    
    mock_session = AsyncMock()
    
    service = TeamAssemblyService(
        audit_service=mock_audit,
        session=mock_session,
        system_user_id=uuid4()
    )
    
    team_data = ScrapedTeamData(
        name="Team Visma",
        season_year=2024,
        sponsors=["Visma", "Lease a Bike"],
        uci_code="TJV",
        tier="WorldTour"
    )
    
    await service.create_team_era(team_data, confidence=0.95)
    
    mock_audit.create_edit.assert_called_once()
