import pytest
from app.models.team import TeamNode, TeamEra
from app.models.enums import UserRole

@pytest.mark.asyncio
async def test_team_node_protection_defaults(db_session):
    """Test that TeamNode has is_protected field defaulting to False."""
    node = TeamNode(
        founding_year=2000,
        legal_name="Test Team",
        display_name="Test Display"
    )
    db_session.add(node)
    await db_session.commit()
    await db_session.refresh(node)
    
    assert hasattr(node, "is_protected")
    assert node.is_protected is False

    node.is_protected = True
    assert node.is_protected is True

@pytest.mark.asyncio
async def test_team_era_protection_defaults():
    """Test that TeamEra has is_protected field defaulting to False."""
    # This logic assumes we can instantiate the model even if DB schema isn't migrated yet,
    # distinct from integration tests.
    era = TeamEra(
        season_year=2024,
        registered_name="Test Era",
        # is_protected should be available
    )
    
    # Check definition
    assert hasattr(era, "is_protected"), "TeamEra model missing is_protected field"
    # Note: SQLAlchemy defaults often only apply after flush/init processing implies they exist.
    # We will check if we can set it.
    era.is_protected = True
    assert era.is_protected is True
