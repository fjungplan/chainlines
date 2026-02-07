import React from 'react';
import CenteredPageLayout from '../components/layout/CenteredPageLayout';
import Card from '../components/common/Card';
import './AboutPage.css'; // Reuse AboutPage styles for consistency

export default function ChangeLogPage() {
    return (
        <CenteredPageLayout>
            <Card title="Project Change Log">
                <section>
                    <h2>v0.9.4 - 2026-02-07: Timeline & Optimizer Refinement</h2>
                    <ul>
                        <li><strong>Timeline</strong>: Implemented "Sort by End Year" toggle with secondary sorting criteria for improved visual flow.</li>
                        <li><strong>Timeline</strong>: Fixed Minimap synchronization to guarantee layout consistency with the main timeline view.</li>
                        <li><strong>Timeline</strong>: Added adaptive velocity-based zoom for smoother navigation at deep zoom levels.</li>
                        <li><strong>Optimizer</strong>: Decoupled Live vs Profile settings and refined chain building logic for strict temporal continuity.</li>
                        <li><strong>Data</strong>: Enhanced Team Creation with Dissolution Year support and Source URL tracking.</li>
                        <li><strong>Stability</strong>: Enforced lineage link uniqueness and resolved Sponsor creation reliability issues.</li>
                    </ul>
                </section>

                <section>
                    <h2>v0.9.3 - 2026-02-06: Versioning & Transparency</h2>
                    <ul>
                        <li><strong>Versioning</strong>: Integrated project versioning transparency and this dedicated Change Log page.</li>
                        <li><strong>UI Geometry</strong>: Pushed timeline copyright 20px inwards to prevent overlap with the collapsed minimap border.</li>
                        <li><strong>Optimizer</strong>: Implemented structural pruning in the Family Discovery Service to automatically eliminate redundant layouts during component mergers.</li>
                        <li><strong>Maintenance</strong>: Completed lineage invalidation hooks and added TeamEra year-change events to ensure layout freshness.</li>
                    </ul>
                </section>

                <section>
                    <h2>v0.9.0 - 2026-02-05: Multi-Profile Optimization Engine</h2>
                    <ul>
                        <li><strong>Optimizer</strong>: Implemented a multi-profile optimization system (A/B/C configurations) allowing independent persistence of layout settings.</li>
                        <li><strong>Analytics</strong>: Added GA detail stats and a comprehensive penalty breakdown (blockers, crossings, family splay).</li>
                        <li><strong>Diagnostics</strong>: Integrated a persistent optimizer logging system with real-time log retrieval.</li>
                        <li><strong>Refinement</strong>: Normalized Y-indices to eliminate unnecessary swimlane gaps and improved family naming heuristics.</li>
                        <li><strong>Sponsorship</strong>: Scrubbed redundant sponsor color overrides in the UI and refined brand naming logic based on nodal membership.</li>
                        <li><strong>Stability</strong>: Resolved CI test regressions regarding logging, discovery thresholds, and migration schema.</li>
                    </ul>
                </section>

                <section>
                    <h2>v0.8.6 - 2026-02-03: Layout & API Stabilization</h2>
                    <ul>
                        <li><strong>Stability</strong>: Resolved critical layout alignment regressions appearing after the January deployment.</li>
                        <li><strong>UX</strong>: Restored node tooltip interactivity and fixed API client base URL normalization.</li>
                        <li><strong>Optimizer</strong>: Switched to <code>apiClient</code> for optimizer configurations to ensure correct base URL and authentication headers in production.</li>
                    </ul>
                </section>

                <section>
                    <h2>v0.8.5 - 2026-01-16: Scraper & Admin Deployment</h2>
                    <ul>
                        <li><strong>Smart Scraper</strong>: Implemented the full Phase 1-3 scraper pipeline with LLM-based data extraction and record assembly.</li>
                        <li><strong>Arbitration</strong>: Integrated an LLM Conflict Arbiter for automated lineage decisions (mergers, splits, transfers).</li>
                        <li><strong>Admin</strong>: Created the Scraper Admin UI with run history, background task controls, and live log streaming.</li>
                        <li><strong>Lineage</strong>: Added dedicated Era Transfer and Swap UI buttons for manual record correction.</li>
                        <li><strong>Localization</strong>: Implemented a comprehensive <code>CountryMapper</code> covering all 206 IOC countries with ISO normalization.</li>
                        <li><strong>UX</strong>: Refined the timeline minimap drag behavior, fixed coordinate mapping jumps, and restored tooltip interactions.</li>
                        <li><strong>Audit</strong>: Finalized the Audit Log moderation workflow with polling and real-time notification badges.</li>
                        <li><strong>Search</strong>: Improved SearchBar with accent-insensitivity and fuzzy ranking (exact &gt; starts-with &gt; contains).</li>
                        <li><strong>Visualization</strong>: Added viscous connector transition markers and implemented dynamic physical zoom thresholds.</li>
                        <li><strong>User Tools</strong>: Implemented "My Edits" page and a GDPR-compliant account deletion workflow.</li>
                        <li><strong>Interaction</strong>: Separated vertical scroll from zoom (Ctrl+Scroll) and added navigation hint overlays.</li>
                        <li><strong>Maintenance</strong>: Added database synchronization scripts for push/pull operations and sponsor consolidation tools.</li>
                    </ul>
                </section>

                <section>
                    <h2>v0.6.2 - 2025-12-18: Production Environment Setup</h2>
                    <ul>
                        <li><strong>Infrastructure</strong>: Finalized production-ready Nginx, Caddy, and SSL/TLS configuration.</li>
                        <li><strong>Security</strong>: Integrated Google OAuth 2.0 with JWT-based sessions and role-based access control (RBAC).</li>
                        <li><strong>Refinement</strong>: Optimized the layout engine for swimlane crossing reduction and added transition markers.</li>
                        <li><strong>Stability</strong>: Resolved production build issues by reverting Tailwind CSS to vanilla CSS and fixing nginx MIME type mappings.</li>
                        <li><strong>Assets</strong>: Integrated global country codes and standardized SVG flag icons across the UI.</li>
                        <li><strong>Improved</strong>: Refactored rendering logic for node color stability and resolved deployment lockfile issues.</li>
                        <li><strong>Workspace</strong>: Enhanced "New Era" workflow and team maintenance responsiveness.</li>
                    </ul>
                </section>

                <section>
                    <h2>v0.5.1 - 2025-12-08: Initial Production Push</h2>
                    <ul>
                        <li><strong>Launch</strong>: Initial deployment of the ChainLines platform (formerly 'Velograph') to the primary VPS.</li>
                        <li><strong>Visualization</strong>: Implemented the core Sankey-style layout algorithm with jersey slice rendering and interactive tooltips.</li>
                        <li><strong>Workspace</strong>: Created the Edit Metadata, Merge, and Split wizards for collaborative team history editing.</li>
                        <li><strong>Performance</strong>: Added viewport virtualization (ViewportManager) and Level of Detail (LOD) rendering logic to maintain 60fps.</li>
                        <li><strong>Auth</strong>: Implemented the moderation queue and administrative user promotion system.</li>
                        <li><strong>Foundation</strong>: Established the Python/FastAPI/Postgres backend with Alembic-based schema migrations and automated backup scripts.</li>
                        <li><strong>Compliance</strong>: Integrated a GDPR-compliant self-hosted font system and official legal documentation.</li>
                        <li><strong>Testing</strong>: Stabilized test infrastructure for SQLite/Postgres parity and added fictional timeline seed scripts.</li>
                    </ul>
                </section>
            </Card>
        </CenteredPageLayout>
    );
}
