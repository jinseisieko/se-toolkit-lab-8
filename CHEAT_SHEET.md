# Lab 8 Cheat Sheet — The Agent is the Interface

## Project Overview

- **Goal**: Build a Telegram bot + web client that talks to an LMS backend using natural language via an AI agent (nanobot)
- **Key Pattern**: Agent = LLM + Tools (MCP) + Memory + Channels (WebSocket, Telegram) + Scheduled jobs (cron)
- **VM-based**: Everything runs on the university VM, not local machine
- **Ports**:
  - `42002` — Gateway/Caddy (main entry point)
  - `42005` — Qwen Code API (LLM proxy)
  - `42001` — Backend (LMS API)
  - `42010` — VictoriaLogs
  - `42011` — VictoriaTraces

---

## ⚠️ Setup Notes (Actual Deployment)

### Qwen Code API — Using Old Proxy

The new `qwen-code-api` service in `docker-compose.yml` may have build issues with the submodule. **Alternative**: use the old `qwen-code-oai-proxy` from `~/qwen-code-oai-proxy/`:

```bash
# Start the old proxy instead
cd ~/qwen-code-oai-proxy
docker compose up -d
```

**API Key**: The old proxy uses a different API key. Check `~/qwen-code-oai-proxy/.env`:

```bash
QWEN_API_KEY=qwen-api-key-lab6-2026  # Use this in .env.docker.secret
```

**Update `.env.docker.secret`**:

```text
QWEN_CODE_API_KEY=qwen-api-key-lab6-2026  # Not the oauth token from ~/.qwen/
```

### DNS Configuration for Docker

If you see DNS errors during build, add Google DNS to Docker:

```bash
# On VM
echo '{"dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

### Port Conflicts — Stop Lab 7 First

Labs 7 and 8 use the same ports (42001-42005). Always stop Lab 7 before starting Lab 8:

```bash
cd ~/se-toolkit-lab-7
docker compose --env-file .env.docker.secret down
```

### Quick Setup Checklist

```bash
# 1. Clone with submodules
git clone --recurse-submodules https://github.com/YOUR_USERNAME/se-toolkit-lab-8

# 2. Create and configure .env.docker.secret
cp .env.docker.example .env.docker.secret
# Edit: LMS_API_KEY, QWEN_CODE_API_KEY, NANOBOT_ACCESS_KEY, AUTOCHECKER_*

# 3. Stop Lab 7 (if running)
cd ~/se-toolkit-lab-7 && docker compose --env-file .env.docker.secret down

# 4. Start Lab 8
cd ~/se-toolkit-lab-8
docker compose --env-file .env.docker.secret up --build -d

# 5. Populate database (via Swagger UI or curl)
curl -X POST http://localhost:42001/pipeline/sync -H 'Authorization: Bearer YOUR_LMS_API_KEY'

# 6. Verify
docker compose --env-file .env.docker.secret ps
curl http://localhost:42005/v1/models -H "Authorization: Bearer YOUR_QWEN_API_KEY"
```

---

## Architecture

```
[Browser/Flutter] or [Telegram Bot]
         ↓
    Caddy (reverse proxy on :42002)
         ↓
    /ws/chat → nanobot webchat channel
                   ↓
           nanobot gateway (agent loop)
              ↙          ↘
    [MCP: lms]        [MCP: observability]
         ↓                    ↓
   LMS Backend         VictoriaLogs / VictoriaTraces
         ↓
    PostgreSQL
