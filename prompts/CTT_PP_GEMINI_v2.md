# **Cycling Team Lineage \- Implementation Blueprint & Prompts**

Status: Ready for Execution  
Purpose: A step-by-step guide to building the application using an AI Coding Assistant.

## **Strategy Overview**

This blueprint builds the application in layers, moving from the Data Layer (Bottom) to the Interface Layer (Top).

1. **Phase 1: The Core Foundation.** Establish Docker environment, database connection, and "Managerial Node" architecture.  
2. **Phase 2: The Sponsor Engine.** Implement "Corporate Hierarchy" and "Jersey Slice" logic.  
3. **Phase 3: The Gentle Scraper.** Build infrastructure for low-velocity, round-robin scraping.  
4. **Phase 4: Auth & Access.** Secure the API and implement User Role hierarchy.  
5. **Phase 5: Frontend Mobile (The Companion).** Build React shell and List View (mobile fallback).  
6. **Phase 6: Logic & Visualization.** Implement "Wizard" logic for merges/splits and D3.js "River" visualization.

## **Phase 1: The Core Foundation**

### **Prompt 1: Skeleton & Environment**

I am building a "Cycling Team Lineage" application using Python FastAPI, PostgreSQL, and Docker. 

Please set up the initial project skeleton.

Requirements:  
1\. Create a \`docker-compose.yml\` file with:  
   \- A \`web\` service (Python 3.11) running FastAPI.  
   \- A \`db\` service running PostgreSQL 15\.  
2\. Create a basic directory structure:  
   \- \`app/main.py\` (Hello World endpoint).  
   \- \`app/core/config.py\` (Environment variables using Pydantic Settings).  
   \- \`app/db/session.py\` (SQLAlchemy async engine setup).  
3\. configure \`alembic\` for database migrations.  
4\. Include a \`requirements.txt\` with fastapi, uvicorn, sqlalchemy, asyncpg, alembic, and pydantic-settings.  
5\. Provide a test instruction to ensure the app connects to the DB successfully on startup.

Focus on best practices: clean folder structure and async database drivers.

### **Prompt 2: The Managerial Node (Domain Model)**

Now let's implement the core data models based on the "Managerial Continuity" concept.

References:  
\- A "Managerial Node" is a persistent legal entity.  
\- A "Team Era" is a specific season (year) within that node.

Tasks:  
1\. Create SQLAlchemy models in \`app/models/team.py\`:  
   \- \`TeamNode\`: UUID primary key, founding\_year, dissolution\_year.  
   \- \`TeamEra\`: UUID pk, foreign key to Node, season\_year, registered\_name, uci\_code, tier\_level.  
   \- Add a UniqueConstraint on \`TeamEra\` for (node\_id, season\_year).  
2\. Generate an Alembic migration script to create these tables.  
3\. Create Pydantic schemas in \`app/schemas/team.py\` for reading/writing these models.  
4\. Implement a CRUD service in \`app/services/team\_service.py\` to create a Node and add Eras to it.  
5\. Write a \`pytest\` test case that:  
   \- Creates a Node.  
   \- Adds a Team Era (e.g., "Team Sky 2010").  
   \- Tries to add a duplicate Era for 2010 (should fail).

Ensure all DB operations are async.

## **Phase 2: The Sponsor Engine**

### **Prompt 3: Sponsor Hierarchy & Jersey Slices**

We need to implement the high-fidelity Sponsor system to support "Jersey Slice" visualization.

Context:  
\- \`SponsorMaster\`: The parent company (e.g., Soudal Group).  
\- \`SponsorBrand\`: The marketing name (e.g., Lotto-Soudal).  
\- \`TeamSponsorLink\`: Links an Era to a Brand with a "prominence" % (the slice height).

Tasks:  
1\. Create models in \`app/models/sponsor.py\`:  
   \- \`SponsorMaster\`, \`SponsorBrand\`.  
   \- \`TeamSponsorLink\`: FKs to Era and Brand, \`prominence\_percent\` (int), \`rank\_order\` (int).  
2\. Add a database constraint (or application logic) to ensure \`prominence\_percent\` is \<= 100\.  
3\. Update Alembic migrations.  
4\. Update the \`team\_service.py\` to allow adding sponsors to an Era.  
5\. Write a test case:  
   \- Create a Master ("Soudal Group") and Brand ("Soudal").  
   \- Link it to a Team Era with 60% prominence.  
   \- Verify the data structure can be retrieved via the API.

## **Phase 3: The Gentle Scraper**

### **Prompt 4: The Scheduler Infrastructure**

We are implementing the "Gentle Scraper" infrastructure. It needs to run tasks in a round-robin fashion with high latency to avoid IP bans.

Tasks:  
1\. Create a new service \`app/scraper/scheduler.py\`.  
2\. Implement a class \`GentleScheduler\` that:  
   \- Maintains a queue of tasks.  
   \- Implements a \`process\_queue\` method.  
   \- Enforces a configurable delay (default 2 seconds for test, but designed for 15s) between requests to the \*same domain\*.  
3\. Create a mock function \`fetch\_url(url)\` that simply sleeps and returns true.  
4\. Write an async test that:  
   \- Queues 3 URLs for "site-a.com" and 1 URL for "site-b.com".  
   \- Verifies that the scheduler processes "site-a" requests with the required delay, but interleaves "site-b" if possible.  
     
Note: We are not parsing HTML yet, just building the traffic-shaping engine.

### **Prompt 5: The "Seeder" Logic**

Now we connect the Scraper to the Database using the "Seeder" strategy.

Tasks:  
1\. Modify \`TeamEra\` model to add:  
   \- \`is\_manual\_override\` (bool, default False).  
   \- \`source\_origin\` (str).  
2\. Create a service \`app/scraper/seeder.py\`.  
   \- Function \`seed\_team\_era(data: TeamEraCreate)\`:  
   \- Logic: Check if Era exists.  
     \- If No: Create it.  
     \- If Yes AND \`is\_manual\_override\` is True: Do nothing (Log "Skipped due to lock").  
     \- If Yes AND \`is\_manual\_override\` is False: Update the record.  
3\. Write a test case:  
   \- Manually create an Era and set \`is\_manual\_override \= True\`.  
   \- Attempt to "Seed" over it with different data via the service.  
   \- Assert the data did NOT change.

## **Phase 4: Auth & Access**

### **Prompt 6: User Roles & Google Auth Stub**

We need to secure the application and handle User Roles.

Tasks:  
1\. Create a \`User\` model with fields: \`email\`, \`role\` (Guest, New, Trusted, Admin), \`edit\_count\`.  
2\. Implement a Dependency \`get\_current\_user\` in \`app/api/deps.py\`.  
   \- For now, stub the Google Token verification: Accept a header \`X-Test-Email\` and find/create the user in DB.  
3\. Create a Permission Dependency \`require\_role(role\_name)\`:  
   \- \`New\` users can only read.  
   \- \`Trusted\` users can write.  
4\. Protect the \`POST /team-eras\` endpoint so only \`Trusted\` users can access it.  
5\. Write a test:  
   \- Try to post as a "New" user (should 403).  
   \- Try to post as a "Trusted" user (should 200).

## **Phase 5: Frontend Mobile (The Companion)**

### **Prompt 7: React Setup & List View**

Let's switch to the Frontend. We need a React app that serves as the "Mobile Companion".

Tasks:  
1\. Create a \`frontend\` folder with a React \+ Vite setup (TypeScript).  
2\. Configure \`nginx\` or \`vite\` proxy to talk to the FastAPI backend.  
3\. Create a \`TeamList\` component:  
   \- Fetches data from \`GET /teams\`.  
   \- Renders a simple vertical list: Year | Team Name | Tier.  
4\. Add a Search Bar that filters the list client-side.  
5\. Ensure the styling is mobile-first (responsive).  
6\. Provide the Dockerfile for the frontend to run in the compose stack.

## **Phase 6: Logic & Visualization**

### **Prompt 8: The Wizard Logic (Backend)**

We need to handle "Structural Events" (Merges/Splits) in the backend.

Tasks:  
1\. Create a \`LineageEvent\` model in \`app/models/lineage.py\`:  
   \- \`previous\_node\_id\`, \`next\_node\_id\`, \`event\_type\` (MERGE, SPLIT, TRANSFER).  
2\. Create a service method \`execute\_merge(node\_ids\_to\_merge: list\[UUID\], new\_era\_data: dict)\`:  
   \- Logic:   
     1\. Mark \`dissolution\_year\` on old nodes.  
     2\. Create a NEW Node.  
     3\. Create \`LineageEvent\` links connecting old nodes to the new node.  
3\. Write a test:  
   \- Create Node A and Node B.  
   \- Call \`execute\_merge\`.  
   \- Assert Node A and B are dissolved.  
   \- Assert Node C exists.  
   \- Assert Links exist from A-\>C and B-\>C.

### **Prompt 9: D3.js Data Transformation**

Finally, let's prepare the data for the D3 Visualization.

Tasks:  
1\. Create an endpoint \`GET /api/visualization/river\`.  
2\. It needs to return a JSON object optimized for a Sankey diagram:  
   \- \`nodes\`: List of all Team Eras with their "Jersey Slice" colors/percentages.  
   \- \`links\`: Connections based on \`LineageEvent\` and simple year-over-year continuity within a Node.  
3\. The response format should look like:  
   \`{ "nodes": \[{id, year, name, slices: \[{color, percent}\]}\], "links": \[{source, target, type}\] }\`  
4\. Write a test verifying that a single Managerial Node with 3 Eras produces 3 Nodes and 2 Links (Continuity links) in the JSON.  
