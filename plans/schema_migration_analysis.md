# Schema Migration Analysis Report

## 1. Overview

The project is transitioning from an existing schema (with terms like `paying_agent_id`, `snapshot_id`) to a new schema defined in `schema_sql_ddl.sql` and documented in `final_schema_doc.md`. This report provides a deep analysis of the changes required in the codebase.

## 2. Key Concept Changes

### 2.1 Core Entity Renaming

| Old Concept | New Concept | Notes |
|-------------|-------------|-------|
| `paying_agent_id` (implied) | `node_id` (`team_node`) | The persistent team entity is now explicitly called `TeamNode` (was `TeamNode` already) |
| `snapshot_id` | `era_id` (`team_era`) | The season snapshot is now called `TeamEra` (was `TeamEra` already) |
| `contract_id` (in team_sponsor_link) | `link_id` | The sponsorship contract is now called `TeamSponsorLink` (same) |
| `previous_node_id`/`next_node_id` | `predecessor_node_id`/`successor_node_id` | Lineage event columns renamed for clarity |
| `paying_agent` (table) | `team_node` (table) | Table name unchanged (already `team_node`) |

### 2.2 New Columns and Fields

**TeamNode** (`team_node` table) adds:
- `legal_name` (VARCHAR(255) UNIQUE NOT NULL) – internal identifier (PAYING AGENT name)
- `display_name` (VARCHAR(255))
- `owned_by_sponsor_master_id` (UUID) – for pre-2005 sponsor ownership
- `is_protected` (BOOLEAN DEFAULT FALSE)
- `latest_team_name`, `latest_uci_code`, `current_tier` (cached from most recent era)
- `is_active` (generated column)
- `source_url`, `source_notes`
- `created_by`, `last_modified_by` (user audit)

**TeamEra** (`team_era` table) adds:
- `valid_from`, `valid_until` (DATE) – for mid-season changes
- `is_name_auto_generated` (BOOLEAN DEFAULT TRUE)
- `is_manual_override` (already exists)
- `is_auto_filled` (BOOLEAN DEFAULT FALSE)
- `has_license` (BOOLEAN DEFAULT FALSE)
- `source_origin` (VARCHAR(50))
- `source_url`, `source_notes`
- `created_by`, `last_modified_by`

**SponsorMaster** and **SponsorBrand** add audit fields and protection.

**LineageEvent** (`lineage_event` table) adds:
- `event_date` (DATE) – specific date of event
- `source_url`, `source_notes`
- `created_by`, `last_modified_by`

### 2.3 New Tables

1. **`users`** – OAuth authentication and user roles (EDITOR, TRUSTED_EDITOR, MODERATOR, ADMIN)
2. **`edit_history`** – Wikipedia-style revision tracking with full JSON snapshots

## 3. Mapping Table: Old vs New Columns

