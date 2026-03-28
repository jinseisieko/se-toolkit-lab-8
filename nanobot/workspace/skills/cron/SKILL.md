---
name: cron
description: Use the built-in cron tool for scheduled reminders
always: true
---

# Cron Skill

The `cron` tool allows you to schedule **reminder notifications** that prompt the user to take action or ask for an update.

## Available Actions

### `cron({"action": "add", "user_id": str, "channel": str, "message": str, "interval_minutes": int})`

Schedule a recurring reminder.

**Parameters:**
- `user_id`: The user's ID (extract from session, e.g., `8281248569` from `telegram:8281248569`)
- `channel`: The channel name (e.g., `telegram`, `webchat`)
- `message`: The reminder message to send
- `interval_minutes`: How often to send the reminder

### `cron({"action": "list", "user_id": str, "channel": str})`

List all scheduled reminders for a user/channel.

### `cron({"action": "remove", "job_id": int, "user_id": str, "channel": str})`

Remove a specific reminder by job ID.

## Usage Pattern for Health Checks

Since cron sends **reminders** (not automated reports), use this pattern:

1. **Create a reminder** that prompts the user to request a health check:
   ```
   "Time for LMS health check! Ask me: 'What went wrong?' or 'Check system health'"
   ```

2. **When the user sees the reminder**, they ask you to run the check

3. **You then execute** the observability investigation flow:
   - Call `logs_error_count` with `time_range: "10m"`
   - Call `logs_search` to get error details
   - Call `traces_get` with a trace_id from the logs
   - Summarize findings

## Session Context

Extract `user_id` and `channel` from the current session:
- Session format: `{channel}:{user_id}` (e.g., `telegram:8281248569` or `webchat:12345`)
- For webchat: channel is `webchat`, user_id is the session identifier

## Example Flow

**User**: "Create a health check that runs every 2 minutes"

**You**:
1. Extract session info (e.g., `webchat:12345`)
2. Call `cron` with:
   - `action: "add"`
   - `user_id: "12345"`
   - `channel: "webchat"`
   - `interval_minutes: 2`
   - `message: "Time for LMS health check! Ask me 'What went wrong?' to investigate recent errors."`
3. Confirm: "I've scheduled a reminder every 2 minutes. When you see it, just ask me 'What went wrong?' and I'll run a full investigation."

## Important Limitations

- Cron **cannot** execute tools automatically — it only sends reminder messages
- Cron **cannot** post formatted reports — it sends the reminder text only
- For automated periodic tasks, consider `HEARTBEAT.md` instead (but note Task 4 requires cron)
