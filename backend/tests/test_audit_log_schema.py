"""
Tests for Audit Log schemas, enums, and EditHistory model extensions.

TDD: These tests are written BEFORE implementation to define expected behavior.
"""
import pytest
from datetime import datetime, date
from uuid import uuid4
from pydantic import ValidationError

from app.models.enums import EditStatus, EditAction


class TestEditStatusEnum:
    """Test that EditStatus enum has the required REVERTED value."""
    
    def test_reverted_status_exists(self):
        """REVERTED should be a valid EditStatus value."""
        assert hasattr(EditStatus, 'REVERTED')
        assert EditStatus.REVERTED.value == "REVERTED"
    
    def test_all_statuses_exist(self):
        """All expected statuses should exist."""
        expected = {'PENDING', 'APPROVED', 'REJECTED', 'REVERTED'}
        actual = {s.value for s in EditStatus}
        assert expected.issubset(actual)
    
    def test_status_serializes_to_string(self):
        """EditStatus should serialize to its string value."""
        assert str(EditStatus.REVERTED) == "EditStatus.REVERTED"
        assert EditStatus.REVERTED.value == "REVERTED"


class TestEditHistoryModel:
    """Test EditHistory model with new revert fields."""
    
    @pytest.mark.asyncio
    async def test_edit_history_has_reverted_fields(self, async_session):
        """EditHistory should have reverted_at and reverted_by columns."""
        from app.models.edit import EditHistory
        from app.models.user import User
        
        # Create a test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            google_id="test_google_id",
            display_name="Test User"
        )
        async_session.add(user)
        await async_session.flush()
        
        # Create an EditHistory with the new fields
        edit = EditHistory(
            entity_type="team_node",
            entity_id=uuid4(),
            user_id=user.user_id,
            action=EditAction.UPDATE,
            status=EditStatus.REVERTED,
            snapshot_after={"test": "data"},
            reverted_at=datetime.utcnow(),
            reverted_by=user.user_id
        )
        async_session.add(edit)
        await async_session.commit()
        
        # Verify the fields are stored correctly
        await async_session.refresh(edit)
        assert edit.status == EditStatus.REVERTED
        assert edit.reverted_at is not None
        assert edit.reverted_by == user.user_id
    
    @pytest.mark.asyncio
    async def test_reverted_fields_nullable(self, async_session):
        """reverted_at and reverted_by should be nullable."""
        from app.models.edit import EditHistory
        from app.models.user import User
        
        user = User(
            user_id=uuid4(),
            email="test2@example.com",
            google_id="test_google_id_2",
            display_name="Test User 2"
        )
        async_session.add(user)
        await async_session.flush()
        
        # Create EditHistory without reverted fields
        edit = EditHistory(
            entity_type="team_node",
            entity_id=uuid4(),
            user_id=user.user_id,
            action=EditAction.CREATE,
            status=EditStatus.PENDING,
            snapshot_after={"test": "data"}
        )
        async_session.add(edit)
        await async_session.commit()
        
        await async_session.refresh(edit)
        assert edit.reverted_at is None
        assert edit.reverted_by is None


class TestAuditLogSchemas:
    """Test Pydantic schemas for Audit Log."""
    
    def test_user_summary_schema(self):
        """UserSummary should validate correctly."""
        from app.schemas.audit_log import UserSummary
        
        summary = UserSummary(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            display_name="John Doe",
            email="john@example.com"
        )
        assert summary.display_name == "John Doe"
    
    def test_user_summary_optional_display_name(self):
        """UserSummary display_name should be optional."""
        from app.schemas.audit_log import UserSummary
        
        summary = UserSummary(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            display_name=None,
            email="john@example.com"
        )
        assert summary.display_name is None
    
    def test_audit_log_entry_response(self):
        """AuditLogEntryResponse should validate correctly."""
        from app.schemas.audit_log import AuditLogEntryResponse, UserSummary
        
        entry = AuditLogEntryResponse(
            edit_id="550e8400-e29b-41d4-a716-446655440000",
            status="PENDING",
            entity_type="TEAM",
            entity_name="Team Alpha",
            action="UPDATE",
            submitted_by=UserSummary(
                user_id="550e8400-e29b-41d4-a716-446655440001",
                display_name="Jane Doe",
                email="jane@example.com"
            ),
            submitted_at=datetime.utcnow(),
            reviewed_by=None,
            reviewed_at=None,
            summary="Updated team name"
        )
        assert entry.entity_name == "Team Alpha"
        assert entry.reviewed_by is None
    
    def test_audit_log_detail_response_includes_permissions(self):
        """AuditLogDetailResponse should include action permission flags."""
        from app.schemas.audit_log import AuditLogDetailResponse, UserSummary
        
        detail = AuditLogDetailResponse(
            edit_id="550e8400-e29b-41d4-a716-446655440000",
            status="PENDING",
            entity_type="TEAM",
            entity_name="Team Alpha",
            action="UPDATE",
            submitted_by=UserSummary(
                user_id="550e8400-e29b-41d4-a716-446655440001",
                display_name="Jane Doe",
                email="jane@example.com"
            ),
            submitted_at=datetime.utcnow(),
            reviewed_by=None,
            reviewed_at=None,
            summary="Updated team name",
            snapshot_before={"name": "Old Name"},
            snapshot_after={"name": "New Name"},
            source_url=None,
            source_notes="Correcting typo",
            review_notes=None,
            can_approve=True,
            can_reject=True,
            can_revert=False,
            can_reapply=False
        )
        assert detail.can_approve is True
        assert detail.can_revert is False
    
    def test_revert_request_schema(self):
        """RevertRequest should allow optional notes."""
        from app.schemas.audit_log import RevertRequest
        
        req = RevertRequest(notes="Reverting due to error")
        assert req.notes == "Reverting due to error"
        
        req_no_notes = RevertRequest()
        assert req_no_notes.notes is None
    
    def test_reapply_request_schema(self):
        """ReapplyRequest should allow optional notes."""
        from app.schemas.audit_log import ReapplyRequest
        
        req = ReapplyRequest(notes="Re-applying after fix")
        assert req.notes == "Re-applying after fix"
