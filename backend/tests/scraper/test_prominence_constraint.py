"""Test that 0% prominence is now allowed."""
import pytest
from app.models.sponsor import TeamSponsorLink

def test_zero_prominence_allowed():
    """Validate that 0% prominence passes validation."""
    # This should NOT raise ValueError
    link = TeamSponsorLink.__new__(TeamSponsorLink)
    result = link.validate_prominence("prominence_percent", 0)
    assert result == 0

def test_negative_prominence_rejected():
    """Validate that negative prominence is still rejected."""
    link = TeamSponsorLink.__new__(TeamSponsorLink)
    with pytest.raises(ValueError):
        link.validate_prominence("prominence_percent", -1)

def test_over_100_rejected():
    """Validate that >100% is still rejected."""
    link = TeamSponsorLink.__new__(TeamSponsorLink)
    with pytest.raises(ValueError):
        link.validate_prominence("prominence_percent", 101)
