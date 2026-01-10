from unittest.mock import MagicMock
import pytest
from app.scraper.orchestration.phase1 import DiscoveryService

# Mock Config or Dependencies if needed
class MockGTIndex:
    def is_relevant(self, name_slug, year):
        # Mock Peugeot as relevant for pre-1991
        if "peugeot" in name_slug:
            return True
        return False

@pytest.fixture
def service():
    scraper = MagicMock()
    checkpoint = MagicMock()
    
    # Instantiate with required mocks
    s = DiscoveryService(scraper=scraper, checkpoint_manager=checkpoint)
    s._gt_index = MockGTIndex()
    
    # Inject the set for testing
    s._relevant_identities = set() 
    return s

def test_is_relevant_post_1999_tier1_2(service):
    """Post-1999, Tier 1 and 2 should always be relevant."""
    # Sig: team_name, tier, year
    assert service._is_relevant("tier-1-team", 1, 2005) is True
    assert service._is_relevant("tier-2-team", 2, 2005) is True

def test_is_relevant_post_1999_tier3_default(service):
    """Post-1999, Tier 3 is irrelevant by default."""
    assert service._is_relevant("random-conti-team", 3, 2005) is False

def test_is_relevant_post_1999_tier3_historical(service):
    """Post-1999, Tier 3 IS relevant if identity is known (was T1/T2 before)."""
    identity = "team-historical-giant"
    service._relevant_identities.add(identity)
    
    # We need to update _is_relevant to accept identity. 
    # For TDD, we call it with the extra arg that we plan to add.
    # New Sig Plan: team_name, tier, year, team_identity=None
    
    assert service._is_relevant("team-historical-renamed", 3, 2005, team_identity=identity) is True

def test_is_relevant_1991_1998_tier2(service):
    """1991-1998: Tier 1 is kept. Tier 2 is kept ONLY if GT relevant."""
    
    # Tier 1 always yes
    assert service._is_relevant("team-telekom", 1, 1995) is True
    
    # Tier 2 - checking GT index logic
    # "unknown-small-team" is not in MockGTIndex
    assert service._is_relevant("unknown-small-team", 2, 1995) is False

def test_is_relevant_pre_1991(service):
    """Pre-1991: Only if in GT Index."""
    assert service._is_relevant("peugeot-cycles", 1, 1980) is True # Mocked as relevant
    assert service._is_relevant("unknown-local-club", 1, 1980) is False
