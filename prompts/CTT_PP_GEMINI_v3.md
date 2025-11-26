# **Cycling Team Lineage \- Implementation Blueprint & Prompts**

Status: Ready for Execution  
Purpose: A rigorous, step-by-step guide to building the application using an AI Coding Assistant.

## **Strategy Overview**

This blueprint builds the application in layers, moving from the Data Layer (Bottom) to the Interface Layer (Top).

1. **Phase 0: The Dockerized Foundation.** Infrastructure, DB connection, and migrations.  
2. **Phase 1: The Core Data Layer.** "Managerial Node" and "Team Era" CRUD.  
3. **Phase 2: The Sponsor Engine.** "Corporate Hierarchy" and "Jersey Slice" logic.  
4. **Phase 3: The Gentle Scraper (Infra).** Low-velocity, round-robin scheduler.  
5. **Phase 4: Scraper Logic (Seeding).** Parsing and safe upserts with locking.  
6. **Phase 5: Auth & Access.** User roles and API security.  
7. **Phase 6: Structural Events.** Backend logic for Merges and Splits.  
8. **Phase 7: Frontend Foundation.** React shell and Mobile List View.  
9. **Phase 8: Desktop Visualization.** D3.js "River" and Sankey layout.  
10. **Phase 9: The Wizard & Polish.** Frontend forms for events and deployment prep.

## **Phase 0: The Dockerized Foundation (Infrastructure)**

**Goal:** Get a running container environment with a healthy database connection.

### **Prompt 0.1: Project Skeleton & Docker**

Create a new project structure for the Cycling Team Lineage Timeline application with the following requirements:

PROJECT STRUCTURE:  
\- Root directory with docker-compose.yml  
\- backend/ directory (Python FastAPI)  
\- frontend/ directory (React with Vite) \- empty for now  
\- .env.example file

DOCKER COMPOSE REQUIREMENTS:  
\- PostgreSQL 15 service:  
  \- Container name: cycling\_db  
  \- Environment variables: POSTGRES\_USER, POSTGRES\_PASSWORD, POSTGRES\_DB  
  \- Volume: cycling\_postgres\_data:/var/lib/postgresql/data  
  \- Port 5432 exposed to host  
  \- Healthcheck: pg\_isready \-U user \-d db  
\- Backend service:  
  \- Build context: ./backend  
  \- Command: uvicorn app.main:app \--reload \--host 0.0.0.0 \--port 8000  
  \- Volume: ./backend:/app  
  \- Ports: 8000:8000  
  \- Depends on: db (condition: service\_healthy)  
  \- Env file: .env

BACKEND SETUP (backend/):  
\- Dockerfile: Python 3.11-slim  
\- requirements.txt containing:  
  \- fastapi\>=0.109.0  
  \- uvicorn\[standard\]\>=0.27.0  
  \- sqlalchemy\>=2.0.25  
  \- asyncpg\>=0.29.0  
  \- alembic\>=1.13.1  
  \- pydantic-settings\>=2.1.0  
  \- psycopg2-binary\>=2.9.9 (for sync operations if needed)  
\- app/main.py: Basic FastAPI app with root endpoint returning {"status": "ok"}

