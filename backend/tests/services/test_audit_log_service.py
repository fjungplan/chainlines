"""
Tests for AuditLogService entity name resolution.

TDD: These tests are written BEFORE implementation to define expected behavior.
"""
import pytest
from datetime import date, datetime
from uuid import uuid4

from app.models.user import User, UserRole
from app.models.team import TeamEra, TeamNode
from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.models.lineage import LineageEvent
from app.models.enums import LineageEventType


class TestResolveEntityName:
    """Test that UUIDs are resolved to human-readable names."""
    
    @pytest.fixture
    async def test_user(self, async_session):
        """Create a test user for foreign keys."""
        user = User(
            user_id=uuid4(),
            email="resolver_test@example.com",
            google_id="resolver_test_id",
            display_name="Resolver Test User"
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def test_team_node(self, async_session, test_user):
        """Create a test team node."""
        node = TeamNode(
            legal_name="Test Racing Ltd",
            display_name="Test Racing",
            founding_year=2020,
            created_by=test_user.user_id
        )
        async_session.add(node)
        await async_session.flush()
        return node
    
    @pytest.fixture
    async def test_team_era(self, async_session, test_user, test_team_node):
        """Create a test team era."""
        era = TeamEra(
            node_id=test_team_node.node_id,
            season_year=2024,
            valid_from=date(2024, 1, 1),
            registered_name="Test Racing 2024",
            tier_level=1,
            created_by=test_user.user_id
        )
        async_session.add(era)
        await async_session.flush()
        return era
    
    @pytest.fixture
    async def test_sponsor_master(self, async_session, test_user):
        """Create a test sponsor master."""
        master = SponsorMaster(
            legal_name="Big Corp International",
            display_name="Big Corp",
            created_by=test_user.user_id
        )
        async_session.add(master)
        await async_session.flush()
        return master
    
    @pytest.fixture
    async def test_sponsor_brand(self, async_session, test_user, test_sponsor_master):
        """Create a test sponsor brand."""
        brand = SponsorBrand(
            master_id=test_sponsor_master.master_id,
            brand_name="BigCorp Energy",
            default_hex_color="#FF5500",
            created_by=test_user.user_id
        )
        async_session.add(brand)
        await async_session.flush()
        return brand
    
    @pytest.fixture
    async def test_sponsor_link(self, async_session, test_user, test_team_era, test_sponsor_brand):
        """Create a test sponsor link."""
        link = TeamSponsorLink(
            era_id=test_team_era.era_id,
            brand_id=test_sponsor_brand.brand_id,
            rank_order=1,
            prominence_percent=50,
            created_by=test_user.user_id
        )
        async_session.add(link)
        await async_session.flush()
        return link
    
    @pytest.fixture
    async def test_lineage_event(self, async_session, test_user, test_team_node):
        """Create a test lineage event with two nodes."""
        successor_node = TeamNode(
            legal_name="New Racing Ltd",
            display_name="New Racing",
            founding_year=2024,
            created_by=test_user.user_id
        )
        async_session.add(successor_node)
        await async_session.flush()
        
        event = LineageEvent(
            predecessor_node_id=test_team_node.node_id,
            successor_node_id=successor_node.node_id,
            event_year=2024,
            event_type=LineageEventType.LEGAL_TRANSFER,
            created_by=test_user.user_id
        )
        async_session.add(event)
        await async_session.flush()
        return event, test_team_node, successor_node

    @pytest.mark.asyncio
    async def test_resolve_team_node_name(self, async_session, test_team_node):
        """Resolving a team_node entity should return the display_name or legal_name."""
        from app.services.audit_log_service import AuditLogService
        
        name = await AuditLogService.resolve_entity_name(
            async_session, "team_node", test_team_node.node_id
        )
        # Should prefer display_name if available
        assert name == "Test Racing"
    
    @pytest.mark.asyncio
    async def test_resolve_team_node_fallback_to_legal_name(self, async_session, test_user):
        """If display_name is None, should fall back to legal_name."""
        from app.services.audit_log_service import AuditLogService
        
        node = TeamNode(
            legal_name="Legal Only Ltd",
            display_name=None,
            founding_year=2020,
            created_by=test_user.user_id
        )
        async_session.add(node)
        await async_session.flush()
        
        name = await AuditLogService.resolve_entity_name(
            async_session, "team_node", node.node_id
        )
        assert name == "Legal Only Ltd"
    
    @pytest.mark.asyncio
    async def test_resolve_team_era_name(self, async_session, test_team_era):
        """Resolving a team_era entity should return registered_name with year."""
        from app.services.audit_log_service import AuditLogService
        
        name = await AuditLogService.resolve_entity_name(
            async_session, "team_era", test_team_era.era_id
        )
        assert name == "Test Racing 2024 (2024)"
    
    @pytest.mark.asyncio
    async def test_resolve_sponsor_master_name(self, async_session, test_sponsor_master):
        """Resolving a sponsor_master entity should return display_name or legal_name."""
        from app.services.audit_log_service import AuditLogService
        
        name = await AuditLogService.resolve_entity_name(
            async_session, "sponsor_master", test_sponsor_master.master_id
        )
        assert name == "Big Corp"
    
    @pytest.mark.asyncio
    async def test_resolve_sponsor_brand_name(self, async_session, test_sponsor_brand, test_sponsor_master):
        """Resolving a sponsor_brand entity should return brand_name with master name."""
        from app.services.audit_log_service import AuditLogService
        
        name = await AuditLogService.resolve_entity_name(
            async_session, "sponsor_brand", test_sponsor_brand.brand_id
        )
        assert name == "BigCorp Energy (Big Corp)"
    
    @pytest.mark.asyncio
    async def test_resolve_sponsor_link_name(self, async_session, test_sponsor_link, test_team_era, test_sponsor_brand):
        """Resolving a team_sponsor_link entity should return era + brand info."""
        from app.services.audit_log_service import AuditLogService
        
        name = await AuditLogService.resolve_entity_name(
            async_session, "team_sponsor_link", test_sponsor_link.link_id
        )
        # Format: "Brand → Era (Year)"
        assert "BigCorp Energy" in name
        assert "Test Racing 2024" in name
    
    @pytest.mark.asyncio
    async def test_resolve_lineage_event_name(self, async_session, test_lineage_event):
        """Resolving a lineage_event entity should return predecessor → successor."""
        from app.services.audit_log_service import AuditLogService
        
        event, predecessor, successor = test_lineage_event
        
        name = await AuditLogService.resolve_entity_name(
            async_session, "lineage_event", event.event_id
        )
        # Format: "Predecessor → Successor (Year)"
        assert "Test Racing" in name
        assert "New Racing" in name
        assert "2024" in name
    
    @pytest.mark.asyncio
    async def test_resolve_unknown_entity_returns_id(self, async_session):
        """Unknown entity type should return the UUID as a string."""
        from app.services.audit_log_service import AuditLogService
        
        fake_id = uuid4()
        name = await AuditLogService.resolve_entity_name(
            async_session, "unknown_type", fake_id
        )
        assert name == str(fake_id)
    
    @pytest.mark.asyncio
    async def test_resolve_missing_entity_returns_unknown(self, async_session):
        """Entity that doesn't exist should return 'Unknown'."""
        from app.services.audit_log_service import AuditLogService
        
        fake_id = uuid4()
        name = await AuditLogService.resolve_entity_name(
            async_session, "team_node", fake_id
        )
        assert name == "Unknown"
