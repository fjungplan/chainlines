---
id: "0c1f30a0-4abf-46c9-88c5-810ed03c46e3"
title: "Investigate UCI Code Mandate"
date: "2026-01-15T19:21:45.458127400Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

The frontend of the Add new era CRUD forces me to add an UCI code. It's not marked as mandatory and as far as I know it's also not mandatory from DB side. Can you please check?

*Edited relevant file*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Edited relevant file*

*Viewed [team.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/team.py) *

*Viewed [team.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/schemas/team.py) *

*Viewed [TeamEraEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraEditor.jsx) *

*Edited relevant file*

*Searched filesystem*

*Edited relevant file*

*User accepted the command `pytest backend/tests/repro_uci_code.py`*

*Viewed [TeamEraTransferModal.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraTransferModal.jsx) *

*Edited relevant file*

### User Input

please implement (test first)

*Searched filesystem*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/models/test_team_era_validation.py`*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

I'm trying to save this as a new era for the Crédit Agricole team for 1935 but once I click save it always reverts to 2009 and also change the name back to Crédit Agricole! When I create a new era right now it pre-populates with the info from the previous, latest era. I want it to be pre-populated from the _selected_ era instead, and of course that it saves my changes, not the pre-populated data!

*Edited relevant file*

*Searched filesystem*

*Grep searched codebase*

*User accepted the command `grep -r "TeamEraEditor" frontend/src`*

*Grep searched codebase*

*Viewed [TeamMaintenancePage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/TeamMaintenancePage.jsx) *

*Edited relevant file*

*Searched filesystem*

*Grep searched codebase*

*Viewed [teams.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1/teams.py) *

*Viewed [team_service.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/services/team_service.py) *

*Viewed [TeamEraBubbles.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraBubbles.jsx) *

*Viewed [teams.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/api/teams.js) *

*Edited relevant file*

### User Input

awesome! let's go! Test first!

*Searched filesystem*

*Searched filesystem*

*Viewed [task.md](file:///C:/Users/fjung/.gemini/antigravity/brain/0c1f30a0-4abf-46c9-88c5-810ed03c46e3/task.md) *

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

yeah still doesn't really work: I'm trying to save this but it doesn't take 1935 as era year!

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

ReferenceError: useRef is not defined

    at TeamEraEditor (http://localhost:5173/src/components/maintenance/TeamEraEditor.jsx?t=1768506452626:30:41)
    at div
    at TeamMaintenancePage (http://localhost:5173/src/pages/maintenance/TeamMaintenancePage.jsx?t=1768506114832:30:39)
    at RenderedRoute (http://localhost:5173/node_modules/.vite/deps/react-router-dom.js?v=fda4010b:4108:5)
    at Outlet (http://localhost:5173/node_modules/.vite/deps/react-router-dom.js?v=fda4010b:4514:26)
    at main
    at div
    at Layout (http://localhost:5173/src/components/layout/MainLayout.jsx:25:40)
    at RenderedRoute (http://localhost:5173/node_modules/.vite/deps/react-router-dom.js?v=fda4010b:4108:5)
    at Routes (http://localhost:5173/node_modules/.vite/deps/react-router-dom.js?v=fda4010b:4578:5)
    at Router (http://localhost:5173/node_modules/.vite/deps/react-router-dom.js?v=fda4010b:4521:15)
    at BrowserRouter (http://localhost:5173/node_modules/.vite/deps/react-router-dom.js?v=fda4010b:5267:5)
    at ErrorBoundary (http://localhost:5173/src/components/ErrorDisplay.jsx:93:5)
    at App
    at AuditLogProvider (http://localhost:5173/src/contexts/AuditLogContext.jsx:28:36)
    at AuthProvider (http://localhost:5173/src/contexts/AuthContext.jsx:23:32)
    at QueryClientProvider (http://localhost:5173/node_modules/.vite/deps/@tanstack_react-query.js?v=fda4010b:3030:3)
    at GoogleOAuthProvider (http://localhost:5173/node_modules/.vite/deps/@react-oauth_google.js?v=fda4010b:42:32)

*Viewed [TeamEraEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraEditor.jsx) *

*Edited relevant file*

*Edited relevant file*

*Viewed [TeamEraEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraEditor.jsx) *

*Edited relevant file*

### User Input

still doesn't take it, neither on save, not on save&close (which by the way only saves and doesn't close)

*Edited relevant file*

*Edited relevant file*

### User Input

aah wait it took it

### User Input

but it hasn't updated the era list on the right

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

...and back again, it really didn't take it!

### User Input

it's still saved as 2009

*Edited relevant file*

*Edited relevant file*

### User Input

you probably need to look either for "Crédit Agricole" (the team name), or "Peugeot - Hutchinson", which is the era I tried to add for 1935 but that ended up being saved for 2009 instead (and still can't be changed to 1935).

*Viewed [TeamEraEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraEditor.jsx) *

*Edited relevant file*

### User Input

II don't like the "Plausible cause" here, I'd like facts! Please investigate again. This must be in the layer between the UI and the database somewhere!.

*Viewed [team.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/schemas/team.py) *

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

please commit

*Edited relevant file*

*Edited relevant file*

*User accepted the command `git status`*

*User accepted the command `git branch --show-current`*

*Edited relevant file*

*User accepted the command `rm backend/tests/repro_uci_code.py`*

*User accepted the command `git add frontend/src/api/teams.js frontend/src/components/maintenance/TeamEraBubbles.jsx frontend/src/components/maintenance/TeamEraEditor.jsx frontend/src/pages/maintenance/TeamMaintenancePage.jsx backend/tests/models/test_team_era_validation.py`*

*User accepted the command `git commit -m "fix(eras): fix era creation persistence, list refresh (cache bust), and pre-population logic"`*

### User Input

what happens when I click "Approve" on an audit log entry? (not from the documentation, but according to the code)?

*Searched filesystem*

*Viewed [audit_log_service.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/services/audit_log_service.py) *

*Viewed [audit_log.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1/audit_log.py) *

*Listed directory [v1](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1) *

*Viewed [moderation.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1/moderation.py) *

*Viewed [edits.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1/edits.py) *

*Viewed [moderation_service.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/services/moderation_service.py) *

*Viewed [audit_log_service.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/services/audit_log_service.py) *

### User Input

can you please check what happened to the latest few audit log events (created by user "smart_scraper" (UUID 00000000001 (lots of zeros) and approved by me fjungplan@gmail.com)? In the last 15-20min. There is at least one lineage event that doesn't seem to have been created!

*Edited relevant file*

*User accepted the command `python backend/scripts/validate_recent_edits.py`*

*Viewed [database.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/db/database.py) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `python backend/scripts/validate_recent_edits.py`*

*Listed directory [chainlines](file:///c:/Users/fjung/Documents/DEV/chainlines) *

*Edited relevant file*

*User accepted the command `python backend/scripts/validate_recent_edits.py`*

*User accepted the command `python -c "
import asyncio
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.getcwd())
from app.db.database import async_session_maker
from app.models.team import TeamNode
from sqlalchemy import select

