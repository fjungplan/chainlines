# Exhaustive Technical History (v0.1.0 - v0.9.3)

### v0.9.3 - 2026-02-06
- **Feature**: Integrated Project Change Log and versioning transparency in UI.
- **Improved**: Normalized UI layout by pushing timeline copyright 20px inwards to clear minimap frame.
- **Fix**: Implemented `_prune_superseded_layouts` in `FamilyDiscoveryService` to eliminate redundant family layouts during structural mergers.
- **Fix**: Completed `invalidate_on_link_delete` hook and added `TeamEra` year-change invalidation events.

### v0.9.0 - 2026-02-05
- **Feature**: Multi-profile Layout Optimization system (A/B/C profiles) with independent config persistence.
- **Feature**: Genetic Algorithm detail stats and penalty breakdown (blockers, crossings, family splay).
- **Feature**: Persistent GA logging system with backend retrieval API.
- **Fix**: Scrubbed redundant sponsor color overrides in frontend UI.
- **Fix**: Resolved optimizer discovery service failure.
- **Improvement**: Enhanced family naming logic based on predominant nodal membership.
- **Fix**: Normalized optimizer Y-indices to eliminate unnecessary swimlane gaps.
- **Fix**: Resolved CI test regressions regarding logging, discovery thresholds, and migration schema.

### v0.8.6 - 2026-02-03
- **Fix**: Resolved critical layout alignment regressions appearing after the January deployment.
- **Fix**: Restored node tooltip interactivity.
- **Fix**: Base URL normalization for API client (removed hardcoded localhost).
- **Fix**: Use `apiClient` for optimizer config to ensure correct base URL and auth headers.

### v0.8.5 - 2026-01-16
- **Feature**: Implemented Era Transfer and Swap UI buttons for lineage correction.
- **Fix**: Resolved encoding and syntax issues in database synchronization scripts.
- **Feature**: "My Edits" page with robust entity resolution fallback.
- **Feature**: GDPR-compliant account deletion workflow.
- **Feature**: Focus Mode for team lineage filtering (Ancestors + Descendants).
- **Improved**: Proportional canvas scaling with bottom-aligned initial view.
- **Improved**: Dynamic node and row heights based on `pixelsPerYear`.
- **Improved**: Drawer slide-over behavior for sidebars.
- **Fix**: Minimap drag jump elimination and bounded dragging logic.
- **Fix**: Visual size of lineage link markers made dynamic based on zoom level.
- **Fix**: Relaxed UCI validation to allow alphanumeric codes (backend + DB).
- **Feature**: Detailed lineage event timeline with icons and merging logic.

### v0.8.4 - 2026-01-13
- **Improved**: Refined timeline UI aesthetics and sidebar toggle subtle visibility.
- **Fix**: Resolved node label positioning and contrast issues with drop shadows.

### v0.8.3 - 2026-01-12
- **Improved**: Enhanced scraper accuracy with Phase 1 & 2 structural safeguards.
- **Feature**: Added progress logging to scraper discovery loop.
- **Fix**: Resolved country attribute error in team assembly phase.

### v0.8.2 - 2026-01-09
- **Fix**: Optimized sponsor extraction and persistence logic in scraper pipeline.
- **Fix**: Implemented `CountryMapper` for IOC/UCI ISO code normalization (206 countries).

### v0.8.1 - 2026-01-06
- **Feature**: Integrated Title Sponsor extraction and tier-based list optimization.
- **Feature**: Added hyper-granular logging across all 3 scraper phases.
- **Fix**: Updated `tier_mapper` with CyclingFlash-specific era mappings.

### v0.8.0 - 2026-01-05
- **Feature**: Smart Scraper Core (Phases 1-3) implementation.
- **Feature**: LLM-based Lineage Decision Engine (LEGAL_TRANSFER, MERGE, SPLIT).
- **Feature**: Scraper Admin UI with live log streaming and run history.
- **Feature**: Secondary source scrapers (CyclingRanking, Wikipedia, Memoire).
- **Feature**: `WorkerPool` with semaphore-based concurrency limits.
- **Feature**: Checkpoint/resume system using JSON persistence.

### v0.7.2 - 2025-12-29
- **Feature**: Finalized Audit Log moderation workflow and UI polish.
- **Improved**: Added logging for moderation actions and user promotions.
- **Fix**: Resolved async lazy loading issues in lineage relationship traversal.

### v0.7.1 - 2025-12-29
- **Feature**: Audit Log UI with notification badge and polling mechanism.
- **Improvement**: Enhanced metadata validation for community edits.

### v0.7.0 - 2025-12-28
- **Feature**: Complete User Maintenance UI with role management.
- **Refactor**: Streamlined Button component system and standardized CSS variables.

### v0.6.5 - 2025-12-23
- **Feature**: Role-Based Editing workflow implementation.
- **Improved**: Data cleanup tools for sponsor maintenance.

### v0.6.4 - 2025-12-22
- **Improvement**: Enhanced "New Era" creation workflow and UX.
- **Maintenance**: Global sponsor data cleanup engine via brand transfer modal.

### v0.6.3 - 2025-12-18
- **Feature**: Google OAuth and Admin assignment persistence.
- **Fix**: Implemented Google OAuth callback security and .env protection.
- **Improved**: Frontend build arguments for Google Client ID injection.

