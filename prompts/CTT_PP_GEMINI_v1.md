Professional Cycling Team Timeline Visualization - Blueprint, Architecture & Prompts
Blueprint & Architecture Strategy
This project is broken down into 6 distinct phases to manage complexity. We start with the data foundation (Backend) before moving to the visualization (Frontend).

Tech Stack Strategy:
Backend: Python (FastAPI) + SQLAlchemy + SQLite (initially, easy to upgrade to PostgreSQL).
Frontend: React + D3.js (for the complex Sankey visualization).
Testing: pytest for backend data logic, manual verification via API responses and seed scripts.
---

Phase 1: Core Data Foundation (Backend)We start by building the "Spiritual Team" data model. Without a solid database schema for Lineages, Entities, and Sponsorships, the visualization is impossible.
Phase 2: The Scraper EngineBefore building the UI, we need data. We will build a modular scraping engine to fetch data (simulated initially to avoid IP bans during dev).
Phase 3: Basic API & ManagementExposing the data via REST endpoints so the frontend can consume it.
Phase 4: Frontend Skeleton & D3 SetupSetting up the React environment and integrating D3.js.
Phase 5: The Sankey VisualizationThe core challenge—rendering the lineage flows, time scales, and connections.
Phase 6: Interaction & PolishAdding sidebars, zoom, pan, and final integration.
---

Iterative Prompt Chain
Feed these prompts to a code-generation LLM one by one. Verify the output of each step before moving to the next.
---

Phase 1: The Data Foundation
---
Prompt 1: Database Setup & Models
Context: We are building a Professional Cycling Team Timeline Visualization. The core concept is a "Team Lineage" (the spiritual succession of a team) which contains multiple "Team Entities" (specific time periods/names).

Task:
1. Set up a basic FastAPI project structure with SQLAlchemy and SQLite.
2. Create the database models for `Team_Lineage` and `Team_Entity` based on the specification:
   - `Team_Lineage`: id, primary_name, founding_year, notes.
   - `Team_Entity`: id, lineage_id (FK), start_date, end_date.
3. Create a Pydantic model for creating and reading these entities.
4. Write a `database.py` file that initializes the DB.
5. Write a script `seed_data.py` that creates one sample lineage (e.g., "Team Sky/Ineos") with 3 historical entities (Sky 2010-2018, Ineos 2019-2020, Ineos Grenadiers 2021-Present) to verify the relationships work.

Constraints:
- Use modern Python type hints.
- Ensure foreign keys are correctly set up.
- The seed script must print out the lineage and its children entities to console to prove it works.
---

Prompt 2: Adding Sponsorships & Properties
Context: Building on the previous step, we need to add complexity to the data model. Teams have properties (Names, UCI Codes) and Sponsors that change over time.

Task:
1. Update the SQLAlchemy models to include:
   - `Team_Property_Link`: id, entity_id (FK), property_type (Enum: NAME, UCI_CODE, TIER, NATIONALITY), property_value, start_date, end_date.
   - `Sponsor_Master`: id, legal_name, country.
   - `Sponsor_Brand`: id, sponsor_id (FK), brand_name.
   - `Team_Sponsor_Link`: id, entity_id (FK), brand_id (FK), sponsor_rank (Enum), start_date, end_date.
2. Update `seed_data.py` to:
   - Add "Team Sky" and "Ineos" as sponsors.
   - Link them to the existing entities created in Prompt 1.
   - Add "UCI_CODE" properties (e.g., 'SKY', 'IGD') to the entities.
3. Run the seed script and print a summary: "Team Entity [Name] sponsored by [Sponsor] from [Start] to [End]".

Constraints:
- Use Enums for property types and sponsor ranks.
- Ensure date logic allows for NULL end_dates (current active status).
---

Phase 2: Data Ingestion (The Scraper)
---
Prompt 3: Scraper ArchitectureContext: We need to ingest data. We will create a scraper pattern.

Task:
1. Create a directory `scraper/`.
2. Create an abstract base class `BaseScraper` with methods `fetch_team(url: str)` and `parse_team(html: str)`.
3. Create a `MockScraper` implementation that inherits from `BaseScraper`. Instead of making HTTP requests, it should return hardcoded HTML strings or JSON dictionaries representing "Jumbo-Visma" history.
4. Create a service `ingestion_service.py` that takes a scraper instance, runs it, and saves the resulting data into the SQL database using the models from Phase 1.
5. Write a test script `run_ingest.py` that runs the MockScraper and asserts that "Jumbo-Visma" is now in the SQLite database.

Constraints:
- Do not actually hit external websites yet.
- Focus on the transformation logic: Scraper Data -> DB Models.
---