async def check_names():
    async with async_session_maker() as session:
        stmt = select(TeamNode).where(TeamNode.legal_name.ilike('%Intermarch%'))
        result = await session.execute(stmt)
        nodes = result.scalars().all()
        for n in nodes:
            print(f'Found: {n.legal_name} (ID: {n.node_id})')

        stmt = select(TeamNode).where(TeamNode.legal_name.ilike('%Vacansoleil%'))
        result = await session.execute(stmt)
        nodes = result.scalars().all()
        for n in nodes:
             print(f'Found: {n.legal_name} (ID: {n.node_id})')

if __name__ == '__main__':
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_names())
"`*

*Edited relevant file*

*User accepted the command `rm backend/scripts/validate_recent_edits.py`*

*Edited relevant file*

### User Input

did you add the "loud fail" and case-insensitivity to "Revert edit " too? because I would like to just go to the approved entry, revert it, and then re-apply it instead of creating it manually from scratch.

### User Input

welp... didn't fail, but didn't go to the DB either! audit log entry see screenshot

*Viewed [lineage.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/lineage.py) *

*User accepted the command `python -c "
import asyncio
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.getcwd())
from app.db.database import async_session_maker
from app.models.edit import EditHistory
from app.models.lineage import LineageEvent
from sqlalchemy import select

async def inspect():
    async with async_session_maker() as session:
        # Find the edit with 'retry' in notes or just the latest approved lineage event
        stmt = select(EditHistory).where(
            EditHistory.entity_type == 'lineage_event',
            EditHistory.review_notes.ilike('%retry%')
        ).order_by(EditHistory.reviewed_at.desc())
        
        result = await session.execute(stmt)
        edit = result.scalars().first()
        
        if not edit:
            print('No edit found with retry notes')
            return

        print(f'Edit ID: {edit.edit_id}')
        print(f'Snapshot After: {edit.snapshot_after}')
        
        # Check if event exists
        event = await session.get(LineageEvent, edit.entity_id)
        if event:
            print(f'LineageEvent FOUND: ID={event.event_id}')
            print(f'Year: {event.event_year}')
            print(f'Predecessor: {event.predecessor_node_id}')
            print(f'Successor: {event.successor_node_id}')
        else:
            print('LineageEvent NOT FOUND in DB')

if __name__ == '__main__':
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect())
"`*

