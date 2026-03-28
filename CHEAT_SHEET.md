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

### Qwen Code API — Fixed Build

The `qwen-code-api` service had a Dockerfile bug where source code was copied **after** `uv sync`, causing `ModuleNotFoundError`. This was fixed by:

1. Copying `src/` **before** running `uv sync`
2. Using `--no-editable` flag so the package installs correctly

**If you encounter `ModuleNotFoundError: qwen_code_api`**, update your `qwen-code-api/Dockerfile`:

```dockerfile
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install the package (not editable) so the module is properly available
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable
```

Then rebuild:

```bash
cd ~/se-toolkit-lab-8
docker compose --env-file .env.docker.secret build --no-cache qwen-code-api
docker compose --env-file .env.docker.secret up -d qwen-code-api
```

**API Key**: Use the key from `.env.docker.secret`:

```text
QWEN_CODE_API_KEY=qwen-api-key-lab6-2026
```

> **Important**: The OAuth token in `~/.qwen/oauth_creds.json` is used by the Qwen CLI for authentication. The `qwen-code-api` service uses the API key from `.env.docker.secret`.

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

## Task 2 — Deploy Agent and Add Web Client

### Architecture

```
browser -> caddy (:42002) -> nanobot webchat channel (:8765) -> nanobot gateway (:18790) -> mcp_lms -> backend
                                                                   -> mcp_webchat -> webchat channel (UI relay)
                                                                   -> qwen-code-api -> Qwen
```

### nanobot-websocket-channel Submodule

Add the WebSocket channel repo as a submodule:

```bash
git submodule add https://github.com/inno-se-toolkit/nanobot-websocket-channel
git submodule update --init --recursive
```

This repo contains:

- `nanobot-webchat/` — WebSocket channel plugin for nanobot
- `mcp-webchat/` — MCP server for structured UI messages
- `client-web-flutter/` — Flutter web chat client
- `nanobot-channel-protocol/` — Shared protocol definitions

### Install Webchat Packages

```bash
cd nanobot
uv add nanobot-webchat --editable ../nanobot-websocket-channel/nanobot-webchat
uv add mcp-webchat --editable ../nanobot-websocket-channel/mcp-webchat
```

Update root `pyproject.toml` to include workspace members:

```toml
[tool.uv.workspace]
members = [
  "backend",
  "qwen-code-api",
  "mcp/mcp-lms",
  "nanobot",
  "nanobot-websocket-channel/nanobot-channel-protocol",
  "nanobot-websocket-channel/mcp-webchat",
  "nanobot-websocket-channel/nanobot-webchat",
]

[tool.uv.sources]
nanobot-webchat = { path = "nanobot-websocket-channel/nanobot-webchat", editable = true }
mcp-webchat = { path = "nanobot-websocket-channel/mcp-webchat", editable = true }
nanobot-channel-protocol = { path = "nanobot-websocket-channel/nanobot-channel-protocol", editable = true }
```

### nanobot/Dockerfile Pattern

Key patterns for the nanobot Dockerfile:

```dockerfile
ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy root workspace files
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy mcp packages from mcp context
COPY --from=mcp mcp-lms /app/mcp/mcp-lms

# Copy nanobot-websocket-channel from workspace context
COPY --from=workspace nanobot-websocket-channel /app/nanobot-websocket-channel

# Copy nanobot project files
COPY pyproject.toml /app/nanobot/pyproject.toml
COPY . /app/nanobot

# Copy config.json explicitly (gitignored but needed for runtime)
COPY config.json /app/nanobot/config.json

# Sync dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    cd /app/nanobot && uv sync --frozen --no-dev

# --- Stage 2: runtime image ---
ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Setup user matching host UID/GID for bind mounts
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --system --gid ${APP_GID} appgroup && \
    useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home appuser

COPY --from=builder --chown=appgroup:appgroup /app /app
COPY config.json /app/nanobot/config.json

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/nanobot
USER ${APP_UID}:${APP_GID}

ENTRYPOINT ["python", "/app/nanobot/entrypoint.py"]
```

### entrypoint.py Pattern

The entrypoint resolves environment variables into the config at runtime:

