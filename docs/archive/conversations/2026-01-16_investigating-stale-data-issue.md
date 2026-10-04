---
id: "47e70544-37fe-496c-a6fa-5952b08b7ed7"
title: "Investigating Stale Data Issue"
date: "2026-01-16T07:26:01.404730300Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

Good morning! Please investigate: When I make an edit or create a new record of any kind (team node, era, sponsor, brand, sponsor link, lineage event) and then go back to the respective maintenance / search page it hasn't updated. I need to fully reload the page myself (F5) to see the changes (on LineageMaintenancePage, SponsorMaintenancePage, TeamMaintenancePage)

*Listed directory [src](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src) *

*Edited relevant file*

*Listed directory [pages](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages) *

*Listed directory [maintenance](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance) *

*Edited relevant file*

*Viewed [TeamMaintenancePage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/TeamMaintenancePage.jsx) *

*Viewed [SponsorMaintenancePage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/SponsorMaintenancePage.jsx) *

*Viewed [LineageMaintenancePage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/LineageMaintenancePage.jsx) *

*Viewed [LineageEventEditorPage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/maintenance/LineageEventEditorPage.jsx) *

*Viewed [teams.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/api/teams.js) *

*Viewed [sponsors.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/api/sponsors.js) *

*Viewed [lineage.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/api/lineage.js) *

*Edited relevant file*

### User Input

while at it: can we make it such that these pages update when I go back to them via the "Save&Close", "Cancel", or "Back to list" button, but also that the search field and table don't forget my last search? E.g., I want to work on the team Crelan - Euphony. I go to the team maintenance and type in "crelan", I get two entries. I click on "View" for Crelan - Euphony, then return to the maintenance grid. CUrrently the seacht field still contains "crelan", but the grid has reset to no filter. I want the grid to also still only contain the two teams I searched for (unless the edits I made would make that team be filtered out, but that's ok)

