---
name: observability
description: Use VictoriaLogs and VictoriaTraces MCP tools for debugging and monitoring
always: true
---

# Observability Skill

You have access to VictoriaLogs and VictoriaTraces through MCP tools. Use them to investigate errors, trace request flows, and monitor system health.

## Available Observability Tools

### Log Tools (VictoriaLogs)
- `mcp_obs_logs_search` — Search logs using LogsQL queries
- `mcp_obs_logs_error_count` — Count errors per service over a time window

### Trace Tools (VictoriaTraces)
- `mcp_obs_traces_list` — List recent traces for a service
- `mcp_obs_traces_get` — Fetch a specific trace by ID

## Investigation Strategy

### When user asks about errors

1. **Start with error count** — Call `logs_error_count` with a narrow time window (e.g., `10m` or `1h`) to see if there are recent errors and which services are affected

2. **Search for details** — If errors exist, call `logs_search` with:
   - `time_range`: Match the error count window
   - `query`: Include `severity:ERROR` and optionally `service.name:"Service Name"`
   
3. **Extract trace_id** — From the log results, look for `trace_id` fields in error records

4. **Fetch full trace** — Call `traces_get` with the trace_id to see the complete request flow and identify where the failure occurred

5. **Summarize findings** — Provide a concise summary:
   - What service had errors
   - How many errors occurred
   - What the error was (from logs)
   - Where in the request flow it failed (from traces)

### Query Patterns

**Search for recent errors in a specific service:**
```
query: _time:10m service.name:"Learning Management Service" severity:ERROR
time_range: 10m
```

**Count errors across all services:**
```
time_range: 1h
service: (leave empty for all services)
```

**Get traces for a service:**
```
service: Learning Management Service
limit: 20
```

## Response Guidelines

- **Be concise** — Summarize findings, don't dump raw JSON
- **Use narrow time windows** — Prefer `10m` or `1h` to avoid historical noise
- **Focus on the LMS backend** — When asked about "errors", prioritize `service.name:"Learning Management Service"`
- **Connect logs to traces** — Always try to find a trace_id in error logs and fetch the full trace
- **Explain what you found** — "I found 3 errors in the LMS backend in the last 10 minutes. The errors occurred when querying the database. Trace ID abc123 shows the failure happened in the db_query span."

## Example Flow

**User**: "Any LMS backend errors in the last 10 minutes?"

**You**:
1. Call `logs_error_count` with `time_range: 10m`, `service: "Learning Management Service"`
2. If errors > 0:
   - Call `logs_search` with `query: "service.name:\"Learning Management Service\" severity:ERROR"`, `time_range: 10m`
   - Extract a `trace_id` from the results
   - Call `traces_get` with that `trace_id`
   - Summarize: "Yes, I found {count} errors. The logs show {error message}. The trace shows the failure occurred at {span name}."
3. If errors = 0:
   - "No errors found in the LMS backend in the last 10 minutes."

## When No Errors Found

If the user asks about errors but none exist in the time window:
- Report that clearly: "No errors found in {service} in the last {time_range}."
- Optionally offer to check a longer time window or different service