```python
#!/usr/bin/env python3
import json
import os
import sys

def main():
    config_path = "/app/nanobot/config.json"
    resolved_path = "/app/nanobot/config/config.resolved.json"
    workspace_path = "/app/nanobot/workspace"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Inject LLM settings
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL")
    llm_api_model = os.environ.get("LLM_API_MODEL")
    
    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base_url:
        config["providers"]["custom"]["apiBase"] = llm_api_base_url
    if llm_api_model:
        config["agents"]["defaults"]["model"] = llm_api_model
    
    # Gateway settings
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT")
    
    if gateway_host:
        config["gateway"]["host"] = gateway_host
    if gateway_port:
        config["gateway"]["port"] = int(gateway_port)
    
    # Webchat channel settings
    webchat_host = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT")
    
    if "channels" not in config:
        config["channels"] = {}
    
    if webchat_host or webchat_port:
        config["channels"]["webchat"] = {"enabled": True, "allowFrom": ["*"]}
        if webchat_host:
            config["channels"]["webchat"]["host"] = webchat_host
        if webchat_port:
            config["channels"]["webchat"]["port"] = int(webchat_port)
    
    # MCP servers
    if "tools" not in config:
        config["tools"] = {"mcpServers": {}}
    if "mcpServers" not in config["tools"]:
        config["tools"]["mcpServers"] = {}
    
    # LMS MCP server
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")
    
    if lms_backend_url or lms_api_key:
        if "lms" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["lms"] = {
                "command": "python",
                "args": ["-m", "mcp_lms"],
            }
        if "env" not in config["tools"]["mcpServers"]["lms"]:
            config["tools"]["mcpServers"]["lms"]["env"] = {}
        if lms_backend_url:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
        if lms_api_key:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key
    
    # Webchat MCP server
    webchat_relay_url = os.environ.get("NANOBOT_WEBSOCKET_RELAY_URL")
    webchat_token = os.environ.get("NANOBOT_WEBSOCKET_TOKEN")
    
    if webchat_relay_url or webchat_token:
        if "webchat" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["webchat"] = {
                "command": "python",
                "args": ["-m", "mcp_webchat"],
            }
        if "env" not in config["tools"]["mcpServers"]["webchat"]:
            config["tools"]["mcpServers"]["webchat"]["env"] = {}
        if webchat_relay_url:
            config["tools"]["mcpServers"]["webchat"]["env"]["NANOBOT_WEBSOCKET_RELAY_URL"] = webchat_relay_url
        if webchat_token:
            config["tools"]["mcpServers"]["webchat"]["env"]["NANOBOT_WEBSOCKET_TOKEN"] = webchat_token
    
    # Write resolved config
    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Using config: {resolved_path}", file=sys.stderr)
    
    # Launch nanobot gateway
    os.execvp("nanobot", ["nanobot", "gateway", "--config", resolved_path, "--workspace", workspace_path])

if __name__ == "__main__":
    main()
```

### docker-compose.yml Environment Variables

For the nanobot service:

```yaml
environment:
  # LLM settings (Docker internal networking)
  - LLM_API_KEY=${QWEN_CODE_API_KEY}
  - LLM_API_BASE_URL=http://qwen-code-api:8080/v1
  - LLM_API_MODEL=${LLM_API_MODEL}
  
  # Gateway settings
  - NANOBOT_GATEWAY_CONTAINER_ADDRESS=0.0.0.0
  - NANOBOT_GATEWAY_CONTAINER_PORT=18790
  
  # Webchat channel settings
  - NANOBOT_WEBCHAT_CONTAINER_ADDRESS=0.0.0.0
  - NANOBOT_WEBCHAT_CONTAINER_PORT=8765
  
  # Access key for WebSocket authentication
  - NANOBOT_ACCESS_KEY=${NANOBOT_ACCESS_KEY}
  
  # MCP webchat settings
  - NANOBOT_WEBSOCKET_RELAY_URL=ws://nanobot:${NANOBOT_WEBCHAT_CONTAINER_PORT}
  - NANOBOT_WEBSOCKET_TOKEN=${NANOBOT_ACCESS_KEY}
  
  # LMS MCP settings (use container service names)
  - NANOBOT_LMS_BACKEND_URL=http://backend:8000
  - NANOBOT_LMS_API_KEY=${LMS_API_KEY}
```

