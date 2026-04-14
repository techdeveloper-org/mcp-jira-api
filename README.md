# mcp-jira-api

![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Part of claude-workflow-engine](https://img.shields.io/badge/part%20of-claude--workflow--engine-orange)

Jira MCP server for [Claude Workflow Engine](https://github.com/techdeveloper-org/claude-workflow-engine). Provides full Jira Cloud and Jira Server/Data Center integration — create and transition issues, search with JQL, add comments, link GitHub PRs, and manage the complete issue lifecycle directly from Claude Code. Supports Jira Cloud REST API v3 with Atlassian Document Format (ADF) and Jira Server/Data Center REST API v2 with plain text, all over stdio transport using Python stdlib only (no external HTTP dependencies).

---

## Features

- **Jira Cloud support** — REST API v3, ADF-formatted descriptions and comments, email + API token authentication
- **Jira Server / Data Center support** — REST API v2, plain text bodies, username + password or Personal Access Token (PAT) via Bearer auth
- **10 MCP tools** covering the full issue lifecycle: create, read, search, transition, comment, update, link PR, list projects, health check
- **JQL search** — query issues with full Jira Query Language support, configurable field selection and pagination
- **PR linking** — attach GitHub pull request URLs to Jira issues as remote links
- **Transition by name** — transition issues using human-readable status names (e.g., "In Progress", "Done") without needing numeric transition IDs
- **ADF auto-detection** — automatically selects ADF (Cloud v3) or plain text (Server v2) based on `JIRA_API_VERSION`
- **Stdlib-only HTTP** — uses `urllib.request` exclusively; no `requests` or other runtime dependencies
- **Windows-safe encoding** — ASCII-only source code, cp1252 compatible for Windows environments
- **Structured error responses** — Jira API error messages extracted and returned clearly

---

## Tool Reference

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `jira_create_issue` | Create a new Jira issue | `project_key` (required), `summary` (required), `issue_type` (default: "Task"), `description`, `priority`, `assignee`, `labels` |
| `jira_get_issue` | Fetch a single issue by key | `issue_key` (required), `fields` (comma-separated list, optional) |
| `jira_search_issues` | Search issues using JQL | `jql` (required), `max_results` (default: 20), `start_at` (default: 0), `fields` (optional) |
| `jira_get_transitions` | List available transitions for an issue | `issue_key` (required) |
| `jira_transition_issue` | Move an issue to a new status by transition name | `issue_key` (required), `transition_name` (required, e.g., "In Progress"), `comment` (optional) |
| `jira_add_comment` | Add a comment to an issue | `issue_key` (required), `body` (required) |
| `jira_link_pr` | Attach a GitHub PR URL as a remote link | `issue_key` (required), `pr_url` (required), `pr_title` (optional), `pr_number` (optional) |
| `jira_list_projects` | List accessible Jira projects | `max_results` (default: 50), `project_type` (optional, e.g., "software") |
| `jira_update_issue` | Update fields on an existing issue | `issue_key` (required), `summary`, `description`, `priority`, `assignee`, `labels`, `status_comment` (all optional) |
| `jira_health_check` | Verify connectivity and credentials | _(no parameters)_ |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/techdeveloper-org/mcp-jira-api.git
cd mcp-jira-api
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

The server uses Python stdlib for HTTP (`urllib.request`). The primary dependency is the `mcp` package (FastMCP framework):

```
mcp>=1.0.0
```

### 3. Configure in Claude Code

Add the server to your `~/.claude/settings.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "jira-api": {
      "command": "python",
      "args": ["/path/to/mcp-jira-api/server.py"],
      "env": {
        "JIRA_URL": "https://your-org.atlassian.net",
        "JIRA_USER": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token",
        "JIRA_API_VERSION": "3",
        "JIRA_AUTH_METHOD": "basic"
      }
    }
  }
}
```

---

## Configuration

All configuration is provided via environment variables. The server reads these at tool call time, so changes take effect without restarting Claude Code.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JIRA_URL` | Yes | — | Base URL of your Jira instance, e.g., `https://company.atlassian.net` (Cloud) or `https://jira.company.com` (Server). Trailing slash is stripped automatically. |
| `JIRA_USER` | Yes | — | Email address for Jira Cloud, or username for Jira Server. |
| `JIRA_API_TOKEN` | Yes | — | API token for Jira Cloud (generated at [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens)), or Personal Access Token / password for Jira Server. |
| `JIRA_API_VERSION` | No | `3` | Set to `3` for Jira Cloud (ADF format) or `2` for Jira Server/Data Center (plain text). |
| `JIRA_AUTH_METHOD` | No | `basic` | Authentication method: `basic` sends `Basic base64(user:token)`, `bearer` sends `Bearer {token}` (for PAT on Jira Server). |
| `ENABLE_JIRA` | No | `0` | Pipeline integration flag. Set to `1` to activate Jira lifecycle steps (8/9/10/11/12) in the Claude Workflow Engine pipeline. |

### Obtaining a Jira Cloud API Token

1. Log in to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Copy the token and set it as `JIRA_API_TOKEN`
4. Set `JIRA_USER` to the email address associated with your Atlassian account

### Obtaining a Jira Server PAT

1. Log in to your Jira Server instance
2. Navigate to **Profile > Personal Access Tokens**
3. Create a new token and copy it
4. Set `JIRA_API_TOKEN` to the token value and `JIRA_AUTH_METHOD` to `bearer`

---

## Usage Examples

### Create an issue

```
Create a Jira issue in project PROJ for the login bug we just found.
Summary: "Login fails with SSO when session expires"
Type: Bug, Priority: High
```

The `jira_create_issue` tool is called with:

```
project_key: "PROJ"
summary: "Login fails with SSO when session expires"
issue_type: "Bug"
description: "Users are unable to log in via SSO after their session expires. The error page shows a 401 response."
priority: "High"
labels: ["authentication", "sso"]
```

Returns the created issue key (e.g., `PROJ-142`) and a direct URL to the issue.

---

### Search issues with JQL

```
Find all open bugs assigned to me in the PROJ project created this week.
```

The `jira_search_issues` tool is called with:

```
jql: "project = PROJ AND issuetype = Bug AND status != Done AND assignee = currentUser() AND created >= startOfWeek()"
max_results: 20
fields: "summary,status,priority,assignee,created"
```

Returns a list of matching issues with the requested fields.

---

### Transition an issue to In Progress

```
Mark PROJ-142 as In Progress now that I am starting implementation.
```

The `jira_transition_issue` tool is called with:

```
issue_key: "PROJ-142"
transition_name: "In Progress"
comment: "Starting implementation. Branch: feature/PROJ-142-login-sso-fix"
```

The tool fetches available transitions for the issue, finds the one matching "In Progress" (case-insensitive), and executes the transition. The optional comment is posted to the issue.

---

### Link a GitHub PR to a Jira issue

```
Link the PR https://github.com/my-org/my-repo/pull/87 to PROJ-142.
```

The `jira_link_pr` tool is called with:

```
issue_key: "PROJ-142"
pr_url: "https://github.com/my-org/my-repo/pull/87"
pr_title: "Fix SSO login failure on session expiry"
pr_number: 87
```

Creates a remote link on the Jira issue pointing to the GitHub PR. The link appears in the issue's **Development** or **Links** panel depending on your Jira configuration.

---

## Pipeline Integration (Claude Workflow Engine)

When `ENABLE_JIRA=1`, the Claude Workflow Engine pipeline manages the full Jira issue lifecycle across Steps 8 through 12. Each pipeline step performs a specific Jira action:

| Pipeline Step | Action | Jira Tool Used | Effect |
|---------------|--------|----------------|--------|
| Step 8 — Issue Creation | Create Jira issue linked to GitHub Issue | `jira_create_issue` | Jira issue created with GitHub Issue URL in description; Jira key stored in pipeline state for branch naming |
| Step 9 — Branch Creation | Name branch from Jira key | _(state read)_ | Branch named `feature/PROJ-123` using the Jira issue key from Step 8 |
| Step 10 — Implementation | Transition to In Progress | `jira_transition_issue`, `jira_add_comment` | Issue moved to "In Progress"; comment posted with implementation start timestamp |
| Step 11 — PR + Code Review | Link PR, transition to In Review | `jira_link_pr`, `jira_transition_issue` | GitHub PR URL attached as remote link; issue transitioned to "In Review" |
| Step 11 — Post-Merge | Post merge comment | `jira_add_comment` | Comment added with merged PR number and branch name |
| Step 12 — Issue Closure | Transition to Done | `jira_transition_issue`, `jira_add_comment` | Issue closed with "Done" transition; implementation summary comment posted |

To enable the full lifecycle:

```bash
ENABLE_JIRA=1 python scripts/3-level-flow.py --task "your task"
```

The pipeline stores the Jira issue key in `FlowState` after Step 8 and threads it through all subsequent steps automatically.

---

## Jira Cloud vs. Jira Server / Data Center

| Capability | Jira Cloud | Jira Server / Data Center |
|------------|------------|--------------------------|
| REST API version | v3 | v2 |
| Description format | ADF (Atlassian Document Format) | Plain text / wiki markup |
| Comment format | ADF | Plain text |
| Authentication | `Basic base64(email:api_token)` | `Basic base64(user:password)` or `Bearer {PAT}` |
| `JIRA_API_VERSION` | `3` (default) | `2` |
| `JIRA_AUTH_METHOD` | `basic` (default) | `basic` or `bearer` |
| `JIRA_USER` | Email address | Username |
| `JIRA_API_TOKEN` | API token from id.atlassian.com | Password or Personal Access Token |
| Remote links (`jira_link_pr`) | Supported via `/rest/api/3/issue/{key}/remotelink` | Supported via `/rest/api/2/issue/{key}/remotelink` |

The server auto-selects ADF or plain text based on `JIRA_API_VERSION`. No code changes are needed when switching between Cloud and Server — only environment variable changes are required.

---

## Project Structure

```
mcp-jira-api/
+-- server.py           # MCP server entry point (10 tools, FastMCP, urllib.request)
+-- base/               # Shared base package (MCPResponse, @mcp_tool_handler, AtomicJsonStore)
|   +-- decorators.py   # @mcp_tool_handler decorator for uniform error handling
+-- input_validator.py  # Input validation utilities
+-- mcp_errors.py       # Structured error type definitions
+-- rate_limiter.py     # Token bucket rate limiter
+-- requirements.txt    # Runtime dependencies (mcp>=1.0.0)
+-- README.md
```

The `base/` directory contains the shared library used across all 13 MCP servers in the Claude Workflow Engine ecosystem. It provides the `@mcp_tool_handler` decorator (uniform error wrapping and response formatting) and `MCPResponse` builder.

---

## Part of Claude Workflow Engine

This server is one of 13 MCP servers that power the [Claude Workflow Engine](https://github.com/techdeveloper-org/claude-workflow-engine), a LangGraph-based orchestration pipeline for automating end-to-end Claude Code development workflows.

| Server | Tools | Purpose |
|--------|-------|---------|
| [mcp-session-mgr](https://github.com/techdeveloper-org/mcp-session-mgr) | 14 | Session lifecycle |
| [mcp-git-ops](https://github.com/techdeveloper-org/mcp-git-ops) | 14 | Git operations |
| [mcp-github-api](https://github.com/techdeveloper-org/mcp-github-api) | 12 | GitHub PR and issue management |
| [mcp-policy-enforcement](https://github.com/techdeveloper-org/mcp-policy-enforcement) | 11 | Policy compliance |
| [mcp-token-optimizer](https://github.com/techdeveloper-org/mcp-token-optimizer) | 10 | Token reduction (60-85% savings) |
| [mcp-pre-tool-gate](https://github.com/techdeveloper-org/mcp-pre-tool-gate) | 13 | Pre-tool validation |
| [mcp-post-tool-tracker](https://github.com/techdeveloper-org/mcp-post-tool-tracker) | 6 | Post-tool tracking |
| [mcp-standards-loader](https://github.com/techdeveloper-org/mcp-standards-loader) | 7 | Standards hot-reload |
| [mcp-uml-diagram](https://github.com/techdeveloper-org/mcp-uml-diagram) | 15 | UML diagram generation |
| [mcp-drawio-diagram](https://github.com/techdeveloper-org/mcp-drawio-diagram) | 5 | Draw.io editable diagrams |
| **mcp-jira-api** | **10** | **Jira issue lifecycle (this repo)** |
| [mcp-jenkins-ci](https://github.com/techdeveloper-org/mcp-jenkins-ci) | 10 | Jenkins CI/CD |
| [mcp-figma](https://github.com/techdeveloper-org/mcp-figma) | 10 | Figma design-to-code |

---

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository and create a feature branch from `main`
2. Keep all Python source files ASCII-only (cp1252 safe for Windows)
3. Do not add external HTTP dependencies — use `urllib.request` from stdlib
4. Add or update tests for any new tool or changed behavior
5. Run the existing test suite before submitting a pull request:

   ```bash
   pytest tests/
   ```

6. Follow the existing code style: PEP 8, type hints on all function signatures, docstrings on all public functions
7. Open a pull request with a clear description of the change and the problem it solves

For bugs or feature requests, open an issue on GitHub.

---

## License

MIT License. See [LICENSE](LICENSE) for full text.

Copyright (c) 2024 techdeveloper-org