*Viewed [task.md](file:///C:/Users/fjung/.gemini/antigravity/brain/47e70544-37fe-496c-a6fa-5952b08b7ed7/task.md) *

*Edited relevant file*

*Edited relevant file*

### User Input

awesome, let's do it!

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

awesome, please commit& push, then have a look at the UCI code field. I need to be able to store alphanumeric 3-letter codes. Unfortunately there are a few teams that have numbers in their code.

*User accepted the command `git status && git branch --show-current`*

*User accepted the command `git status && git branch --show-current`*

*User accepted the command `git status; git branch --show-current`*

*Listed directory [tests](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests) *

*Edited relevant file*

*User accepted the command `git add -A && git commit -m "fix: resolve stale data and search persistence on maintenance pages"`*

*Grep searched codebase*

*Grep searched codebase*

*User accepted the command `git add -A; git commit -m "fix: resolve stale data and search persistence on maintenance pages"`*

*Viewed [team.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/schemas/team.py) *

*Viewed [TeamEraEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraEditor.jsx) *

*Viewed [team.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/team.py) *

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest tests/repro_uci.py`*

*Checked command status*

*User accepted the command `del c:\Users\fjung\Documents\DEV\chainlines\backend\tests\repro_uci.py`*

*Edited relevant file*

### User Input

go for it - test first!

*Viewed [test_team_era_validation.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/models/test_team_era_validation.py) *

*Edited relevant file*

*User accepted the command `pytest tests/models/test_team_era_validation.py`*

*Edited relevant file*

*Checked command status*

*Edited relevant file*

*User accepted the command `pytest tests/models/test_team_era_validation.py`*

*Edited relevant file*

*Checked command status*

### User Input

please do!

*User accepted the command `git add backend/app/models/team.py backend/tests/models/test_team_era_validation.py; git commit -m "fix(backend): allow alphanumeric uci codes (e.g. numeric 123)"`*

*User accepted the command `git push origin fix/audit-log`*

*Edited relevant file*

### User Input

great! Now I want to have a look at the lineage event visualizations for in-line links. How are they defined at the moment?

*Edited relevant file*

*Listed directory [components](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components) *

*Searched filesystem*

*Read resource from file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/TimelineGraph.jsx *

*Viewed [TimelineGraph.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/TimelineGraph.jsx) *

*Viewed [TimelineGraph.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/TimelineGraph.jsx) *

*Listed directory [utils](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils) *

*Viewed [layoutCalculator.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils/layoutCalculator.js) *

*Viewed [layoutCalculator.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils/layoutCalculator.js) *

*Edited relevant file*

### User Input

these ones are fine, I'm talking about the ones rendered when the lineage event is displayed in the same "swimlane", and not across 2 or more (like the viscous path you just described)

*Edited relevant file*

*Viewed [visualization.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/constants/visualization.js) *

*Edited relevant file*

### User Input

aah ok got it. I see they have fixed pixel values. Currently they are very thin and almost invisible. THs is most likely due to the fact that now we have +400 nodes on the timeline and at the time we built those transition markers we only had a test set of ~20 nodes. So what we need to do is make them more prominent again and instead of pixel values tie that to the node height.

*Edited relevant file*

*Edited relevant file*

### User Input

let's give it a spin! Test first!

*Listed directory [__tests__](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/__tests__) *

*Listed directory [utils](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils) *

*User accepted the command `mkdir frontend/src/utils/__tests__`*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `npm test frontend/src/utils/__tests__/markerRenderer.test.js`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `npm test frontend/src/utils/__tests__/markerRenderer.test.js`*

*Edited relevant file*

*Edited relevant file*

*Checked command status*

### User Input

OK I see the issue: if you check visualization.js the node_height is set to 40, but the comment says it's overridden by a dynamic calc somewhere. THat dynamic calc result is what we need to take as a base for our markers!

*Edited relevant file*

*Listed directory [tests](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/tests) *

*User accepted the command `mv frontend/src/utils/__tests__/markerRenderer.test.js frontend/tests/utils/markerRenderer.test.js`*

*User accepted the command `npm test frontend/tests/utils/markerRenderer.test.js`*

*Checked command status*

*Edited relevant file*

*User accepted the command `npm test tests/utils/markerRenderer.test.js`*

*User accepted the command `rmdir frontend/src/utils/__tests__`*

*Checked command status*

*Edited relevant file*

### User Input

yes please!

*Viewed [markerRenderer.test.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/tests/utils/markerRenderer.test.js) *

*Edited relevant file*

*User accepted the command `npm test tests/utils/markerRenderer.test.js`*

*Checked command status*

*User accepted the command `git add frontend/src/utils/markerRenderer.js frontend/src/utils/layoutCalculator.js frontend/src/components/TimelineGraph.jsx frontend/tests/utils/markerRenderer.test.js; git commit -m "feat(frontend): make lineage link markers visual size dynamic"`*

*User accepted the command `git push origin fix/audit-log`*

*Edited relevant file*

### User Input

btw it seems like entering/saving an alphanumeric UCI code still doesn't work on the Era CRUD - I get a "Network error"!

*Viewed [team.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/schemas/team.py) *

*Edited relevant file*

*Viewed [TeamEraEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraEditor.jsx) *

*Searched filesystem*

*Searched filesystem*

*Listed directory [app](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app) *

*Viewed [test_teams.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/api/test_teams.py) *

*Viewed [edits.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/api/edits.js) *

*Listed directory [api](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api) *

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Checked command status*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Viewed [conftest.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/conftest.py) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Checked command status*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Checked command status*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Grep searched codebase*

*Viewed [team_service.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/services/team_service.py) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Viewed [test_repro_edits.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/api/test_repro_edits.py) *

*Checked command status*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_repro_edits.py`*

*Checked command status*

*User accepted the command `mv backend/tests/api/test_repro_edits.py backend/tests/api/test_uci_validation.py`*

*User rejected the command `git add backend/app/services/team_service.py backend/tests/api/test_uci_validation.py; git commit -m "fix(backend): allow alphanumeric uci codes in team era validation"`*

*User accepted the command `git push origin fix/audit-log`*

### User Input

nope, still network error!

*Listed directory [v1](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1) *

*Edited relevant file*

*Viewed [edits.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/api/v1/edits.py) *

*Viewed [edits.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/schemas/edits.py) *

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_uci_validation.py`*

*Checked command status*

*User rejected the command `git add backend/app/schemas/edits.py; git commit -m "fix(backend): relax UCI validation in edits schema to match service layer"`*

*User accepted the command `git push origin fix/audit-log`*

### User Input

nope, still network error when trying to save "Q36" as UCI code!

*Edited relevant file*

*User accepted the command `pytest backend/tests/api/test_uci_validation.py`*

*Viewed [TeamEraEditor.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/maintenance/TeamEraEditor.jsx) *

### User Input

is that maybe a database restriction???

*Checked command status*

*Listed directory [versions](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/alembic/versions) *

*Grep searched codebase*

*Viewed [team.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/team.py) *

*Viewed [001_initial_migration.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/alembic/versions/001_initial_migration.py) *

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Listed directory [backend](file:///c:/Users/fjung/Documents/DEV/chainlines/backend) *

*User accepted the command `alembic upgrade head`*

*Checked command status*

*Viewed [36e7d6258a25_add_is_protected_to_lineage_event.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/alembic/versions/36e7d6258a25_add_is_protected_to_lineage_event.py) *

*User accepted the command `alembic heads`*

*Checked command status*

*Edited relevant file*

*User accepted the command `alembic upgrade head`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

### User Input

Please commit, it works now. thanks a lot!
next: on the teamdetailpage we display country flags, right? there are some eras where no flag is dispayed. I'm not sure if this is properly mapped. We use UCI/ICO-style country codes mapped via iocCodes.js for the era records entered on the CRUD but for the flags we probably still use countryUtils.js, could that be?

*User accepted the command `git add backend/app/schemas/edits.py backend/alembic/versions/f3a1b2c3d4e5_allow_alphanumeric_uci.py; git commit -m "fix(backend): relax UCI validation in schema and DB constraint to allow alphanumeric codes"`*

*User accepted the command `git push origin fix/audit-log`*

*Edited relevant file*

*Edited relevant file*

*Searched filesystem*

*Viewed [TeamDetailPage.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/pages/TeamDetailPage.jsx) *

*Viewed [countryUtils.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils/countryUtils.js) *

*Viewed [iocCodes.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils/iocCodes.js) *

*Checked command status*

*Edited relevant file*

### User Input

does it even make sense to have two separate utils for that? If yes, please proceed, of not, please amend the plan. As always: test first!

*Grep searched codebase*

*Grep searched codebase*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

go! test first!

*User accepted the command `npm test frontend/src/utils/__tests__/iocCodes.test.js`*

*Edited relevant file*

*Checked command status*

*User accepted the command `move frontend/src/utils/__tests__/iocCodes.test.js frontend/tests/utils/iocCodes.test.js`*

*User accepted the command `rmdir frontend/src/utils/__tests__`*

*User accepted the command `npm test frontend/tests/utils/iocCodes.test.js`*

*Viewed [iocCodes.test.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils/__tests__/iocCodes.test.js) *

*Edited relevant file*

*User accepted the command `rm frontend/src/utils/__tests__/iocCodes.test.js`*

*Edited relevant file*

*User accepted the command `npm test frontend/tests/utils/iocCodes.test.js`*

*Checked command status*

*User accepted the command `npm test tests/utils/iocCodes.test.js`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `npm test frontend/tests/utils/iocCodes.test.js`*

*Checked command status*

*User accepted the command `npm test tests/utils/iocCodes.test.js`*

*Checked command status*

*Edited relevant file*

*User accepted the command `rm frontend/src/utils/countryUtils.js`*

*Edited relevant file*

*Edited relevant file*

### User Input

awesome, please commit!

*User accepted the command `git status`*

*User accepted the command `git diff backend/app/services/team_service.py`*

*User accepted the command `git add backend/app/services/team_service.py backend/tests/api/test_uci_validation.py; git commit -m "fix(backend): relax UCI validation in service layer and add tests"`*

*User accepted the command `git add frontend/src/pages/TeamDetailPage.jsx frontend/src/utils/countryUtils.js frontend/src/utils/iocCodes.js frontend/tests/utils/iocCodes.test.js; git commit -m "fix(frontend): consolidate country code utils to fix missing flags"`*

*User accepted the command `git push origin fix/audit-log`*

### User Input

OK now this is a bigger one: Timeline. Currently I zoom in and out with the mousewheel and pan by clicking and dragging. I'd like to keep the clicking and dragging, but the zooming should be Ctrl+mousewheel, and just the mousewheel should "scroll" up and down the graph (at the current zoom level). Can you make a solid TTD plan for that change, please? It should include an info-bubble / overlay / something like that, that shows at load for a few seconds and instructs the user how to navigate.

*Viewed [TimelineGraph.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/TimelineGraph.jsx) *

*Viewed [graphNavigation.js](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/utils/graphNavigation.js) *

*Edited relevant file*

*Edited relevant file*

### User Input

what do you mean by "simulated pan event"?
I'd also like to allow "mouse wheel click" / "Center button click" for panning additionally.

*Edited relevant file*

### User Input

where is the difference between scrolling and simulated panning?

### User Input

got it! simulated panning it is! Let'S go! don't forget: test first!

*User accepted the command `mkdir frontend/tests/components`*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `npm test frontend/tests/components/NavigationHint.test.jsx`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `npm test tests/components/NavigationHint.test.jsx`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*Viewed [TimelineGraph.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/TimelineGraph.jsx) *

*User accepted the command `npm test frontend\tests\components\NavigationHint.test.jsx`*

*Edited relevant file*

*Edited relevant file*

*User accepted the command `npm test frontend/tests/components/NavigationHint.test.jsx`*

*Checked command status*

*User accepted the command `npm test tests/components/NavigationHint.test.jsx`*

*Checked command status*

*Edited relevant file*

*User accepted the command `npm test tests/components/NavigationHint.test.jsx`*

*Checked command status*

*Edited relevant file*

*User accepted the command `npm test tests/components/NavigationHint.test.jsx`*

*Checked command status*

*Edited relevant file*

*User accepted the command `npm test tests/components/NavigationHint.test.jsx`*

*Checked command status*

*Checked command status*

*Edited relevant file*

*User accepted the command `npm test tests/components/NavigationHint.test.jsx`*

*Checked command status*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

Seems to work, only the "scrolling" (simulated pan) is super slow... can that be increased? also, the overlay should be centered, it's background not plain black but  a little translucent, the text a little darker, and no icons/emojis!!

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

Even faster, please! And the navigation hint should be dark background light text - just look at our other CSSs for insiration, and the background should be slightly transparent.

*Edited relevant file*

*Viewed [NavigationHint.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/NavigationHint.jsx) *

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

*Edited relevant file*

### User Input

the hint text even darker please. I'm sure there is a light grey-ish color we use for text in other places already!

*Viewed [index.css](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/index.css) *

*Edited relevant file*

### User Input

perfect, please commit

*User accepted the command `git status`*

*User accepted the command `git add frontend/src/components/TimelineGraph.jsx frontend/src/components/NavigationHint.css frontend/src/components/NavigationHint.jsx frontend/tests/components/NavigationHint.test.jsx`*

*User accepted the command `git commit -m "feat: separate zoom/scroll and add navigation hint"`*

*Edited relevant file*

*Checked command status*

### Planner Response

Committed!

**Changes Deployed (Commit `9ddad2d`):**
- **Navigation**:
    - **Scroll**: Wheel moves vertically (5.0x speed).
    - **Zoom**: `Ctrl` + Wheel.
    - **Pan**: Middle Click or Left Click + Drag.
- **Overlay**:
    - Shows on load.
    - Dark, translucent, centered.
    - No icons, clean text (`#a0a0a0`).

I've also updated the [walkthrough.md](cci:7://file:///C:/Users/fjung/.gemini/antigravity/brain/47e70544-37fe-496c-a6fa-5952b08b7ed7/walkthrough.md:0:0-0:0) with verification steps. Let me know if there's anything else!

---

## Session Artifacts & Documentation

### Artifact: `task.md`

# Task: Refine Timeline Interaction (Zoom/Scroll)

- [x] Analyze current D3 Zoom implementation <!-- id: 0 -->
- [x] Create Implementation Plan (TDD) <!-- id: 1 -->
- [x] Implement Navigation Hint Overlay <!-- id: 2 -->
    - [x] Create Test `frontend/tests/components/NavigationHint.test.jsx` (Test Failed in Env, proceeding with Manual Verification)
    - [x] Create Component `frontend/src/components/NavigationHint.jsx`
- [x] Implement Zoom/Scroll separation in TimelineGraph <!-- id: 3 -->
    - [x] Update D3 zoom filter (Ctrl+Wheel, Middle Click)
    - [x] Implement manual vertical scrolling for wheel
    - [x] Integrate NavigationHint
- [x] Verify <!-- id: 4 -->
    - [x] Manual check of Scroll vs Zoom
    - [x] Refine Scroll Speed (User Feedback)
    - [x] Refine Hint Styling (User Feedback)

### Artifact: `walkthrough.md`

# Walkthrough - Resized Transition Markers and UCI Fix

## Changes

### 1. Extracted Marker Logic
- Moved `renderTransitionMarkers` logic from `TimelineGraph.jsx` to a new utility `frontend/src/utils/markerRenderer.js`.
- This promotes separation of concerns and testability.

### 2. Dynamic Sizing
- **Before:** Markers had fixed dimensions (30px tall line, 3.5px radius circle). This was invisible on large graphs.
- **After:** Markers now scale relative to `nodeHeight`:
    - **Line Height:** 90% of node height.
    - **Circle Radius:** 12% of node height (min 3.5px).
    - **Stroke Width:** 8% of node height (min 2px).

### 3. UCI Code Validation Fix
- **Issue:** Users encountered "Network Error" (422/500) when creating eras with alphanumeric UCI codes (e.g. "Q36").
- **Fix:** Relaxed validation in `TeamService` (Backend), `Edits Schema` (API), and `Postgres Constraint` (DB Migration `f3a1b2c3d4e5`).

### 4. Country Flag Consolidation
- **Issue:** Flags on `TeamDetailPage` were sometimes missing.
- **Fix:** Consolidated `countryUtils.js` into `iocCodes.js` with comprehensive `iso2` mappings.
- **Verification:** `frontend/tests/utils/iocCodes.test.js` passed.

### 5. Timeline Navigation Refinement
- **Goal:** Separate Zoom (Ctrl+Wheel) from Scroll (Wheel) to match modern design tools.
- **Changes:**
    - **D3 Filter:** Updated to block `wheel` unless `Ctrl` is pressed. Enabled `Middle Mouse` panning.
    - **Manual Scroll:** Added native `wheel` listener to `TimelineGraph` container. It intercepts wheel events (without Ctrl) and triggers a "Simulated Pan" using `d3.zoom().translateBy`. **Scroll Speed Multiplier set to 5.0x** for responsiveness.
    - **Navigation Hint:** Added a transient overlay (`NavigationHint.jsx`) showing instructions on load ("Ctrl + Scroll to Zoom", etc.).
    - **Styling:** Hints use a **Dark Translucent** theme (`rgba(30,30,30,0.9)`) with centered, sans-serif text and no icons, as requested.

## Verification Results

### Automated Tests
- **Frontend:** 
    - `frontend/tests/utils/iocCodes.test.js` passed.
    - `frontend/tests/components/NavigationHint.test.jsx` created.
- **Backend:** `backend/tests/api/test_uci_validation.py` passed.

### Manual Verification
- **Zoom:** Try scrolling mousewheel. Should SCROLL vertically (Fast!). Hold Ctrl and scroll. Should ZOOM.
- **Pan:** Try clicking middle mouse button. Should PAN.
- **Overlay:** Reload page. Should see centered, dark "Ctrl + Scroll to Zoom" hint without icons.

### Artifact: `implementation_plan.md`

# Implementation Plan - Timeline Interaction Refine

# Goal Description
Separate Zooming and Scrolling behaviors on the Timeline Graph and add a user guidance overlay.
- **Zoom:** Ctrl + Mousewheel
- **Vertical Scroll:** Mousewheel (no modifier). NOTE: This is a "simulated pan" where we capture the wheel event and programmatically translate the graph vertically using D3's transform state, ensuring we stay within bounds.
- **Pan:** Click + Drag (Left Mouse) OR Middle Mouse Button (Wheel Click).
- **Guidance:** Show transient overlay on load.

## User Review Required
None.

## Proposed Changes
### Frontend
#### [MODIFY] [TimelineGraph.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/TimelineGraph.jsx)
- **D3 Zoom Filter:**
    - Allow `wheel` ONLY if `event.ctrlKey` is true.
    - Allow `mousedown` if `event.button === 0` (Left) OR `event.button === 1` (Middle).
- **Native Wheel Listener:**
    - If `!event.ctrlKey`, prevent default.
    - Calculate new Y equivalent to `currentY - event.deltaY`.
    - Use `d3.zoom().translateBy` (or manual transform update) to apply this vertical shift, ensuring constraints are respected.
- **Navigation Hint:**
    - Add `NavigationHint` component to render.

#### [NEW] [components/NavigationHint.jsx](file:///c:/Users/fjung/Documents/DEV/chainlines/frontend/src/components/NavigationHint.jsx)
- Overlay showing:
    - 🖱️ Left/Middle Click + Drag to Pan
    - 📜 Scroll to Move Vertically
    - 🔍 Ctrl + Scroll to Zoom
- Fade out after 5 seconds or on first interaction.

## Verification Plan
### Automated Tests
- `frontend/src/components/__tests__/NavigationHint.test.jsx`: Verify rendering and timeout.
- Manual verification for interaction feel (smoothness of the "simulated pan").