### caddy/Caddyfile Routes

```caddy
# WebSocket route for nanobot webchat
handle /ws/chat {
    reverse_proxy http://nanobot:{$NANOBOT_WEBCHAT_CONTAINER_PORT}
}

# Flutter web client route
handle_path /flutter* {
    root * /srv/flutter
    try_files {path} /index.html
    file_server
}
```

### Testing WebSocket Endpoint

```bash
# Using Python (if websocat not available)
docker exec se-toolkit-lab-8-nanobot-1 python -c "
import asyncio, json, websockets

async def main():
    uri = 'ws://localhost:8765?access_key=nanobot-key'
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({'content': 'What labs are available?'}))
        print(await ws.recv())

asyncio.run(main())
"

# Expected response format:
# {"type":"text","content":"Here are the available labs:...","format":"markdown"}
```

### nanobot/config.json Structure

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
      "apiKey": "qwen-api-key-lab6-2026",
      "apiBase": "http://localhost:42005/v1"
    }
  },
  "gateway": {
    "host": "0.0.0.0",
    "port": 18790
  },
  "channels": {
    "webchat": {
      "enabled": true,
      "allowFrom": ["*"],
      "host": "0.0.0.0",
      "port": 8765
    }
  },
  "tools": {
    "mcpServers": {
      "lms": {
        "command": "python",
        "args": ["-m", "mcp_lms"],
        "env": {
          "NANOBOT_LMS_BACKEND_URL": "http://backend:8000",
          "NANOBOT_LMS_API_KEY": "my-key"
        }
      },
      "webchat": {
        "command": "python",
        "args": ["-m", "mcp_webchat"],
        "env": {
          "NANOBOT_WEBSOCKET_RELAY_URL": "ws://nanobot:8765",
          "NANOBOT_WEBSOCKET_TOKEN": "nanobot-key"
        }
      }
    }
  }
}
```

### Common Issues & Fixes — Task 2

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `No channels enabled` in logs | webchat channel not in config | Check `entrypoint.py` injects `NANOBOT_WEBCHAT_*` env vars |
| `No module named mcp_webchat` | Package not installed | Run `uv add mcp-webchat --editable ../nanobot-websocket-channel/mcp-webchat` |
| `Invalid access key` on WebSocket | Wrong or missing `access_key` query param | Use `ws://...:8765?access_key=YOUR_KEY` |
| Empty page at `/flutter` | Flutter volume not mounted in Caddy | Uncomment `client-web-flutter:/srv/flutter:ro` in caddy volumes |
| WebSocket disconnects immediately | Access key mismatch | Ensure `NANOBOT_ACCESS_KEY` matches what you pass in URL |
| Slow replies (10-30s) | Model rate limit / busy | Normal behavior, not broken |
| `Distribution not found` in Docker build | Wrong relative paths in pyproject.toml | Use `../../nanobot-websocket-channel/...` from nanobot context |
| Submodule empty after clone | Not initialized | Run `git submodule update --init --recursive` |

### Build Order

Always build before starting services (especially with `additional_contexts`):

```bash
# Build nanobot first (has additional_contexts: workspace, mcp)
docker compose --env-file .env.docker.secret build nanobot

# Build Flutter client
docker compose --env-file .env.docker.secret build client-web-flutter

# Then start all services
docker compose --env-file .env.docker.secret up -d
```

### Good Log Signs

