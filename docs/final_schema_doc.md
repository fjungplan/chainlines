# ChainLines - Final Database Schema v1.0
**Professional Cycling Team Lineage & Sponsorship Visualization**

---

## Executive Summary

This database schema models the complete history of professional cycling teams from 1900 to present, tracking:
- **Team identities** (the persistent legal entities - "Paying Agents")
- **Seasonal snapshots** (year-by-year team configurations)
- **Sponsor relationships** (hierarchical brand structure with visual prominence)
- **Lineage events** (mergers, splits, transfers, spiritual succession)
- **Editorial workflow** (wiki-style collaborative editing with moderation)

### Core Concepts

**TEAM_NODE (Paying Agent)**: The persistent legal/managerial entity that owns the team license and employs riders. This is the "true" team that survives name changes and rebrands.

**TEAM_ERA (Season Snapshot)**: A single season's configuration including team name, UCI code, tier level, and sponsor composition. Multiple eras can exist per season to handle mid-season changes.

**Sponsor Hierarchy**: Parent companies (SPONSOR_MASTER) own multiple brands (SPONSOR_BRAND), which sponsor teams through contracts (TEAM_SPONSOR_LINK) with visual prominence percentages.

**Lineage Tracking**: Binary relationships between team nodes representing structural changes (legal transfers, spiritual succession, mergers, splits).

---

## Table Definitions

