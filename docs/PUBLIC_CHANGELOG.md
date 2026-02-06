# ChainLines Project Change Log

### v0.9.3 - 2026-02-06: Versioning & Transparency
- **Versioning**: Integrated project versioning transparency and this dedicated Change Log page.
- **UI Geometry**: Pushed timeline copyright 20px inwards to prevent overlap with the collapsed minimap border.
- **Optimizer**: Implemented structural pruning in the Family Discovery Service to automatically eliminate redundant layouts during component mergers.
- **Maintenance**: Completed lineage invalidation hooks and added TeamEra year-change events to ensure layout freshness.

### v0.9.0 - 2026-02-05: Multi-Profile Optimization Engine
- **Optimizer**: Implemented a multi-profile optimization system (A/B/C configurations) allowing independent persistence of layout settings.
- **Analytics**: Added GA detail stats and a comprehensive penalty breakdown (blockers, crossings, family splay).
- **Diagnostics**: Integrated a persistent optimizer logging system with real-time log retrieval.
- **Refinement**: Normalized Y-indices to eliminate unnecessary swimlane gaps and improved family naming heuristics.
- **Sponsorship**: Scrubbed redundant sponsor color overrides in the UI and refined brand naming logic based on nodal membership.
- **Stability**: Resolved CI test regressions regarding logging, discovery thresholds, and migration schema.

### v0.8.6 - 2026-02-03: Layout & API Stabilization
- **Stability**: Resolved critical layout alignment regressions appearing after the January deployment.
- **UX**: Restored node tooltip interactivity and fixed API client base URL normalization.
- **Optimizer**: Switched to `apiClient` for optimizer configurations to ensure correct base URL and authentication headers in production.

### v0.8.5 - 2026-01-16: Scraper & Admin Deployment
- **Smart Scraper**: Implemented the full Phase 1-3 scraper pipeline with LLM-based data extraction and record assembly.
- **Arbitration**: Integrated an LLM Conflict Arbiter for automated lineage decisions (mergers, splits, transfers).
- **Sources**: Added support for CyclingRanking, Wikipedia (multi-language), and Memoire du Cyclisme (via Wayback Machine proxy).
- **Admin**: Created the Scraper Admin UI with run history, background task controls, and live log streaming.
- **Lineage**: Added dedicated Era Transfer and Swap UI buttons for manual record correction.
- **Localization**: Implemented a comprehensive `CountryMapper` covering all 206 IOC countries with ISO normalization.
- **UX**: Refined the timeline minimap drag behavior, fixed coordinate mapping jumps, and restored tooltip interactions.
- **Audit**: Finalized the Audit Log moderation workflow with polling and real-time notification badges.
- **Search**: Improved SearchBar with accent-insensitivity and fuzzy ranking (exact > starts-with > contains).
- **Visualization**: Added viscous connector transition markers and implemented dynamic physical zoom thresholds.
- **User Tools**: Implemented "My Edits" page and a GDPR-compliant account deletion workflow.
- **Interaction**: Separated vertical scroll from zoom (Ctrl+Scroll) and added navigation hint overlays.
- **Maintenance**: Added database synchronization scripts for push/pull operations and sponsor consolidation tools.

### v0.6.2 - 2025-12-18: Production Environment Setup
- **Infrastructure**: Finalized production-ready Nginx, Caddy, and SSL/TLS configuration.
- **Security**: Integrated Google OAuth 2.0 with JWT-based sessions and role-based access control (RBAC).
- **Refinement**: Optimized the layout engine for swimlane crossing reduction and added transition markers.
- **Stability**: Resolved production build issues by reverting Tailwind CSS to vanilla CSS and fixing nginx MIME type mappings.
- **Assets**: Integrated global country codes and standardized SVG flag icons across the UI.
- **Improved**: Refactored rendering logic for node color stability and resolved deployment lockfile issues.
- **Workspace**: Enhanced "New Era" workflow and team maintenance responsiveness.

### v0.5.1 - 2025-12-08: Initial Production Push
- **Launch**: Initial deployment of the ChainLines platform (formerly 'Velograph') to the primary VPS.
- **Visualization**: Implemented the core Sankey-style layout algorithm with jersey slice rendering and interactive tooltips.
- **Workspace**: Created the Edit Metadata, Merge, and Split wizards for collaborative team history editing.
- **Performance**: Added viewport virtualization (ViewportManager) and Level of Detail (LOD) rendering logic to maintain 60fps.
- **Auth**: Implemented the moderation queue and administrative user promotion system.
- **Foundation**: Established the Python/FastAPI/Postgres backend with Alembic-based schema migrations and automated backup scripts.
- **Compliance**: Integrated a GDPR-compliant self-hosted font system and official legal documentation.
- **Testing**: Stabilized test infrastructure for SQLite/Postgres parity and added fictional timeline seed scripts.
