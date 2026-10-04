---
id: "257f0ae5-e791-4730-b11f-434e8a5ec770"
title: "Implementing Scraper API Endpoint"
date: "2026-01-04T19:03:27.242025200Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

# SLICE 14: API Endpoint

## Context
Create an admin-only API endpoint to trigger the scraper remotely.

**Dependencies:** SLICE 13 must be complete.

## Prompt

You are implementing SLICE 14 of the Smart Scraper project. Follow TDD strictly.

### TASK 14.1: Scraper Start Endpoint (Test: Admin Only)

**Test First:**
Create `backend/tests/api/test_scraper_api.py`:
```python
"""Test Scraper API endpoints."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_scraper_start_requires_admin(client: AsyncClient):
    """POST /api/admin/scraper/start requires admin role."""
    response = await client.post("/api/admin/scraper/start")
    assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_scraper_start_as_admin(
    client: AsyncClient,
    admin_auth_headers
):
    """Admin can start scraper."""
    with patch('app.api.admin.scraper.run_scraper_background') as mock:
        mock.return_value = {"task_id": "test-123"}
        
        response = await client.post(
            "/api/admin/scraper/start",
            json={"phase": 1, "tier": "1"},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 202
        assert "task_id" in response.json()
```

**Implementation:**
Create `backend/app/api/admin/scraper.py`:
```python
"""Scraper admin API endpoints."""
import uuid
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from app.api.deps import get_current_admin_user

router = APIRouter(prefix="/scraper", tags=["scraper"])

class ScraperStartRequest(BaseModel):
    """Request to start scraper."""
    phase: int = 1
    tier: str = "1"
    resume: bool = False
    dry_run: bool = False

class ScraperStartResponse(BaseModel):
    """Response from starting scraper."""
    task_id: str
    message: str

# In-memory task tracking (use Redis in production)
_tasks: dict = {}

async def run_scraper_background(task_id: str, request: ScraperStartRequest):
    """Background task to run scraper."""
    from app.scraper.cli import run_scraper
    
    _tasks[task_id] = {"status": "running", "phase": request.phase}
    
    try:
        await run_scraper(
            phase=request.phase,
            tier=request.tier,
            resume=request.resume,
            dry_run=request.dry_run
        )
        _tasks[task_id]["status"] = "completed"
    except Exception as e:
        _tasks[task_id] = {"status": "failed", "error": str(e)}


@router.post("/start", response_model=ScraperStartResponse, status_code=202)
async def start_scraper(
    request: ScraperStartRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_admin_user)
):
    """Start the scraper as a background task."""
    task_id = str(uuid.uuid4())
    
    background_tasks.add_task(
        run_scraper_background,
        task_id,
        request
    )
    
    return ScraperStartResponse(
        task_id=task_id,
        message=f"Scraper Phase {request.phase} started"
    )


@router.get("/status/{task_id}")
async def get_scraper_status(
    task_id: str,
    current_user = Depends(get_current_admin_user)
):
    """Get status of a scraper task."""
    if task_id not in _tasks:
        return {"status": "not_found"}
    return _tasks[task_id]
```

**Verify:** Run `pytest backend/tests/api/test_scraper_api.py -v`

---

### TASK 14.2: Register Router

**Implementation:**
Update `backend/app/api/admin/__init__.py`:
```python
from app.api.admin.scraper import router as scraper_router
# ... existing imports ...
```

Update `backend/main.py`:
```python
from app.api.admin.scraper import router as scraper_router

app.include_router(scraper_router, prefix="/api/admin")
```

---

## Finalize Slice 14

**Step 1: Update Task Checklist**

Edit `docs/SMART_SCRAPER_TASKS.md` and mark the following as complete:
```markdown
- [x] 14.1 Create `POST /api/admin/scraper/start`
- [x] 14.2 Implement background task execution
- [x] 14.3 Create `GET /api/admin/scraper/status`
- [x] 14.4 Add admin-only authorization
- [x] **SLICE 14 COMMITTED**
```