*User accepted the command `python -c "
import asyncio
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.getcwd())
from app.db.database import async_session_maker
from app.models.edit import EditHistory, EditStatus
from app.models.lineage import LineageEvent
from sqlalchemy import select

async def inspect():
    async with async_session_maker() as session:
        # Get LATEST approved lineage event
        stmt = select(EditHistory).where(
            EditHistory.entity_type == 'lineage_event',
            EditHistory.status == EditStatus.APPROVED
        ).order_by(EditHistory.reviewed_at.desc())
        
        result = await session.execute(stmt)
        edit = result.scalars().first()
        
        if not edit:
            print('No approved edit found')
            return

        print(f'Edit ID: {edit.edit_id}')
        print(f'Snapshot After: {edit.snapshot_after}')
        
        if 'event_year' not in edit.snapshot_after and 'year' not in edit.snapshot_after:
             print('CRITICAL: NO YEAR IN SNAPSHOT')

if __name__ == '__main__':
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect())
"`*

*User accepted the command `python -c "
import asyncio
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.getcwd())
from app.db.database import async_session_maker
from app.models.edit import EditHistory
from sqlalchemy import select, String, cast

async def inspect():
    async with async_session_maker() as session:
        # Search for text from user screenshot
        reason_fragment = '%German Wikipedia explicitly states that after Vacansoleil-DCM was dissolved%'
        
        # We might need to cast snapshot to string to search inside JSONB
        stmt = select(EditHistory).where(
            cast(EditHistory.snapshot_after, String).ilike(reason_fragment)
        )
        
        result = await session.execute(stmt)
        edit = result.scalars().first()
        
        if not edit:
            print('No edit found matching reasoning text')
            return

        print(f'Edit ID: {edit.edit_id}')
        print(f'Status: {edit.status}')
        print(f'Snapshot After: {edit.snapshot_after}')

if __name__ == '__main__':
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect())
"`*

*Edited relevant file*

*User accepted the command `python backend/scripts/test_null_year.py`*

*Edited relevant file*

*User accepted the command `python backend/scripts/test_null_year.py`*

*Edited relevant file*

*User accepted the command `rm backend/scripts/test_null_year.py`*

*Edited relevant file*

### User Input

hmm yeah I don't like that. That's risky and opens huge gaps for manipulation. Loud fail should be enough (but I should get it!)

*Edited relevant file*

### User Input

Can you please check all remaining audit log entries of all types for missing mandatory details, and just get rid of them if they are incomplete?

*Edited relevant file*

*User rejected the command `python backend/scripts/cleanup_invalid_edits.py`*

### User Input

I mean pending records only of course

### User Input

actually, no, that's a bad idea. Loud fail for all kinds of audit log entries with any kind of missing data is much better. then I can still use the "notes" text to recreate tehm myself!

*User accepted the command `rm backend/scripts/cleanup_invalid_edits.py`*

*Viewed [audit_log_service.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/services/audit_log_service.py) *

*Viewed [audit_log_service.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/services/audit_log_service.py) *

*Edited relevant file*

*Edited relevant file*

### User Input

great, please commit that!

*Edited relevant file*

*User rejected the command `git add backend/app/services/audit_log_service.py`*

