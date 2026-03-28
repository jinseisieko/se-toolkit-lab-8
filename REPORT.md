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

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

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
