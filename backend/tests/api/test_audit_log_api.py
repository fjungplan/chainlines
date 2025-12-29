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
        assert len(data) == 1  # Only the pending edit
        assert data[0]["status"] == "PENDING"
    
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
        assert len(data) == 2
        statuses = {item["status"] for item in data}
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
        # Verify descending order by submitted_at
        for i in range(len(data) - 1):
            assert data[i]["submitted_at"] >= data[i + 1]["submitted_at"]
    
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