```

### Services in `docker-compose.yml`

| Service | Purpose | Port | Notes |
|---------|---------|------|-------|
| `backend` | FastAPI LMS API | 42001 | — |
| `postgres` | PostgreSQL database | 42004 | — |
| `qwen-code-api` | LLM proxy | 42005 | ⚠️ May have build issues — use `~/qwen-code-oai-proxy` instead |
| `nanobot` | AI agent gateway (Task 1+) | 18790 (internal) | Uncomment in Task 2 |
| `caddy` | Reverse proxy | 42002 | — |
| `victorialogs` | Log storage | 42010 | — |
| `victoriatraces` | Trace storage | 42011 | — |
| `otel-collector` | OpenTelemetry collector | — | — |

> **Note**: If `qwen-code-api` container fails with `ModuleNotFoundError`, use the old proxy:
>
> ```bash
> cd ~/qwen-code-oai-proxy && docker compose up -d
> # Then set QWEN_CODE_API_KEY=qwen-api-key-lab6-2026 in .env.docker.secret
> ```

---

## Task Summary

| Task | What You Build | Key Files |
|------|----------------|-----------|
| **Task 1** | Install nanobot, configure Qwen API, add MCP tools, write skill prompt | `nanobot/config.json`, `nanobot/workspace/skills/lms/SKILL.md`, `mcp/mcp-lms/` |
| **Task 2** | Dockerize nanobot, add WebSocket channel, add Flutter web client | `nanobot/Dockerfile`, `nanobot/entrypoint.py`, `nanobot-websocket-channel/`, `caddy/Caddyfile` |
| **Task 3** | Add observability MCP tools (VictoriaLogs/VictoriaTraces) | `mcp/mcp-obs/`, `nanobot/workspace/skills/observability/SKILL.md` |
| **Task 4** | Investigate failure, schedule health check, fix planted bug | Backend code fix, cron jobs |

---

## Key Commands

### Setup

```bash
# Clone with submodules (if submodule is empty, run: git submodule update --init --recursive)
git clone --recurse-submodules https://github.com/YOUR_USERNAME/se-toolkit-lab-8

# Install dependencies
cd se-toolkit-lab-8
uv sync --dev

# Create env file
cp .env.docker.example .env.docker.secret

# IMPORTANT: Edit .env.docker.secret with your values:
# - LMS_API_KEY (choose any)
# - QWEN_CODE_API_KEY (use qwen-api-key-lab6-2026 if using old proxy)
# - NANOBOT_ACCESS_KEY (choose any)
# - AUTOCHECKER_API_LOGIN (your university email)
# - AUTOCHECKER_API_PASSWORD (GitHub username + Telegram alias)

# Stop Lab 7 first (port conflict fix)
cd ~/se-toolkit-lab-7
docker compose --env-file .env.docker.secret down

# Start services (build first if using additional_contexts)
cd ~/se-toolkit-lab-8
docker compose --env-file .env.docker.secret build
docker compose --env-file .env.docker.secret up --build -d

# Check services
docker compose --env-file .env.docker.secret ps --format "table {{.Service}}\t{{.Status}}"

# Populate database (ETL sync)
curl -X POST http://localhost:42001/pipeline/sync -H 'Authorization: Bearer YOUR_LMS_API_KEY'
# Expected: {"new_records":14506,"total_records":14506}

# Verify Qwen API
curl http://localhost:42005/v1/models -H "Authorization: Bearer YOUR_QWEN_API_KEY"
```

### Task 1 — Local Testing

```bash
cd nanobot
uv run nanobot agent --logs --session cli:test -c ./config.json -m "What labs are available?"
```

### Task 2 — Deploy

```bash
# Build nanobot first (has additional_contexts)
docker compose --env-file .env.docker.secret build nanobot
docker compose --env-file .env.docker.secret up -d

# Check logs
docker compose --env-file .env.docker.secret logs nanobot --tail 50

# Test WebSocket
echo '{"content":"test"}' | websocat "ws://localhost:42002/ws/chat?access_key=KEY"
```

### Task 3 — Observability

```bash
# VictoriaLogs UI: http://localhost:42002/utils/victorialogs/select/vmui
# VictoriaTraces UI: http://localhost:42002/utils/victoriatraces

# Query logs via API
curl -s "http://localhost:42010/select/logsql/query?query=_time:1h%20severity:ERROR"
```

### Task 4 — Failure Investigation

```bash
# Stop PostgreSQL to trigger failure
docker compose --env-file .env.docker.secret stop postgres