### v0.6.2 - 2025-12-18
- **🚀 DEPLOY**: Production Infrastructure Setup (Nginx, Caddy, SSL).
- **Fix**: Reverted Tailwind CSS integration to resolve production build complexity.
- **Fix**: Resolved deployment permissions and nginx MIME type mapping.
- **Feature**: Integrated Global Country Codes and SVG Flag consistency.

### v0.6.1 - 2025-12-18
- **Fix**: Resolved nginx cache invalidation issues on production.
- **Improvement**: Refactored rendering logic for node color stability.

### v0.6.0 - 2025-12-17
- **Structure**: Core Data Model refactor for schema consistency.
- **Fix**: Resolved deployment lockfile issues.

### v0.5.5 - 2025-12-16
- **Feature**: Fictional timeline seed generation script for testing.
- **Fix**: Resolved node coordinate drift in multi-year lineages.

### v0.5.4 - 2025-12-13
- **Feature**: Swimlane crossing optimization and viscous connector transition markers.
- **Feature**: Viscous connector implementation for smooth lineage transitions.

### v0.5.3 - 2025-12-10
- **Infrastructure**: Automated VPS deployment and database backup automation.
- **Improved**: Log collection scripts for remote troubleshooting.

### v0.5.2 - 2025-12-08
- **Branding**: Rebranded project to ChainLines.
- **Legal**: GDPR-compliant self-hosted font system and official legal docs.

### v0.5.1 - 2025-12-08
- **🚀 DEPLOY**: First internal production push.
- **Infrastructure**: Updated seed files and production environment definitions.

### v0.5.0 - 2025-12-07
- **Feature**: Global Dark Theme application across entire UI.
- **Fix**: Stabilized test infrastructure for SQLite/Postgres parity.

### v0.4.5 - 2025-12-05
- **Fix**: Integrated structural edit wizards into TimelineGraph UI.
- **Improved**: React wizard success handlers with user feedback.

### v0.4.4 - 2025-12-05
- **Feature**: Implementation of Moderation Queue for community contributions.
- **Feature**: Backend moderation endpoints with stats and filtering.

### v0.4.3 - 2025-12-05
- **Feature**: Implemented Split Wizard React component (3-step flow).
- **Fix**: Multi-team split validation handles up to 5 resulting teams.
- **Feature**: Automatic manual override flag on split-created eras.

### v0.4.2 - 2025-12-05
- **Feature**: Implemented Merge Wizard React component (3-step flow).
- **Fix**: Validator implementation for team names and merge reasoning.
- **Feature**: Eager-loading for merge relationships to prevent async lazy-load issues.

### v0.4.1 - 2025-12-05
- **Feature**: Collaborative Edit Metadata Wizard implementation.
- **Feature**: Edit model with JSONB change tracking and version history.
- **Fix**: Resolved DuplicateTableError in migrations with idempotency checks.

### v0.4.0 - 2025-12-05
- **Feature**: Google OAuth + JWT Authentication integration.
- **Feature**: Role-Based Access Control (RBAC) with user banning support.

### v0.3.5 - 2025-11-30
- **Performance**: Frontend Virtualization (ViewportManager) implementation.
- **Performance**: LOD (Level of Detail) rendering and Performance Monitor utility.
- **Fix**: Upgraded to Node 20 for Vite 7.2.4 compatibility.

### v0.3.4 - 2025-11-29
- **Feature**: Integrated SearchBar with fuzzy ranking (exact > starts-with > contains).
- **Feature**: GraphNavigation utility for animated focus and path highlighting.

### v0.3.3 - 2025-11-29
- **Feature**: Interactive Controls for zoom levels and year-range filtering.
- **Feature**: DetailRenderer for zoom-dependent arrowheads and textures.

### v0.3.2 - 2025-11-29
- **Feature**: Advanced Tooltip system and Builder pattern implementation.
- **Feature**: Jersey Slice rendering using sponsor color proportions.

### v0.3.1 - 2025-11-29
- **Feature**: Sankey-style layout algorithm implementation.
- **Feature**: Initial React Frontend shell with Loading/Error handling.

### v0.3.0 - 2025-11-29
- **Feature**: ProCyclingStats team data scraper.
- **Feature**: D3.js setup with basic zoom/pan container.

### v0.2.1 - 2025-11-28
- **Fix**: ETag/If-None-Match conditional headers and mobile-optimized views.

### v0.2.0 - 2025-11-28
- **API**: Public Read API implementation for team history.
- **UI**: Initial Timeline display and Team Detail mobile views.

### v0.1.3 - 2025-11-26
- **Structure**: Sponsor data model and service implementation.
- **Fix**: SQLite-safe constraints and relationship stabilization.

### v0.1.2 - 2025-11-26
- **Feature**: Canonicalization of single-leg MERGE/SPLIT events.

### v0.1.1 - 2025-11-26
- **Structure**: Unified Database Migration System using Alembic.
- **Fix**: Async migration tests with isolated engine support.

### v0.1.0 - 2025-11-26
- **Foundation**: Dual-stack Docker setup (Postgres/alpine, FastAPI, Vite).
- **Model**: Managerial Node and Team Era schema initialization.
