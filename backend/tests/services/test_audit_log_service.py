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


class TestCanModerateEdit:
    """Test permission checking for edit moderation."""
    
    @pytest.fixture
    async def admin_user(self, async_session):
        """Create an admin user."""
        from app.models.enums import UserRole
        user = User(
            user_id=uuid4(),
            email="admin@example.com",
            google_id="admin_google_id",
            display_name="Admin User",
            role=UserRole.ADMIN
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def moderator_user(self, async_session):
        """Create a moderator user."""
        from app.models.enums import UserRole
        user = User(
            user_id=uuid4(),
            email="mod@example.com",
            google_id="mod_google_id",
            display_name="Mod User",
            role=UserRole.MODERATOR
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def editor_user(self, async_session):
        """Create an editor user."""
        from app.models.enums import UserRole
        user = User(
            user_id=uuid4(),
            email="editor@example.com",
            google_id="editor_google_id",
            display_name="Editor User",
            role=UserRole.EDITOR
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.mark.asyncio
    async def test_admin_can_moderate_admin_edit(self, async_session, admin_user):
        """Admin can moderate edits submitted by another admin."""
        from app.services.audit_log_service import AuditLogService
        
        another_admin = User(
            user_id=uuid4(),
            email="admin2@example.com",
            google_id="admin2_google_id",
            role=UserRole.ADMIN
        )
        async_session.add(another_admin)
        await async_session.flush()
        
        result = AuditLogService.can_moderate_edit(admin_user, another_admin)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_admin_can_moderate_moderator_edit(self, async_session, admin_user, moderator_user):
        """Admin can moderate edits submitted by a moderator."""
        from app.services.audit_log_service import AuditLogService
        
        result = AuditLogService.can_moderate_edit(admin_user, moderator_user)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_admin_can_moderate_editor_edit(self, async_session, admin_user, editor_user):
        """Admin can moderate edits submitted by an editor."""
        from app.services.audit_log_service import AuditLogService
        
        result = AuditLogService.can_moderate_edit(admin_user, editor_user)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_moderator_can_moderate_editor_edit(self, async_session, moderator_user, editor_user):
        """Moderator can moderate edits submitted by an editor."""
        from app.services.audit_log_service import AuditLogService
        
        result = AuditLogService.can_moderate_edit(moderator_user, editor_user)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_moderator_can_moderate_moderator_edit(self, async_session, moderator_user):
        """Moderator can moderate edits submitted by another moderator."""
        from app.services.audit_log_service import AuditLogService
        
        another_mod = User(
            user_id=uuid4(),
            email="mod2@example.com",
            google_id="mod2_google_id",
            role=UserRole.MODERATOR
        )
        async_session.add(another_mod)
        await async_session.flush()
        
        result = AuditLogService.can_moderate_edit(moderator_user, another_mod)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_moderator_cannot_moderate_admin_edit(self, async_session, moderator_user, admin_user):
        """Moderator CANNOT moderate edits submitted by an admin."""
        from app.services.audit_log_service import AuditLogService
        
        result = AuditLogService.can_moderate_edit(moderator_user, admin_user)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_editor_cannot_moderate_any_edit(self, async_session, editor_user, moderator_user):
        """Editor cannot moderate any edits."""
        from app.services.audit_log_service import AuditLogService
        
        result = AuditLogService.can_moderate_edit(editor_user, moderator_user)
        assert result is False


class TestIsMostRecentApproved:
    """Test chronology checking for revert operations."""
    
    @pytest.fixture
    async def test_user(self, async_session):
        """Create a test user."""
        user = User(
            user_id=uuid4(),
            email="chrono_test@example.com",
            google_id="chrono_test_id",
            display_name="Chrono Test User"
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def test_entity_id(self):
        """Create a consistent entity ID for testing."""
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_single_approved_is_most_recent(self, async_session, test_user, test_entity_id):
        """A single approved edit is the most recent."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        edit = EditHistory(
            entity_type="team_node",
            entity_id=test_entity_id,
            user_id=test_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_after={"test": "data"},
            reviewed_at=datetime.utcnow()
        )
        async_session.add(edit)
        await async_session.commit()
        
        result = await AuditLogService.is_most_recent_approved(async_session, edit)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_older_approved_is_not_most_recent(self, async_session, test_user, test_entity_id):
        """An older approved edit is NOT the most recent."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        from datetime import timedelta
        
        # Create older approved edit
        older_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_entity_id,
            user_id=test_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_after={"version": 1},
            reviewed_at=datetime.utcnow() - timedelta(hours=1)
        )
        async_session.add(older_edit)
        await async_session.flush()
        
        # Create newer approved edit
        newer_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_entity_id,
            user_id=test_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_after={"version": 2},
            reviewed_at=datetime.utcnow()
        )
        async_session.add(newer_edit)
        await async_session.commit()
        
        # Older edit should NOT be most recent
        result = await AuditLogService.is_most_recent_approved(async_session, older_edit)
        assert result is False
        
        # Newer edit SHOULD be most recent
        result = await AuditLogService.is_most_recent_approved(async_session, newer_edit)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_pending_edit_is_not_most_recent_approved(self, async_session, test_user, test_entity_id):
        """A pending edit is not considered 'most recent approved'."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        edit = EditHistory(
            entity_type="team_node",
            entity_id=test_entity_id,
            user_id=test_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.PENDING,
            snapshot_after={"test": "data"}
        )
        async_session.add(edit)
        await async_session.commit()
        
        result = await AuditLogService.is_most_recent_approved(async_session, edit)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_approved_with_pending_sibling_is_still_most_recent(self, async_session, test_user, test_entity_id):
        """An approved edit is still most recent even if there's a newer pending edit."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        from datetime import timedelta
        
        # Create approved edit
        approved_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_entity_id,
            user_id=test_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_after={"version": 1},
            reviewed_at=datetime.utcnow() - timedelta(hours=1)
        )
        async_session.add(approved_edit)
        await async_session.flush()
        
        # Create newer pending edit
        pending_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_entity_id,
            user_id=test_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.PENDING,
            snapshot_after={"version": 2}
        )
        async_session.add(pending_edit)
        await async_session.commit()
        
        # Approved should still be the most recent APPROVED
        result = await AuditLogService.is_most_recent_approved(async_session, approved_edit)
        assert result is True


