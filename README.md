# mcp-jira-api

A FastMCP server providing **Jira Api** capabilities for Claude Code workflows.

---

## Overview

Jira integration supporting both Cloud (v3, ADF document format) and Server/Data Center (v2, plain text). Creates, searches, transitions, and links issues. Automatically wraps Cloud comments in ADF document format. JQL-powered issue search.

---

## Tools

| Tool | Description |
|------|-------------|
| `jira_create_issue` | Create a Jira issue (project, type, summary, description, priority) |
| `jira_get_issue` | Get full issue details by key (PROJ-123) |
| `jira_search_issues` | JQL search with field projection and pagination |
| `jira_transition_issue` | Transition issue to new status (To Do/In Progress/Done) |
| `jira_add_comment` | Add a comment (auto ADF-wrapped for Cloud) |
| `jira_link_pr` | Link a pull request URL to an issue as a remote link |
| `jira_list_projects` | List all accessible Jira projects |
| `jira_get_transitions` | Get available transitions for an issue |
| `jira_update_issue` | Update issue fields (summary, description, assignee, labels) |
| `jira_health_check` | Verify Jira URL, credentials, and API version |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/techdeveloper-org/mcp-jira-api.git
cd mcp-jira-api
```

### 2. Install dependencies

```bash
pip install mcp fastmcp
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

---

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | Jira server URL (required) |
| `JIRA_EMAIL` | Jira account email (for Cloud Basic auth) |
| `JIRA_API_TOKEN` | Jira API token (Cloud) or password (Server) |
| `JIRA_DEFAULT_PROJECT` | Default project key (optional) |

---

## Usage in Claude Code

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "jira-api": {
      "command": "python",
      "args": [
        "/path/to/mcp-jira-api/server.py"
      ],
      "env": {}
    }
  }
}
```

---

## Benefits

- Cloud + Server support with automatic API version detection
- ADF auto-wrapping means plain text comments work on Cloud without format errors
- PR linking creates bi-directional traceability (Jira issue <-> GitHub PR)
- Full lifecycle: create -> in progress -> in review -> done

---

## Requirements

- Python 3.8+
- `mcp fastmcp`
- See `requirements.txt` for pinned versions

---

## Project Context

This MCP server is part of the **Claude Workflow Engine** ecosystem — a LangGraph-based
orchestration pipeline for automating Claude Code development workflows.

Related repos:
- [`claude-workflow-engine`](https://github.com/techdeveloper-org/claude-workflow-engine) — Main pipeline
- [`mcp-base`](https://github.com/techdeveloper-org/mcp-base) — Shared base utilities used by all MCP servers

---

## License

Private — techdeveloper-org
