
# Prompt Plan for Cycling Timeline Project
This document contains detailed prompts A1–H6 for the code-generation LLM.  
Each prompt is self-contained, TDD-focused, incremental, and free of orphaned code.

---

# PHASE A — PROJECT SETUP

## Prompt A1 – Create Project Skeleton
```
You are generating code for step A1.

Goal:
Create the project skeleton for a FastAPI + SQLAlchemy backend.

Requirements:
- Directory structure:
  app/
    api/
    models/
    schemas/
    services/
    infrastructure/
    tests/
- Implement main.py with health endpoint `/health`
- Add pyproject.toml with dependencies:
  fastapi, uvicorn, sqlalchemy, alembic, psycopg[binary], pydantic, pydantic-settings,
  pytest, httpx, factory-boy, testcontainers
- Include initial test for /health
- No business logic
```

## Prompt A2 – Configure Linting & Pre-Commit
```
Implement:
- Ruff config
- Black config
- Pre-commit hooks for formatting + lint
- CI-safe configs
Provide all config files.
```

## Prompt A3 – Configure CI & Testing
```
Implement GitHub Actions workflow:
- Python 3.11
- Install dependencies
- Run tests
- Run lint + format
Provide workflow file and badges.
```

---

# PHASE B — DATABASE

## Prompt B1 – Configure Database Connection
```
Implement:
- app/infrastructure/db.py with SQLAlchemy engine + sessionmaker
- Pydantic DatabaseSettings
- get_session dependency
- Test using Testcontainers
```

## Prompt B2 – Create Base Models
```
Implement:
- Base declarative class
- Timestamp mixin
- UUID primary key helper
- Tests for base models
```

## Prompt B3 – UCI_Tier_Definition
```
Implement migration, SQLAlchemy model, Pydantic schema, CRUD API, tests.

Fields:
- tier_id (PK)
- tier_level (unique int)
- description
- notes (optional)

Constraints:
- tier_level unique
- tier_id stable
```

## Prompt B4 – Sponsor_Master
```
Implement table:
- sponsor_id (PK)
- legal_name
- parent_company
- country
- industry_sector
- website
- notes

CRUD + tests.
```

## Prompt B5 – Team_Lineage
```
Implement fields:
- lineage_id
- primary_name
- founding_year
- notes
CRUD + tests.
```

## Prompt B6 – Team_Entity
```
Implement fields:
- entity_id
- lineage_id (FK)
- start_date
- end_date

CRUD + tests.
```

## Prompt B7 – Team_Property_Link
```
Implement fields:
- property_id
- entity_id (FK)
- property_type (Enum)
- property_value
- start_date
- end_date
- confidence_score
- source_references
- notes

CRUD + tests.
```

## Prompt B8 – Team_Sponsor_Link
```
Implement fields:
- link_id
- entity_id
- brand_id
- sponsor_rank (Enum)
- display_order
- start_date
- end_date
- confidence_score
- source_references

CRUD + tests.
```

## Prompt B9 – Team_Succession_Link
```
Implement fields with enums for link_type and qualifiers.

CRUD + traversal endpoint.
Include tests verifying lineage continuity.
```

## Prompt B10 – Supporting Tables
```
Implement:
- UCI_Tier_Label_History
- Data_Source
- Data_Conflict
- Audit_Log
- Color_Scheme

All migrations, models, schemas, CRUD, tests.
```

## Prompt B11 – Seed Data
```
Seed Tier definitions.
Provide alembic seed script + tests verifying seed.
```

---

# PHASE C — API LAYER

## Prompt C1 – Health + Metadata
```
Create endpoints:
- /health
- /meta/version
Fully tested.
```

## Prompt C2 – Sponsor CRUD
```
Implement sponsor CRUD endpoints.
Add search & pagination.
Write full API tests.
```

## Prompt C3 – Lineage CRUD
```
Implement Lineage CRUD.
Add endpoint:
GET /lineages/{id}/entities
With tests.
```

## Prompt C4 – Team_Entity CRUD
```
Implement CRUD with validation:
- start_date < end_date
Add tests.
```

## Prompt C5 – Property Links
```
CRUD for team properties.
Add endpoint:
GET /entities/{id}/properties
With tests.
```

## Prompt C6 – Sponsorship Links
```
CRUD + endpoint:
GET /entities/{id}/sponsors
Test ranking + display_order logic.
```

## Prompt C7 – Succession Endpoints
```
CRUD + endpoint:
GET /lineages/{id}/graph
Return predecessor/successor graph.
Write tests verifying graph shape.
```

---

# PHASE D — CONFLICT ENGINE

## Prompt D1 – Conflict Detection Framework
```
Implement detection service:
- Takes normalized scrape result
- Compares to DB
- Emits Data_Conflict rows
Test with mocked data.
```

