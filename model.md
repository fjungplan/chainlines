# Data Model & Architecture Context

## 1. Domain Overview
This project tracks the evolutionary history of professional cycling teams.
* **Managerial Node (`TeamNode`):** The persistent legal entity behind a team. It survives name changes.
* **Team Era (`TeamEra`):** A specific season (year) snapshot of a team. Contains the specific name, jersey, and sponsors for that year.
* **Lineage Event:** Connects nodes (Merges, Splits, Rebrands).

## 2. Database Schema (PostgreSQL/SQLAlchemy)

### A. Core Lineage
**`TeamNode`** (The persistent entity)
* `node_id` (UUID, PK): Unique identifier.
* `legal_name` (String): Internal identifier (e.g., "Lefevere Management").
* `founding_year` (Int): Year the structure began.
* `dissolution_year` (Int, Nullable): Year it ceased to exist.
* `is_active` (Boolean): Computed (dissolution_year is NULL).

**`TeamEra`** (Yearly Snapshot)
* `era_id` (UUID, PK)
* `node_id` (UUID, FK -> TeamNode)
* `season_year` (Int): The specific season (e.g., 2024).
* `registered_name` (String): The team name for that year (e.g., "Soudal Quick-Step").
* `uci_code` (String(3)): UCI abbreviation (e.g., "SOQ").
* `country_code` (String(3)): ISO country code.
* `tier_level` (Int): 1=WorldTour, 2=ProTeam, 3=Continental.
* `is_manual_override` (Bool): If True, scraper will not overwrite this record.

### B. Graph Connections
**`LineageEvent`** (The Edges)
* `event_id` (UUID, PK)
* `predecessor_node_id` (UUID, FK -> TeamNode): The "Old" team.
* `successor_node_id` (UUID, FK -> TeamNode): The "New" team.
* `event_year` (Int): When the change happened.
* `event_type` (Enum):
    * `LEGAL_TRANSFER`: Standard license transfer.
    * `SPIRITUAL_SUCCESSION`: New legal entity, but same staff/riders.
    * `MERGE`: Two nodes becoming one.
    * `SPLIT`: One node becoming two.
* `is_protected` (Boolean): If True, only `MODERATOR`/`ADMIN` can edit.

### Chainlines Data Model & Architecture

## 1. Domain Overview (The "Source of Truth")

The system follows a **Node/Era/Event** architecture to handle the complex, non-linear history of professional cycling teams.

### A. TeamNode (The "Paying Agent")
The persistent legal/financial entity. While a team's name (era) changes every year based on sponsors, the `TeamNode` represents the underlying license holder and continuity.
*   *Key Fields:* `legal_name`, `display_name`, `founding_year`, `dissolution_year`.

### B. TeamEra (The "Season Snapshot")
A snapshot of a team's identity for a specific period (usually one season).
*   *Key Fields:* `registered_name`, `uci_code`, `season_year`, `tier_level`.
*   *Links:* Associated with multiple `SponsorBrand` entities via `TeamSponsorLink`.

### C. Lineage Event (The "Bridge")
Expresses how one `TeamNode` relates to another over time.
*   *Types:* `LEGAL_TRANSFER`, `SPIRITUAL_SUCCESSION`, `MERGE`, `SPLIT`.

---

## 2. Database Schema (SQLAlchemy Ground Truth)

### A. Team Management
**`TeamNode`**
* `node_id` (UUID, PK)
* `legal_name` (String, Unique) - The official license holder name.
* `display_name` (String) - Human-readable preferred name.
* `founding_year` (Integer)
* `dissolution_year` (Integer, Nullable)
* `latest_team_name` (String) - Cached current name.
* `latest_uci_code` (String, 3) - Cached current UCI code.
* `current_tier` (Integer) - 1 (WorldTeam), 2 (ProTeam), 3 (Continental).
* `is_active` (Boolean) - Computed: `dissolution_year IS NULL`.
* `is_protected` (Boolean) - Admin-only modification.
* `source_url` / `source_notes` (Metadata)

**`TeamEra`**
* `era_id` (UUID, PK)
* `node_id` (FK -> TeamNode)
* `season_year` (Integer)
* `registered_name` (String) - The full sponsor-name for that year.
* `uci_code` (String, 3)
* `country_code` (String, 3) - ISO alpha-3.
* `tier_level` (Integer) - 1, 2, or 3.
* `valid_from` / `valid_until` (Date)
* `has_license` (Boolean)
* `is_auto_filled` / `is_manual_override` (Flags)
* `source_origin` (e.g., "CyclingFlash")
* `wikipedia_history_content` (TEXT, Nullable) - Cached Wikipedia "History" section for lineage decisions.

**`TeamNode`**
* `node_id` (UUID, PK)
* `legal_name` (String, Unique) - The official license holder name.
* `display_name` (String) - Human-readable preferred name.
* `founding_year` (Integer)
* `dissolution_year` (Integer, Nullable)
* `latest_team_name` (String) - Cached current name.
* `latest_uci_code` (String, 3) - Cached current UCI code.
* `current_tier` (Integer) - 1 (WorldTeam), 2 (ProTeam), 3 (Continental).
* `is_active` (Boolean) - Computed: `dissolution_year IS NULL`.
* `is_protected` (Boolean) - Admin-only modification.
* `external_ids` (JSONB, Nullable) - Cross-source IDs: `{"wikidata": "Q123", "cyclingranking": "...", "memoire": "..."}`.
* `source_url` / `source_notes` (Metadata)

### B. Sponsor System
**`SponsorMaster`**
* `legal_name` (Unique) - e.g., "Volkswagen AG".
* `display_name` - e.g., "Volkswagen".
* `industry_sector` - e.g., "Automotive".

**`SponsorBrand`**
* `brand_name` - e.g., "Skoda".
* `default_hex_color` - Primary brand color.

**`TeamSponsorLink`**
* `rank_order` - 1 (Title Sponsor), 2 (Secondary), etc.
* `prominence_percent` - Contribution to total team identity (1-100).
* `hex_color_override` - Kit-specific color.

### C. Moderation & Audit Log
**`EditHistory`** (Table: `edit_history`)
* `edit_id` (UUID, PK)
* `entity_type` (String) - e.g., "team_node", "sponsor_brand".
* `entity_id` (UUID) - Target of the change.
* `user_id` (FK -> User) - Submitter.
* `action` (Enum) - `CREATE`, `UPDATE`, `DELETE`.
* `status` (Enum) - `PENDING`, `APPROVED`, `REJECTED`, `REVERTED`.
* `snapshot_before` (JSON) - State before change.
* `snapshot_after` (JSON) - State after change.
* `reverted_by` / `reverted_at` (Revert tracking).
* **Intelligence Metadata**:
    * `confidence_score` (0.0 - 1.0) - For automated/LLM edits.
    * **Auto-Approval Threshold**: Changes with `confidence_score` ≥ 0.90 are auto-approved by the "Smart Scraper" System User.

### D. User Management
**`User`** (Table: `users`)
* `role`: `EDITOR`, `TRUSTED_EDITOR`, `MODERATOR`, `ADMIN`.
* **Smart Scraper Bot**: UUID `00000000-0000-0000-0000-000000000001`.

## 3. Key Constraints
1.  **Strict Async**: All DB access MUST use the `AsyncSession`.
2.  **Immutability**: Approved IDs (`node_id`, `era_id`, `master_id`) never change.
3.  **Audit First**: Any non-trivial mutation should generate an `EditHistory` entry.
4.  **Immutability:** Once a `TeamNode` is dissolved, it cannot have new `TeamEra` entries added after the dissolution year.