### 1. USER
**Purpose**: Authentication and authorization via Google OAuth

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user_id` | UUID | PRIMARY KEY | Unique user identifier |
| `google_id` | VARCHAR(255) | UNIQUE, NOT NULL | Google OAuth identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| `display_name` | VARCHAR(255) | | User's display name |
| `avatar_url` | VARCHAR(500) | | Profile picture URL |
| `role` | ENUM | NOT NULL | EDITOR, TRUSTED_EDITOR, MODERATOR, ADMIN |
| `approved_edits_count` | INTEGER | DEFAULT 0 | Count for auto-promotion to TRUSTED_EDITOR |
| `is_banned` | BOOLEAN | DEFAULT FALSE | Account suspension flag |
| `banned_reason` | TEXT | NULLABLE | Reason for ban |
| `created_at` | TIMESTAMP | NOT NULL | Account creation timestamp |
| `last_login_at` | TIMESTAMP | NULLABLE | Last login timestamp |

**Role Hierarchy**:
- **EDITOR**: Can submit edits (requires approval)
- **TRUSTED_EDITOR**: Edits go live immediately (earned through contributions)
- **MODERATOR**: Can approve/reject edits
- **ADMIN**: Full control (manage users, toggle protection)

---

### 2. EDIT_HISTORY
**Purpose**: Wikipedia-style revision history with full snapshots

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `edit_id` | UUID | PRIMARY KEY | Unique edit identifier |
| `entity_type` | VARCHAR(50) | NOT NULL | Table name (team_node, team_era, etc.) |
| `entity_id` | UUID | NOT NULL | ID of record being edited |
| `user_id` | UUID | FK → USER (SET NULL) | User who created the edit |
| `action` | ENUM | NOT NULL | CREATE, UPDATE, DELETE |
| `status` | ENUM | NOT NULL | PENDING, APPROVED, REJECTED, APPLIED |
| `reviewed_by` | UUID | FK → USER (SET NULL) | Moderator who reviewed |
| `reviewed_at` | TIMESTAMP | NULLABLE | Review timestamp |
| `review_notes` | TEXT | NULLABLE | Approval/rejection reason |
| `snapshot_before` | JSONB | NULLABLE | Full record state before edit |
| `snapshot_after` | JSONB | NOT NULL | Full record state after edit |
| `source_url` | VARCHAR(500) | NULLABLE | Reference URL |
| `source_notes` | TEXT | NULLABLE | Manual documentation |
| `created_at` | TIMESTAMP | NOT NULL | Edit creation timestamp |

**Workflow**:
- **EDITOR** submissions → PENDING → requires moderator approval
- **TRUSTED_EDITOR** submissions → APPLIED immediately (unless record protected)
- **Protected records** → always PENDING regardless of user role

---

### 3. TEAM_NODE
**Purpose**: The persistent team entity (Paying Agent / managerial node)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `node_id` | UUID | PRIMARY KEY | Unique team node identifier |
| `legal_name` | VARCHAR(255) | UNIQUE, NOT NULL | Internal identifier (PAYING AGENT name) |
| `display_name` | VARCHAR(255) | NULLABLE | Public-facing name (for disambiguation) |
| `founding_year` | INTEGER | NOT NULL | Year team was founded (soft warn if < 1850 or > current+5) |
| `dissolution_year` | INTEGER | NULLABLE | Year team dissolved/ceased operations |
| `owned_by_sponsor_master_id` | UUID | FK → SPONSOR_MASTER (SET NULL) | Pre-2005: sponsor owns team |
| `is_protected` | BOOLEAN | DEFAULT FALSE | Requires approval for ALL edits (protects node + eras + lineage) |
| `latest_team_name` | VARCHAR(255) | NULLABLE | Cached from most recent era |
| `latest_uci_code` | VARCHAR(3) | NULLABLE | Cached from most recent era |
| `current_tier` | INTEGER | NULLABLE | Cached from most recent era (1, 2, or 3) |
| `is_active` | BOOLEAN | COMPUTED | TRUE if dissolution_year IS NULL |
| `source_url` | VARCHAR(500) | NULLABLE | Reference URL |
| `source_notes` | TEXT | NULLABLE | Manual documentation |
| `created_by` | UUID | FK → USER (SET NULL) | User who created record |
| `last_modified_by` | UUID | FK → USER (SET NULL) | User who last modified record |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Protection Scope**: When `is_protected = TRUE`, protects:
- The team node itself
- All TEAM_ERA records
- All LINEAGE_EVENT records (where this node is predecessor/successor)
- All TEAM_SPONSOR_LINK records (through era protection)

---

### 4. TEAM_ERA
**Purpose**: Season-specific team configuration snapshot

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `era_id` | UUID | PRIMARY KEY | Unique era identifier |
| `node_id` | UUID | FK → TEAM_NODE (CASCADE), NOT NULL | Parent team node |
| `season_year` | INTEGER | NOT NULL | Calendar year of season |
| `valid_from` | DATE | NOT NULL | Start date (for mid-season changes) |
| `valid_until` | DATE | NULLABLE | End date (NULL if current) |
| `registered_name` | VARCHAR(255) | NOT NULL | Official team name (derived from sponsors or manual) |
| `uci_code` | VARCHAR(3) | NULLABLE | 3-letter UCI team code (e.g., "TJV") |
| `is_name_auto_generated` | BOOLEAN | DEFAULT TRUE | TRUE if name derived from sponsors |
| `is_manual_override` | BOOLEAN | DEFAULT FALSE | TRUE if manually entered - prevents auto-overwrite |
| `is_auto_filled` | BOOLEAN | DEFAULT FALSE | TRUE if gap-filled from previous era |
| `tier_level` | INTEGER | NULLABLE | 1, 2, or 3 (NULL for pre-license era) |
| `has_license` | BOOLEAN | DEFAULT FALSE | TRUE if UCI license exists |
| `source_origin` | VARCHAR(50) | NULLABLE | manual, scraped, gap-filled, cascaded |
| `source_url` | VARCHAR(500) | NULLABLE | Reference URL |
| `source_notes` | TEXT | NULLABLE | Manual documentation |
| `created_by` | UUID | FK → USER (SET NULL) | User who created record |
| `last_modified_by` | UUID | FK → USER (SET NULL) | User who last modified record |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Constraints**:
- UNIQUE (`node_id`, `season_year`, `valid_from`) - allows multiple eras per season
- CHECK (`tier_level` IN (1, 2, 3) OR `tier_level` IS NULL)
- CHECK (`uci_code` IS NULL OR (`LENGTH(uci_code)` = 3 AND `uci_code` ~ '^[A-Z]{3}$'))

**Auto-Fill Logic**:
- When manual era created between existing eras, system auto-fills gaps
- **Smart Propagation**: New manual entry only updates FORWARD (not backward)
- Example: Manual 2008 between 2005 and 2010 → updates 2009, leaves 2006-2007 alone
- `is_manual_override = TRUE` protects era from future auto-overwrite

---

### 5. SPONSOR_MASTER
**Purpose**: Parent company owning multiple brands

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `master_id` | UUID | PRIMARY KEY | Unique sponsor master identifier |
| `legal_name` | VARCHAR(255) | UNIQUE, NOT NULL | Internal identifier (parent company name) |
| `display_name` | VARCHAR(255) | NULLABLE | Public-facing name (for disambiguation) |
| `industry_sector` | VARCHAR(100) | NULLABLE | Business sector (e.g., "Beverages") |
| `is_protected` | BOOLEAN | DEFAULT FALSE | Requires approval for ALL edits (protects master + brands) |
| `source_url` | VARCHAR(500) | NULLABLE | Reference URL |
| `source_notes` | TEXT | NULLABLE | Manual documentation |
| `created_by` | UUID | FK → USER (SET NULL) | User who created record |
| `last_modified_by` | UUID | FK → USER (SET NULL) | User who last modified record |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Protection Scope**: When `is_protected = TRUE`, protects:
- The sponsor master itself
- All SPONSOR_BRAND records
- All TEAM_SPONSOR_LINK records (through brand protection)

---

### 6. SPONSOR_BRAND
**Purpose**: Individual brand identity under parent company

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `brand_id` | UUID | PRIMARY KEY | Unique brand identifier |
| `master_id` | UUID | FK → SPONSOR_MASTER (CASCADE), NOT NULL | Parent company |
| `brand_name` | VARCHAR(255) | NOT NULL | Internal identifier (e.g., "Coca-Cola") |
| `display_name` | VARCHAR(255) | NULLABLE | Public-facing name (for disambiguation) |
| `default_hex_color` | VARCHAR(7) | NOT NULL | Brand primary color (#RRGGBB) |
| `source_url` | VARCHAR(500) | NULLABLE | Reference URL |
| `source_notes` | TEXT | NULLABLE | Manual documentation |
| `created_by` | UUID | FK → USER (SET NULL) | User who created record |
| `last_modified_by` | UUID | FK → USER (SET NULL) | User who last modified record |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Constraints**:
- UNIQUE (`master_id`, `brand_name`) - brand names unique per parent company
- CHECK (`default_hex_color` ~ '^#[0-9A-Fa-f]{6}$')

---

### 7. TEAM_SPONSOR_LINK
**Purpose**: Sponsorship contract linking brand to team era

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `link_id` | UUID | PRIMARY KEY | Unique link identifier |
| `era_id` | UUID | FK → TEAM_ERA (CASCADE), NOT NULL | Team era being sponsored |
| `brand_id` | UUID | FK → SPONSOR_BRAND (CASCADE), NOT NULL | Sponsor brand |
| `rank_order` | INTEGER | NOT NULL | Sponsor ranking (1 = main sponsor) |
| `prominence_percent` | INTEGER | NOT NULL | Visual weight in jersey (1-100) |
| `hex_color_override` | VARCHAR(7) | NULLABLE | Overrides brand default color |
| `source_url` | VARCHAR(500) | NULLABLE | Reference URL |
| `source_notes` | TEXT | NULLABLE | Manual documentation |
| `created_by` | UUID | FK → USER (SET NULL) | User who created record |
| `last_modified_by` | UUID | FK → USER (SET NULL) | User who last modified record |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Constraints**:
- UNIQUE (`era_id`, `rank_order`) - no duplicate ranks per era
- UNIQUE (`era_id`, `brand_id`) - no duplicate brands per era
- CHECK (`prominence_percent` > 0 AND `prominence_percent` <= 100)

**Business Rule** (Soft Validation):
- All sponsors for an era should sum to 100% prominence
- Application warns if sum ≠ 100% but allows override

**Default Distribution** (when auto-generating):
- 2 sponsors: 60% / 40%
- 3 sponsors: 40% / 30% / 30%
- 4 sponsors: 40% / 20% / 20% / 20%

---

### 8. LINEAGE_EVENT
**Purpose**: Structural relationships between team nodes

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `event_id` | UUID | PRIMARY KEY | Unique event identifier |
| `predecessor_node_id` | UUID | FK → TEAM_NODE (CASCADE), NOT NULL | Source team node |
| `successor_node_id` | UUID | FK → TEAM_NODE (CASCADE), NOT NULL | Target team node |
| `event_year` | INTEGER | NOT NULL | Year of lineage event |
| `event_date` | DATE | NULLABLE | Specific date (defaults to Jan 1 of event_year) |
| `event_type` | ENUM | NOT NULL | LEGAL_TRANSFER, SPIRITUAL_SUCCESSION, MERGE, SPLIT |
| `notes` | TEXT | NULLABLE | Additional context |
| `source_url` | VARCHAR(500) | NULLABLE | Reference URL |
| `source_notes` | TEXT | NULLABLE | Manual documentation |
| `created_by` | UUID | FK → USER (SET NULL) | User who created record |
| `last_modified_by` | UUID | FK → USER (SET NULL) | User who last modified record |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Constraints**:
- CHECK (`predecessor_node_id` != `successor_node_id`)
- CHECK (`event_year` >= 1900 AND `event_year` <= 2100)

**Event Types**:
- **LEGAL_TRANSFER**: License/rights transfer from one team to another
- **SPIRITUAL_SUCCESSION**: Informal continuation (common in pre-license era)
- **MERGE**: Multiple teams combining (stored as separate events: A→C, B→C)
- **SPLIT**: One team branching (stored as separate events: A→B, A→C)

**Temporal Validation** (Soft):
- Default assumption: predecessor dissolves Dec 31 (event_year - 1), successor founded Jan 1 (event_year)
- Warn if event_year more than 1 year from predecessor dissolution or successor founding
- Allow mid-lifetime merges/splits (team continues before/after event)

---

## Relationship Summary

### Foreign Key Relationships with Cascade Rules

```
USER
├─→ EDIT_HISTORY.user_id (SET NULL)
├─→ EDIT_HISTORY.reviewed_by (SET NULL)
├─→ TEAM_NODE.created_by (SET NULL)
├─→ TEAM_NODE.last_modified_by (SET NULL)
├─→ TEAM_ERA.created_by (SET NULL)
├─→ TEAM_ERA.last_modified_by (SET NULL)
├─→ SPONSOR_MASTER.created_by (SET NULL)
├─→ SPONSOR_MASTER.last_modified_by (SET NULL)
├─→ SPONSOR_BRAND.created_by (SET NULL)
├─→ SPONSOR_BRAND.last_modified_by (SET NULL)
├─→ TEAM_SPONSOR_LINK.created_by (SET NULL)
├─→ TEAM_SPONSOR_LINK.last_modified_by (SET NULL)
├─→ LINEAGE_EVENT.created_by (SET NULL)
└─→ LINEAGE_EVENT.last_modified_by (SET NULL)

