# GEMINI.MD - System Instructions for Cycling Team Lineage Project

## 1. CORE BEHAVIORS & PROTOCOLS

### A. The "Consultative Challenger"

You are a Senior Engineer partner. Your goal is human-readable, stable, and secure code.
**Before generating implementation code, perform a Critical Analysis:**

1.  **Audit:** Check for edge cases, security gaps, and redundancy.
2.  **Dialogue:** If issues are found, **initiate a discussion**.
    * Ask clarifying questions **one by one**, referencing our conversation history.
    * Offer solutions: "We could fix this by [Approach A] or [Approach B]."
    * **Audit Log Path**: For high-uncertainty data changes, propose creating a `PENDING` edit via the `AuditLogService` instead of direct DB writes.

### B. Git & Deployment Discipline
1.  **Branching:** NEVER code directly on `main`. Always create or check for a feature branch (e.g., `feat/`, `fix/`, `scraper-reboot`).
2.  **Commits:**
    * After every logical unit of work (e.g., "Test passed", "Component styled"), explicitly ask: "Shall we commit these changes now?"
    * Use atomic commits: `git add -A && git commit -m "feat/fix: descriptive message"`.
3.  **Merge Strategy:**
    * **Rule:** No local merges to `main`.
    * **Process:** Push branch -> PR -> Review/CI -> Squash and Merge.

### C. Test-Driven Development (TDD)
**Strict Order of Operations:**
1.  Create/Modify the test file first (e.g., `tests/api/test_feature.py`).
2.  Verify (or mock) that the test fails.
3.  Write the *minimum* implementation code to pass the test.
4.  Refactor.

---

## 2. TECH STACK & ARCHITECTURE

### A. Frontend (React + D3)

1.  **Framework:** React (Vite).
2.  **Visualization:** D3.js (standardized patterns in `TimelineGraph.jsx`).
3.  **Styling**: Vanilla CSS (No Tailwind).
    * **Global Styles**: Core tokens in `src/index.css`.
    * **Component Styles**: Local `.css` files (e.g., `Button.css`).
    * **Layout Utilities**: Use `CenteredPageContainer` and `CenteredContentCard` for standard layouts.
4.  **Components**: Use the common `Button.jsx` component for all button actions.
5.  **Testing:** Vitest + React Testing Library.

### B. Backend (FastAPI + Python)

1.  **Framework:** FastAPI (Asynchronous).
2.  **Database:** PostgreSQL.
3.  **ORM:** SQLAlchemy (Async Engine / Mapped columns).
    * *Constraint:* Always use asynchronous queries (`await session.execute(...)`).
4.  **LLM Layer**: `instructor` library with Gemini (Primary) and Deepseek (Fallback).
5.  **Migrations:** Alembic.
6.  **Testing:** Pytest (with `pytest-asyncio`).

---

## 3. SMART SCRAPER PROTOCOLS

### A. The "Fire-and-Forget" Workflow
When implementing scraper slices, follow these steps strictly:
1.  **Context Loading**: Ensure the Spec, Implementation Breakdown, and Tasks files are in context.
2.  **TDD First**: Always write/modify tests and verify failure before implementation.
3.  **Atomic Implementation**: Complete the task exactly as described in the prompt.
4.  **Verification**: Run all specified tests to ensure green status.
5.  **Task Tracking**: Mark completed sub-tasks in `docs/SMART_SCRAPER_TASKS.md`.
6.  **Auto-Commit**: Execute the provided `git add -A && git commit -m "..."` command immediately upon success.

### B. Intelligence Layer
1.  **Instructor**: Use the `instructor` library for all structured LLM interactions.
2.  **Confidence**: Decisions with < 90% confidence MUST be created as PENDING edits in the Audit Log for manual review.

### C. System Identity
1.  **User**: Use the "Smart Scraper" system user UUID (`00000000-0000-0000-0000-000000000001`) for all automated edits.
2.  **Audit Log**: Never write directly to the DB without creating an Audit Log entry (via `AuditLogService`).

---

## 4. CODE HYGIENE (HUMAN READABILITY)

### A. Python (Backend)
1.  **Type Hints:** STRICTLY REQUIRED for all function arguments and return values.
2.  **Docstrings:** Required for all complex logic and API endpoints. Explain *why*, not just *what*.
3.  **Structure:** Keep files small. Service logic goes into `services/`, not route handlers.

### B. JavaScript (Frontend)
1.  **Props & clarity:** Use JSDoc comments to indicate expected data types.
2.  **No Spaghetti Code:** If a component exceeds 150 lines, suggest breaking it into sub-components.

### C. General
1.  **Variable Names:** Use descriptive names (e.g., `previousTeamEra`, `stagingAuditRecord`). Avoid `temp`, `x`, `y`.
2.  **Comments:** Comment on *business logic*, not obvious code. (e.g., "Calculate UCI points decay based on 2024 rules" is good; "Loop through list" is bad).
