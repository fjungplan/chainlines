"""Tests for Audit Log filtering functionality."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid

from app.models.user import User
from app.models.edit import EditHistory
from app.models.enums import UserRole, EditAction, EditStatus


@pytest.fixture
async def moderator_user(db_session: AsyncSession):
    """Create a moderator user for testing."""
    user = User(
        user_id=uuid.uuid4(),
        google_id="test_google_id_moderator",
        email="moderator@test.com",
        display_name="Test Moderator",
        role=UserRole.MODERATOR
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_edits(db_session: AsyncSession, moderator_user: User):
    """Create sample edit history entries for testing filters."""
    edits = []
    
    # Create edits with different entity types
    # TeamNode edit (PENDING)
    edit1 = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="TeamNode",
        entity_id=uuid.uuid4(),
        user_id=moderator_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        snapshot_after={"legal_name": "Test Team 1"},
        created_at=datetime.utcnow() - timedelta(days=5)
    )
    edits.append(edit1)
    
    # TeamEra edit (APPROVED)
    edit2 = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="TeamEra",
        entity_id=uuid.uuid4(),
        user_id=moderator_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.APPROVED,
        snapshot_after={"registered_name": "Test Era 1"},
        created_at=datetime.utcnow() - timedelta(days=4),
        reviewed_by=moderator_user.user_id,
        reviewed_at=datetime.utcnow() - timedelta(days=4)
    )
    edits.append(edit2)
    
    # SponsorMaster edit (REJECTED)
    edit3 = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="SponsorMaster",
        entity_id=uuid.uuid4(),
        user_id=moderator_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.REJECTED,
        snapshot_after={"legal_name": "Test Sponsor"},
        created_at=datetime.utcnow() - timedelta(days=3),
        reviewed_by=moderator_user.user_id,
        reviewed_at=datetime.utcnow() - timedelta(days=3)
    )
    edits.append(edit3)
    
    # Another TeamNode edit (APPROVED)
    edit4 = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="TeamNode",
        entity_id=uuid.uuid4(),
        user_id=moderator_user.user_id,
        action=EditAction.UPDATE,
        status=EditStatus.APPROVED,
        snapshot_after={"legal_name": "Test Team 2"},
        created_at=datetime.utcnow() - timedelta(days=2),
        reviewed_by=moderator_user.user_id,
        reviewed_at=datetime.utcnow() - timedelta(days=2)
    )
    edits.append(edit4)
    
    # LineageEvent edit (PENDING)
    edit5 = EditHistory(
        edit_id=uuid.uuid4(),
        entity_type="LineageEvent",
        entity_id=uuid.uuid4(),
        user_id=moderator_user.user_id,
        action=EditAction.CREATE,
        status=EditStatus.PENDING,
        snapshot_after={"predecessor_id": str(uuid.uuid4()), "successor_id": str(uuid.uuid4())},
        created_at=datetime.utcnow() - timedelta(days=1)
    )
    edits.append(edit5)
    
    for edit in edits:
        db_session.add(edit)
    
    await db_session.commit()
    return edits


@pytest.fixture
def moderator_token(moderator_user: User) -> str:
    """Generate JWT token for moderator user."""
    from app.core.security import create_access_token
    return create_access_token({"sub": str(moderator_user.user_id)})


class TestAuditLogFilters:
    """Test suite for audit log filtering."""
    
    @pytest.mark.asyncio
    async def test_entity_type_filter_case_insensitive(
        self, 
        client: AsyncClient, 
        moderator_user: User,
        moderator_token: str,
        sample_edits: list
    ):
        """Entity type filter should work case-insensitively."""
        # Test lowercase input (frontend sends "team_node")
        # Pass all statuses to avoid default PENDING filter
        response = await client.get(
            "/api/v1/audit-log",
            params={
                "entity_type": "team_node",
                "status": ["PENDING", "APPROVED", "REJECTED", "REVERTED"],
                "limit": 100
            },
            headers={"Authorization": f"Bearer {moderator_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find the 2 TeamNode edits (1 PENDING, 1 APPROVED)
        assert len(data["items"]) == 2, f"Expected 2 TeamNode edits, got {len(data['items'])}"
        for item in data["items"]:
            assert item["entity_type"] == "TeamNode"
    
    @pytest.mark.asyncio
    async def test_entity_type_filter_exact_case(
        self, 
        client: AsyncClient, 
        moderator_user: User,
        moderator_token: str,
        sample_edits: list
    ):
        """Entity type filter should work with exact case match."""
        response = await client.get(
            "/api/v1/audit-log",
            params={
                "entity_type": "TeamEra",
                "status": ["PENDING", "APPROVED", "REJECTED", "REVERTED"],
                "limit": 100
            },
            headers={"Authorization": f"Bearer {moderator_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find the 1 TeamEra edit
        assert len(data["items"]) == 1
        assert data["items"][0]["entity_type"] == "TeamEra"
    
    @pytest.mark.asyncio
    async def test_status_filter_single(
        self, 
        client: AsyncClient, 
        moderator_user: User,
        moderator_token: str,
        sample_edits: list
    ):
        """Status filter should work with a single status."""
        response = await client.get(
            "/api/v1/audit-log",
            params={"status": ["APPROVED"], "limit": 100},
            headers={"Authorization": f"Bearer {moderator_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find 2 APPROVED edits
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert item["status"] == "APPROVED"
    
    @pytest.mark.asyncio
    async def test_status_filter_multiple(
        self, 
        client: AsyncClient, 
        moderator_user: User,
        moderator_token: str,
        sample_edits: list
    ):
        """Status filter should work with multiple statuses."""
        response = await client.get(
            "/api/v1/audit-log",
            params={"status": ["PENDING", "REJECTED"], "limit": 100},
            headers={"Authorization": f"Bearer {moderator_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find 3 edits (2 PENDING + 1 REJECTED)
        assert len(data["items"]) == 3
        statuses = {item["status"] for item in data["items"]}
        assert statuses == {"PENDING", "REJECTED"}
    
    @pytest.mark.asyncio
    async def test_combined_filters(
        self, 
        client: AsyncClient, 
        moderator_user: User,
        moderator_token: str,
        sample_edits: list
    ):
        """Entity type and status filters should work together."""
        response = await client.get(
            "/api/v1/audit-log",
            params={
                "entity_type": "team_node",  # lowercase
                "status": ["APPROVED"],
                "limit": 100
            },
            headers={"Authorization": f"Bearer {moderator_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find 1 APPROVED TeamNode edit
        assert len(data["items"]) == 1
        assert data["items"][0]["entity_type"] == "TeamNode"
        assert data["items"][0]["status"] == "APPROVED"
