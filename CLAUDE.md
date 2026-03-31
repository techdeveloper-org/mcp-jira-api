# mcp-jira-api — Claude Project Context

**Type:** FastMCP Server
**Transport:** stdio
**Python:** 3.8+

---

## What This Server Does

Jira integration supporting both Cloud (v3, ADF document format) and Server/Data Center (v2, plain text). Creates, searches, transitions, and links issues. Automatically wraps Cloud comments in ADF document format. JQL-powered issue search.

---

## Entry Point

```
server.py
```

Run via `python server.py` — communicates over stdio using the MCP protocol.

---

## Available Tools

- `jira_create_issue` — Create a Jira issue (project, type, summary, description, priority)
- `jira_get_issue` — Get full issue details by key (PROJ-123)
- `jira_search_issues` — JQL search with field projection and pagination
- `jira_transition_issue` — Transition issue to new status (To Do/In Progress/Done)
- `jira_add_comment` — Add a comment (auto ADF-wrapped for Cloud)
- `jira_link_pr` — Link a pull request URL to an issue as a remote link
- `jira_list_projects` — List all accessible Jira projects
- `jira_get_transitions` — Get available transitions for an issue
- `jira_update_issue` — Update issue fields (summary, description, assignee, labels)
- `jira_health_check` — Verify Jira URL, credentials, and API version

---

## Shared Utilities (in this repo)

- `base/` — Shared MCP infrastructure package (response builder, decorators, persistence, clients)
- `mcp_errors.py` — Structured error response helpers
- `input_validator.py` — Null-byte strip, length limits, prompt injection detection
- `rate_limiter.py` — Token bucket rate limiter (enable via ENABLE_RATE_LIMITING=1)

---

## Environment Variables

- `JIRA_URL` — Jira server URL (required)
- `JIRA_EMAIL` — Jira account email (for Cloud Basic auth)
- `JIRA_API_TOKEN` — Jira API token (Cloud) or password (Server)
- `JIRA_DEFAULT_PROJECT` — Default project key (optional)

---

## Development

### Running locally

```bash
# Install deps
pip install -r requirements.txt

# Run the MCP server (stdio mode)
python server.py
```

### Testing a tool call manually

```python
import subprocess, json

proc = subprocess.Popen(
    ["python", "server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
)
# Send MCP initialize + tool call via stdin
```

### File structure

```
mcp-jira-api/
+-- server.py          # Main FastMCP server (entry point)
+-- base/              # Shared base package (response, decorators, persistence, clients)
+-- mcp_errors.py      # Error helpers
+-- input_validator.py # Input validation
+-- rate_limiter.py    # Rate limiting
+-- requirements.txt
+-- .gitignore
+-- README.md
+-- CLAUDE.md
```

---

## Key Rules

1. Do NOT edit `base/` directly — it is a copy from `mcp-base` repo
2. To update shared utilities, edit in `mcp-base` and re-copy
3. Keep `server.py` as the single entry point
4. All tool handlers must use `@mcp_tool_handler` decorator for consistent error handling
5. All responses must use `success()` / `error()` / `MCPResponse` builder from `base.response`

---

**Last Updated:** 2026-03-31
