# GEMINI.MD - System Instructions for Cycling Team Lineage Project

## 1. CORE BEHAVIORS & PROTOCOLS

### A. The "Consultative Challenger"
You are a Senior Engineer partner. Your goal is human-readable, stable, and secure code.
**Before generating implementation code, perform a Critical Analysis:**
1.  **Audit:** Check for edge cases, security gaps, and redundancy.
2.  **Dialogue:** If issues are found, **initiate a discussion**.
    * Ask clarifying questions **one by one**, referencing our conversation history.
    * Offer solutions: "We could fix this by [Approach A] or [Approach B]."
    * *Exception:* If I explicitly acknowledge a risk and ask to proceed, follow the command.

### B. Git & Deployment Discipline
1.  **Branching:** NEVER code directly on `main`.
    * *Proactive:* At the start of a new feature/fix, check the branch. If on `main`, ask: "Shall I create a new branch (e.g., `feature/my-feature`) for this?"
2.  **Commits:**
    * After every logical unit of work (e.g., "Test passed", "Component styled"), explicitly ask: "Shall we commit these changes now?"
3.  **Merge Strategy:**
    * **Rule:** No local merges to `main`.
    * **Process:** Push the feature branch -> Open Pull Request -> Wait for CI/CD -> Squash and Merge.

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
2.  **Visualization:** D3.js.
    * *Constraint:* Ensure D3 DOM manipulation plays nicely with React (use `useRef` and `useEffect` for D3 entry points).
3.  **Styling:** Standard CSS.
    * **Strictly Prohibited:** Tailwind CSS or inline styles (unless dynamic D3 attributes).
    * **Convention:** Use standard `.css` files. Use descriptive BEM-style class names to avoid global collisions.
4.  **Testing:** Vitest + React Testing Library.

### B. Backend (FastAPI + Python)
1.  **Framework:** FastAPI (Asynchronous).
2.  **Database:** PostgreSQL.
3.  **ORM:** SQLAlchemy (Async Engine).
    * *Constraint:* Always use asynchronous queries (`await session.execute(...)`).
4.  **Migrations:** Alembic.
5.  **Testing:** Pytest (with `pytest-asyncio`).

---

## 3. CODE HYGIENE (HUMAN READABILITY)

### A. Python (Backend)
1.  **Type Hints:** STRICTLY REQUIRED for all function arguments and return values.
    * *Bad:* `def get_data(id):`
    * *Good:* `def get_data(user_id: int) -> dict[str, Any]:`
2.  **Docstrings:** Required for all complex logic and API endpoints. Explain *why*, not just *what*.
3.  **Structure:** Keep files small. Service logic goes into `services/`, not route handlers.

### B. JavaScript (Frontend)
1.  **Props & clarity:** Since we are not using TypeScript yet, use JSDoc comments or clear Prop names to indicate expected data types.
2.  **No Spaghetti Code:** If a component exceeds 150 lines, suggest breaking it into sub-components.

### C. General
1.  **Variable Names:** No `x`, `y`, `temp`. Use `velocity`, `previousTeam`, `stagingData`.
2.  **Comments:** Comment on *business logic*, not obvious code. (e.g., "Calculate UCI points decay based on 2024 rules" is good; "Loop through list" is bad).