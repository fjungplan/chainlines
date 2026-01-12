import pytest
from pydantic import ValidationError
from app.schemas.user import UserAdminRead
from app.models.enums import UserRole
import uuid
from datetime import datetime

def test_user_admin_read_validation_system_email():
    """
    Test that the UserAdminRead schema validates (or fails to validate) 
    the system user's email format.
    
    Before the fix, this should raise a ValidationError because 'system@chainlines.local' 
    is rejected by Pydantic's strict EmailStr.
    """
    user_data = {
        "user_id": uuid.uuid4(),
        "role": UserRole.ADMIN,
        "created_at": datetime.now(),
        "email": "system@chainlines.local",  # The problematic email
        "google_id": "system_smart_scraper",
        "display_name": "smart_scraper",
        "is_banned": False,
        "approved_edits_count": 0
    }

    # In the "Red" phase, we expect this to FAIL if the schema uses EmailStr
    # So we assert that it raises ValidationError to prove the issue exists
    # OR, if following strict TDD for the *fix*, we write the test expecting success 
    # and watch it fail. The user asked for "Test first", usually meaning 
    # "write the test that SHOULD pass but currently fails".
    
    # So I will write the expectation that it SHOULD VALIDATE, and expect the test runner to show failure.
    
    model = UserAdminRead(**user_data)
    assert model.email == "system@chainlines.local"