| Table | Old Column (Current) | New Column (Target) | Change Type | Notes |
|-------|----------------------|---------------------|-------------|-------|
| team_node | `node_id` (UUID) | `node_id` | Unchanged | Primary key |
| team_node | `founding_year` | `founding_year` | Unchanged | |
| team_node | `dissolution_year` | `dissolution_year` | Unchanged | |
| team_node | (none) | `legal_name` | **ADD** | Required, unique |
| team_node | (none) | `display_name` | **ADD** | |
| team_node | (none) | `owned_by_sponsor_master_id` | **ADD** | FK to sponsor_master |
| team_node | (none) | `is_protected` | **ADD** | |
| team_node | (none) | `latest_team_name` | **ADD** | Cached |
| team_node | (none) | `latest_uci_code` | **ADD** | Cached |
| team_node | (none) | `current_tier` | **ADD** | Cached |
| team_node | (none) | `is_active` | **ADD** | Generated column |
| team_node | (none) | `source_url`, `source_notes` | **ADD** | |
| team_node | (none) | `created_by`, `last_modified_by` | **ADD** | FK to users |
| team_era | `era_id` | `era_id` | Unchanged | |
| team_era | `node_id` | `node_id` | Unchanged | FK to team_node |
| team_era | `season_year` | `season_year` | Unchanged | |
| team_era | `registered_name` | `registered_name` | Unchanged | |
| team_era | `uci_code` | `uci_code` | Unchanged | |
| team_era | `tier_level` | `tier_level` | Unchanged | |
| team_era | `source_origin` | `source_origin` | Unchanged | |
| team_era | `is_manual_override` | `is_manual_override` | Unchanged | |
| team_era | (none) | `valid_from`, `valid_until` | **ADD** | Date range |
| team_era | (none) | `is_name_auto_generated` | **ADD** | |
| team_era | (none) | `is_auto_filled` | **ADD** | |
| team_era | (none) | `has_license` | **ADD** | |
| team_era | (none) | `source_url`, `source_notes` | **ADD** | |
| team_era | (none) | `created_by`, `last_modified_by` | **ADD** | |
| lineage_event | `event_id` | `event_id` | Unchanged | |
| lineage_event | `previous_node_id` | `predecessor_node_id` | **RENAME** | FK to team_node |
| lineage_event | `next_node_id` | `successor_node_id` | **RENAME** | FK to team_node |
| lineage_event | `event_year` | `event_year` | Unchanged | |
| lineage_event | `event_type` | `event_type` | Unchanged | |
| lineage_event | `notes` | `notes` | Unchanged | |
| lineage_event | (none) | `event_date` | **ADD** | |
| lineage_event | (none) | `source_url`, `source_notes` | **ADD** | |
| lineage_event | (none) | `created_by`, `last_modified_by` | **ADD** | |
| sponsor_master | (existing columns) | (add `display_name`, `is_protected`, audit fields) | **ADD** | |
| sponsor_brand | (existing columns) | (add `display_name`, audit fields) | **ADD** | |
| team_sponsor_link | `contract_id` | `link_id` | **RENAME** | |
| team_sponsor_link | `snapshot_id` | `era_id` | **RENAME** (already) | Already `era_id` in current? Check. |
| team_sponsor_link | `brand_id` | `brand_id` | Unchanged | |
| team_sponsor_link | `rank_order` | `rank_order` | Unchanged | |
| team_sponsor_link | `prominence_percent` | `prominence_percent` | Unchanged | |
| team_sponsor_link | `hex_color_override` | `hex_color_override` | Unchanged | |
| team_sponsor_link | (none) | `source_url`, `source_notes` | **ADD** | |
| team_sponsor_link | (none) | `created_by`, `last_modified_by` | **ADD** | |

## 4. High-Risk Files

### 4.1 Backend Models and Schemas

1. **`backend/app/models/team.py`** – Must be updated with new columns, relationships, and validations.
2. **`backend/app/models/lineage.py`** – Column renames (`previous_node_id` → `predecessor_node_id`, `next_node_id` → `successor_node_id`) and new fields.
3. **`backend/app/models/sponsor.py`** (not listed but likely exists) – Needs audit fields and protection.
4. **`backend/app/schemas/team.py`** – Schemas must reflect new fields.
5. **`backend/app/schemas/team_detail.py`** – May need updates for new lineage column names.
6. **`backend/app/schemas/timeline.py`** – Uses `previous_node_id`/`next_node_id` in links.

### 4.2 Services with Complex Logic

1. **`backend/app/services/edit_service.py`** – Contains merge/split logic that creates lineage events. Must adapt to new column names and possibly new validation.
2. **`backend/app/services/lineage_service.py`** – Heavily uses `previous_node_id` and `next_node_id`. High risk.
3. **`backend/app/services/team_service.py`** – Team creation and updates, must handle new fields (legal_name, protection, etc.).
4. **`backend/app/services/team_detail_service.py`** – Builds team history, depends on lineage event structure.
5. **`backend/app/core/graph_builder.py`** – Constructs D3.js graph using `previous_node_id` and `next_node_id`.