TEAM_NODE
├─→ TEAM_ERA.node_id (CASCADE)
├─→ LINEAGE_EVENT.predecessor_node_id (CASCADE)
└─→ LINEAGE_EVENT.successor_node_id (CASCADE)

TEAM_ERA
└─→ TEAM_SPONSOR_LINK.era_id (CASCADE)

SPONSOR_MASTER
├─→ SPONSOR_BRAND.master_id (CASCADE)
└─→ TEAM_NODE.owned_by_sponsor_master_id (SET NULL)

SPONSOR_BRAND
└─→ TEAM_SPONSOR_LINK.brand_id (CASCADE)
```

---

## Key Design Decisions

### 1. Temporal Modeling
- **Multiple eras per season**: Allows mid-season sponsor changes, bankruptcies
- **Date ranges** (`valid_from`, `valid_until`): Precise temporal boundaries
- **Gap-filling**: Automatically creates continuous timeline for visualization

### 2. Protection & Moderation
- **Two-tier protection**: TEAM_NODE protection (team + dependencies) vs. SPONSOR_MASTER protection (sponsor hierarchy)
- **Role-based workflow**: EDITOR → PENDING, TRUSTED_EDITOR → APPLIED, Protected → always PENDING
- **Full audit trail**: Wikipedia-style snapshots preserve complete history

### 3. Sponsor Modeling
- **Hierarchical structure**: Parent companies own multiple brands
- **Visual prominence**: Percentage-based jersey representation
- **Color flexibility**: Default brand color with per-contract override

### 4. Lineage Tracking
- **Binary relationships**: Simplifies D3.js visualization
- **Separate events for complex cases**: MERGE (A→C, B→C), SPLIT (A→B, A→C)
- **Always bidirectional**: Both predecessor and successor required

### 5. Historical Accuracy
- **Pre-2005 sponsor ownership**: Modeled via `owned_by_sponsor_master_id`
- **Pre-license era**: `tier_level` nullable, `has_license` flag
- **Flexible naming**: Auto-generation from sponsors with manual override capability

---

## Tier System Lookup (Application Layer)

| Date Range | Tier 1 | Tier 2 | Tier 3 |
|------------|--------|--------|--------|
| 1990–1995 | Professional | N/A | N/A |
| 1996–2004 | Trade Team I (GS1) | Trade Team II (GS2) | Trade Team III (GS3) |
| 2005–2014 | UCI ProTeam | Pro Continental | Continental |
| 2015–2019 | UCI WorldTeam | Pro Continental | Continental |
| 2020–Present | UCI WorldTeam | UCI ProTeam | Continental |

**Implementation**: Store only `tier_level` (1, 2, 3) in database; compute label from `season_year` + lookup table.

---

## Migration from Current Schema

### Existing Tables (Keep Names)
- `team_node` ✓ (rename `paying_agent_id` → `node_id`)
- `team_era` ✓ (rename `snapshot_id` → `era_id`, `paying_agent_id` → `node_id`)
- `sponsor_master` ✓
- `sponsor_brand` ✓
- `team_sponsor_link` ✓ (rename `contract_id` → `link_id`, `snapshot_id` → `era_id`)
- `lineage_event` ✓

### New Tables
- `users` (OAuth authentication)
- `edit_history` (revision tracking)

### New Fields to Add
**TEAM_NODE**:
- `display_name`, `is_protected`, `latest_team_name`, `latest_uci_code`, `current_tier`, `is_active`
- `source_url`, `source_notes`, `created_by`, `last_modified_by`

**TEAM_ERA**:
- `uci_code`, `is_name_auto_generated`, `is_manual_override`, `is_auto_filled`, `source_origin`
- `source_url`, `source_notes`, `created_by`, `last_modified_by`

**SPONSOR_MASTER**:
- `display_name`, `is_protected`
- `source_url`, `source_notes`, `created_by`, `last_modified_by`

**SPONSOR_BRAND**:
- `display_name`
- `source_url`, `source_notes`, `created_by`, `last_modified_by`

**TEAM_SPONSOR_LINK**:
- `source_url`, `source_notes`, `created_by`, `last_modified_by`

**LINEAGE_EVENT**:
- Rename `previous_node_id` → `predecessor_node_id`, `next_node_id` → `successor_node_id`
- Add `event_date`
- `source_url`, `source_notes`, `created_by`, `last_modified_by`

### Data Considerations
- All existing data is mock data → **fresh start with clean schema**
- Create initial "system" user for backfilling `created_by` if importing any historical data

---

## Implementation Checklist

### Phase 1: Core Schema
- [ ] Create `users` table
- [ ] Create `edit_history` table
- [ ] Modify `team_node` (add new fields)
- [ ] Modify `team_era` (add new fields)
- [ ] Modify `sponsor_master` (add new fields)
- [ ] Modify `sponsor_brand` (add new fields)
- [ ] Modify `team_sponsor_link` (add new fields)
- [ ] Modify `lineage_event` (add new fields, rename columns)

### Phase 2: Constraints & Indexes
- [ ] Add UNIQUE constraints
- [ ] Add CHECK constraints
- [ ] Add foreign key constraints with cascade rules
- [ ] Add indexes (defer to performance testing)

### Phase 3: Application Logic
- [ ] Implement tier label lookup (year → label mapping)
- [ ] Implement auto-fill logic (gap detection and propagation)
- [ ] Implement protection checks (TEAM_NODE, SPONSOR_MASTER)
- [ ] Implement approval workflow (PENDING → APPROVED → APPLIED)
- [ ] Implement prominence validation (sum to 100% warning)
- [ ] Implement temporal validation (lineage event dates)

### Phase 4: Testing
- [ ] Test auto-fill edge cases (backward protection, forward cascade)
- [ ] Test protection inheritance (node → eras, master → brands)
- [ ] Test cascade deletes (team → eras → links → lineage)
- [ ] Test approval workflow (EDITOR vs. TRUSTED_EDITOR)
- [ ] Test concurrent edits (optimistic locking)

---

## Notes & Rationale

### Why "TEAM_NODE" instead of "PAYING_AGENT"?
- **Maintains consistency** with existing codebase
- **Clearer domain language** for developers
- **Accurate concept preserved** in field descriptions

### Why JSONB for snapshots instead of separate history tables?
- **Simplicity**: Single table for all entity types
- **Flexibility**: Schema changes don't break history
- **Wikipedia model**: Proven pattern for revision tracking

### Why separate SPONSOR_MASTER and SPONSOR_BRAND?
- **Real-world accuracy**: Coca-Cola Company owns Coca-Cola, Sprite, Fanta
- **Reusability**: Same parent company sponsors multiple teams with different brands
- **Historical tracking**: Brand rebranding without losing parent company continuity

### Why `is_manual_override` separate from `is_auto_filled`?
- **Different concerns**: Origin vs. protection
- **Clear semantics**: "This was manually entered" vs. "Don't overwrite this"
- **Audit trail**: Track how data entered system

### Why both `predecessor_node_id` AND `successor_node_id` required?
- **Lineage events are relationships**: Always connect two teams
- **Team creation/dissolution**: Use `founding_year`/`dissolution_year` on TEAM_NODE
- **Simpler visualization**: D3.js expects edges with two endpoints

---

## Glossary

**Paying Agent**: The legal entity (management company) that holds the UCI license and employs riders. The persistent identifier for team continuity across name changes.

**Season Snapshot**: A year-specific configuration of a team including name, tier, sponsors, and metadata.

**Jersey Slice**: Visual representation of team jersey using sponsor colors weighted by prominence percentage.

**Lineage Event**: A structural change in team identity (merger, split, transfer, succession).

**Auto-Fill**: Automatic gap-filling between manually entered eras to create continuous timeline.

**Smart Propagation**: Forward-only cascade when inserting manual era between existing eras (updates future, preserves past).

**Protection**: Flag preventing automated changes; requires moderator approval for all edits.

**Tier Level**: UCI classification system (1 = WorldTeam, 2 = ProTeam, 3 = Continental).

**UCI Code**: 3-letter team identifier assigned by Union Cycliste Internationale.

---

## Version History

**v1.0** (Current)
- Initial schema design based on comprehensive domain analysis
- Full audit trail and moderation workflow
- Hierarchical sponsor structure
- Smart auto-fill with protection mechanisms
- Optimized for D3.js visualization

---

**Document Status**: ✅ FINALIZED - Ready for Implementation

**Last Updated**: December 2024

**Schema Validation**: Reviewed with domain expert, all business rules captured
