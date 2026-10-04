---
id: "d080cb21-88cb-4279-aae7-4f088256a157"
title: "Sync Local DB with Remote"
date: "2026-01-17T15:56:19.554434100Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

Hey there, long time no see ;-)
TO contine I need your assistance to fetch the current remote DB from prod and overwrite my local DB with it.

*Viewed [sync_db.ps1](file:///c:/Users/fjung/Documents/DEV/chainlines/sync_db.ps1) *

*User accepted the command `docker ps`*

*User accepted the command `ssh -o BatchMode=yes -o ConnectTimeout=5 root@116.203.192.168 "echo connection_success"`*

### User Input

I assume we can use sync_db.ps1 for that

*User accepted the command `ssh root@116.203.192.168 "docker ps"`*

*User accepted the command `powershell -ExecutionPolicy Bypass -File .\sync_db.ps1 -Mode pull`*

### Planner Response

The database synchronization has been completed successfully using [sync_db.ps1](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/sync_db.ps1:0:0-0:0).

**Summary of actions:**
1.  Verified local and remote Docker container configurations.
2.  Executed [sync_db.ps1](cci:7://file:///c:/Users/fjung/Documents/DEV/chainlines/sync_db.ps1:0:0-0:0) in `pull` mode.
    *   **Remote Dump:** Successfully created and downloaded `sync_dump.sql` from `116.203.192.168`.
    *   **Local Restore:** Dropped the existing `cycling_lineage` database and restored the schema and data from the remote dump.
    *   **Data Verification:** Output indicates successful copy of data rows (e.g., `COPY 15642` records).

Your local database is now an exact clone of production. You are ready to proceed with development on this fresh data.