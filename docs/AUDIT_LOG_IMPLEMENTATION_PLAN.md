# Audit Log Implementation Plan

Rename and refactor the existing Moderation Queue into a unified **Audit Log** that serves as both a moderation queue (for pending approvals) and an audit history (for all changes).

## User Review Required

> [!IMPORTANT]
> **6 Entity Types**: This plan covers Teams, Eras, Sponsors, Brands, Sponsor Links, and Lineage Events. Each needs a tailored diff view component.

> [!WARNING]
> **Breaking Change**: The route `/moderation` will be renamed to `/audit-log`. Existing bookmarks will break.

---

## Proposed Changes

### Backend: Enums & Models

#### [MODIFY] [enums.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/enums.py)
- Add `REVERTED = "REVERTED"` to [EditStatus](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/enums.py#14-19) enum
- Update [EditType](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/enums.py#27-33) enum to include all 6 entity types explicitly:
  ```python
  class EditType(str, enum.Enum):
      TEAM = "TEAM"           # TeamNode changes
      ERA = "ERA"             # TeamEra changes  
      SPONSOR = "SPONSOR"     # SponsorMaster changes
      BRAND = "BRAND"         # SponsorBrand changes
      SPONSOR_LINK = "SPONSOR_LINK"  # Team-Sponsor link changes
      LINEAGE = "LINEAGE"     # Merge/Split events
  ```

#### [MODIFY] [edit.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/edit.py)
- Add `reverted_at` column (TIMESTAMP, nullable)
- Add `reverted_by` column (GUID FK to users, nullable)

---

### Backend: Schemas

#### [MODIFY] [moderation.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/schemas/moderation.py)
Rename to `audit_log.py` and update schemas:

```python
class AuditLogEntryResponse(BaseModel):
    edit_id: str
    status: str  # PENDING, APPROVED, REJECTED, REVERTED
    entity_type: str  # TEAM, ERA, SPONSOR, BRAND, SPONSOR_LINK, LINEAGE
    entity_name: str  # Human-readable name (resolved from UUID)
    action: str  # CREATE, UPDATE, DELETE
    submitted_by: UserSummary  # {user_id, display_name, email}
    submitted_at: datetime
    reviewed_by: Optional[UserSummary]
    reviewed_at: Optional[datetime]
    summary: str  # Reason → Internal Note → Rejection notes (priority)
    
class AuditLogDetailResponse(BaseModel):
    # All fields from AuditLogEntryResponse plus:
    snapshot_before: Dict[str, Any]  # With human-readable names
    snapshot_after: Dict[str, Any]   # With human-readable names
    source_url: Optional[str]
    source_notes: Optional[str]
    review_notes: Optional[str]
    can_approve: bool  # Based on current user role vs submitter role
    can_reject: bool
    can_revert: bool   # Only if most recent approved
    can_reapply: bool  # Only if reverted/rejected and chronologically valid

class AuditLogFilters(BaseModel):
    status: Optional[List[str]] = ["PENDING"]  # Default to pending only
    entity_type: Optional[str] = None
    user_id: Optional[str] = None  # Filter by submitter
    entity_id: Optional[str] = None  # Filter by specific entity
    entity_search: Optional[str] = None  # Search by entity name
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    
class RevertRequest(BaseModel):
    notes: Optional[str] = None
    
class ReapplyRequest(BaseModel):
    notes: Optional[str] = None
```

---

### Backend: Service Layer

#### [MODIFY] [moderation_service.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/services/moderation_service.py)
Rename to `audit_log_service.py` and add:

1. **Human-readable name resolution**:
   ```python
   async def resolve_entity_name(session, entity_type, entity_id, snapshot) -> str:
       """Resolve UUID references to human-readable names."""
   ```

2. **Revert logic**:
   ```python
   async def revert_edit(session, edit, admin, notes) -> ReviewEditResponse:
       """Revert the most recent approved edit for an entity."""
       # Validate: is this the most recent approved edit?
       # Validate: permission check (mod can't revert admin edits)
       # Restore snapshot_before to entity
       # Set status = REVERTED, reverted_by, reverted_at
   ```

3. **Re-apply logic**:
   ```python
   async def reapply_edit(session, edit, admin, notes) -> ReviewEditResponse:
       """Re-apply a reverted or rejected edit."""
       # Validate: chronologically valid (no newer approved edits)
       # Validate: permission check
       # Apply snapshot_after to entity
       # Set status = APPROVED
   ```

4. **Permission checking**:
   ```python
   def can_moderate_edit(current_user, edit_submitter) -> bool:
       """Mods cannot override admin decisions."""
       if current_user.role == UserRole.ADMIN:
           return True
       if edit_submitter.role == UserRole.ADMIN:
           return False  # Mods can't touch admin edits
       return current_user.role == UserRole.MODERATOR
   ```

5. **Pending count endpoint** (for notification badge):
   ```python
   async def get_pending_count(session) -> int:
       """Return count of pending edits."""
   ```

---

### Backend: API Routes

#### [MODIFY] [moderation.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1/moderation.py)
Rename to `audit_log.py` and update:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/audit-log` | GET | List edits with filters, pagination, sorting (newest first) |
| `/api/v1/audit-log/{edit_id}` | GET | Get single edit with full detail + resolved names |
| `/api/v1/audit-log/{edit_id}/approve` | POST | Approve pending edit |
| `/api/v1/audit-log/{edit_id}/reject` | POST | Reject pending edit (notes required) |
| `/api/v1/audit-log/{edit_id}/revert` | POST | Revert approved edit |
| `/api/v1/audit-log/{edit_id}/reapply` | POST | Re-apply reverted/rejected edit |
| `/api/v1/audit-log/stats` | GET | Get stats + pending count |
| `/api/v1/audit-log/pending-count` | GET | Just the pending count (for badge) |

All endpoints require `MODERATOR` or `ADMIN` role.

---

### Frontend: API Client

#### [MODIFY] [moderation.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/api/moderation.js)
Rename to `auditLog.js` and update:
- Change base URL from `/moderation` to `/audit-log`
- Add methods: `getEditDetail`, `revertEdit`, `reapplyEdit`, `getPendingCount`

---

### Frontend: List Page

#### [NEW] [AuditLogPage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/AuditLogPage.jsx)
Pattern: Match [TeamMaintenancePage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/TeamMaintenancePage.jsx) structure:
- `maintenance-page-container` wrapper
- `maintenance-content-card` inner container
- Header with title + back link to admin panel
- Filter controls section
- Sortable table with columns: Status, Entity Type, Entity Name, Action, Submitted By, Date, Reviewed By, Summary
- Row click → navigate to detail view
- Default sort: newest first (`created_at DESC`)

#### [NEW] [AuditLogPage.css](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/AuditLogPage.css)
- Status badges with icons
- Filter bar styling
- Match existing maintenance page CSS patterns

---

### Frontend: Detail/Editor Page

#### [NEW] [AuditLogEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/AuditLogEditor.jsx)
Pattern: Match `TeamNodeEditor.jsx` / `UserEditor.jsx` structure:
- Header with back button + edit title
- Two-column diff layout: Before (left) | After (right)
- Route entity type to appropriate diff component
- Action buttons based on status + permissions:
  - Pending: Approve, Reject (modal for notes)
  - Approved: Revert (if most recent)
  - Rejected/Reverted: Re-apply (if chronologically valid)
- Metadata section: Submitted by, Date, Reviewer, Source URL/Notes

#### [NEW] [AuditLogEditor.css](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/AuditLogEditor.css)

---

### Frontend: Diff Components (6 types)

#### [NEW] [diffs/TeamDiff.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/diffs/TeamDiff.jsx)
Field-by-field diff for TeamNode: `legal_name`, `display_name`, `founding_year`, `dissolution_year`, `is_protected`

#### [NEW] [diffs/EraDiff.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/diffs/EraDiff.jsx)
Field-by-field diff for TeamEra: `registered_name`, `uci_code`, `country_code`, `tier_level`, `valid_from`, `season_year`

#### [NEW] [diffs/SponsorDiff.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/diffs/SponsorDiff.jsx)
Field-by-field diff for SponsorMaster: `legal_name`, `display_name`, `industry_sector`

#### [NEW] [diffs/BrandDiff.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/diffs/BrandDiff.jsx)
Field-by-field diff for SponsorBrand: `brand_name`, `display_name`, `default_hex_color` (with color swatch)

#### [NEW] [diffs/SponsorLinkDiff.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/diffs/SponsorLinkDiff.jsx)
Field-by-field diff: `era_name`, `brand_name`, `prominence`, `rank`, `hex_color_override`

#### [NEW] [diffs/LineageDiff.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/diffs/LineageDiff.jsx)
For merge/split: Show predecessor team(s) names → successor team(s) names, event type, year

#### [NEW] [diffs/DiffTable.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/diffs/DiffTable.jsx)
Shared component for rendering field-by-field comparison table with highlight for changed values

#### [NEW] [diffs/DiffTable.css](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/diffs/DiffTable.css)

---

### Frontend: Navigation & Badge

#### [MODIFY] [UserMenu.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/layout/UserMenu.jsx)
1. Change "Moderation Queue" → "Audit Log"
2. Change route from `/moderation` to `/audit-log`
3. Show for both Moderators AND Admins (currently admin-only)
4. Add `NotificationBadge` component next to menu item

#### [MODIFY] [UserMenu.css](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/UserMenu.css)
- Add badge styles for pending count

#### [NEW] [NotificationBadge.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/common/NotificationBadge.jsx)
```jsx
// Yellow/bright circle with number, positioned bottom-right of parent
function NotificationBadge({ count }) {
  if (!count || count <= 0) return null;
  return <span className="notification-badge">{count}</span>;
}
```

#### [NEW] [NotificationBadge.css](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/common/NotificationBadge.css)

#### [MODIFY] User avatar button in [UserMenu.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/layout/UserMenu.jsx)
- Wrap avatar with container that can show `NotificationBadge`

---

### Frontend: Routing

#### [MODIFY] [App.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/App.jsx)
- Remove `/moderation` route
- Add `/audit-log` route → `AuditLogPage`
- Add `/audit-log/:editId` route → `AuditLogEditor`

---

### Frontend: Pending Count Context (Optional Enhancement)

#### [NEW] [AuditLogContext.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/contexts/AuditLogContext.jsx)
- Fetch pending count on mount (for mods/admins)
- Poll every 60 seconds to keep badge updated
- Expose `pendingCount` to components

---

### Delete Old Files

#### [DELETE] [ModerationQueuePage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/ModerationQueuePage.jsx)
#### [DELETE] [ModerationQueuePage.css](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/ModerationQueuePage.css)

---

## Error Handling Strategy

| Scenario | Handling |
|----------|----------|
| Edit not found | 404 with "Edit not found" message |
| Edit not in expected status | 400 with "Edit is not [pending/approved/etc]" |
| Permission denied (mod vs admin) | 403 with "Insufficient permissions to modify this edit" |
| Chronologically invalid reapply | 400 with "Cannot re-apply: newer edits exist" |
| Revert non-latest edit | 400 with "Can only revert the most recent approved edit" |
| Rejection without notes | 400 with "Rejection notes are required" |
| Network errors | Frontend toast with retry option |

---

## Verification Plan

### Automated Tests

#### Backend Tests

**Existing tests to update:**
- [test_moderation_service_full.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/services/test_moderation_service_full.py) - Rename and extend with revert/reapply tests

**New tests to add:**

| Test File | Test Cases |
|-----------|------------|
| `tests/services/test_audit_log_service.py` | `test_revert_most_recent_approved`, `test_revert_fails_if_not_latest`, `test_reapply_reverted_edit`, `test_reapply_fails_chronologically`, `test_mod_cannot_revert_admin_edit`, `test_resolve_entity_names` |
| `tests/api/test_audit_log_api.py` | `test_list_with_filters`, `test_get_detail_with_resolved_names`, `test_approve_endpoint`, `test_reject_requires_notes`, `test_revert_endpoint`, `test_reapply_endpoint`, `test_pending_count_endpoint`, `test_moderator_access`, `test_admin_access` |

**Run command:**
```bash
cd backend && pytest tests/services/test_audit_log_service.py tests/api/test_audit_log_api.py -v
```

#### Frontend Tests

| Test File | Test Cases |
|-----------|------------|
| `tests/pages/maintenance/AuditLogPage.test.jsx` | `renders filter controls`, `loads and displays edits`, `filters by status`, `sorts by date`, `navigates to detail on row click` |
| `tests/components/AuditLogEditor.test.jsx` | `renders diff view`, `shows approve/reject for pending`, `shows revert for approved`, `approve calls API`, `reject requires notes` |
| `tests/components/NotificationBadge.test.jsx` | `renders nothing when count is 0`, `displays count`, `applies correct styling` |

**Run command:**
```bash
cd frontend && npm test
```

### Manual Verification

1. **Login as Admin** → Verify "Audit Log" appears in user menu with pending badge
2. **Submit an edit as Editor** → Verify it appears in Audit Log as pending
3. **View edit detail** → Verify before/after diff shows human-readable names
4. **Approve edit** → Verify status changes, entity updated
5. **Revert approved edit** → Verify status = REVERTED, entity restored
6. **Re-apply reverted edit** → Verify status = APPROVED, entity updated again
7. **Reject pending edit** → Verify notes are required
8. **Login as Moderator** → Verify cannot revert admin-submitted edits
9. **Filter tests** → Verify all filters work as expected
10. **Badge updates** → Verify pending count badge updates after actions
