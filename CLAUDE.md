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

## Available Tools (41 total: 10 core + 15 Scrum Master + 16 Advanced Analytics)

### Core Jira Tools (10)

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

### Scrum Master -- Board & Sprint Infrastructure (5)

- `jira_get_boards` — List Scrum/Kanban boards accessible to the configured user
- `jira_get_sprints` — List sprints for a board (filter by state: active/future/closed)
- `jira_create_sprint` — Create a new sprint on a Scrum board
- `jira_start_sprint` — Start a future sprint (transitions state to active)
- `jira_close_sprint` — Close (complete) an active sprint

### Scrum Master -- Ceremony Facilitation (5)

- `jira_plan_sprint` — Sprint planning report with capacity and velocity context
- `jira_daily_standup` — Daily Scrum report for the active sprint
- `jira_sprint_review` — Sprint Review report with delivered vs. not-delivered breakdown
- `jira_retrospective` — Sprint Retrospective report with RE score and Tuckman stage
- `jira_refine_backlog` — Backlog Refinement report with WSJF scoring template

### Scrum Master -- Analytics (5)

- `jira_get_velocity` — Sprint velocity history and NASSCOM AgileX benchmark comparison
- `jira_get_sprint_metrics` — Comprehensive metrics for a specific sprint (burndown, WIP, health)
- `jira_track_impediments` — Impediment and blocker tracking with MTTR analysis
- `jira_team_health` — Team health dashboard across recent sprints (Tuckman + composite score)
- `jira_monte_carlo_forecast` — Monte Carlo simulation for probabilistic sprint delivery forecast

### Advanced Analytics -- Team Health & Forecasting (8)

- `jira_spotify_health_check` — Run Spotify Squad Health Check scoring for a team
- `jira_psychological_safety` — Compute Edmondson Psychological Safety Scale score for a team
- `jira_cognitive_load` — Compute Team Topology Cognitive Load Index (CLI) for a team's domain portfolio
- `jira_attrition_forecast` — Forecast cumulative attrition impact on team velocity using exponential model
- `jira_pert_estimate` — Compute a PERT task estimate (optimistic / most-likely / pessimistic)
- `jira_scrum_of_scrums` — Compute Scrum of Scrums Brook's Law overhead and optimal team count
- `jira_ist_capacity` — Compute IST timezone distributed team effective capacity
- `jira_multi_sprint_holidays` — Forecast India national holidays across consecutive sprint windows

### Advanced Analytics -- Flow Metrics & Governance (8)

- `jira_rate_limit_status` — Return the current rate limiter bucket status (read-only)
- `jira_burndown_chart` — Fetch sprint burndown data and compute burndown health metrics
- `jira_cfd_analysis` — Fetch cumulative flow diagram data and apply Little's Law analysis
- `jira_cycle_time_analysis` — Compute cycle time distribution for issues resolved in a sprint
- `jira_throughput_forecast` — Forecast future sprint throughput using a Poisson model
- `jira_automation_analyzer` — Analyze Jira automation rule queue stability and DAG cycle safety
- `jira_tco_analysis` — Compute Total Cost of Ownership and NPV comparison for Jira licensing tiers
- `jira_nasscom_mapping` — Map Jira sprint data to NASSCOM AgileX L1-L5 maturity dimensions

---

## Shared Utilities (in this repo)

- `base/` — Shared MCP infrastructure package (response builder, decorators, persistence, clients)
- `agile_client.py` — Jira Software Agile REST API client (/rest/agile/1.0/); mirrors
                       server.py _request() interface; zero dependency on scrum_calculator.py
- `scrum_calculator.py` — Pure statistical computation for Scrum tools; no network I/O;
                           stdlib only (random, statistics, math, datetime); all functions
                           are stateless pure functions; independently testable without mocks
- `mcp_errors.py` — Structured error response helpers
- `input_validator.py` — Null-byte strip, length limits, prompt injection detection
- `rate_limiter.py` — Token bucket rate limiter (enable via ENABLE_RATE_LIMITING=1)
- `idempotency.py` — Atomic (O_CREAT|O_EXCL) idempotency memo backing the optional
                       `idempotency_key` parameter on non-idempotent create/trigger tools

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
+-- server.py           # Main FastMCP server (entry point, 41 tools)
+-- agile_client.py     # NEW: Jira Agile REST API client (/rest/agile/1.0/)
+-- scrum_calculator.py # NEW: Pure statistical computation (no network I/O)
+-- base/               # Shared base package (response, decorators, persistence, clients)
+-- mcp_errors.py       # Error helpers
+-- input_validator.py  # Input validation
+-- rate_limiter.py     # Rate limiting
+-- docs/
|       architecture-blueprint.md   # Internal architecture blueprint
|       context-delivery-plan.md    # Internal orchestration artifact
|       jql-library.md              # 25+ JQL queries + Agile API endpoint reference
|       automation-rules.md         # 5 Jira automation rules with DAG cycle checks
|       sprint-dashboard.md         # 7 dashboard widget specifications
|       ceremony-scripts.md         # Facilitator scripts for 5 Scrum ceremonies
+-- tests/
|       __init__.py
|       fixtures/
|           boards_response.json
|           sprints_response.json
|           sprint_issues_response.json
|           velocity_response.json
|           sprint_detail_response.json
|       test_agile_client.py
|       test_scrum_calculator.py
|       test_tools_integration.py
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

**Last Updated:** 2026-05-28
