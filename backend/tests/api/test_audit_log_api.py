"""
Tests for Audit Log API endpoints.

TDD: These tests are written BEFORE implementation to define expected behavior.
"""
import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4
from unittest.mock import patch

from app.models.user import User, UserRole
from app.models.team import TeamNode, TeamEra
from app.models.edit import EditHistory
from app.models.enums import EditStatus, EditAction


class TestAuditLogListEndpoint:
    """Test GET /api/v1/audit-log endpoint."""
    
    @pytest.fixture
    async def admin_user(self, isolated_session):
        """Create an admin user."""
        user = User(
            user_id=uuid4(),
            email="api_admin@example.com",
            google_id="api_admin_id",
            display_name="API Admin",
            role=UserRole.ADMIN
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def moderator_user(self, isolated_session):
        """Create a moderator user."""
        user = User(
            user_id=uuid4(),
            email="api_mod@example.com",
            google_id="api_mod_id",
            display_name="API Mod",
            role=UserRole.MODERATOR
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def editor_user(self, isolated_session):
        """Create an editor user."""
        user = User(
            user_id=uuid4(),
            email="api_editor@example.com",
            google_id="api_editor_id",
            display_name="API Editor",
            role=UserRole.EDITOR
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def test_team_node(self, isolated_session, editor_user):
        """Create a team node for testing."""
        node = TeamNode(
            legal_name="API Test Team",
            display_name="API Team",
            founding_year=2020,
            created_by=editor_user.user_id
        )
        isolated_session.add(node)
        await isolated_session.flush()
        return node
    
    @pytest.fixture
    async def sample_edits(self, isolated_session, editor_user, admin_user, test_team_node):
        """Create a variety of edits for testing filters."""
        edits = []
        
        # Pending edit
        pending = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.PENDING,
            snapshot_after={"legal_name": "Pending Change"}
        )
        isolated_session.add(pending)
        edits.append(pending)
        
        # Approved edit
        approved = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "Old"},
            snapshot_after={"legal_name": "Approved Change"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow() - timedelta(hours=1)
        )
        isolated_session.add(approved)
        edits.append(approved)
        
        # Rejected edit
        rejected = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.REJECTED,
            snapshot_after={"legal_name": "Rejected Change"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow(),
            review_notes="Not appropriate"
        )
        isolated_session.add(rejected)
        edits.append(rejected)
        
        # Reverted edit
        reverted = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.REVERTED,
            snapshot_before={"legal_name": "Before Revert"},
            snapshot_after={"legal_name": "Reverted Change"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow() - timedelta(hours=2),
            reverted_by=admin_user.user_id,
            reverted_at=datetime.utcnow()
        )
        isolated_session.add(reverted)
        edits.append(reverted)
        
        await isolated_session.commit()
        return edits
    
    @pytest.mark.asyncio
    async def test_list_defaults_to_pending(self, client, isolated_session, admin_user, sample_edits):
        """List endpoint should default to showing only pending edits."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.user_id)})
        
        response = await client.get(
            "/api/v1/audit-log",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1  # Only the pending edit
        assert data["items"][0]["status"] == "PENDING"
    
    @pytest.mark.asyncio
    async def test_list_filter_by_status(self, client, isolated_session, admin_user, sample_edits):
        """Can filter by status."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.user_id)})
        
        response = await client.get(
            "/api/v1/audit-log?status=APPROVED&status=REJECTED",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        statuses = {item["status"] for item in data["items"]}
        assert statuses == {"APPROVED", "REJECTED"}
    
    @pytest.mark.asyncio
    async def test_list_sorted_newest_first(self, client, isolated_session, admin_user, sample_edits):
        """Edits should be sorted by created_at descending (newest first)."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.user_id)})
        
        response = await client.get(
            "/api/v1/audit-log?status=PENDING&status=APPROVED&status=REJECTED&status=REVERTED",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        # Verify descending order by submitted_at
        for i in range(len(items) - 1):
            assert items[i]["submitted_at"] >= items[i + 1]["submitted_at"]
    
    @pytest.mark.asyncio
    async def test_moderator_can_access(self, client, isolated_session, moderator_user, sample_edits):
        """Moderators can access the audit log."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(moderator_user.user_id)})
        
        response = await client.get(
            "/api/v1/audit-log",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_editor_cannot_access(self, client, isolated_session, editor_user, sample_edits):
        """Regular editors cannot access the audit log."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(editor_user.user_id)})
        
        response = await client.get(
            "/api/v1/audit-log",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403


class TestAuditLogPendingCount:
    """Test GET /api/v1/audit-log/pending-count endpoint."""
    
    @pytest.fixture
    async def admin_user(self, isolated_session):
        """Create an admin user."""
        user = User(
            user_id=uuid4(),
            email="count_admin@example.com",
            google_id="count_admin_id",
            display_name="Count Admin",
            role=UserRole.ADMIN
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def pending_edits(self, isolated_session, admin_user):
        """Create some pending edits."""
        entity_id = uuid4()
        for i in range(3):
            edit = EditHistory(
                entity_type="team_node",
                entity_id=entity_id,
                user_id=admin_user.user_id,
                action=EditAction.UPDATE,
                status=EditStatus.PENDING,
                snapshot_after={"version": i}
            )
            isolated_session.add(edit)
        await isolated_session.commit()
    
    @pytest.mark.asyncio
    async def test_pending_count_returns_correct_count(self, client, isolated_session, admin_user, pending_edits):
        """Pending count endpoint returns correct number."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.user_id)})
        
        response = await client.get(
            "/api/v1/audit-log/pending-count",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3


class TestAuditLogDetailEndpoint:
    """Test GET /api/v1/audit-log/{edit_id} endpoint."""
    
    @pytest.fixture
    async def admin_user(self, isolated_session):
        """Create an admin user."""
        user = User(
            user_id=uuid4(),
            email="detail_admin@example.com",
            google_id="detail_admin_id",
            display_name="Detail Admin",
            role=UserRole.ADMIN
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def editor_user(self, isolated_session):
        """Create an editor user."""
        user = User(
            user_id=uuid4(),
            email="detail_editor@example.com",
            google_id="detail_editor_id",
            display_name="Detail Editor",
            role=UserRole.EDITOR
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def test_team_node(self, isolated_session, editor_user):
        """Create a team node for testing."""
        node = TeamNode(
            legal_name="Detail Test Team",
            display_name="Detail Team",
            founding_year=2020,
            created_by=editor_user.user_id
        )
        isolated_session.add(node)
        await isolated_session.flush()
        return node
    
    @pytest.fixture
    async def approved_edit(self, isolated_session, editor_user, admin_user, test_team_node):
        """Create an approved edit."""
        edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "Old Name"},
            snapshot_after={"legal_name": "Detail Test Team"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow()
        )
        isolated_session.add(edit)
        await isolated_session.commit()
        return edit
    
    @pytest.mark.asyncio
    async def test_get_detail_returns_full_info(self, client, isolated_session, admin_user, approved_edit, test_team_node):
        """Detail endpoint returns full edit information with resolved names."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.user_id)})
        
        response = await client.get(
            f"/api/v1/audit-log/{approved_edit.edit_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["edit_id"] == str(approved_edit.edit_id)
        assert data["status"] == "APPROVED"
        assert data["entity_name"] == "Detail Team"  # Resolved name
        assert "snapshot_before" in data
        assert "snapshot_after" in data
        assert "can_revert" in data  # Permission flags
    
    @pytest.mark.asyncio
    async def test_get_detail_not_found(self, client, isolated_session, admin_user):
        """Returns 404 for non-existent edit."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.user_id)})
        
        response = await client.get(
            f"/api/v1/audit-log/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404


class TestAuditLogRevertEndpoint:
    """Test POST /api/v1/audit-log/{edit_id}/revert endpoint."""
    
    @pytest.fixture
    async def admin_user(self, isolated_session):
        """Create an admin user."""
        user = User(
            user_id=uuid4(),
            email="revert_api_admin@example.com",
            google_id="revert_api_admin_id",
            display_name="Revert API Admin",
            role=UserRole.ADMIN
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def moderator_user(self, isolated_session):
        """Create a moderator user."""
        user = User(
            user_id=uuid4(),
            email="revert_api_mod@example.com",
            google_id="revert_api_mod_id",
            display_name="Revert API Mod",
            role=UserRole.MODERATOR
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def editor_user(self, isolated_session):
        """Create an editor user."""
        user = User(
            user_id=uuid4(),
            email="revert_api_editor@example.com",
            google_id="revert_api_editor_id",
            display_name="Revert API Editor",
            role=UserRole.EDITOR
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def test_team_node(self, isolated_session, editor_user):
        """Create a team node for testing."""
        node = TeamNode(
            legal_name="Revert API Team",
            display_name="Revert Team",
            founding_year=2020,
            created_by=editor_user.user_id
        )
        isolated_session.add(node)
        await isolated_session.flush()
        return node
    
    @pytest.fixture
    async def approved_edit(self, isolated_session, editor_user, admin_user, test_team_node):
        """Create an approved edit that can be reverted."""
        edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "Old Name"},
            snapshot_after={"legal_name": "Revert API Team"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow()
        )
        isolated_session.add(edit)
        await isolated_session.commit()
        return edit
    
    @pytest.mark.asyncio
    async def test_revert_success(self, client, isolated_session, admin_user, approved_edit):
        """Successfully revert an approved edit."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.user_id)})
        
        response = await client.post(
            f"/api/v1/audit-log/{approved_edit.edit_id}/revert",
            headers={"Authorization": f"Bearer {token}"},
            json={"notes": "Reverting for testing"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REVERTED"
    
    @pytest.mark.asyncio
    async def test_moderator_cannot_revert_admin_edit(self, client, isolated_session, admin_user, moderator_user, test_team_node):
        """Moderator cannot revert an admin's edit."""
        from app.core.security import create_access_token
        
        # Create edit by admin
        admin_edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=admin_user.user_id,  # Admin submitted
            action=EditAction.UPDATE,
            status=EditStatus.APPROVED,
            snapshot_before={"legal_name": "Admin Old"},
            snapshot_after={"legal_name": "Admin New"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow()
        )
        isolated_session.add(admin_edit)
        await isolated_session.commit()
        
        token = create_access_token({"sub": str(moderator_user.user_id)})
        response = await client.post(
            f"/api/v1/audit-log/{admin_edit.edit_id}/revert",
            headers={"Authorization": f"Bearer {token}"},
            json={}
        )
        
        assert response.status_code == 403


class TestAuditLogReapplyEndpoint:
    """Test POST /api/v1/audit-log/{edit_id}/reapply endpoint."""
    
    @pytest.fixture
    async def admin_user(self, isolated_session):
        """Create an admin user."""
        user = User(
            user_id=uuid4(),
            email="reapply_api_admin@example.com",
            google_id="reapply_api_admin_id",
            display_name="Reapply API Admin",
            role=UserRole.ADMIN
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def editor_user(self, isolated_session):
        """Create an editor user."""
        user = User(
            user_id=uuid4(),
            email="reapply_api_editor@example.com",
            google_id="reapply_api_editor_id",
            display_name="Reapply API Editor",
            role=UserRole.EDITOR
        )
        isolated_session.add(user)
        await isolated_session.flush()
        return user
    
    @pytest.fixture
    async def test_team_node(self, isolated_session, editor_user):
        """Create a team node for testing."""
        node = TeamNode(
            legal_name="Reapply API Team",
            display_name="Reapply Team",
            founding_year=2020,
            created_by=editor_user.user_id
        )
        isolated_session.add(node)
        await isolated_session.flush()
        return node
    
    @pytest.fixture
    async def reverted_edit(self, isolated_session, editor_user, admin_user, test_team_node):
        """Create a reverted edit that can be re-applied."""
        edit = EditHistory(
            entity_type="team_node",
            entity_id=test_team_node.node_id,
            user_id=editor_user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.REVERTED,
            snapshot_before={"legal_name": "Old Name"},
            snapshot_after={"legal_name": "Reapply API Team"},
            reviewed_by=admin_user.user_id,
            reviewed_at=datetime.utcnow() - timedelta(hours=1),
            reverted_by=admin_user.user_id,
            reverted_at=datetime.utcnow()
        )
        isolated_session.add(edit)
        await isolated_session.commit()
        return edit
    
    @pytest.mark.asyncio
    async def test_reapply_success(self, client, isolated_session, admin_user, reverted_edit):
        """Successfully re-apply a reverted edit."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.user_id)})
        
        response = await client.post(
            f"/api/v1/audit-log/{reverted_edit.edit_id}/reapply",
            headers={"Authorization": f"Bearer {token}"},
            json={"notes": "Re-applying after review"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"


