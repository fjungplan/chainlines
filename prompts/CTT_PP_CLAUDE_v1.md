# **Cycling Team Lineage \- Master Implementation Blueprint**

Status: Ready for Execution  
Philosophy: Incremental, Test-Driven, "No Orphaned Code."  
Goal: Provide granular prompts for an AI Coding Assistant to build the project from scratch without ambiguity.

## **Phase 0: Infrastructure & Skeleton**

**Objective:** Establish the containerized environment, database, and test runner before writing domain code.

### **Prompt 0.1: Project Root & Docker**

I am starting a new project: "Cycling Team Lineage".  
Stack: Python 3.11 (FastAPI), PostgreSQL 15, React (Vite), Docker Compose.

Task: Initialize the project structure and Docker infrastructure.

1\. Create the following file structure:  
   \- \`root/\`  
     \- \`backend/\`  
     \- \`frontend/\` (keep empty for now)  
     \- \`docker-compose.yml\`  
     \- \`.gitignore\` (standard python/node/docker exclusions)

2\. Create \`backend/Dockerfile\`:  
   \- Use \`python:3.11-slim\`.  
   \- Set workdir \`/app\`.  
   \- Install system dependencies for building python drivers (\`gcc\`, \`libpq-dev\`).  
   \- Copy \`requirements.txt\` and install.  
   \- Copy \`.\` to \`/app\`.

3\. Create \`backend/requirements.txt\`:  
   \- \`fastapi==0.109.2\`  
   \- \`uvicorn\[standard\]==0.27.1\`  
   \- \`sqlalchemy==2.0.27\`  
   \- \`alembic==1.13.1\`  
   \- \`asyncpg==0.29.0\`  
   \- \`psycopg2-binary==2.9.9\` (for sync operations if needed)  
   \- \`pydantic-settings==2.1.0\`  
   \- \`pytest==8.0.0\`  
   \- \`pytest-asyncio==0.23.5\`  
   \- \`httpx==0.26.0\`

4\. Create \`docker-compose.yml\`:  
   \- Service \`db\`:  
     \- Image: \`postgres:15-alpine\`  
     \- Environment: \`POSTGRES\_USER=postgres\`, \`POSTGRES\_PASSWORD=postgres\`, \`POSTGRES\_DB=cycling\`  
     \- Ports: \`5432:5432\`  
     \- Volumes: \`postgres\_data:/var/lib/postgresql/data\`  
     \- Healthcheck: \`pg\_isready \-U postgres\`  
   \- Service \`backend\`:  
     \- Build: \`./backend\`  
     \- Command: \`uvicorn app.main:app \--reload \--host 0.0.0.0\`  
     \- Volumes: \`./backend:/app\`  
     \- Ports: \`8000:8000\`  
     \- Depends on: \`db\` (condition: service\_healthy)  
     \- Environment: \`DATABASE\_URL=postgresql+asyncpg://postgres:postgres@db:5432/cycling\`

5\. Create \`backend/app/main.py\`:  
   \- Minimal FastAPI app.  
   \- Root endpoint \`GET /\` returning \`{"status": "ok"}\`.

Output: The content of all files and instructions to run \`docker compose up \--build\`.

### **Prompt 0.2: Database Config & Connectivity**

Context: Docker is running. Backend needs to talk to DB.

Task: Configure Async SQLAlchemy.

1\. Create \`backend/app/core/config.py\`:  
   \- Use \`pydantic-settings\`.  
   \- Class \`Settings\`: defines \`DATABASE\_URL\`.  
   \- Instantiate \`settings\`.

2\. Create \`backend/app/db/session.py\`:  
   \- Create \`AsyncEngine\` using \`create\_async\_engine(settings.DATABASE\_URL)\`.  
   \- Create \`AsyncSession\` factory \`async\_sessionmaker\`.  
   \- Create dependency \`get\_db() \-\> AsyncGenerator\[AsyncSession, None\]\`.

3\. Update \`backend/app/main.py\`:  
   \- Add endpoint \`GET /health/db\`.  
   \- Inject \`db: AsyncSession \= Depends(get\_db)\`.  
   \- Execute \`SELECT 1\`.  
   \- Return \`{"db\_status": "connected"}\`.

Verification: Provide a curl command to test the health endpoint while Docker is running.

### **Prompt 0.3: Migration System (Alembic)**

Context: DB Connected.  
Task: Setup Migrations.

1\. Initialize Alembic:  
   \- Run \`alembic init \-t async alembic\` inside \`backend/\`.  
   \- (Provide instructions for me to run this, or generate the files if you can).

2\. Modify \`backend/alembic.ini\`:  
   \- Set \`sqlalchemy.url\` to the driver string (or leave placeholder if handled in env.py).

3\. Modify \`backend/alembic/env.py\`:  
   \- Import \`app.core.config.settings\`.  
   \- Set \`config.set\_main\_option("sqlalchemy.url", settings.DATABASE\_URL)\`.  
   \- Define \`target\_metadata\`. Import it from a new file \`backend/app/db/base.py\`.

4\. Create \`backend/app/db/base.py\`:  
   \- Define \`Base \= declarative\_base()\`.

5\. Create \`backend/scripts/migrate.sh\`:  
   \- Helper script to run \`alembic revision \--autogenerate\` and \`alembic upgrade head\`.

Verification: Instructions to generate an initial "empty" revision to prove Alembic connects.

### **Prompt 0.4: Test Infrastructure Setup**

Context: Infrastructure ready.  
Task: Configure Pytest for Async.

1\. Create \`backend/pytest.ini\`:  
   \- Add \`asyncio\_mode \= auto\`.  
   \- Set pythonpath to \`.\`.

2\. Create \`backend/tests/conftest.py\`:  
   \- Define fixture \`async\_client\`: yields \`httpx.AsyncClient\` connected to the FastAPI app.  
   \- Define fixture \`db\_session\`: yields a session that rolls back after each test (to keep DB clean).

3\. Create \`backend/tests/test\_health.py\`:  
   \- Test \`GET /\` returns 200\.  
   \- Test \`GET /health/db\` returns 200\.

Verification: Run \`docker compose exec backend pytest\` and confirm pass.

## **Phase 1: Core Domain (Managerial Node)**

**Objective:** Implement the core entity TeamNode with TDD.

### **Prompt 1.1: TeamNode Model & Migration**

Context: Alembic and Base ready.  
Task: Create TeamNode entity.

1\. Create \`backend/app/models/team.py\`:  
   \- Class \`TeamNode(Base)\`.  
   \- \`id\`: UUID (primary\_key, default=uuid4).  
   \- \`founding\_year\`: int (nullable).  
   \- \`dissolution\_year\`: int (nullable).  
   \- \`created\_at\`: datetime (default=now).  
   \- \`updated\_at\`: datetime (onupdate=now).

2\. Update \`backend/app/db/base.py\`:  
   \- Import \`TeamNode\` so Alembic sees it.

3\. Generate Migration:  
   \- Provide command to create revision \`create\_team\_node\`.  
   \- Provide instructions to apply it.

### **Prompt 1.2: TeamNode Schemas & CRUD**

Context: Table exists.  
Task: Implement Pydantic Schemas and CRUD Service.

1\. Create \`backend/app/schemas/team.py\`:  
   \- \`TeamNodeBase\`: founding\_year, dissolution\_year.  
   \- \`TeamNodeCreate\`: inherits Base.  
   \- \`TeamNodeRead\`: inherits Base, adds \`id\`, \`created\_at\`. Config \`from\_attributes=True\`.

2\. Create \`backend/app/services/team\_service.py\`:  
   \- \`create\_node(db, data: TeamNodeCreate) \-\> TeamNode\`.  
   \- \`get\_node(db, node\_id) \-\> TeamNode\`.

3\. Create \`backend/tests/test\_team\_service.py\`:  
   \- Test \`create\_node\`: asserts ID is generated and data matches.  
   \- Test \`get\_node\`: asserts data retrieval.

Verification: Run pytest.

### **Prompt 1.3: TeamNode API**

Context: Service layer ready.  
Task: Expose API.

1\. Create \`backend/app/api/endpoints/teams.py\`:  
   \- \`POST /teams/\`: calls service, returns \`TeamNodeRead\`.  
   \- \`GET /teams/{id}\`: calls service, returns \`TeamNodeRead\`.

2\. Register Router in \`backend/app/main.py\`.

3\. Create \`backend/tests/api/test\_teams.py\`:  
   \- Test POST /teams/ (201 Created).  
   \- Test GET /teams/{id} (200 OK).  
   \- Test GET /teams/{non\_existent} (404 Not Found).

Verification: Run pytest.

## **Phase 2: Team Eras (Snapshots)**

**Objective:** Implement TeamEra (Yearly snapshot) with validation.

### **Prompt 2.1: TeamEra Model**

Context: TeamNode exists.  
Task: Create TeamEra model (1-to-many from Node).

1\. Update \`backend/app/models/team.py\`:  
   \- Class \`TeamEra(Base)\`.  
   \- \`id\`: UUID.  
   \- \`node\_id\`: UUID (FK team\_node.id).  
   \- \`season\_year\`: int.  
   \- \`registered\_name\`: str.  
   \- \`uci\_code\`: str(3).  
   \- \`tier\_level\`: int.  
   \- Constraints: \`UniqueConstraint(node\_id, season\_year)\`.  
   \- Relationship: \`node \= relationship("TeamNode", back\_populates="eras")\`.

2\. Update \`TeamNode\`:  
   \- \`eras \= relationship("TeamEra", back\_populates="node")\`.

3\. Migration:  
   \- Generate \`create\_team\_era\`.  
   \- Apply.

### **Prompt 2.2: Schemas & Validation**

Context: Model ready.  
Task: Pydantic Validation.

1\. Update \`backend/app/schemas/team.py\`:  
   \- \`TeamEraCreate\`: season\_year, registered\_name, uci\_code, tier\_level.  
   \- \`TeamEraRead\`: adds id, node\_id.  
   \- \`TeamNodeRead\`: add field \`eras: List\[TeamEraRead\]\`.  
   \- Validator: Ensure \`season\_year\` is between 1900 and 2100\.

2\. Update \`backend/app/services/team\_service.py\`:  
   \- \`add\_era(db, node\_id, data: TeamEraCreate) \-\> TeamEra\`.  
   \- Catch \`IntegrityError\` (duplicate year) and raise FastAPI \`HTTPException(400)\`.

3\. Test \`backend/tests/test\_team\_era.py\`:  
   \- Test adding an era.  
   \- Test adding duplicate year to same node (expect failure).

### **Prompt 2.3: Era API Endpoints**

Context: Service ready.  
Task: API endpoints.

1\. Update \`backend/app/api/endpoints/teams.py\`:  
   \- \`POST /teams/{id}/eras\`: Add era to node.  
   \- \`GET /teams/{id}\`: Ensure response now includes \`eras\` list.

2\. Test \`backend/tests/api/test\_eras.py\`:  
   \- Create node via API.  
   \- Add era 2010\.  
   \- Add era 2011\.  
   \- Fetch node and verify 2 eras present.

## **Phase 3: The Sponsor Engine (Complex Data)**

**Objective:** Implement Many-to-Many Sponsor Hierarchy with attributes.

### **Prompt 3.1: Sponsor Models**

Context: Team Core done.  
Task: Sponsor Master and Brand tables.

1\. Create \`backend/app/models/sponsor.py\`:  
   \- \`SponsorMaster\`: id, legal\_name, industry.  
   \- \`SponsorBrand\`: id, master\_id, brand\_name, default\_hex\_color.

2\. Update \`backend/app/db/base.py\` imports.  
3\. Migration: Generate and apply.

### **Prompt 3.2: Link Model (Jersey Slice)**

Context: Sponsor models exist.  
Task: Link Era to Sponsor.

1\. Update \`backend/app/models/sponsor.py\`:  
   \- \`TeamSponsorLink\`: id, era\_id (FK), brand\_id (FK), prominence\_percent (int), rank\_order (int).

2\. Update \`backend/app/models/team.py\`:  
   \- Add relationship \`sponsors\` to \`TeamEra\`.

3\. Migration: Generate and apply.

### **Prompt 3.3: Sponsor Service & Validation**

Context: DB ready.  
Task: Logic for "Jersey Slices".

1\. Create \`backend/app/schemas/sponsor.py\`:  
   \- \`SponsorLinkCreate\`: brand\_id, percent, order.  
   \- \`SponsorLinkRead\`: flattened (brand\_name, color, percent).

2\. Create \`backend/app/services/sponsor\_service.py\`:  
   \- \`create\_master(...)\`.  
   \- \`create\_brand(...)\`.  
   \- \`set\_era\_sponsors(db, era\_id, links: List\[SponsorLinkCreate\])\`.  
     \- \*\*Logic:\*\* Validate that \`sum(link.percent for link in links) \<= 100\`. Raise error if \> 100\.  
     \- Clear existing links for era, insert new ones.

3\. Test \`backend/tests/test\_sponsor\_logic.py\`:  
   \- Test: Create sponsors.  
   \- Test: Assign 60% \+ 40% (Pass).  
   \- Test: Assign 60% \+ 50% (Fail).

## **Phase 4: Scraper Infrastructure (Async)**

**Objective:** Round-robin scheduler logic (no parsing yet).

### **Prompt 4.1: Scheduler Class**

Context: Building "Gentle Scraper".  
Task: Domain Queue Logic.

1\. Create \`backend/app/scraper/scheduler.py\`:  
   \- Class \`GentleScheduler\`.  
   \- Attributes: \`queues: Dict\[domain, Deque\]\`, \`last\_access: Dict\[domain, float\]\`.  
   \- Method \`add\_task(url)\`.  
   \- Method \`get\_next\_task(cooldown=2.0) \-\> str | None\`.  
     \- Logic: Iterate domains. If \`now \- last\_access \> cooldown\`, pop task and return. Else skip.

2\. Test \`backend/tests/scraper/test\_scheduler.py\`:  
   \- Add tasks for 'siteA' and 'siteB'.  
   \- \`get\_next\_task\` \-\> 'siteA'.  
   \- Immediate \`get\_next\_task\` \-\> 'siteB' (because A is on cooldown).  
   \- Verify non-blocking behavior.

### **Prompt 4.2: Scraper DB Locking**

Context: Scraper needs to respect manual edits.  
Task: Add locking fields.

1\. Update \`TeamEra\` model:  
   \- \`is\_manual\_override\`: bool (default False).  
   \- \`source\_origin\`: str (nullable).

2\. Migration: Generate and apply.

### **Prompt 4.3: Seeder Service**

Context: DB ready.  
Task: Safe Upsert Logic.

1\. Create \`backend/app/scraper/seeder.py\`:  
   \- \`seed\_era(db, node\_id, data, source)\`.  
   \- Logic:  
     \- Check if era exists.  
     \- If yes and \`is\_manual\_override\` is True \-\> Log skip.  
     \- If yes and False \-\> Update.  
     \- If no \-\> Create.

2\. Test \`backend/tests/scraper/test\_seeder.py\`:  
   \- Manually create era, set override=True.  
   \- Call seed\_era with DIFFERENT name.  
   \- Assert name unchanged.

## **Phase 5: Auth & Security**

**Objective:** RBAC (Role Based Access Control).

### **Prompt 5.1: User Model**

Context: Securing API.  
Task: User entity.

1\. Create \`backend/app/models/user.py\`:  
   \- \`User\`: id, email, role (enum: GUEST, NEW, TRUSTED, ADMIN), edit\_count.

2\. Migration: Generate and apply.

### **Prompt 5.2: Auth Dependency**

Context: Models ready.  
Task: Stub Authentication.

1\. Create \`backend/app/api/deps.py\`:  
   \- \`get\_current\_user\`: checks \`X-User-Email\` header. Upserts user in DB as NEW if missing.  
   \- \`require\_role(role\_list)\`: dependency checking \`user.role\`.

2\. Update \`backend/app/api/endpoints/teams.py\`:  
   \- Protect write endpoints with \`require\_role(\["TRUSTED", "ADMIN"\])\`.

3\. Test \`backend/tests/api/test\_auth.py\`:  
   \- Test write access with NEW user (403).  
   \- Test write access with TRUSTED user (200).

## **Phase 6: Structural Events (Graph)**

**Objective:** Backend logic for merges/splits.

### **Prompt 6.1: Lineage Model**

Context: Graph Logic.  
Task: Lineage Event Table.

1\. Create \`backend/app/models/lineage.py\`:  
   \- \`LineageEvent\`: id, prev\_node\_id, next\_node\_id, event\_type (MERGE, SPLIT), year.

2\. Migration: Generate and apply.

### **Prompt 6.2: Merge Transaction**

Context: DB ready.  
Task: Atomic Merge.

1\. Create \`backend/app/services/lineage\_service.py\`:  
   \- \`execute\_merge(db, node\_ids\_to\_merge, new\_team\_data, year)\`.  
   \- Logic (Transaction):  
     1\. Set \`dissolution\_year\` on old nodes.  
     2\. Create \`new\_node\`.  
     3\. Create \`LineageEvent\` rows linking old-\>new.

2\. Test \`backend/tests/test\_lineage.py\`:  
   \- Setup Node A, Node B.  
   \- Run merge.  
   \- Assert A and B dissolved.  
   \- Assert C exists.  
   \- Assert LineageEvents exist.

## **Phase 7: Frontend Foundation**

**Objective:** React Setup and Mobile List.

### **Prompt 7.1: Vite Setup**

Context: Moving to Frontend.  
Task: Initialize React.

1\. Create \`frontend/\` directory.  
2\. Initialize Vite: \`npm create vite@latest . \-- \--template react-ts\`.  
3\. Install: \`axios\`, \`react-router-dom\`, \`@tanstack/react-query\`, \`tailwindcss\`, \`postcss\`, \`autoprefixer\`.  
4\. Init Tailwind: \`npx tailwindcss init \-p\`.  
5\. Update \`frontend/vite.config.ts\`: Proxy \`/api\` to \`http://backend:8000\`.  
6\. Update \`docker-compose.yml\`: Add frontend service (node:18, command dev).

Output: Dockerfile and Configs.

### **Prompt 7.2: API Client**

Context: React running.  
Task: Typed Axios Client.

1\. Create \`frontend/src/types/schema.ts\` (Match Pydantic models).  
2\. Create \`frontend/src/api/client.ts\`:  
   \- \`axios.create({ baseURL: '/api' })\`.  
   \- \`getTeams()\`, \`getTeam(id)\`.

### **Prompt 7.3: Mobile List**

Context: API Client ready.  
Task: Companion View.

1\. Create \`frontend/src/components/TeamList.tsx\`:  
   \- Fetch teams via React Query.  
   \- Render list: \`Year | Name | Tier\`.  
   \- Search input filter.  
2\. Update \`App.tsx\` to render it.

Verification: Check browser localhost:5173.

## **Phase 8: Desktop Visualization**

**Objective:** D3.js River Chart.

### **Prompt 8.1: Viz API**

Context: Backend.  
Task: Visualization Endpoint.

1\. Create \`backend/app/api/endpoints/viz.py\`:  
   \- \`GET /viz/river\`: returns JSON graph \`{nodes: \[\], links: \[\]}\`.  
   \- Logic: Convert Eras to nodes (calculating jersey colors), LineageEvents to links.

2\. Test: Verify JSON structure.

### **Prompt 8.2: React D3**

Context: Frontend.  
Task: Basic D3 Canvas.

1\. Install \`d3\`, \`@types/d3\`.  
2\. Create \`frontend/src/components/RiverChart.tsx\`.  
3\. Setup \`useRef\` SVG.  
4\. Fetch data.  
5\. Render \`\<rect\>\` for nodes using computed coordinates (mock coordinates first).

### **Prompt 8.3: The Slice Rendering**

Context: D3 setup.  
Task: Render Jersey Slices.

1\. Update \`RiverChart.tsx\`.  
2\. Map \`node.sponsors\`.  
3\. For each node, draw stacked \`\<rect\>\` inside a \`\<g\>\` based on percentage height.  
4\. Apply hex colors from API.

## **Phase 9: Wizard & Polish**

**Objective:** Editing UI and Deployment.

### **Prompt 9.1: Edit Modal**

Context: Frontend.  
Task: Metadata Editor.

1\. Create \`frontend/src/components/Wizard/EditEraModal.tsx\`.  
2\. Form: Name, UCI Code.  
3\. Submit via mutation \`PUT /teams/eras/{id}\`.  
4\. Add Edit button to \`TeamList\` items.

### **Prompt 9.2: Production Docker**

Context: Features complete.  
Task: Prod Config.

1\. Create \`frontend/nginx.conf\`.  
2\. Create \`frontend/Dockerfile.prod\` (Multi-stage build).  
3\. Update \`docker-compose.prod.yml\`:  
   \- Backend: run migration script on boot.  
   \- Frontend: serve via Nginx.  
