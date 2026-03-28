"""Stdio MCP server exposing observability tools."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel

from mcp_obs.settings import ObservabilitySettings
from mcp_obs.tools import TOOL_SPECS, TOOLS_BY_NAME


@dataclass
class ObservabilityClient:
    """Simple client holding observability settings."""

    victorialogs_url: str
    victoriatraces_url: str


def _text(data: Any) -> list[TextContent]:
    """Convert data to text content."""
    if isinstance(data, BaseModel):
        payload = data.model_dump()
    elif isinstance(data, (list, tuple)):
        payload = [item.model_dump() if isinstance(item, BaseModel) else item for item in data]
    else:
        payload = data
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, default=str))]


def create_server(client: ObservabilityClient) -> Server:
    """Create MCP server with observability tools."""
    server = Server("observability")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [spec.as_tool() for spec in TOOL_SPECS]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        spec = TOOLS_BY_NAME.get(name)
        if spec is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        try:
            args = spec.model.model_validate(arguments or {})
            result = await spec.handler(client, args)
            return _text(result)
        except Exception as exc:
            return [
                TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")
            ]

    _ = list_tools, call_tool
    return server


async def main() -> None:
    """Main entry point."""
    settings = ObservabilitySettings()
    client = ObservabilityClient(
        victorialogs_url=settings.victorialogs_url,
        victoriatraces_url=settings.victoriatraces_url,
    )
    server = create_server(client)
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