Phase 3: The API Layer
---
Prompt 4: REST API EndpointsContext: We have a database and a way to seed it. Now we need to serve this data to a frontend.

Task:
1. In FastAPI, create the following endpoints:
   - `GET /lineages`: Returns a list of all lineages.
   - `GET /lineages/{id}`: Returns full details of a lineage, including nested `entities`, their `properties`, and `sponsors`.
2. Use Pydantic schemas to format the output nicely (nested JSON structure).
3. Ensure the JSON response includes a "calculated_name" for the entity based on its active 'NAME' property for that period.
4. Write a test file `test_api.py` using `TestClient` to verify the `GET /lineages/{id}` endpoint returns the "Team Sky" data we seeded earlier.

Constraints:
- The JSON structure must be clean and ready for a frontend to consume without heavy processing.
---

Phase 4: Frontend Setup
---
Prompt 5: React + D3 ScaffoldContext: Switching to Frontend. We need to visualize this data.

Task:
1. Create a basic React structure (single file `App.jsx` is fine for this iteration or component based if preferred, but keep it simple).
2. Install `d3` and `axios`.
3. Create a `TimelineContainer` component.
4. In `useEffect`, fetch the data from the local FastAPI backend (`http://localhost:8000/lineages`).
5. For now, just render a simple HTML list (<ul>) of the teams and their start/end dates to verify connectivity.
6. Add a "Loading" state and an "Error" state.

Constraints:
- Ensure CORS is handled in the FastAPI backend (add CORSMiddleware).
---

Phase 5: The Visualization (The Core Challenge)
---
Prompt 6: Basic D3 Timeline RenderingContext: We have data in React. Now we need to draw the timeline.

Task:
1. Create a `SankeyChart` component using D3.js.
2. Define dimensions (width, height, margins).
3. Create a time scale (X-axis) using `d3.scaleTime` spanning from 2010 to 2025.
4. Create a band scale or ordinal scale (Y-axis) for the Lineages.
5. Draw rectangles (`rect`) for each `Team_Entity`.
   - X position: based on start_date.
   - Width: based on (end_date - start_date).
   - Y position: assigned by the Lineage ID.
6. Add a simple axis at the bottom showing years.

Constraints:
- Use a hardcoded width/height for now.
- If end_date is null, assume "today".
- Color the rectangles gray for now.
---

Prompt 7: Lineage Connections & ColorsContext: The rectangles are drawn. Now we need to connect them to show continuity and add sponsor colors.

Task:
1. Update `SankeyChart` to draw SVG `lines` or `paths` connecting the end of one entity to the start of the next entity within the same lineage.
2. Update the API (if needed) or frontend logic to assign a color to each entity based on its primary sponsor.
3. Apply these colors to the rectangles.
4. Add a simple tooltip (using standard HTML `title` attribute or a simple D3 text overlay) that shows the Team Name when hovering over a rectangle.

Constraints:
- Visual continuity is key. The line should connect the vertical center of the predecessor to the vertical center of the successor.
---

Phase 6: Polish & Interaction
---
Prompt 8: Zoom & PanContext: The timeline is too wide to fit on one screen. We need zoom capabilities.

Task:
1. Implement D3 Zoom behavior on the SVG container.
2. Allow the user to pan horizontally (scroll through time) and zoom in/out (expand/contract the time scale).
3. When zooming, the X-axis (years) should update dynamically.
4. Ensure the rectangles and connection lines rescale correctly.

Constraints:
- Restrict zoom to X-axis only (we don't want to stretch the rows vertically).
---

Prompt 9: Sidebar DetailsContext: Clicking a team should show details.

Task:
1. Add an `onClick` handler to the team rectangles in the D3 chart.
2. Create a `Sidebar` component in React (floating right panel).
3. When a team is clicked, pass the entity data to the `Sidebar` state.
4. The Sidebar should display:
   - Full Team Name.
   - Active Sponsors for that period.
   - Start/End Dates.
   - A list of all historical names for that lineage.

Constraints:
- If no team is selected, the sidebar is hidden.
---

Prompt 10: Integration & CleanupContext: Final assembly.

Task:
1. Ensure the FastAPI backend is running.
2. Ensure the React frontend is connected.
3. Add a "Reset View" button to the frontend that resets the D3 zoom transform.
4. Polish the CSS (Tailwind is assumed available) to make the sidebar and chart look professional.
5. Add error handling: If the API is down, show a friendly message in the main view.

Constraints:
- No orphaned code. Ensure the database seed script, API, and frontend work as a cohesive unit.
