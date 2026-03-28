"""Tool specifications and handlers for observability MCP server."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx
from mcp.types import Tool
from pydantic import BaseModel

if TYPE_CHECKING:
    from mcp_obs.server import ObservabilityClient


class LogsSearchParams(BaseModel):
    """Parameters for searching logs."""

    query: str = "severity:ERROR"
    limit: int = 50
    time_range: str = "1h"


class LogsErrorCountParams(BaseModel):
    """Parameters for counting errors."""

    time_range: str = "1h"
    service: str | None = None


class TracesListParams(BaseModel):
    """Parameters for listing traces."""

    service: str = "Learning Management Service"
    limit: int = 20


class TracesGetParams(BaseModel):
    """Parameters for getting a specific trace."""

    trace_id: str


ToolPayload = BaseModel | dict | list
ToolHandler = Callable[[ObservabilityClient, BaseModel], Awaitable[ToolPayload]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    model: type[BaseModel]
    handler: ToolHandler

    def as_tool(self) -> Tool:
        schema = self.model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("title", None)
        return Tool(name=self.name, description=self.description, inputSchema=schema)


async def logs_search_handler(
    client: ObservabilityClient, args: LogsSearchParams
) -> dict:
    """Search logs using VictoriaLogs LogsQL."""
    url = f"{client.victorialogs_url}/select/logsql/query"
    query = f"_time:{args.time_range} {args.query}"
    params = {"query": query, "limit": str(args.limit)}

    async with httpx.AsyncClient() as http:
        response = await http.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def logs_error_count_handler(
    client: ObservabilityClient, args: LogsErrorCountParams
) -> dict:
    """Count errors per service over a time window."""
    url = f"{client.victorialogs_url}/select/logsql/query"
    query = f"_time:{args.time_range} severity:ERROR"
    if args.service:
        query += f' service.name:"{args.service}"'
    query += " | stats count() by service.name"
    params = {"query": query}

    async with httpx.AsyncClient() as http:
        response = await http.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def traces_list_handler(
    client: ObservabilityClient, args: TracesListParams
) -> dict:
    """List recent traces for a service."""
    url = f"{client.victoriatraces_url}/select/jaeger/api/traces"
    params = {"service": args.service, "limit": str(args.limit)}

    async with httpx.AsyncClient() as http:
        response = await http.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def traces_get_handler(
    client: ObservabilityClient, args: TracesGetParams
) -> dict:
    """Fetch a specific trace by ID."""
    url = f"{client.victoriatraces_url}/select/jaeger/api/traces/{args.trace_id}"

    async with httpx.AsyncClient() as http:
        response = await http.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()


# Tool specs
TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="logs_search",
        description="Search VictoriaLogs using LogsQL. Use severity:ERROR for errors, "
        'service.name:"Service Name" to filter by service. '
        "Extract trace_id from results to fetch full traces.",
        model=LogsSearchParams,
        handler=logs_search_handler,
    ),
    ToolSpec(
        name="logs_error_count",
        description="Count errors per service over a time window. "
        "Returns aggregated error counts grouped by service name.",
        model=LogsErrorCountParams,
        handler=logs_error_count_handler,
    ),
    ToolSpec(
        name="traces_list",
        description="List recent traces for a service from VictoriaTraces. "
        "Returns trace IDs, operation names, and durations.",
        model=TracesListParams,
        handler=traces_list_handler,
    ),
    ToolSpec(
        name="traces_get",
        description="Fetch a specific trace by ID from VictoriaTraces. "
        "Shows the full span hierarchy for debugging request flows.",
        model=TracesGetParams,
        handler=traces_get_handler,
    ),
]

TOOLS_BY_NAME: dict[str, ToolSpec] = {spec.name: spec for spec in TOOL_SPECS}
