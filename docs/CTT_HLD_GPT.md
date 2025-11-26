# Cycling Team Lineage Timeline Specification

# 1. Project overview & goals

**Product name (working):** Cycling Lineage Timeline

**Primary goal:**
An open-source, public, wiki-style web application that visualizes the lineage of professional men’s cycling teams (WorldTeam-level + important ProTeams and predecessors) from 1900 → present. Focus on team entities (license/organization), name periods, sponsor evolution, merges/splits (formal & informal), and clean interactive timeline visualizations.

**Key constraints / non-goals at v1:**
- No rider-level data (out of scope for v1).
- No logos or images required initially
- No public API initially.
- Open-source / free-to-use stack.
- Collaborative editing with wiki-style audit trail; immediate publishing, optional moderation later.

---

# 2. Scope & feature summary

**Must-have (v1):**
- Data model to represent teams (immutable ID), team name periods, sponsor brands/groups & sponsor periods with role & prominence, kit colors, and directed lineage links (formal and informal).
- Scraper(s) for prioritized sources (PCS, FirstCycling, Wikipedia [EN/DE/FR/IT/ES/NL], FirstCycling, CQRanking, CyclingRanking, others).
- Scraper reconciliation rules (weighted consensus + priority resolution; PCS weighted higher).
- Interactive horizontal timeline visualization with zoom, mini-map, hover/click highlights, vertical stacked sponsor slices, Bézier connectors for lineage.
- Hybrid editor (forms + mini-timelines) with full revision history & rollback, conflict warnings, and audit logging.
- Manual rescrape trigger for selected sources; initial scraping automation.
- Support day-level timestamps, year-level rendering granularity; intra-season splits supported.
- Public read-only browsing; editing requires account.
- Open-source repository and Docker-friendly deployment.

**Nice-to-have (later):**
- Moderation workflow (approval gating).
- Optional Neo4j/graph DB integration for complex graph queries.
- Optional rider-level cues.
- Import/export features (CSV/JSON).
- API endpoints for developers (future).

---

# 3. High-level architecture (recommended)

**Stack:**
- Backend: Python FastAPI
- ORM / Migrations: SQLAlchemy + Alembic
- Database: PostgreSQL
- Caching / Job queue: Redis + Celery
- Frontend: React + D3.js
- Visualization acceleration: optional PixiJS/WebGL
- Scraping: Scrapy + BeautifulSoup; Selenium/Playwright fallback
- Containerization: Docker + Compose
- Auth: Local accounts, session-based or JWT
- Observability: Prometheus + Grafana + Sentry
- Source repo: GitHub/GitLab (MIT/Apache 2.0)

---

# 4. Data model (developer-ready summary)

**Core tables:**
- team
- team_name_period
- sponsor_group
- sponsor_brand
- team_sponsor_period
- team_color_period
- lineage_link
- scrape_evidence
- user
- revision
- year_snapshot (optional caching)

**Notes:** Use JSONB for flexible fields; dates with DATE/TIMESTAMP; indexes for start/end date, GIN for JSONB.

---

# 5. Key API / internal endpoints

**Read-only:**
- `GET /api/v1/timeline`
- `GET /api/v1/team/{team_id}`
- `GET /api/v1/sponsor/{sponsor_brand_id}`
- `GET /api/v1/minimap`

**Editor/Admin:**
- Scrape trigger, CRUD for team, name period, sponsor period, lineage link, revision rollback.
- Conflict dashboard and merge/split review endpoints.

---

# 6. Scraping & identity-resolution strategy

- Scraper fetches pages from prioritized sources.
- Extract structured items and store in `scrape_evidence`.
- Weighted confidence scores per source.
- Conflict detection for low confidence or contradictory data.
- Identity resolution rules: auto-merge high-confidence, suggest editor review medium, separate low.
- Sponsor timeline consolidation: weighted consensus + priority tie-breaking.

---

# 7. Editor UX & UI spec

