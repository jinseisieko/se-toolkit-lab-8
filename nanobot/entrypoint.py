#!/usr/bin/env python3
"""
Entrypoint for nanobot gateway Docker container.

Resolves environment variables into config.json at runtime,
then launches nanobot gateway.
"""

import json
import os
import sys


def main():
    # Read the base config
    config_path = "/app/nanobot/config.json"
    resolved_path = "/app/nanobot/config/config.resolved.json"
    workspace_path = "/app/nanobot/workspace"

    # Ensure config directory exists and is writable
    config_dir = os.path.dirname(resolved_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, mode=0o755, exist_ok=True)

    # Check if config file exists
    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        print(
            "Make sure nanobot/config.json exists or is mounted via Docker volume",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(config_path, "r") as f:
        config = json.load(f)

    # Inject environment variables
    # LLM provider settings
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL")
    llm_api_model = os.environ.get("LLM_API_MODEL")

    # Note: Docker networking uses service names (e.g., http://qwen-code-api:8080/v1)
    # so no localhost replacement is needed here

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

    # MCP servers environment variables
    if "tools" not in config:
        config["tools"] = {"mcpServers": {}}
    if "mcpServers" not in config["tools"]:
        config["tools"]["mcpServers"] = {}

    # LMS MCP server env vars
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
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = (
                lms_backend_url
            )
        if lms_api_key:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = (
                lms_api_key
            )

    # Webchat MCP server env vars
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
            config["tools"]["mcpServers"]["webchat"]["env"][
                "NANOBOT_WEBSOCKET_RELAY_URL"
            ] = webchat_relay_url
        if webchat_token:
            config["tools"]["mcpServers"]["webchat"]["env"][
                "NANOBOT_WEBSOCKET_TOKEN"
            ] = webchat_token

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_path}", file=sys.stderr)

    # Launch nanobot gateway
    os.execvp(
        "nanobot",
        [
            "nanobot",
            "gateway",
            "--config",
            resolved_path,
            "--workspace",
            workspace_path,
        ],
    )


if __name__ == "__main__":
    main()
