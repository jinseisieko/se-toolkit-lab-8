# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

**Question: "What is the agentic loop?"**

```
The agentic loop is the core iterative cycle that an autonomous AI agent follows
to accomplish tasks. It's the fundamental pattern that enables agents to act    
independently and adaptively.

The Basic Loop                                                                  

 Perceive → Think → Act → Observe → (repeat)                                    

Typical Stages                                                                  

 1 Perceive/Input — The agent receives information about its environment, goals,
   or user requests                                                             
 2 Think/Reason — The agent processes the input, plans actions, and makes       
   decisions (often using an LLM)                                               
 3 Act — The agent executes actions using available tools (APIs, file           
   operations, web searches, etc.)                                              
 4 Observe/Reflect — The agent observes the results of its actions and evaluates
   progress                                                                     
 5 Iterate — Based on observations, the agent decides whether to continue,      
   adjust its plan, or terminate                                                

Key Characteristics                                                             

 • Autonomy: The agent drives the loop without constant human intervention      
 • Adaptivity: Each iteration can adjust based on new information               
 • Goal-directed: The loop continues until the objective is achieved or deemed  
   impossible                                                                   
 • Tool use: Agents leverage external tools to extend their capabilities beyond 
   pure reasoning                                                               
```

**Question: "What labs are available in our LMS?"** (no MCP tools yet)

The agent explored the filesystem instead of querying the LMS backend:

```
Based on my exploration of the workspace, here are the available labs in the    
LMS:                                                                            

Required Labs                                                                   

 • Task 1 (lab/tasks/required/task-1.md)                                        
 • Task 2 (lab/tasks/required/task-2.md)                                        
 • Task 3 (lab/tasks/required/task-3.md)                                        
 • Task 4 (lab/tasks/required/task-4.md)                                        
 • Task 5 (lab/tasks/required/task-5.md)                                        

Optional Labs                                                                   

 • Task 1 (lab/tasks/optional/task-1.md)                                        
```

This confirms the bare agent has no live LMS backend access — it inspects local repo files instead.

## Task 1B — Agent with LMS tools

**Question: "What labs are available?"** (with MCP tools)

```
Here are the available labs:                                                    

 1 Lab 01 – Products, Architecture & Roles                                      
 2 Lab 02 — Run, Fix, and Deploy a Backend Service                              
 3 Lab 03 — Backend API: Explore, Debug, Implement, Deploy                      
 4 Lab 04 — Testing, Front-end, and AI Agents                                   
 5 Lab 05 — Data Pipeline and Analytics Dashboard                               
 6 Lab 06 — Build Your Own Agent                                                
 7 Lab 07 — Build a Client with an AI Coding Agent                              
 8 Lab 08 — lab-08                                                              
```

**Question: "Is the LMS backend healthy?"**

```
Yes, the LMS backend is healthy! It currently has 56 items in the system.
```

The agent now calls MCP tools (`mcp_lms_lms_labs`, `mcp_lms_lms_health`) and returns real backend data.

## Task 1C — Skill prompt

**Question: "Show me the scores"** (without specifying a lab)

```
I'll help you view the scores. First, let me get the list of available labs so  
you can choose which one you'd like to see.                                     

Here are the available labs:                                                    

 1 Lab 01 – Products, Architecture & Roles                                      
 2 Lab 02 — Run, Fix, and Deploy a Backend Service                              
 3 Lab 03 — Backend API: Explore, Debug, Implement, Deploy                      
 4 Lab 04 — Testing, Front-end, and AI Agents                                   
 5 Lab 05 — Data Pipeline and Analytics Dashboard                               
 6 Lab 06 — Build Your Own Agent                                                
 7 Lab 07 — Build a Client with an AI Coding Agent                              
 8 Lab 08 — lab-08                                                              

Which lab would you like to see the scores for?                                 
```

The skill prompt works — the agent asks for lab selection when the parameter is missing.

## Task 2A — Deployed agent

**Nanobot startup log excerpt:**

```
nanobot-1  | Using config: /app/nanobot/config/config.resolved.json
nanobot-1  | 🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
nanobot-1  | 2026-03-28 10:55:05.192 | INFO     | nanobot.channels.manager:_init
_channels:58 - WebChat channel enabled
nanobot-1  | ✓ Channels enabled: webchat
nanobot-1  | ✓ Heartbeat: every 1800s
nanobot-1  | 2026-03-28 10:55:07.100 | INFO     | nanobot.agent.tools.mcp:connec
t_mcp_servers:246 - MCP server 'lms': connected, 9 tools registered
nanobot-1  | 2026-03-28 10:55:08.372 | INFO     | nanobot.agent.tools.mcp:connec
t_mcp_servers:246 - MCP server 'webchat': connected, 1 tools registered
nanobot-1  | 2026-03-28 10:55:08.372 | INFO     | nanobot.agent.loop:run:280 - A
gent loop started
```

The nanobot gateway is running as a Docker service with:

- WebChat channel enabled
- MCP LMS server connected (9 tools)
- MCP WebChat server connected (1 tool for UI messages)

## Task 2B — Web client

**WebSocket test through Caddy:**

```
Request: {"content": "What labs are available?"}
Response: {"type":"text","content":"Here are the available labs:\n\n1. **Lab 01**
 – Products, Architecture & Roles\n2. **Lab 02** — Run, Fix, and Deploy a Backend
 Service\n3. **Lab 03** — Backend API: Explore, Debug, Implement, Deploy\n4. **
Lab 04** — Testing, Front-end, and AI Agents\n5. **Lab 05** — Data Pipeline and
Analytics Dashboard\n6. **Lab 06** — Build Your Own Agent\n7. **Lab 07** — Build
 a Client with an AI Coding Agent\n8. **lab-08**\n\nWould you like more details
about any specific lab, such as pass rates, completion statistics, or learner
performance?","format":"markdown"}
```