# After fix, rebuild backend
docker compose --env-file .env.docker.secret build backend
docker compose --env-file .env.docker.secret up -d
```

---

## Environment Variables (`.env.docker.secret`)

| Variable | Purpose |
|----------|---------|
| `LMS_API_KEY` | Backend API authentication |
| `QWEN_CODE_API_KEY` | LLM API key |
| `NANOBOT_ACCESS_KEY` | Web client login password |
| `BOT_TOKEN` | Telegram bot token (optional) |
| `HOST_UID` / `HOST_GID` | Run container as host user for bind mounts |
| `LLM_API_BASE_URL` | `http://localhost:42005/v1` (VM) or `http://qwen-code-api:8080/v1` (Docker) |

---

## MCP Tools

### LMS MCP (`mcp-lms`)

| Tool | Purpose |
|------|---------|
| `lms_health` | Check backend health |
| `lms_labs` | List available labs |
| `lms_pass_rates` | Get lab pass rates |
| `lms_scores` | Get learner scores for a lab |
| `lms_completion` | Get completion stats |
| `lms_timeline` | Get submission timeline |
| `lms_top_learners` | Get top performers |

### Observability MCP (`mcp-obs`)

| Tool | Purpose |
|------|---------|
| `logs_search` | Search VictoriaLogs by query |
| `logs_error_count` | Count errors per service |
| `traces_list` | List recent traces for a service |
| `traces_get` | Fetch specific trace by ID |

### Webchat MCP (`mcp-webchat`)

| Tool | Purpose |
|------|---------|
| `mcp_webchat_ui_message` | Send structured UI (choice/confirm/composite) to active chat |

---

## Nanobot Config Structure (`nanobot/config.json`)

```json
{
  "agents": {
    "defaults": {
      "model": "coder-model",
      "provider": "custom",
      "workspace": "./workspace"
    }
  },
  "providers": {
    "custom": {
      "apiKey": "${LLM_API_KEY}",
      "apiBase": "${LLM_API_BASE_URL}"
    }
  },
  "gateway": {
    "host": "0.0.0.0",
    "port": 18790
  },
  "channels": {
    "webchat": {
      "enabled": true,
      "allowFrom": ["*"]
    }
  },
  "tools": {
    "mcpServers": {
      "lms": {
        "command": "python",
        "args": ["-m", "mcp_lms"],
        "env": {
          "NANOBOT_LMS_BACKEND_URL": "...",
          "NANOBOT_LMS_API_KEY": "..."
        }
      },
      "obs": {
        "command": "python",
        "args": ["-m", "mcp_obs"],
        "env": {...}
      },
      "webchat": {
        "command": "python",
        "args": ["-m", "mcp_webchat"],
        "env": {...}
      }
    }
  }
}
```

---

## Common Issues & Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: qwen_code_api` | Submodule not built correctly | Use old proxy: `cd ~/qwen-code-oai-proxy && docker compose up -d` |
| `Connection error` in Flutter | LLM API key not resolved | Check `entrypoint.py` reads correct env vars; use `qwen-api-key-lab6-2026` for old proxy |
| Empty `/flutter` page | Flutter volume not mounted | Uncomment `client-web-flutter:/srv/flutter:ro` in Caddy |
| WebSocket disconnects | Wrong `NANOBOT_ACCESS_KEY` | Clear browser data, re-enter key |
| Slow replies | Model rate limit / busy | Wait 10-30s, not necessarily broken |
| `404 Items not found` when DB down | Planted bug in backend | Fix exception handling in backend code |
| DNS errors in Docker | University DNS issues | Add `{"dns": ["8.8.8.8"]}` to `/etc/docker/daemon.json` |
| Port conflicts (42001-42005) | Lab 7 still running | `cd ~/se-toolkit-lab-7 && docker compose --env-file .env.docker.secret down` |
| `getaddrinfo EAI_AGAIN` | Docker DNS resolution | Add Google DNS to `/etc/docker/daemon.json` and restart Docker |
| Submodule empty (`qwen-code-api/`) | Not initialized | Run `git submodule update --init --recursive` |

### Qwen API Key Confusion

There are **two different API keys**:

