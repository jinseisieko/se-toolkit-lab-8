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

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