### 4.3 Tests

1. **`backend/tests/test_split_event.py`** – Tests split events using `previous_node_id`.
2. **`backend/tests/test_merge_event.py`** – Tests merge events using `next_node_id`.
3. **`backend/tests/test_lineage.py`** – Tests lineage event functionality.
4. **`backend/tests/integration/test_timeline_integration.py`** – Integration tests for timeline.
5. **`backend/tests/api/test_team_detail.py`** – API tests for team detail.

### 4.4 Database Migrations

1. **`backend/alembic/versions/003_add_lineage_event.py`** – Contains column definitions that may conflict.
2. **`backend/alembic/versions/002_add_team_era.py`** – May need updates for new columns.

### 4.5 Frontend Types

Although not scanned, frontend types that reference `previous_node_id`/`next_node_id` (e.g., in `TimelineLink`) will need updates.

## 5. Recommended Refactoring Steps

### Phase 1: Database Schema Migration

1. **Create new tables** (`users`, `edit_history`) via migration.
2. **Add new columns** to existing tables (team_node, team_era, sponsor_master, sponsor_brand, team_sponsor_link, lineage_event).
3. **Rename columns** in `lineage_event`: `previous_node_id` → `predecessor_node_id`, `next_node_id` → `successor_node_id`.
4. **Update foreign key constraints** and indexes accordingly.
5. **Create triggers** for `updated_at` (if not already present).
6. **Insert system user** (user_id 00000000-0000-0000-0000-000000000000).

### Phase 2: Backend Models Update

1. Update SQLAlchemy models (`team.py`, `lineage.py`, `sponsor.py`) to match new schema.
2. Update Pydantic schemas (`schemas/team.py`, `schemas/team_detail.py`, `schemas/timeline.py`, etc.) to include new fields and renamed columns.
3. Update enums if needed (`EventType` already includes required values).
4. Adjust relationships and validators.

### Phase 3: Service Layer Adaptation

1. Update `lineage_service.py` to use new column names.
2. Update `edit_service.py` merge/split logic.
3. Update `team_service.py` to handle `legal_name`, `is_protected`, etc.
4. Update `graph_builder.py` for renamed columns in links.
5. Update `team_detail_service.py` for lineage column changes.

### Phase 4: Test Updates

1. Update test fixtures to use new column names.
2. Adjust test assertions for renamed columns.
3. Add tests for new functionality (protection, audit fields, etc.).
4. Run existing test suite to ensure no regressions.

### Phase 5: Frontend Updates

1. Update TypeScript interfaces (if any) to reflect renamed columns.
2. Verify that API responses are correctly parsed.

### Phase 6: Data Migration

1. Backfill `legal_name` for existing team nodes (using a derived value or placeholder).
2. Backfill `created_by`/`last_modified_by` with system user.
3. Backfill `source_origin` for existing eras.
4. Ensure `valid_from`/`valid_until` are populated (default to whole season).

### Phase 7: Validation and Deployment

1. Run comprehensive integration tests.
2. Perform smoke tests on critical paths (team creation, merge, split, timeline visualization).
3. Deploy in stages (migration, application update, data backfill).

## 6. Additional Considerations

- **Data Integrity**: The migration must preserve existing relationships (lineage events, sponsorships).
- **Performance**: New indexes may be needed for `legal_name`, `is_protected`, etc.
- **Backward Compatibility**: Consider a period where both old and new column names are supported (dual writes) to allow gradual rollout. However, given the project stage, a clean break may be acceptable.
- **Documentation**: Update API documentation and internal docs to reflect new schema.

## 7. Next Steps

1. Review this analysis with the team.
2. Create detailed migration scripts.
3. Implement changes step-by-step, verifying each phase.

---
*Report generated on 2025-12-15*