OUTPUT:  
\- File tree  
\- Content of docker-compose.yml, backend/Dockerfile, backend/requirements.txt, backend/app/main.py  
\- Instructions to run \`docker compose up \--build\`

### **Prompt 0.2: Database Configuration**

Context: Docker containers are running.  
Task: Configure the Async Database connection using SQLAlchemy 2.0.

FILES TO CREATE/MODIFY:  
1\. \`backend/app/core/config.py\`:  
   \- Use \`pydantic-settings\` BaseSettings  
   \- Fields: POSTGRES\_USER, POSTGRES\_PASSWORD, POSTGRES\_SERVER, POSTGRES\_DB, DATABASE\_URL (computed property)

2\. \`backend/app/db/session.py\`:  
   \- Create \`AsyncEngine\` using \`create\_async\_engine(settings.DATABASE\_URL)\`  
   \- Create \`AsyncSession\` factory using \`async\_sessionmaker\`  
   \- Create \`get\_db\` dependency generator that yields the session

3\. \`backend/app/main.py\`:  
   \- Add a \`/health\` endpoint that accepts \`db: AsyncSession \= Depends(get\_db)\`  
   \- Execute \`await db.execute(text("SELECT 1"))\` to verify connection  
   \- Return {"database": "online"}

TESTING:  
\- Provide a curl command to test the health endpoint.

### **Prompt 0.3: Migrations Setup**

Context: DB connection is established.  
Task: Configure Alembic for async migrations.

STEPS:  
1\. Run \`alembic init \-t async alembic\` inside the backend directory (provide instructions).  
2\. Modify \`backend/alembic.ini\`:  
   \- Set \`sqlalchemy.url\` to use the environment variable or driver string.  
3\. Modify \`backend/alembic/env.py\`:  
   \- Import \`app.core.config.settings\` to set the sqlalchemy.url dynamically.  
   \- Import \`app.db.base\` (create if missing) to set \`target\_metadata\`.  
   \- Ensure the async engine setup uses the correct configuration.  
4\. Create \`backend/app/db/base.py\`:  
   \- Create a \`Base\` class using \`DeclarativeBase\` from SQLAlchemy.  
5\. Provide a makefile or shell script \`run\_migrations.sh\` to run \`alembic revision \--autogenerate\` and \`alembic upgrade head\`.

SUCCESS CRITERIA:  
\- Alembic can connect to the DB container.  
\- An initial (empty) revision can be generated.

## **Phase 1: The Core Data Layer (Managerial Node)**

**Goal:** Implement the "Managerial Node" and "Team Era" logic with CRUD.

### **Prompt 1.1: The TeamNode Model**

Context: Alembic is ready.  
Task: Implement the persistent "Managerial Node" entity.

FILES TO CREATE/MODIFY:  
1\. \`backend/app/models/team.py\`:  
   \- Class \`TeamNode\` inheriting from \`Base\`.  
   \- \`id\`: UUID (primary\_key=True, default=uuid.uuid4)  
   \- \`founding\_year\`: Integer (nullable=True)  
   \- \`dissolution\_year\`: Integer (nullable=True)  
   \- \`created\_at\`: DateTime (server\_default=func.now())  
   \- \`updated\_at\`: DateTime (onupdate=func.now())

2\. \`backend/app/db/base.py\`:  
   \- Import \`TeamNode\` to ensure it is registered in metadata.

3\. \`backend/alembic/env.py\`:  
   \- Ensure target\_metadata imports the updated Base.

ACTION:  
\- Generate migration \`create\_team\_node\_table\`.  
\- Apply migration.  
\- Provide the migration script content for verification.

### **Prompt 1.2: The TeamEra Model**

Context: TeamNode exists.  
Task: Implement the "Team Era" (Yearly Snapshot).

FILES TO CREATE/MODIFY:  
1\. \`backend/app/models/team.py\`:  
   \- Class \`TeamEra\` inheriting from \`Base\`.  
   \- \`id\`: UUID (primary\_key=True, default=uuid.uuid4)  
   \- \`node\_id\`: UUID (ForeignKey("team\_node.id"), nullable=False)  
   \- \`season\_year\`: Integer (nullable=False)  
   \- \`registered\_name\`: String (nullable=False)  
   \- \`uci\_code\`: String (nullable=True, length=3)  
   \- \`tier\_level\`: Integer (nullable=False) \-- 1=WT, 2=Pro, 3=Conti  
   \- Relationship: \`node\` \-\> \`TeamNode\` (back\_populates="eras")  
   \- Constraints: \`UniqueConstraint("node\_id", "season\_year", name="uq\_node\_year")\`

2\. \`backend/app/models/team.py\` (Update TeamNode):  
   \- Add relationship: \`eras\` \-\> \`TeamEra\` (back\_populates="node", cascade="all, delete-orphan")

ACTION:  
\- Generate migration \`create\_team\_era\_table\`.  
\- Apply migration.

### **Prompt 1.3: Pydantic Schemas**

Context: Models exist.  
Task: Create Data Transfer Objects (DTOs) for API validation.

FILES TO CREATE:  
1\. \`backend/app/schemas/team.py\`:  
   \- \`TeamEraBase\`: (season\_year, registered\_name, uci\_code, tier\_level)  
   \- \`TeamEraCreate\`: Inherits Base.  
   \- \`TeamEraRead\`: Inherits Base, adds \`id\`, \`node\_id\`. Config: \`from\_attributes \= True\`.

   \- \`TeamNodeBase\`: (founding\_year, dissolution\_year)  
   \- \`TeamNodeCreate\`: Inherits Base.  
   \- \`TeamNodeRead\`: Inherits Base, adds \`id\`, \`eras: List\[TeamEraRead\]\`. Config: \`from\_attributes \= True\`.

### **Prompt 1.4: CRUD Service & Tests**

Context: Models and Schemas exist.  
Task: Implement Business Logic and Integration Tests.

FILES TO CREATE:  
1\. \`backend/app/services/team\_service.py\`:  
   \- \`create\_node(db: AsyncSession, data: TeamNodeCreate) \-\> TeamNode\`  
   \- \`add\_era\_to\_node(db: AsyncSession, node\_id: UUID, data: TeamEraCreate) \-\> TeamEra\`  
   \- \`get\_node(db: AsyncSession, node\_id: UUID) \-\> TeamNode\` (with selectinload for eras)

2\. \`backend/tests/conftest.py\`:  
   \- Setup \`async\_client\` fixture using \`httpx.AsyncClient\` and \`ASGITransport\`.  
   \- Setup \`db\_session\` fixture that creates a new session per test and rolls back.

3\. \`backend/tests/test\_team\_service.py\`:  
   \- Test 1: \`test\_create\_node\_lifecycle\`: Create a node, add eras for 2010 and 2011, verify fetch includes eras.  
   \- Test 2: \`test\_duplicate\_era\_constraint\`: Try adding 2010 twice, assert IntegrityError.

OUTPUT:  
\- Service code.  
\- Test code.  
\- Command to run \`pytest\`.

## **Phase 2: The Sponsor Engine (The Jersey Slice)**

**Goal:** Implement the complex many-to-many relationship with attributes (Corporate Hierarchy).

### **Prompt 2.1: Sponsor Master & Brand Models**

Context: Team Core is done.  
Task: Implement Sponsor Hierarchy Models.

FILES TO CREATE/MODIFY:  
1\. \`backend/app/models/sponsor.py\`:  
   \- \`SponsorMaster\`:  
     \- \`id\`: UUID (pk)  
     \- \`legal\_name\`: String (unique)  
     \- \`industry\`: String (nullable)  
   \- \`SponsorBrand\`:  
     \- \`id\`: UUID (pk)  
     \- \`master\_id\`: UUID (FK to SponsorMaster)  
     \- \`brand\_name\`: String  
     \- \`default\_hex\_color\`: String (length 7\)  
     \- Relationship: \`master\` \-\> \`SponsorMaster\`

ACTION:  
\- Update \`backend/app/db/base.py\` imports.  
\- Generate and apply migration.

### **Prompt 2.2: The Jersey Slice Link**

Context: Sponsor models exist.  
Task: Link Eras to Sponsors with "Prominence" logic.

FILES TO CREATE/MODIFY:  
1\. \`backend/app/models/sponsor.py\`:  
   \- \`TeamSponsorLink\`:  
     \- \`id\`: UUID (pk)  
     \- \`era\_id\`: UUID (FK team\_era.id)  
     \- \`brand\_id\`: UUID (FK sponsor\_brand.id)  
     \- \`prominence\_percent\`: Integer (CheckConstraint \<= 100\)  
     \- \`rank\_order\`: Integer  
     \- Relationship: \`era\` \-\> \`TeamEra\`, \`brand\` \-\> \`SponsorBrand\`

2\. \`backend/app/models/team.py\`:  
   \- Update \`TeamEra\` to include \`sponsors\` relationship (TeamSponsorLink).

ACTION:  
\- Generate and apply migration.

### **Prompt 2.3: Sponsor Service Logic**

Context: Models ready.  
Task: Logic to assign sponsors and validate percentages.

FILES TO CREATE/MODIFY:  
1\. \`backend/app/schemas/sponsor.py\`:  
   \- \`SponsorLinkCreate\`: (brand\_id, prominence\_percent, rank\_order)  
   \- \`SponsorLinkRead\`: (brand\_name, hex\_color, prominence\_percent) \- requires flattening or nested loading.

2\. \`backend/app/services/sponsor\_service.py\`:  
   \- \`create\_sponsor\_master(...)\`  
   \- \`create\_sponsor\_brand(...)\`  
   \- \`set\_era\_sponsors(db, era\_id, links: List\[SponsorLinkCreate\])\`  
     \- Logic: Query existing links, delete them, insert new ones.  
     \- Logic: \`sum(prominence\_percent)\` must be \<= 100\. Raise ValueError if exceeded.

3\. \`backend/tests/test\_sponsor\_service.py\`:  
   \- Test: Assign 2 sponsors (60% \+ 40%). Assert success.  
   \- Test: Assign 2 sponsors (60% \+ 50%). Assert ValueError.

## **Phase 3: The Gentle Scraper (Infrastructure)**

**Goal:** Build a round-robin scheduler that *waits* between requests.

### **Prompt 3.1: The Scheduler Class**

Context: Switching to Scraper Infrastructure.  
Task: Build the Queue Manager (No Network yet).

FILES TO CREATE:  
1\. \`backend/app/scraper/scheduler.py\`:  
   \- Class \`GentleScheduler\`:  
     \- \`\_\_init\_\_\`: Initialize \`domain\_queues\` (defaultdict of deque) and \`last\_request\_time\` (dict).  
     \- \`add\_task(url: str, parser\_callback: Callable)\`: Parse domain from URL, append to queue.  
     \- \`get\_next\_task(min\_delay: float \= 2.0) \-\> Optional\[Task\]\`:  
       \- Iterate through domains in round-robin.  
       \- Check \`time.time() \- last\_request\_time\[domain\] \> min\_delay\`.  
       \- If ready, pop task, update time, return task.  
       \- If no domain is ready, return None.

TESTING:  
\- Create \`backend/tests/test\_scheduler.py\`:  
  \- Test round-robin ordering (Task A \-\> Task B \-\> Task A).  
  \- Test delay enforcement (Task A1 \-\> Task A2 should fail if called immediately).

### **Prompt 3.2: The Async Worker**

Context: Scheduler logic works.  
Task: Implement the Async Loop.

FILES TO MODIFY:  
1\. \`backend/requirements.txt\`: Add \`httpx\`.  
2\. \`backend/app/scraper/scheduler.py\`:  
   \- Add \`async def run(self)\`:  
     \- Loop \`while True\`.  
     \- \`task \= self.get\_next\_task()\`.  
     \- If task: \`await self.process\_task(task)\` (placeholder).  
     \- If no task: \`await asyncio.sleep(0.1)\` to prevent busy loop.  
   \- Add \`async def process\_task(self, task)\`:  
     \- Use \`httpx.AsyncClient\` to GET the URL.  
     \- Call \`task.callback(response.text)\`.

TESTING:  
\- Mock the \`httpx\` call in \`test\_scheduler.py\` to ensure the loop functions.

## **Phase 4: Scraper Logic (Seeding)**

**Goal:** Connect Scraper \-\> DB without overwriting manual edits.

### **Prompt 4.1: Database Locking**

Context: Core Data Models.  
Task: Add "Anti-Bot" locks to TeamEra.

FILES TO MODIFY:  
1\. \`backend/app/models/team.py\`:  
   \- Add to \`TeamEra\`:  
     \- \`is\_manual\_override\`: Boolean (default=False, nullable=False)  
     \- \`source\_origin\`: String (nullable=True) \-- e.g., "manual", "scraper:pcs"

ACTION:  
\- Generate and apply migration.

### **Prompt 4.2: The Seeder Service**

Context: DB has locks.  
Task: Service to safely upsert scraped data.

FILES TO CREATE:  
1\. \`backend/app/scraper/seeder.py\`:  
   \- \`async def seed\_era(db: AsyncSession, node\_id: UUID, data: TeamEraCreate, source: str)\`:  
     \- Query existing Era by (node\_id, season\_year).  
     \- Case 1: Era missing \-\> Create it. Set source\_origin=source.  
     \- Case 2: Era exists AND is\_manual\_override=True \-\> Log "Skipped locked record". Return existing.  
     \- Case 3: Era exists AND is\_manual\_override=False \-\> Update fields with data. Update source\_origin.

TESTING:  
\- Create \`backend/tests/test\_seeder.py\`:  
  \- Test 1: Seed new era \-\> Created.  
  \- Test 2: Seed existing unlocked era \-\> Updated.  
  \- Test 3: Seed existing locked era \-\> No change.

### **Prompt 4.3: HTML Parser Foundation**

Context: Ready to parse.  
Task: Abstract Base Parser.

FILES TO CREATE:  
1\. \`backend/requirements.txt\`: Add \`beautifulsoup4\`.  
2\. \`backend/app/scraper/parsers/base.py\`:  
   \- Abstract Base Class \`BaseParser\`.  
   \- Abstract method \`parse(html: str) \-\> TeamEraCreate\`.  
   \- Abstract method \`can\_handle(url: str) \-\> bool\`.

### **Prompt 4.4: ProCyclingStats Parser (MVP)**

Context: Base parser exists.  
Task: Parse a real PCS page (Team overview).

FILES TO CREATE:  
1\. \`backend/app/scraper/parsers/pcs.py\`:  
   \- Class \`PCSParser(BaseParser)\`.  
   \- Implementation of \`parse\`:  
     \- Use BeautifulSoup.  
     \- Select \`h1\` for team name.  
     \- Parse URL or page content for Year.  
     \- (Assume simplified HTML structure for now).

TESTING:  
\- Create \`backend/tests/fixtures/pcs\_team.html\` (Copy a snippet of real HTML).  
\- Create \`backend/tests/test\_pcs\_parser.py\`:  
  \- Load fixture.  
  \- Run parser.  
  \- Assert \`registered\_name\` \== "Jumbo-Visma".

## **Phase 5: Auth & Access**

**Goal:** Secure the API.

### **Prompt 5.1: User Model**

Context: Adding Auth.  
Task: User table.

FILES TO CREATE:  
1\. \`backend/app/models/user.py\`:  
   \- Class \`User(Base)\`.  
   \- \`id\`: UUID (pk).  
   \- \`email\`: String (unique, index).  
   \- \`role\`: Enum ("GUEST", "NEW", "TRUSTED", "ADMIN").  
   \- \`edit\_count\`: Integer (default 0).

ACTION:  
\- Update imports.  
\- Generate and apply migration.

### **Prompt 5.2: Auth Dependency (Stubbed)**

Context: Models ready.  
Task: Dependency Injection for Auth.

FILES TO CREATE:  
1\. \`backend/app/api/deps.py\`:  
   \- \`get\_current\_user(request: Request, db: AsyncSession)\`:  
     \- Stub Logic: Check header \`X-Test-Email\`.  
     \- If header exists: \`select user where email=header\`.  
     \- If not found: \`create user(email=header, role=NEW)\`.  
     \- Return User.  
   \- \`require\_role(allowed\_roles: List\[str\])\`:  
     \- Returns a dependency that checks \`current\_user.role\`.  
     \- Raises 403 if insufficient permissions.

### **Prompt 5.3: Endpoint Security**

Context: Deps ready.  
Task: Protect Writes.

FILES TO MODIFY:  
1\. \`backend/app/api/endpoints/teams.py\` (Create if missing):  
   \- \`POST /teams/{node\_id}/eras\`:  
     \- Dependency: \`require\_role(\["TRUSTED", "ADMIN"\])\`.  
     \- Calls \`team\_service.add\_era\_to\_node\`.

TESTING:  
\- \`backend/tests/test\_api\_security.py\`:  
  \- Request with no header \-\> 401\.  
  \- Request with "newbie@test.com" \-\> 403\.  
  \- Request with "trusted@test.com" (Pre-seed this user in DB) \-\> 200\.

## **Phase 6: Structural Events (The Wizard Backend)**

**Goal:** Handle Merges and Splits via transactions.

### **Prompt 6.1: Lineage Event Model**

Context: Managing connections.  
Task: The Lineage Graph table.

FILES TO CREATE:  
1\. \`backend/app/models/lineage.py\`:  
   \- Enum \`EventType\`: MERGE, SPLIT, TRANSFER.  
   \- Class \`LineageEvent(Base)\`:  
     \- \`id\`: UUID (pk).  
     \- \`event\_year\`: Integer.  
     \- \`previous\_node\_id\`: UUID (FK TeamNode).  
     \- \`next\_node\_id\`: UUID (FK TeamNode).  
     \- \`event\_type\`: EventType.  
     \- \`notes\`: Text (nullable).

ACTION:  
\- Generate and apply migration.

### **Prompt 6.2: Structural Logic Service**

Context: Complex Transaction.  
Task: Execute a Merge.

FILES TO CREATE:  
1\. \`backend/app/services/lineage\_service.py\`:  
   \- \`async def execute\_merge(db: AsyncSession, node\_ids: List\[UUID\], new\_team\_data: TeamNodeCreate, year: int)\`:  
     \- Begin Transaction.  
     \- Update all \`node\_ids\`: set \`dissolution\_year \= year\`.  
     \- Create \`new\_node\`.  
     \- For each \`old\_id\` in \`node\_ids\`:  
       \- Create \`LineageEvent(prev=old\_id, next=new\_node.id, type=MERGE, year=year)\`.  
     \- Commit.

TESTING:  
\- \`backend/tests/test\_lineage.py\`:  
  \- Create Node A, Node B.  
  \- Call \`execute\_merge(\[A.id, B.id\], C\_data, 2012)\`.  
  \- Assert A.dissolution\_year \== 2012\.  
  \- Assert C exists.  
  \- Assert 2 LineageEvents exist pointing to C.

## **Phase 7: Frontend Foundation (Mobile List)**

**Goal:** React App talking to FastAPI.

### **Prompt 7.1: React Setup**

Context: Moving to Frontend.  
Task: Init React Project.

COMMANDS/FILES:  
1\. In \`frontend/\`:  
   \- Run \`npm create vite@latest . \-- \--template react-ts\`.  
   \- Install \`npm install axios @tanstack/react-query react-router-dom lucide-react clsx tailwind-merge\`.  
   \- Install Tailwind CSS: \`npm install \-D tailwindcss postcss autoprefixer\`, \`npx tailwindcss init \-p\`.

2\. Configure \`frontend/vite.config.ts\`:  
   \- Add proxy: \`server: { proxy: { '/api': 'http://backend:8000' } }\`.

3\. \`frontend/Dockerfile\`:  
   \- Node 18-alpine.  
   \- \`CMD \["npm", "run", "dev", "--", "--host"\]\`.

OUTPUT:  
\- Dockerfile content.  
\- Updated docker-compose.yml to include frontend service (ports 5173:5173).

### **Prompt 7.2: API Client & Types**

Context: React running.  
Task: Connect to backend.

FILES TO CREATE:  
1\. \`frontend/src/types/index.ts\`:  
   \- Interfaces: \`TeamNode\`, \`TeamEra\`, \`Sponsor\`. Match backend Pydantic schemas.

2\. \`frontend/src/api/client.ts\`:  
   \- Setup Axios instance with baseURL \`/api\`.  
   \- Functions: \`getTeams()\`, \`getTeamDetails(id)\`.

### **Prompt 7.3: Mobile List View**

Context: Client ready.  
Task: The "Companion" View Component.

FILES TO CREATE:  
1\. \`frontend/src/components/TeamList.tsx\`:  
   \- Use \`useQuery\` to fetch teams.  
   \- Return a \`div\` with a list of items.  
   \- Item layout: \`Flex row: Year | Name | Tier Badge\`.  
   \- Add an \`\<input\>\` for client-side text filtering.

2\. \`frontend/src/App.tsx\`:  
   \- Render \`TeamList\`.

## **Phase 8: Desktop Visualization (D3.js)**

**Goal:** The "Jersey Slice" River.

### **Prompt 8.1: Graph JSON Endpoint**

Context: Backend.  
Task: Prepare data for D3.

FILES TO CREATE:  
1\. \`backend/app/schemas/viz.py\`:  
   \- \`VizNode\`: id, year, name, slices: List\[VizSlice(color, percent)\].  
   \- \`VizLink\`: source\_id, target\_id, type.

2\. \`backend/app/api/endpoints/viz.py\`:  
   \- \`GET /viz/river\`:  
     \- Query all Eras. Convert to \`VizNode\` (calculating slices from sponsors).  
     \- Query all LineageEvents. Convert to \`VizLink\`.  
     \- Generate implicit "Continuity" links (Era 2010 \-\> Era 2011 same node).  
     \- Return JSON.

### **Prompt 8.2: React D3 Canvas**

Context: Frontend.  
Task: Setup D3 Canvas.

FILES TO CREATE:  
1\. Install: \`npm install d3 @types/d3\`.  
2\. \`frontend/src/components/RiverChart.tsx\`:  
   \- \`useRef\` for \`\<svg\>\`.  
   \- \`useEffect\`: Fetch data.  
   \- Draw simple circles (\`\<circle\>\`) for nodes and lines (\`\<line\>\`) for links to test coordinates.

### **Prompt 8.3: The Jersey Slice Rendering**

Context: D3 basic setup working.  
Task: Render the Slices.

MODIFICATION:  
1\. \`frontend/src/components/RiverChart.tsx\`:  
   \- Replace \`\<circle\>\` with \`\<g class="node"\>\`.  
   \- Inside group, iterate \`node.slices\`.  
   \- Append \`\<rect\>\`:  
     \- height \= \`totalHeight \* (slice.percent / 100)\`.  
     \- fill \= \`slice.color\`.  
     \- y \= stacked offset.

### **Prompt 8.4: Sankey Layout Algorithm**

Context: Nodes are drawing.  
Task: Positioning (The Topology).

MODIFICATION:  
1\. Implement a basic layout function in JS:  
   \- Group nodes by \`year\`.  
   \- X \= \`year \* columnWidth\`.  
   \- Y \= Simple heuristic (keep node \`i\` at similar Y to node \`i\` in previous year).  
   \- Draw Links: Use \`d3.linkHorizontal\` to draw smooth Bézier curves between rects.

## **Phase 9: The Wizard Frontend & Polish**

**Goal:** Allow users to edit.

### **Prompt 9.1: Edit Metadata Form**

Context: Frontend.  
Task: Edit simple data.

FILES TO CREATE:  
1\. \`frontend/src/components/Wizard/EditEraForm.tsx\`:  
   \- Props: \`era: TeamEra\`.  
   \- Inputs: Registered Name, UCI Code, Tier Level.  
   \- Mutation: \`useMutation\` calling \`PUT /teams/eras/{id}\`.

2\. Integration: Add an "Edit" icon to \`TeamList\` items to open this as a Modal.

### **Prompt 9.2: Structural Event Form**

Context: Frontend.  
Task: The Merge Wizard.

FILES TO CREATE:  
1\. \`frontend/src/components/Wizard/MergeForm.tsx\`:  
   \- State: \`selectedTeamIds\` (Multi-select).  
   \- Inputs: \`newTeamName\`, \`effectiveYear\`.  
   \- Submit: Calls \`POST /lineage/merge\`.

### **Prompt 9.3: Deployment Prep**

Context: App is complete.  
Task: Production Polish.

FILES TO MODIFY:  
1\. \`docker-compose.yml\`:  
   \- Remove volumes (hot reload) for production config example.  
   \- Add \`nginx\` service.

2\. \`nginx/nginx.conf\`:  
   \- Serve \`/\` from frontend build.  
   \- Proxy \`/api\` to backend:8000.

3\. \`backend/entrypoint.sh\`:  
   \- Run \`alembic upgrade head\`.  
   \- Start uvicorn.  
