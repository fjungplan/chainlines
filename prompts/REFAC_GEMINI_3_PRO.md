# Velograph Refactor Plan

## Objectives
- Stabilize async behavior and eliminate lazy-load triggers in the read API.
- Standardize service/repository boundaries and error semantics.
- Improve performance with predictable eager-loading + caching.
- Prepare the backend for Prompt 10 frontend integration.

## Principles
- Non-functional refactor first: retain API contracts unless clearly beneficial.
- Small, reviewable PRs with targeted tests per change.
- Prefer `selectinload` and explicit projections over ad-hoc relationship access.
- Keep Pydantic v2 models lean; minimize nested payloads for mobile.

## Phase A — Data Access Hygiene
- Audit repositories (`TeamRepository`, timeline-related):
	- Ensure all read paths load relationships via `selectinload`.
	- Add explicit `.options(...)` in repository methods rather than services.
- Extract light DTO builders for common views (timeline era, team summary).
- Add guardrails: no lazy-loads in async during serialization.

## Phase B — Service Layer Consolidation
- Clarify responsibilities:
	- `TeamService`: write operations, validations.
	- `TeamDetailService`: team history assembly + transition classification.
	- `TimelineService`: graph building and range filters.
- Extract shared utilities:
	- Status calculation (active/historical/dissolved).
	- Transition classification (MERGED_INTO, ACQUISITION, REVIVAL, SPLIT).
- Define `ServiceError` types → consistent HTTP mapping in routers.

## Phase C — API Consistency & Caching
- Standardize headers on mobile endpoints:
	- `Cache-Control: max-age=300`
	- `ETag` + `If-None-Match` → 304 when unchanged.
- Normalize query/path validation with FastAPI `Query(..., ge/le)` and UUID parsing.
- Ensure consistent 400/404/5xx semantics across endpoints.

## Phase D — Tests & CI
- Unit tests: assert no async lazy loads (history, timeline, sponsors).
- Integration tests: SQLite fixtures; Postgres CI via Alembic migrations.
- Light perf checks: response size bounds, query count where practical.
- Keep CI single-run; avoid duplicate triggers.

## Phase E — Documentation & DevEx
- Update `USER_GUIDE.md` with ETag/Cache-Control behavior and conditional requests.
- Add README notes on async pitfalls and eager-loading strategy.
- Track milestones in `prompts/todo.md` for visibility.

## Milestones
- [ ] Repositories use `selectinload` consistently with explicit options.
- [ ] Services share utilities and avoid implicit lazy loads.
- [ ] Endpoints standardized: headers + error mapping.
- [ ] Tests pass locally and CI; perf checks added.
- [ ] Docs updated; frontend Prompt 10 ready.

## Risks & Mitigations
- Hidden lazy-load regressions → add tests that serialize responses under async and fail on lazy access.
- Scope creep → keep PRs small, phase-by-phase, link back to this plan.

## Delivery Plan
- Open incremental PRs from `refactor/intermediate-phase` to `main` per phase.
- Each PR includes: brief description, tests touched, and any perf observations.