1. **OAuth token** (`~/.qwen/oauth_creds.json`) — Used by the **new** `qwen-code-api` service
2. **Proxy API key** (`qwen-api-key-lab6-2026`) — Used by the **old** `qwen-code-oai-proxy`

**If using old proxy** (recommended if new service fails):

```bash
# Check the key in old proxy config
cat ~/qwen-code-oai-proxy/.env | grep QWEN_API_KEY

# Set in .env.docker.secret
QWEN_CODE_API_KEY=qwen-api-key-lab6-2026
```

---

## Skill Prompt Patterns

### LMS Skill (`workspace/skills/lms/SKILL.md`)

- When user asks about scores/pass-rates without lab → call `lms_labs` first, then ask to choose
- Format percentages/counts nicely
- Use `structured-ui` skill for rendering choices

### Observability Skill (`workspace/skills/observability/SKILL.md`)

- "Any errors?" → `logs_error_count` → `logs_search` → extract `trace_id` → `traces_get`
- Summarize findings, don't dump raw JSON

---

## Git Workflow

```bash
# For each task
git checkout -b task-X-description
# ... make changes ...
git add . && git commit -m "feat: implement task X"
git push origin task-X-description
# Create PR with "Closes #ISSUE_NUMBER"
```

---

## REPORT.md Checklist

- **Task 1A**: Bare agent responses (general questions, no LMS data)
- **Task 1B**: Agent with LMS tools (real lab names, health check)
- **Task 1C**: Skill prompt effect (asks for lab choice)
- **Task 2A**: Deployed agent log excerpt
- **Task 2B**: Flutter chat screenshot with real answers
- **Task 3A**: Log excerpts (happy path + error path), VictoriaLogs screenshot
- **Task 3B**: Trace screenshots (healthy + error)
- **Task 3C**: Agent responses to error queries (normal + failure)
- **Task 4A**: Investigation response with log + trace evidence
- **Task 4B**: Proactive health report screenshot
- **Task 4C**: Bug fix description, post-fix failure check, healthy report

---

## Wiki Pages to Reference

| Page | Topic |
|------|-------|
| `wiki/nanobot.md` | Nanobot architecture |
| `wiki/websocket.md` | WebSocket protocol |
| `wiki/docker-compose.md` | Service configuration |
| `wiki/llm-api.md` | LLM integration |
| `wiki/qwen-code-api.md` | Qwen setup |
| `wiki/vm.md` | VM usage |
| `wiki/coding-agents.md` | Using coding agents |

---

## Quick Reference: URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:42002/` | React dashboard |
| `http://localhost:42002/docs` | Swagger UI (LMS API) |
| `http://localhost:42002/flutter` | Flutter web client |
| `http://localhost:42002/utils/victorialogs/select/vmui` | VictoriaLogs UI |
| `http://localhost:42002/utils/victoriatraces` | VictoriaTraces UI |
| `http://localhost:42002/utils/pgadmin` | pgAdmin |
| `http://localhost:42005/health` | Qwen Code API health |
| `http://localhost:42005/v1/models` | Qwen models endpoint |

---

## Setup Verification Checklist

Run these commands on the VM to verify your setup:

```bash
# 1. All services running
cd ~/se-toolkit-lab-8
docker compose --env-file .env.docker.secret ps
# Expected: backend, postgres, caddy, victorialogs, victoriatraces, otel-collector = "Up"

# 2. Qwen API responding
curl -s http://localhost:42005/v1/models -H "Authorization: Bearer qwen-api-key-lab6-2026"
# Expected: {"object":"list","data":[{"id":"qwen3-coder-plus",...}

# 3. Backend Swagger UI
curl -s http://localhost:42001/docs | head -5
# Expected: <!DOCTYPE html>...

# 4. Database has data
curl -s http://localhost:42001/items/ -H "Authorization: Bearer my-key" | python3 -m json.tool | head -10
# Expected: Array of lab objects

# 5. Gateway working
curl -s http://localhost:42002/ | head -5
# Expected: <!doctype html>...
```