- Global toolbar: zoom, search box, filters, row ordering, "Hide ephemeral teams" toggle.
- Minimap: overview timeline.
- Timeline canvas: horizontal time axis, vertical team rows.
- Team row: vertical stacked sponsor slices, hover highlights lineage, click focus mode.
- Sidebar panel: metadata, sponsor timeline, lineage links, revisions.
- Editor: login required, drag-resize mini-timeline editor, conflict dashboard, rollback functionality.

---

# 8. Visualization rules & rendering details

- Unit: day-level stored, year-level rendered by default.
- Sponsor slices: max 4, vertical stack, horizontal ribbons, gradients.
- Lineage connectors: curved Bézier, styles by type (continuity, merge-in, split-off, informal continuity), hover glow.
- Performance: default 10-year viewport, lazy-load additional years/teams, virtualization, canvas/WebGL fallback if needed.

---

# 9. Data validation & error handling

- Input validation for dates, sponsor ranks, importance.
- Warnings for overlaps, suspicious ranges.
- Scrape errors: retries, backoff, logs.
- Conflict handling: present to editor, no auto-overwrite.
- Security: sanitize inputs, parameterized queries, rate-limits.

---

# 10. Testing plan

**Unit tests:** models, scrapers, reconciliation logic, lineage heuristics, API endpoints.

**Integration tests:** end-to-end timeline API, scraper integration.

**UI tests:** React component + E2E (Playwright/Cypress).

**Performance testing:** zoom/pan, large dataset rendering.

**Security tests:** XSS, auth, rate-limits.

**Acceptance tests:** load default viewport, zoom/focus, editor flows, revisions, scraper evidence/conflicts.

---

# 11. Deployment & operations

- Dockerized backend/frontend, Redis, PostgreSQL.
- CI/CD: GitHub Actions.
- Monitoring: logs, Prometheus/Grafana, Sentry.
- Backups: daily logical dumps, weekly full backups.

---

# 12. Implementation roadmap

- Phase 0: repo, CI, Docker, base backend.
- Phase 1: data model, editor CRUD + revision.
- Phase 2: scraping PCS + Wikipedia, conflict detection.
- Phase 3: timeline visualization (React + D3).
- Phase 4: performance tuning, caching, lazy-loading.
- Phase 5: QA, documentation, public release.

---

# 13. Acceptance criteria & handoff checklist

- DB schema & migrations implemented.
- CRUD + revisions functional.
- Scrapers implemented with evidence storage.
- Weighted reconciliation engine functional.
- Timeline visualization functional with zoom, minimap, focus, hover highlights.
- Editor UI functional, drag-resize mini-timeline, rollback.
- Conflict dashboard functional.
- Tests: unit, integration, UI, performance.
- Docker deployment & CI configured.
- Documentation complete.

---

# 14. Developer notes & gotchas

- Row layout topological.
- Time bucketing: day-level stored, year-level default.
- Overlapping naming periods: allow but flag.
- Conflict resolution: scraper cannot auto-overwrite unless admin-approved.
- Performance: SVG + D3 virtualization first; canvas/WebGL if needed.
- Color palettes: colorblind accessibility.
- Data provenance: tie all decisions to `scrape_evidence`.
- Internationalization support.
- Licensing & attribution for sources.

---

# 15. Example payloads

```json
{
  "id": 17,
  "canonical_name": "Ineos Grenadiers",
  "founding_year": 2010,
  "disbanding_year": null,
  "name_periods": [...],
  "sponsor_periods": [...],
  "colors": [...]
}
```

---

# 16. Documentation & handoff artifacts

- README, architecture diagram, data model ER diagram.
- Scraper mapping docs, reconciliation algorithm doc.
- Editor user manual.
- API docs (OpenAPI/Swagger).
- Test matrix.

---

# 17. Developer next actions

- Initialize repo, CI, Docker.
- Implement DB schema, migrations.
- Team CRUD + revisions.
- Scraper for PCS + evidence storage.
- Timeline payload API + minimal React timeline demo.
- Iterate: more scrapers, editor UI, conflict reconciliation.