**Backend health check:**

```
Request: {"content": "How is the backend doing?"}
Response: {"type":"text","content":"I'll check the backend health for you."...}
```

The Flutter web client is accessible at `http://localhost:42002/flutter` and the WebSocket endpoint at `/ws/chat` is working correctly.

**Files changed for Task 2:**

- `nanobot/entrypoint.py` — resolves env vars into config at runtime
- `nanobot/Dockerfile` — multi-stage build with uv
- `nanobot/config.json` — added webchat channel and mcp-webchat server
- `nanobot/pyproject.toml` — added nanobot-webchat and mcp-webchat dependencies
- `docker-compose.yml` — uncommented nanobot, client-web-flutter, caddy configs
- `caddy/Caddyfile` — added /ws/chat and /flutter routes
- `pyproject.toml` — added nanobot-websocket-channel workspace members
- `nanobot-websocket-channel/` — new submodule for WebSocket channel and Flutter client

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

**Question: "What went wrong?"** (with PostgreSQL stopped)

The agent performed a multi-step investigation using observability tools:

```
I found an error in the Learning Management Service. Here's what went wrong:

## Error Summary

**Issue:** Database connection failure  
**Time:** ~50 minutes ago (11:27 UTC)  
**HTTP Status:** 404 Not Found

## Root Cause

The LMS backend attempted to query the database (`SELECT FROM item`) but the 
**PostgreSQL connection was closed**. The error was:

```

asyncpg.exceptions.InterfaceError: connection is closed

```

## Trace Details

The trace shows a `GET /items/` request that:
1. Started a database connection to `db-lab-8` on PostgreSQL
2. Failed during the `SELECT` operation because the connection was closed
3. Returned a 404 response to the client

This appears to be a **database connection pooling issue** — the connection was 
established but closed before the query could complete.
```

**Key finding:** The agent identified the discrepancy — the backend returned
**404 "Not Found"** but the real issue was a **PostgreSQL connection failure**.
This misleading error message pointed to a bug in the exception handling code.

---

## Task 4B — Proactive health check

**Cron job created:**

The agent created a health check reminder using the `cron` tool:

```
Created! The health check reminder is now active (job ID: `0fdaba46`) and will 
fire every 2 minutes.
```

**Proactive health report:**

When the cron reminder fired, the agent automatically ran the investigation and
posted a health summary to the chat:

```
## LMS Health Check Summary

**Backend Status:** ✅ Healthy (56 items)

**Recent Errors (last 1h):** ⚠️ VictoriaLogs service experiencing issues

**Trace Analysis:**
- Recent traces show all requests completing successfully (HTTP 200)
- One older error trace from ~1 hour ago: database connection closed 
  (asyncpg InterfaceError)
- Current request patterns appear normal with successful database queries

**Observability Note:** VictoriaLogs is returning errors (400 Bad Request / JSON 
decode issues), but VictoriaTraces is working normally. The LMS backend itself 
appears healthy based on trace data.

**Recommendation:** Monitor VictoriaLogs service health. LMS backend is operating 
normally.
```

The proactive health check successfully monitored the system and reported status.

---

## Task 4C — Bug fix and recovery

### 1. Root Cause

**Location:** `backend/src/lms_backend/routers/items.py`, `get_items()` function

**The Bug:** The original code caught ALL exceptions and returned a misleading
**404 "Items not found"** error, even when the database was unreachable:

```python
@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all items."""
    try:
        return await read_items(session)
    except Exception as exc:
        logger.warning(
            "items_list_failed_as_not_found",
            extra={"event": "items_list_failed_as_not_found"},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Items not found",
        ) from exc
```

This hid the real database error (PostgreSQL connection closed) behind a 404,
making debugging difficult.

### 2. Fix

Changed the exception handling to return **500 Internal Server Error** for
database failures, preserving the actual error message:

```python
@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all items."""
    try:
        return await read_items(session)
    except SQLAlchemyError as exc:
        # Database errors (connection failure, query errors, etc.) should be 500
        logger.error(
            "items_list_database_error",
            extra={"event": "items_list_database_error", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(exc)}",
        ) from exc
    except Exception as exc:
        # Unexpected errors should also be 500, not 404
        logger.error(
            "items_list_unexpected_error",
            extra={"event": "items_list_unexpected_error", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(exc)}",
        ) from exc
```

**Changes:**

- Added `SQLAlchemyError` import
- Split exception handling: `SQLAlchemyError` → 500 with DB error details
- Changed log level from `warning` to `error` for proper severity
- Removed misleading "Items not found" message

### 3. Post-fix verification

After rebuilding and redeploying the backend, the fix was verified:

```bash
# Verify fix is in container
docker exec se-toolkit-lab-8-backend-1 cat /app/backend/src/lms_backend/routers/items.py
```

The code now shows the correct 500 error handling for database failures.

### 4. Healthy follow-up

After restarting PostgreSQL, the system returned to healthy status:

```
## LMS Health Check Summary

**Backend Status:** ✅ Healthy (56 items)

**Recent Errors (last 1h):** No errors found

**Trace Analysis:**
- All recent traces show successful HTTP 200 responses
- Database queries completing normally
- No connection errors detected

**Conclusion:** System is operating normally after PostgreSQL recovery.
```

The health check now correctly reports healthy status when the database is
running, and would report the actual database error (500) if PostgreSQL goes
down again.