class TestRevertEdit:
    """Test revert_edit() functionality."""
    
    @pytest.fixture
    async def admin_user(self, async_session):
        """Create an admin user."""
        user = User(
            user_id=uuid4(),
            email="revert_admin@example.com",
            google_id="revert_admin_id",
            display_name="Revert Admin",
            role=UserRole.ADMIN
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def moderator_user(self, async_session):
        """Create a moderator user."""
        user = User(
            user_id=uuid4(),
            email="revert_mod@example.com",
            google_id="revert_mod_id",
            display_name="Revert Mod",
            role=UserRole.MODERATOR
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def editor_user(self, async_session):
        """Create an editor user."""
        user = User(
            user_id=uuid4(),
            email="revert_editor@example.com",
            google_id="revert_editor_id",
            display_name="Revert Editor",
            role=UserRole.EDITOR
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def test_team_node(self, async_session, editor_user):
        """Create a team node for testing."""
        node = TeamNode(
            legal_name="Revert Test Team",
            display_name="Revert Team",
            founding_year=2020,
            created_by=editor_user.user_id
        )
        async_session.add(node)
        await async_session.flush()
        return node
    
    @pytest.fixture
    async def approved_edit(self, async_session, editor_user, test_team_node, admin_user):
        """Create an approved edit that can be reverted."""
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "Old Name"},
            snapshot_after={"legal_name": "Revert Test Team"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow()
        )
        async_session.add(edit)
        await async_session.commit()
        return edit
    
    @pytest.mark.asyncio
    async def test_revert_edit_success(self, async_session, approved_edit, admin_user, test_team_node):
        """Successfully revert an approved edit."""
        from app.services.audit_log_service import AuditLogService
        from app.models.enums import EditStatus
        
        result = await AuditLogService.revert_edit(
            async_session, approved_edit, admin_user, notes="Reverting for test"
        )
        
        assert result.status == "REVERTED"
        assert result.message == "Edit reverted successfully"
        
        # Check edit status was updated
        await async_session.refresh(approved_edit)
        assert approved_edit.status == EditStatus.REVERTED
        assert approved_edit.reverted_by == admin_user.user_id
        assert approved_edit.reverted_at is not None
    
    @pytest.mark.asyncio
    async def test_revert_fails_if_not_most_recent(self, async_session, editor_user, admin_user, test_team_node):
        """Revert should fail if edit is not the most recent approved."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        from datetime import timedelta
        
        # Create older approved edit
        older_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "V1"},
            snapshot_after={"legal_name": "V2"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow() - timedelta(hours=1)
        )
        async_session.add(older_edit)
        await async_session.flush()
        
        # Create newer approved edit
        newer_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "V2"},
            snapshot_after={"legal_name": "V3"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow()
        )
        async_session.add(newer_edit)
        await async_session.commit()
        
        # Try to revert the older edit - should fail
        with pytest.raises(ValueError, match="not the most recent"):
            await AuditLogService.revert_edit(async_session, older_edit, admin_user)
    
    @pytest.mark.asyncio
    async def test_moderator_cannot_revert_admin_edit(self, async_session, admin_user, moderator_user, test_team_node):
        """Moderator cannot revert an edit submitted by an admin."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        # Create an edit submitted by admin
        admin_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=admin_user.user_id,  # Admin submitted this
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "Old"},
            snapshot_after={"legal_name": "New"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow()
        )
        async_session.add(admin_edit)
        await async_session.commit()
        
        # Moderator tries to revert - should fail
        with pytest.raises(PermissionError, match="permission"):
            await AuditLogService.revert_edit(async_session, admin_edit, moderator_user)
    
    @pytest.mark.asyncio
    async def test_revert_pending_edit_fails(self, async_session, editor_user, admin_user, test_team_node):
        """Cannot revert a pending edit."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        pending_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.PENDING,
            snapshot_before={"legal_name": "Old"},
            snapshot_after={"legal_name": "New"}
        )
        async_session.add(pending_edit)
        await async_session.commit()
        
        with pytest.raises(ValueError, match="not approved"):
            await AuditLogService.revert_edit(async_session, pending_edit, admin_user)


class TestReapplyEdit:
    """Test reapply_edit() functionality."""
    
    @pytest.fixture
    async def admin_user(self, async_session):
        """Create an admin user."""
        user = User(
            user_id=uuid4(),
            email="reapply_admin@example.com",
            google_id="reapply_admin_id",
            display_name="Reapply Admin",
            role=UserRole.ADMIN
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def moderator_user(self, async_session):
        """Create a moderator user."""
        user = User(
            user_id=uuid4(),
            email="reapply_mod@example.com",
            google_id="reapply_mod_id",
            display_name="Reapply Mod",
            role=UserRole.MODERATOR
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def editor_user(self, async_session):
        """Create an editor user."""
        user = User(
            user_id=uuid4(),
            email="reapply_editor@example.com",
            google_id="reapply_editor_id",
            display_name="Reapply Editor",
            role=UserRole.EDITOR
        )
        async_session.add(user)
        await async_session.flush()
        return user
    
    @pytest.fixture
    async def test_team_node(self, async_session, editor_user):
        """Create a team node for testing."""
        node = TeamNode(
            legal_name="Reapply Test Team",
            display_name="Reapply Team",
            founding_year=2020,
            created_by=editor_user.user_id
        )
        async_session.add(node)
        await async_session.flush()
        return node
    
    @pytest.fixture
    async def reverted_edit(self, async_session, editor_user, test_team_node, admin_user):
        """Create a reverted edit that can be re-applied."""
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.REVERTED,
            snapshot_before={"legal_name": "Old Name"},
            snapshot_after={"legal_name": "Reapply Test Team"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow(),
            reverted_by=admin_user.user_id,
            reverted_at=datetime.utcnow()
        )
        async_session.add(edit)
        await async_session.commit()
        return edit
    
    @pytest.fixture
    async def rejected_edit(self, async_session, editor_user, test_team_node, admin_user):
        """Create a rejected edit that can be re-applied."""
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.REJECTED,
            snapshot_before={"legal_name": "Old Name"},
            snapshot_after={"legal_name": "Rejected Change"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow(),
            review_notes="Rejected for testing"
        )
        async_session.add(edit)
        await async_session.commit()
        return edit
    
    @pytest.mark.asyncio
    async def test_reapply_reverted_edit_success(self, async_session, reverted_edit, admin_user):
        """Successfully re-apply a reverted edit."""
        from app.services.audit_log_service import AuditLogService
        from app.models.enums import EditStatus
        
        result = await AuditLogService.reapply_edit(
            async_session, reverted_edit, admin_user, notes="Re-applying after review"
        )
        
        assert result.status == "APPROVED"
        assert result.message == "Edit re-applied successfully"
        
        # Check edit status was updated
        await async_session.refresh(reverted_edit)
        assert reverted_edit.status == EditStatus.APPROVED
    
    @pytest.mark.asyncio
    async def test_reapply_rejected_edit_success(self, async_session, rejected_edit, admin_user):
        """Successfully re-apply a rejected edit."""
        from app.services.audit_log_service import AuditLogService
        from app.models.enums import EditStatus
        
        result = await AuditLogService.reapply_edit(
            async_session, rejected_edit, admin_user, notes="Reconsidered, now approved"
        )
        
        assert result.status == "APPROVED"
        
        await async_session.refresh(rejected_edit)
        assert rejected_edit.status == EditStatus.APPROVED
    
    @pytest.mark.asyncio
    async def test_reapply_fails_if_newer_approved_exists(self, async_session, editor_user, admin_user, test_team_node):
        """Re-apply should fail if a newer approved edit exists for same entity."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        from datetime import timedelta
        
        # Create older reverted edit
        older_reverted = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.REVERTED,
            snapshot_before={"legal_name": "V1"},
            snapshot_after={"legal_name": "V2"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow() - timedelta(hours=2),
            reverted_at=datetime.utcnow() - timedelta(hours=1)
        )
        async_session.add(older_reverted)
        await async_session.flush()
        
        # Create newer approved edit
        newer_approved = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "V2"},
            snapshot_after={"legal_name": "V3"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow()
        )
        async_session.add(newer_approved)
        await async_session.commit()
        
        # Try to re-apply the older reverted edit - should fail
        with pytest.raises(ValueError, match="newer approved edit"):
            await AuditLogService.reapply_edit(async_session, older_reverted, admin_user)
    
    @pytest.mark.asyncio
    async def test_moderator_cannot_reapply_admin_edit(self, async_session, admin_user, moderator_user, test_team_node):
        """Moderator cannot re-apply an edit submitted by an admin."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        # Create a reverted edit submitted by admin
        admin_reverted = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=admin_user.user_id,  # Admin submitted this
            action=EditAction.UPDATE,
            status=EditStatus.REVERTED,
            snapshot_before={"legal_name": "Old"},
            snapshot_after={"legal_name": "New"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow(),
            reverted_at=datetime.utcnow()
        )
        async_session.add(admin_reverted)
        await async_session.commit()
        
        # Moderator tries to re-apply - should fail
        with pytest.raises(PermissionError, match="permission"):
            await AuditLogService.reapply_edit(async_session, admin_reverted, moderator_user)
    
    @pytest.mark.asyncio
    async def test_reapply_pending_edit_fails(self, async_session, editor_user, admin_user, test_team_node):
        """Cannot re-apply a pending edit (use approve instead)."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        pending_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.PENDING,
            snapshot_before={"legal_name": "Old"},
            snapshot_after={"legal_name": "New"}
        )
        async_session.add(pending_edit)
        await async_session.commit()
        
        with pytest.raises(ValueError, match="not reverted or rejected"):
            await AuditLogService.reapply_edit(async_session, pending_edit, admin_user)
    
    @pytest.mark.asyncio
    async def test_reapply_already_approved_fails(self, async_session, editor_user, admin_user, test_team_node):
        """Cannot re-apply an already approved edit."""
        from app.services.audit_log_service import AuditLogService
        from app.models.edit import EditHistory
        from app.models.enums import EditStatus, EditAction
        
        approved_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "Old"},
            snapshot_after={"legal_name": "New"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow()
        )
        async_session.add(approved_edit)
        await async_session.commit()
        
        with pytest.raises(ValueError, match="not reverted or rejected"):
            await AuditLogService.reapply_edit(async_session, approved_edit, admin_user)