```
nanobot-1  | Using config: /app/nanobot/config/config.resolved.json
nanobot-1  | 🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
nanobot-1  | 2026-03-28 10:55:05.192 | INFO  | nanobot.channels.manager:_init_channels:58 - WebChat channel enabled
nanobot-1  | ✓ Channels enabled: webchat
nanobot-1  | 2026-03-28 10:55:07.100 | INFO  | nanobot.agent.tools.mcp:connect_mcp_servers:246 - MCP server 'lms': connected, 9 tools registered
nanobot-1  | 2026-03-28 10:55:08.372 | INFO  | nanobot.agent.tools.mcp:connect_mcp_servers:246 - MCP server 'webchat': connected, 1 tools registered
nanobot-1  | 2026-03-28 10:55:08.372 | INFO  | nanobot.agent.loop:run:280 - Agent loop started
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
| `qwen-code-api` | LLM proxy | 42005 | ✅ Fixed: copy src before uv sync, use --no-editable |
| `nanobot` | AI agent gateway (Task 1+) | 18790 (internal) | Uncomment in Task 2 |
| `caddy` | Reverse proxy | 42002 | — |
| `victorialogs` | Log storage | 42010 | — |
| `victoriatraces` | Trace storage | 42011 | — |
| `otel-collector` | OpenTelemetry collector | — | — |

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
# - QWEN_CODE_API_KEY=qwen-api-key-lab6-2026
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
# Install nanobot from pinned commit (avoid infected v0.1.4.post5 release)
cd nanobot
uv add "nanobot-ai @ https://github.com/HKUDS/nanobot/archive/e7d371ec1e6531b28898ec2c869ef338e8dd46ec.zip"

# Install MCP-LMS tools
uv add mcp-lms --editable ../mcp/mcp-lms

# Test bare agent (no MCP tools yet)
uv run nanobot agent --logs --session cli:task1a -c ./config.json -m "What is the agentic loop?"

# Test with MCP tools (expects real backend data)
NANOBOT_LMS_BACKEND_URL=http://localhost:42002 NANOBOT_LMS_API_KEY=my-key \
  uv run nanobot agent --logs --session cli:task1b -c ./config.json -m "What labs are available?"

# Test skill prompt (should ask for lab selection)
uv run nanobot agent --logs --session cli:task1c -c ./config.json -m "Show me the scores"
```

**Expected Results:**

| Test | Expected Behavior |
|------|-------------------|
| `task1a` (bare agent) | Explores filesystem, no backend access |
| `task1b` (with MCP) | Returns real lab names from backend |
| `task1c` (with skill) | Asks user to choose a lab first |

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

| Tool | Purpose | Example Query |
|------|---------|---------------|
| `mcp_lms_lms_health` | Check backend health | "Is the LMS backend healthy?" |
| `mcp_lms_lms_labs` | List available labs | "What labs are available?" |
| `mcp_lms_lms_pass_rates` | Get lab pass rates | "Show pass rates for Lab 01" |
| `mcp_lms_lms_scores` | Get learner scores | "Show me the scores" |
| `mcp_lms_lms_completion_rate` | Get completion stats | "What's the completion rate?" |
| `mcp_lms_lms_timeline` | Get submission timeline | "Show submission timeline" |
| `mcp_lms_lms_top_learners` | Get top performers | "Who are the top learners?" |
| `mcp_lms_lms_groups` | Get group performance | "Show group performance" |
| `mcp_lms_lms_sync_pipeline` | Trigger ETL sync | "Sync the LMS data" |

> **Note**: Tools are prefixed with `mcp_lms_` when called by nanobot.

### Skill Pattern: Missing Lab Parameter

When user asks for scores/pass-rates/completion without naming a lab:

```markdown
1. Call `mcp_lms_lms_labs` first
2. Present labs to user
3. Ask: "Which lab would you like to see?"
4. Use selected lab ID for the actual query
```

**Example:**

```
User: "Show me the scores"
Agent: "Here are the available labs: [1-8]. Which lab would you like to see?"
```

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

