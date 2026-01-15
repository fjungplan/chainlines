
import pytest
from app.models.team import TeamEra

def test_team_era_uci_code_validation_empty_string():
    """Verify that empty string raises ValueError per model validation."""
    era = TeamEra(season_year=2024, registered_name="Test")
    with pytest.raises(ValueError, match="uci_code must be 3 uppercase alphanumeric"):
        era.validate_uci_code("uci_code", "")

def test_team_era_uci_code_validation_none():
    """Verify that None is accepted."""
    era = TeamEra(season_year=2024, registered_name="Test")
    # Should not raise
    result = era.validate_uci_code("uci_code", None)
    assert result is None

def test_team_era_uci_code_validation_valid():
    """Verify that valid UCI code is accepted."""
    era = TeamEra(season_year=2024, registered_name="Test")
    result = era.validate_uci_code("uci_code", "ABC")
    assert result == "ABC"

def test_team_era_uci_code_validation_invalid_format():
    """Verify that invalid format raises ValueError."""
    era = TeamEra(season_year=2024, registered_name="Test")
    with pytest.raises(ValueError, match="uci_code must be 3 uppercase alphanumeric"):
        era.validate_uci_code("uci_code", "AB") # Too short
    with pytest.raises(ValueError, match="uci_code must be 3 uppercase alphanumeric"):
        era.validate_uci_code("uci_code", "abcd") # Too long
    with pytest.raises(ValueError, match="uci_code must be 3 uppercase alphanumeric"):
        era.validate_uci_code("uci_code", "AbC") # Not uppercase