**Step 2: Commit (execute now)**
```bash
git add -A && git commit -m "feat(scraper): add API endpoint

- Add POST /api/admin/scraper/start endpoint
- Add GET /api/admin/scraper/status/{task_id} endpoint
- Admin-only authorization
- Background task execution"
```

---

*Edited relevant file*

*User accepted the command `ls -R backend/app/api`*

*User accepted the command `ls backend/app/api/admin`*

*Viewed [main.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/main.py) *

*Viewed [dependencies.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/dependencies.py) *

*User accepted the command `ls backend/app/api/deps.py`*

*Viewed [admin.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1/admin.py) *

*Viewed [conftest.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/conftest.py) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_scraper_api.py -v`*

*Checked command status*

*Grep searched codebase*

*Grep searched codebase*

*Grep searched codebase*

*User accepted the command `ls backend/app/scraper/cli.py`*

*Viewed [cli.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/cli.py) *

*User accepted the command `mkdir backend/app/api/admin`*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_scraper_api.py -v`*

*Checked command status*

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

*Edited relevant file*

*User accepted the command `git add -A && git commit -m "feat(scraper): add API endpoint

- Add POST /api/admin/scraper/start endpoint
- Add GET /api/admin/scraper/status/{task_id} endpoint
- Admin-only authorization
- Background task execution"`*

*User accepted the command `git add -A`*

*User accepted the command `git commit -m "feat(scraper): add API endpoint

- Add POST /api/admin/scraper/start endpoint
- Add GET /api/admin/scraper/status/{task_id} endpoint
- Admin-only authorization
- Background task execution"`*

*Edited relevant file*

*Edited relevant file*

---

## Session Artifacts & Documentation

### Artifact: `task.md`

# Task: Implement Slice 14 - Scraper API Endpoint

- [x] 14.1 Create `backend/tests/api/test_scraper_api.py`
- [x] 14.2 Implement `backend/app/api/admin/scraper.py`
- [x] 14.3 Register router in `backend/app/api/admin/__init__.py`
- [x] 14.4 Register router in `backend/main.py`
- [x] 14.5 Verify tests
- [x] 14.6 Update `docs/SMART_SCRAPER_TASKS.md`
- [x] 14.7 Commit changes

### Artifact: `walkthrough.md`

# Walkthrough - Slice 14: Scraper API Endpoint

I have implemented the admin-only API endpoints for triggering the scraper and checking its status.

## Changes Made

### Backend Implementation
- **New Admin API Router**: Created [scraper.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/admin/scraper.py) which contains:
  - `POST /api/admin/scraper/start`: Triggers the scraper as a background task. Supports `phase`, `tier`, `resume`, and `dry_run` parameters.
  - `GET /api/admin/scraper/status/{task_id}`: Retrieves the status of a specific scraper task.
- **Admin Package**: Created [__init__.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/admin/__init__.py) to expose the scraper router.
- **Main Application**: Updated [main.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/main.py) to register the new admin router under the `/api/admin` prefix.
- **Authorization**: Integrated `require_admin` dependency to ensure only administrators can access these endpoints.

### Tests
- **API Tests**: Created [test_scraper_api.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/api/test_scraper_api.py) with the following tests:
  - `test_scraper_start_requires_admin`: Verifies that unauthorized requests are rejected (401/403).
  - `test_scraper_start_as_admin`: Verifies that an admin can successfully start the scraper and receive a `task_id`.

## Verification Results

### Automated Tests
Ran `pytest backend/tests/api/test_scraper_api.py -v`:
- `test_scraper_start_requires_admin` - **PASSED**
- `test_scraper_start_as_admin` - **PASSED**

```text
======================== 2 passed, 2 warnings in 0.17s ========================
```

### Task Checklist Updated
Marked Slice 14 as complete in [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md).