### Task 1A/B/C Working Config

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
      "apiKey": "qwen-api-key-lab6-2026",
      "apiBase": "http://localhost:42005/v1"
    }
  },
  "gateway": {
    "host": "0.0.0.0",
    "port": 18790
  },
  "channels": {},
  "tools": {
    "mcpServers": {
      "lms": {
        "command": "python",
        "args": ["-m", "mcp_lms"],
        "env": {
          "NANOBOT_LMS_BACKEND_URL": "http://localhost:42002",
          "NANOBOT_LMS_API_KEY": "my-key"
        }
      }
    }
  }
}
```

> **Note**: `config.json` is gitignored by default. Copy to VM via `scp` or create there.

### Full Config (Tasks 2-4)

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
          "NANOBOT_LMS_BACKEND_URL": "http://backend:8000",
          "NANOBOT_LMS_API_KEY": "${LMS_API_KEY}"
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

### Task 1 Specific

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `No API key configured` | Missing global config | Create `~/.nanobot/config.json` with providers section |
| `Connection error` to LLM | Wrong API key or service down | Check `docker ps` for qwen-code-api; verify QWEN_CODE_API_KEY in .env.docker.secret |
| Agent explores filesystem | No MCP tools configured | Add `mcpServers.lms` to `config.json` |
| MCP tools not appearing | `mcp-lms` not installed | Run `uv add mcp-lms --editable ../mcp/mcp-lms` |
| Agent doesn't ask for lab | Skill prompt not loaded | Check `workspace/skills/lms/SKILL.md` exists with frontmatter |

### General

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: qwen_code_api` | Dockerfile copies src after uv sync | Fix Dockerfile: copy src/ before uv sync, use --no-editable |
| `Connection error` in Flutter | LLM API key not resolved | Check `entrypoint.py` reads correct env vars |
| Empty `/flutter` page | Flutter volume not mounted | Uncomment `client-web-flutter:/srv/flutter:ro` in Caddy |
| WebSocket disconnects | Wrong `NANOBOT_ACCESS_KEY` | Clear browser data, re-enter key |
| Slow replies | Model rate limit / busy | Wait 10-30s, not necessarily broken |
| `404 Items not found` when DB down | Planted bug in backend | Fix exception handling in backend code |
| DNS errors in Docker | University DNS issues | Add `{"dns": ["8.8.8.8"]}` to `/etc/docker/daemon.json` |
| Port conflicts (42001-42005) | Lab 7 still running | `cd ~/se-toolkit-lab-7 && docker compose --env-file .env.docker.secret down` |
| `getaddrinfo EAI_AGAIN` | Docker DNS resolution | Add Google DNS to `/etc/docker/daemon.json` and restart Docker |
| Submodule empty (`qwen-code-api/`) | Not initialized | Run `git submodule update --init --recursive` |
| `config.json` changes not pushed | File is gitignored | Copy via `scp` or create on VM directly |

### Qwen API Key

The API key is configured in `.env.docker.secret`:

```bash
# Check the key in .env.docker.secret
grep QWEN_CODE_API_KEY .env.docker.secret

# Should be:
QWEN_CODE_API_KEY=qwen-api-key-lab6-2026
```

> **Note**: The OAuth token in `~/.qwen/oauth_creds.json` is used by the Qwen CLI for interactive authentication. The `qwen-code-api` service uses the API key from `.env.docker.secret` for API access.

---

## Skill Prompt Patterns

### LMS Skill (`workspace/skills/lms/SKILL.md`)

**Frontmatter (required):**

```markdown
---
name: lms
description: Use LMS MCP tools for live course data
always: true
---
```

**Key Rules:**

- When user asks about scores/pass-rates/completion without lab → call `lms_labs` first, then ask to choose
- Format percentages with 1 decimal (e.g., "75.3%")
- Keep responses concise — summarize, don't dump raw JSON
- When the user asks "what can you do?", explain current tools and limits

**Example Behavior:**

```
User: "Show me the scores"
Agent: [calls lms_labs] → "Here are the available labs: [1-8]. Which lab would you like to see?"
```

### Structured-UI Skill (Shared)

The repo includes `workspace/skills/structured-ui/SKILL.md` for generic choice/confirm/composite behavior on supported chat channels. Your LMS skill should cooperate with it by:

- Calling `lms_labs` when lab choice is needed
- Providing short, readable lab labels
- Providing stable lab values for follow-up tool calls

### Observability Skill (`workspace/skills/observability/SKILL.md`)

**Key Flow:**

```
"Any errors?" → logs_error_count → logs_search → extract trace_id → traces_get → summarize
```

**Rules:**

- Search logs first when user asks about errors
- If you find a trace ID in logs, fetch the full trace
- Summarize findings concisely — don't dump raw JSON

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
