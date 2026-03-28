---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

You have access to the LMS backend through MCP tools. Use them to provide accurate, real-time information about courses, labs, learners, and analytics.

## Available LMS Tools

- `mcp_lms_lms_health` — Check if the backend is healthy and get item count
- `mcp_lms_lms_labs` — List all available labs
- `mcp_lms_lms_pass_rates` — Get pass rate statistics for a specific lab
- `mcp_lms_lms_scores` — Get learner scores for a specific lab
- `mcp_lms_lms_completion_rate` — Get completion statistics for a lab
- `mcp_lms_lms_timeline` — Get submission timeline for a lab
- `mcp_lms_lms_groups` — Get group performance data
- `mcp_lms_lms_top_learners` — Get top performing learners for a lab
- `mcp_lms_lms_learners` — Get learner information
- `mcp_lms_lms_sync_pipeline` — Trigger the ETL sync pipeline

## Strategy Rules

### When Lab Parameter is Missing

If the user asks for scores, pass rates, completion, groups, timeline, or top learners **without naming a lab**:

1. First call `mcp_lms_lms_labs` to get the list of available labs
2. Present the labs to the user and ask them to choose one
3. Use the lab ID from their choice to call the appropriate tool

Example:
- User: "Show me the scores"
- You: Call `lms_labs` first, then ask "Which lab would you like to see scores for? Here are the available labs: [list]"

### Formatting Results

- Format percentages with one decimal place (e.g., "75.3%")
- Show counts as whole numbers
- Keep responses concise — summarize key insights, don't dump raw JSON
- When showing multiple labs, use a numbered list with lab titles

### What Can You Do

When the user asks "what can you do?" or similar:

1. Explain that you can query the LMS backend for:
   - Lab listings and details
   - Pass rates and completion statistics
   - Learner scores and rankings
   - Submission timelines
   - Group performance
2. Mention that you need a specific lab name for detailed analytics
3. Offer to help with a specific question

### Backend Health

If the user asks about system health or if the backend is working:
- Call `mcp_lms_lms_health` to check status
- Report the item count as confirmation

### Error Handling

- If a tool fails, explain what went wrong simply
- If the backend is unreachable, suggest checking if the services are running
- If a lab doesn't exist, offer to list available labs

## Examples

**User**: "Which lab has the lowest pass rate?"
**You**: 
1. Call `lms_labs` to get all labs
2. For each lab, call `lms_pass_rates` 
3. Compare and report the lab with lowest pass rate

**User**: "Show me the scores"
**You**:
1. Call `lms_labs` to get available labs
2. Ask user to specify which lab
3. Once specified, call `lms_scores` with the lab ID

**User**: "Is the backend working?"
**You**: Call `lms_health` and report the result