## Prompt D2 – Conflict Rules Engine
```
Implement rules:
- DATE_MISMATCH
- NAME_VARIATION
- SPONSOR_CONFLICT
- LINEAGE_DISAGREEMENT
- TIER_MISMATCH
- NATIONALITY_CONFLICT

Write unit tests covering each rule.
```

## Prompt D3 – Auto-Resolution Engine
```
Implement automatic rules:
- unanimity
- gold standard + majority
- formatting normalization

Write tests verifying selection.
```

## Prompt D4 – Confidence Scoring
```
Implement scoring formula.
Include tests for each component.
```

## Prompt D5 – Conflict Review API
```
Endpoints:
- /conflicts
- /conflicts/{id}
- resolve conflict

Tests for role-based access + resolution correctness.
```

---

# PHASE E — SCRAPERS

## Prompt E1 – Scraper Base Class
```
Implement base class with:
- fetch(url)
- parse(html)
- normalize(data)
Test using a local HTML fixture.
```

## Prompt E2 – Scraper Registry
```
Allow registering scraper modules.
Implement automatic discovery.
Write tests.
```

## Prompt E3 – ProCyclingStats Team List Scraper
```
Fetch list of PCS teams.
Parse team links and metadata.
Normalize into internal schema.
Test using stored PCS HTML mocks.
```

## Prompt E4 – PCS Team Details Scraper
```
Parse name changes, sponsors, years.
Normalize dates.
Test with fixtures.
```

## Prompt E5 – Wikipedia Infobox Parser
```
Extract:
- names
- dates
- country
- codes
Test multiple language infoboxes.
```

## Prompt E6 – Wikipedia Narrative Parser
```
Parse text for:
- merge
- split
- license transfer
- continuation

Test using mock articles.
```

## Prompt E7 – Scraper Normalizer
```
Map raw fields → canonical schema.
Test transformation logic.
```

## Prompt E8 – Scraper → Conflict Engine Integrator
```
Implement pipeline:
scrape → normalize → detect conflicts → resolve → DB
Test with controlled data.
```

## Prompt E9 – Scraper Scheduler
```
Add periodic runner.
Test dry-run mode.
```

---

# PHASE F — VISUALIZATION API

## Prompt F1 – Lineage Timeline Endpoint
```
Return all Team_Entity bars for a lineage.
Include sponsor color.
Tests verifying correctness.
```

## Prompt F2 – Sponsor Journey Endpoint
```
Return sponsor-team history.
Add tests.
```

## Prompt F3 – Full Timeline Query
```
Return all lineages within time viewport.
Include bar segments + relationships.
Tests required.
```

## Prompt F4 – Color Resolver
```
Resolve sponsor/team colors.
Test fallback rules.
```

---

# PHASE G — FRONTEND (React + D3)

## Prompt G1 – Frontend Project Skeleton
```
Create React + Vite project.
Add TypeScript, ESLint, Prettier.
Implement layout.
```

## Prompt G2 – Global State
```
Implement Zustand or Redux store:
- viewport
- selection
- filters
Test store logic.
```

## Prompt G3 – Timeline Canvas Container
```
Create SVG or canvas root.
Handle resizing.
Add tests.
```

## Prompt G4 – Timeline Rendering Loop
```
Render team bars.
Test using DOM snapshots.
```

## Prompt G5 – Link Rendering
```
Render successor links as paths.
Test geometry.
```

## Prompt G6 – Color Mapper
```
Map sponsor color → bar color.
Test all variations.
```

## Prompt G7 – Tooltip System
```
Implement hover detection.
Test event behavior.
```

## Prompt G8 – Sidebar
```
Show lineage details.
Test rendering and state transitions.
```

## Prompt G9 – Zoom & Pan
```
Implement D3 zoom behavior.
Test zoom boundaries.
```

## Prompt G10 – Search & Filters
```
Implement text search.
Test filtering logic.
```

## Prompt G11 – Accessibility Enhancements
```
Keyboard navigation.
ARIA attributes.
Snapshot tests.
```

---

# PHASE H — CMS / ADMIN PANEL

## Prompt H1 – Login & Auth
```
Implement admin login (JWT).
Test token flow.
```

## Prompt H2 – Conflict Resolution UI
```
List conflicts, edit, resolve.
Test UI state + API calls.
```

## Prompt H3 – Lineage Editor
```
CRUD for lineages.
Test forms.
```

## Prompt H4 – Entity Editor
```
Edit team entities.
Test validation.
```

## Prompt H5 – Sponsor Editor
```
Create/edit sponsors.
Test full cycle.
```

## Prompt H6 – Audit Log View
```
Display audit log with pagination.
Test filtering + UI.
```

---
