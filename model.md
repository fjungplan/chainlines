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

### C. Sponsor System (Many-to-Many)
**`SponsorMaster`** (The Corporation)
* `master_id` (UUID, PK)
* `legal_name` (String): e.g., "Soudal Holding NV".
* `industry_sector` (String): e.g., "Adhesives".
* `is_protected` (Boolean): Access control flag.

**`SponsorBrand`** (The Marketing Name)
* `brand_id` (UUID, PK)
* `master_id` (UUID, FK): Parent company.
* `brand_name` (String): e.g., "Soudal" (or "Fix ALL" for specific races).
* `default_hex_color` (String): e.g., "#FF0000".
* `is_protected` (Boolean): Access control flag.

**`TeamSponsorLink`** (The Connection)
* `link_id` (UUID, PK)
* `era_id` (UUID, FK -> TeamEra)
* `brand_id` (UUID, FK -> SponsorBrand)
* `rank_order` (Int): 1 for Title Sponsor, 2 for Secondary.
* `prominence_percent` (Int): Visual weight for the "Jersey Slice" graph (0-100).

### D. User & Moderation
**`User`**
* `role` (Enum): `GUEST`, `EDITOR`, `TRUSTED_EDITOR` (auto-approves edits), `MODERATOR`, `ADMIN`.

**`Edit`** (Moderation Queue)
* `edit_type`: `METADATA`, `MERGE`, `SPLIT`.
* `changes` (JSON): The payload of proposed changes.
* `status`: `PENDING`, `APPROVED`, `REJECTED`.

## 3. Key Constraints
1.  **Strict Typing:** Backend uses Python 3.11+ type hints.
2.  **Async:** All DB operations use `sqlalchemy.ext.asyncio` (`await session.execute(...)`).
3.  **No Lazy Loading:** Relationships must be eagerly loaded (`options(selectinload(...))`) to prevent async errors.
4.  **Immutability:** Once a `TeamNode` is dissolved, it cannot have new `TeamEra` entries added after the dissolution year.