*User accepted the command `git commit -m "fix(audit): enforce loud failure for missing mandatory data in audit log application"`*

### User Input

sry, I had to interrupt you because the page didn't load but that seems to have been temporary. Please commit & push

*User accepted the command `git status`*

*Viewed [task.md](file:///C:/Users/fjung/.gemini/antigravity/brain/0c1f30a0-4abf-46c9-88c5-810ed03c46e3/task.md) *

*Viewed [walkthrough.md](file:///C:/Users/fjung/.gemini/antigravity/brain/0c1f30a0-4abf-46c9-88c5-810ed03c46e3/walkthrough.md) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `git add backend/app/services/audit_log_service.py`*

*User accepted the command `git commit -m "fix(audit): enforce loud failure for missing mandatory data in audit log application"`*

*User accepted the command `git push`*

*Checked command status*

### User Input

can you explain to me where those era "carD" colors come from? Why are they differnt?

*Listed directory [maintenance](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance) *

*Viewed [TeamEraBubbles.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraBubbles.jsx) *

*User accepted the command `grep -r "era-bubble" frontend/src`*

*Checked command status*

*User accepted the command `findstr /S /C:"era-bubble" frontend\src\*.css`*

*Checked command status*

*Viewed [TeamMaintenancePage.css](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/TeamMaintenancePage.css) *

### User Input

ok makes sense, thank you. Now one last thing for today: the timeline rendering of nodes: Currently, if they don't have a dissolution date, we simply render "until the end", right? Instead I'd like only render from the first until the last era (gaps between eras are "filled"), not beyond, even if there is no dissolution year! Only exception being teams with no dissolution year where the last known era is from "current year - 1", these ones should "keep going".

*Listed directory [visualizations](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/visualizations) *

*Searched filesystem*

*Viewed [TimelineGraph.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/TimelineGraph.jsx) *

*Viewed [layoutCalculator.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils/layoutCalculator.js) *

*Edited relevant file*

### User Input

perfect, pleae commit & push! enough for today!

*Viewed [task.md](file:///C:/Users/fjung/.gemini/antigravity/brain/0c1f30a0-4abf-46c9-88c5-810ed03c46e3/task.md) *

*Viewed [walkthrough.md](file:///C:/Users/fjung/.gemini/antigravity/brain/0c1f30a0-4abf-46c9-88c5-810ed03c46e3/walkthrough.md) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `git add frontend/src/utils/layoutCalculator.js`*

*User accepted the command `git commit -m "feat(viz): smart node duration logic - cap inactive teams at last era"`*

*User accepted the command `git push`*

---

## Session Artifacts & Documentation

### Artifact: `task.md`

# Task: Refine Era Creation and Pre-population

- [x] Fix "Revert" bug in `TeamEraEditor` <!-- id: 3 -->
    - Added error handling for stale cache.
    - Added `lastSavedEraId` ref to skip re-fetching stale data after save (CRITICAL FIX).
    - Added `refreshTrigger` to `TeamEraBubbles` to sync list.
- [x] Fix Era List not updating on save <!-- id: 5 -->
    - [x] Pass a `lastUpdate` timestamp/trigger to `TeamEraBubbles`.
- [x] Fix "Saved as 2009 / List not updating" Bug <!-- id: 6 -->
    - **Root Cause Found**: Backend sends `Cache-Control: max-age=300`. Browser serves stale list.
    - **Fix**: Added `_t` timestamp to `getTeamEras` API call in frontend to force fresh fetch.
- [x] Verify the fix <!-- id: 4 -->
- [x] Verify Audit Log Robustness <!-- id: 7 -->
    - Investigated "Approved but missing" Audit Log entries.
    - **Fix**: Implemented "Loud Fail" (ValueError) in `AuditLogService` for TeamEra, TeamNode, LineageEvent, and SponsorLink creation if mandatory data is missing.
    - Prevents silent failures where edits are marked "Approved" but no data is written.
- [x] Refine Timeline Node Rendering <!-- id: 8 -->
    - **Requirement**: Stop "zombie" bars (infinite duration) for teams that stopped existing but lack a `dissolution_year`.
    - **Fix**: Updated `LayoutCalculator` to cap node duration at the last era's year unless the team is "Active" (last era is current or previous year).

### Artifact: `walkthrough.md`

# Verification: Clone from Selected & Revert Fix

## What was done
- **Clone Feature**: Updated `TeamMaintenancePage` to pass the `baseEraId` (selected era) to `TeamEraEditor` when clicking "+ New Era". The editor now prioritizes this ID for pre-population.
- **Revert Fix (Editor)**: Added `lastSavedEraId` check to `useEffect` in `TeamEraEditor` to prevent re-fetching stale data immediately after save.
- **Persistence Fix (List/Bubbles)**:
    - **Issue**: The backend sends `Cache-Control: max-age=300` for the Era List.
    - **Symptom**: After saving 1935, the browser served the *cached* list (old data) to the EraBubbles component, so the new era didn't appear.
    - **Fix**: Modified `frontend/src/api/teams.js` to add a cache-busting timestamp (`_t=...`) to `getTeamEras` calls. This forces the browser to fetch the fresh list from the server.
- **Audit Log Robustness (Loud Fail)**:
    - **Issue**: Edits with missing mandatory data (e.g., Lineage Events without a year due to scraper bugs) were being marked "Approved" but failing silently in the background constraint checks.
    - **Fix**: Updated `AuditLogService` to explicitly raise `ValueError` ("Loud Fail") if mandatory fields are missing for Eras, Nodes, Sponsors, or Lineage Events. This ensures admins see an error immediately instead of a false "Approved" success.
- **Timeline Visualization**:
    - **Issue**: Teams without a `dissolution_year` were rendered as "infinite" bars extending to the present day, even if they stopped racing in 1950.
    - **Fix**: Updated `LayoutCalculator` to check the `last_era`. If the last era is old (not current/last year), the bar now correctly visualizes as ending at that era, removing "zombie" teams from the modern timeline.

## Verification Steps performed

### 1. Manual Verification (User Action Required)
Please perform the following steps:

#### Test Persistence
1. Open a team (e.g., Peugeot).
2. Create New Era -> Enter **1935**.
3. Click **"Save"**.
4. Verify that:
    - The Form **stays on 1935** (Editor check).
    - The **Era List (Right Column)** refreshes and **shows 1935** (List Cache check).
    - If you reload the page, 1935 is still there.

#### Test Audit "Loud Fail"
1. Attempt to Revert/Re-apply a broken audit log entry (e.g., one missing a year).
2. Verify that the system now shows an **Error** message instead of marking it "Approved".

#### Test Timeline
1. Observe the main Timeline Graph.
2. Verify that old teams (e.g. historical teams from the 1900s) do not have bars extending all the way to 2026 unless they are actually still active.

## Conclusion
The combination of `lastSavedEraId` (Editor state protection) and API Cache Busting (List freshness) ensures the user sees exactly what they saved immediately. Additionally, the backend Audit Log service is now hardened against incomplete data, and the Timeline visualization is cleaner and more accurate.

### Artifact: `implementation_plan.md`

# Bug Fix: Season Year "Reverting" to Default

## Problem
When creating a new era, if the user changes the Season Year (e.g. 1935), it sometimes saves as the default (e.g. 2009). This happens because `loadLatestEraForPrepopulation` is likely re-running and overwriting `formData` with defaults even after user input, or running right before save due to a subtle re-render/effect dependency issue.

## Proposed Changes

### [TeamEraEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraEditor.jsx)
1. **Deduplicate Initialization**:
   - Add `isInitialized` state/ref.
   - Only run `loadLatestEraForPrepopulation` ONCE when `!eraId` AND `!isInitialized`.
   - Prevent it from running on subsequent renders or prop updates unless explicitly reset.

2. **Fix `useEffect` Dependencies**:
   - The current `useEffect` depends on `[eraId, nodeId]`.
   - If `eraId` flips (e.g. during save/close transition), it might trigger a reload.
   - We will decouple "Load Existing" and "Initialize New" into separate effects.

### Backend Verification
- Double check `backend/app/api/v1/teams.py` and `services/team_service.py` to ensure no "auto-correction" of years happens (unlikely, but worth checking).

## Verification
- User Scenario: Select 1990 -> New Era (defaults to 2010?) -> Change to 1935 -> Save -> Result MUST be 1935.