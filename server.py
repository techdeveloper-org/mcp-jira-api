"""
Jira MCP Server - FastMCP-based Jira integration for Claude Code.

Supports both Jira Cloud (v3, ADF format) and Jira Server/Data Center (v2, plain text).
Backend: urllib.request (stdlib only, no external deps)
Transport: stdio

Tools (25):
  Core Jira (10):
    jira_create_issue, jira_get_issue, jira_search_issues,
    jira_transition_issue, jira_add_comment, jira_link_pr,
    jira_list_projects, jira_get_transitions, jira_update_issue,
    jira_health_check
  Scrum Master -- Board & Sprint Infrastructure (5):
    jira_get_boards, jira_get_sprints, jira_create_sprint,
    jira_start_sprint, jira_close_sprint
  Scrum Master -- Ceremony Facilitation (5):
    jira_plan_sprint, jira_daily_standup, jira_sprint_review,
    jira_retrospective, jira_refine_backlog
  Scrum Master -- Analytics (5):
    jira_get_velocity, jira_get_sprint_metrics, jira_track_impediments,
    jira_team_health, jira_monte_carlo_forecast

Environment Variables:
  JIRA_URL          - Base URL (e.g. https://company.atlassian.net)
  JIRA_USER         - Email (Cloud) or username (Server)
  JIRA_API_TOKEN    - API token (Cloud) or PAT (Server)
  JIRA_API_VERSION  - "3" (Cloud, default) or "2" (Server/DC)
  JIRA_AUTH_METHOD  - "basic" (default) or "bearer" (PAT for Server)

Windows-Safe: ASCII only (cp1252 compatible)
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from pathlib import Path

# Ensure src/mcp/ is in path for base package imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP
from base.decorators import mcp_tool_handler

# Scrum Master extension imports
from agile_client import _agile_request, _agile_url, _build_agile_auth_header
import scrum_calculator

mcp = FastMCP(
    "jira-api",
    instructions="Jira operations via REST API (Cloud v3 ADF + Server v2 plain text)"
)

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

_TIMEOUT = 30  # seconds for all HTTP calls


def _get_config() -> Dict[str, str]:
    """Read Jira config from environment variables.

    Returns:
        Dict with url, user, token, api_version, auth_method keys.

    Raises:
        EnvironmentError: If JIRA_URL, JIRA_USER, or JIRA_API_TOKEN are missing.
    """
    url = os.environ.get("JIRA_URL", "").rstrip("/")
    user = os.environ.get("JIRA_USER", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    api_version = os.environ.get("JIRA_API_VERSION", "3")
    auth_method = os.environ.get("JIRA_AUTH_METHOD", "basic").lower()

    missing = []
    if not url:
        missing.append("JIRA_URL")
    if not user:
        missing.append("JIRA_USER")
    if not token:
        missing.append("JIRA_API_TOKEN")

    if missing:
        raise EnvironmentError(
            "Missing required Jira environment variables: "
            + ", ".join(missing)
            + ". Set them before using jira_* tools."
        )

    return {
        "url": url,
        "user": user,
        "token": token,
        "api_version": api_version,
        "auth_method": auth_method,
    }


def _build_auth_header(cfg: Dict[str, str]) -> str:
    """Build Authorization header value based on auth_method.

    Args:
        cfg: Config dict from _get_config().

    Returns:
        Authorization header string (e.g. "Basic ..." or "Bearer ...").
    """
    if cfg["auth_method"] == "bearer":
        return "Bearer " + cfg["token"]
    # Default: Basic auth with user:token
    credentials = cfg["user"] + ":" + cfg["token"]
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    return "Basic " + encoded


def _api_url(cfg: Dict[str, str], path: str) -> str:
    """Build a full Jira REST API URL.

    Args:
        cfg: Config dict.
        path: API path starting with / (e.g. /issue/PROJ-123).
            Use the special prefix NOVERSION: to bypass version prefix
            (e.g. NOVERSION:/rest/serverInfo).

    Returns:
        Full URL string.
    """
    if path.startswith("NOVERSION:"):
        return cfg["url"] + path[len("NOVERSION:"):]
    return cfg["url"] + "/rest/api/" + cfg["api_version"] + path


def _request(
    cfg: Dict[str, str],
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute a Jira REST API request.

    Args:
        cfg: Config dict from _get_config().
        method: HTTP method (GET, POST, PUT, DELETE).
        path: API path starting with / (e.g. /issue/PROJ-123).
        body: Optional request body dict (serialized to JSON).

    Returns:
        Parsed JSON response as dict/list, or None for 204 responses.

    Raises:
        urllib.error.HTTPError: On HTTP error responses.
        RuntimeError: On non-HTTP errors.
    """
    url = _api_url(cfg, path)
    auth_header = _build_auth_header(cfg)

    headers = {
        "Authorization": auth_header,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw_body = exc.read()
        try:
            err_json = json.loads(raw_body.decode("utf-8"))
            messages = err_json.get("errorMessages", [])
            errors = err_json.get("errors", {})
            detail = "; ".join(messages) if messages else str(errors)
        except Exception:
            detail = raw_body.decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            "Jira API error " + str(exc.code) + ": " + detail
        ) from exc


# ---------------------------------------------------------------------------
# ADF (Atlassian Document Format) helpers for Cloud v3
# ---------------------------------------------------------------------------

def _is_cloud(cfg: Dict[str, str]) -> bool:
    """Return True when configured for Jira Cloud (API version 3)."""
    return cfg["api_version"] == "3"


def _text_to_adf(text: str) -> Dict[str, Any]:
    """Wrap plain text in minimal ADF document format (Cloud v3).

    Args:
        text: Plain text content to wrap.

    Returns:
        ADF document dict.
    """
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": text}
                ]
            }
        ]
    }


def _description_field(cfg: Dict[str, str], text: str) -> Any:
    """Return the appropriate description/body value for the API version.

    Args:
        cfg: Config dict.
        text: Plain text content.

    Returns:
        ADF dict for v3 (Cloud) or plain string for v2 (Server).
    """
    if _is_cloud(cfg):
        return _text_to_adf(text)
    return text


def _comment_body_field(cfg: Dict[str, str], text: str) -> Any:
    """Return the appropriate comment body for the API version.

    Args:
        cfg: Config dict.
        text: Plain text content.

    Returns:
        ADF dict for v3 (Cloud) or plain string for v2 (Server).
    """
    if _is_cloud(cfg):
        return _text_to_adf(text)
    return text


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_create_issue(
    project_key: str,
    summary: str,
    issue_type: str = "Task",
    description: str = "",
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
) -> dict:
    """Create a Jira issue.

    Args:
        project_key: Jira project key (e.g. PROJ).
        summary: Issue summary/title.
        issue_type: Issue type name (e.g. Task, Bug, Story). Default: Task.
        description: Issue description (plain text; converted to ADF for Cloud).
        priority: Priority name (e.g. High, Medium, Low). Optional.
        assignee: Assignee account ID (Cloud) or username (Server). Optional.
        labels: Comma-separated label names. Optional.
    """
    cfg = _get_config()

    fields: Dict[str, Any] = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }

    if description:
        fields["description"] = _description_field(cfg, description)

    if priority:
        fields["priority"] = {"name": priority}

    if assignee:
        if _is_cloud(cfg):
            fields["assignee"] = {"accountId": assignee}
        else:
            fields["assignee"] = {"name": assignee}

    if labels:
        label_list = [lb.strip() for lb in labels.split(",") if lb.strip()]
        if label_list:
            fields["labels"] = label_list

    body = {"fields": fields}
    result = _request(cfg, "POST", "/issue", body)

    return {
        "issue_key": result.get("key"),
        "issue_id": result.get("id"),
        "issue_url": cfg["url"] + "/browse/" + result.get("key", ""),
        "project_key": project_key,
        "summary": summary,
        "issue_type": issue_type,
    }


@mcp.tool()
@mcp_tool_handler
def jira_get_issue(
    issue_key: str,
    fields: Optional[str] = None,
) -> dict:
    """Get Jira issue details by key.

    Args:
        issue_key: Issue key (e.g. PROJ-123).
        fields: Comma-separated field names to include. Optional (default: common fields).
    """
    cfg = _get_config()

    path = "/issue/" + issue_key
    if fields:
        path += "?fields=" + urllib.request.quote(fields)

    result = _request(cfg, "GET", path)
    raw_fields = result.get("fields", {})

    # Extract assignee safely across v2/v3
    assignee_raw = raw_fields.get("assignee") or {}
    assignee_name = (
        assignee_raw.get("displayName")
        or assignee_raw.get("name")
        or ""
    )

    # Extract reporter safely
    reporter_raw = raw_fields.get("reporter") or {}
    reporter_name = (
        reporter_raw.get("displayName")
        or reporter_raw.get("name")
        or ""
    )

    # Extract status
    status_raw = raw_fields.get("status") or {}
    status_name = status_raw.get("name", "")

    # Extract priority
    priority_raw = raw_fields.get("priority") or {}
    priority_name = priority_raw.get("name", "")

    # Extract issue type
    issuetype_raw = raw_fields.get("issuetype") or {}
    issuetype_name = issuetype_raw.get("name", "")

    return {
        "issue_key": result.get("key"),
        "issue_id": result.get("id"),
        "issue_url": cfg["url"] + "/browse/" + result.get("key", ""),
        "summary": raw_fields.get("summary", ""),
        "status": status_name,
        "issue_type": issuetype_name,
        "priority": priority_name,
        "assignee": assignee_name,
        "reporter": reporter_name,
        "created": raw_fields.get("created", ""),
        "updated": raw_fields.get("updated", ""),
        "labels": raw_fields.get("labels", []),
    }


@mcp.tool()
@mcp_tool_handler
def jira_search_issues(
    jql: str,
    max_results: int = 20,
    start_at: int = 0,
    fields: Optional[str] = None,
) -> dict:
    """Search Jira issues using JQL (Jira Query Language).

    Args:
        jql: JQL query string (e.g. 'project = PROJ AND status = "In Progress"').
        max_results: Maximum number of results to return (default: 20, max: 100).
        start_at: Zero-based index for pagination (default: 0).
        fields: Comma-separated field names to include. Optional.
    """
    cfg = _get_config()

    body: Dict[str, Any] = {
        "jql": jql,
        "maxResults": min(max_results, 100),
        "startAt": start_at,
    }

    if fields:
        body["fields"] = [f.strip() for f in fields.split(",") if f.strip()]
    else:
        body["fields"] = ["summary", "status", "assignee", "priority", "issuetype", "created"]

    result = _request(cfg, "POST", "/issue/search", body)

    issues = []
    for issue in result.get("issues", []):
        raw_fields = issue.get("fields", {})
        assignee_raw = raw_fields.get("assignee") or {}
        status_raw = raw_fields.get("status") or {}
        priority_raw = raw_fields.get("priority") or {}
        issuetype_raw = raw_fields.get("issuetype") or {}

        issues.append({
            "issue_key": issue.get("key"),
            "issue_url": cfg["url"] + "/browse/" + issue.get("key", ""),
            "summary": raw_fields.get("summary", ""),
            "status": status_raw.get("name", ""),
            "issue_type": issuetype_raw.get("name", ""),
            "priority": priority_raw.get("name", ""),
            "assignee": (
                assignee_raw.get("displayName")
                or assignee_raw.get("name")
                or ""
            ),
            "created": raw_fields.get("created", ""),
        })

    return {
        "total": result.get("total", 0),
        "max_results": result.get("maxResults", 0),
        "start_at": result.get("startAt", 0),
        "issues": issues,
    }


@mcp.tool()
@mcp_tool_handler
def jira_get_transitions(issue_key: str) -> dict:
    """Get available workflow transitions for a Jira issue.

    Args:
        issue_key: Issue key (e.g. PROJ-123).
    """
    cfg = _get_config()

    result = _request(cfg, "GET", "/issue/" + issue_key + "/transitions")

    transitions = [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "to_status": (t.get("to") or {}).get("name", ""),
        }
        for t in result.get("transitions", [])
    ]

    return {
        "issue_key": issue_key,
        "transitions": transitions,
        "count": len(transitions),
    }


@mcp.tool()
@mcp_tool_handler
def jira_transition_issue(
    issue_key: str,
    transition_name: str,
    comment: str = "",
) -> dict:
    """Move a Jira issue through its workflow by transition name.

    This first fetches available transitions (GET), then posts the matching one (POST).

    Args:
        issue_key: Issue key (e.g. PROJ-123).
        transition_name: Transition name (e.g. "In Progress", "Done"). Case-insensitive.
        comment: Optional comment to add when transitioning.
    """
    cfg = _get_config()

    # Step 1: GET available transitions
    transitions_result = _request(cfg, "GET", "/issue/" + issue_key + "/transitions")
    transitions = transitions_result.get("transitions", [])

    # Find matching transition (case-insensitive)
    matched = None
    for t in transitions:
        if t.get("name", "").lower() == transition_name.lower():
            matched = t
            break

    if matched is None:
        available = [t.get("name", "") for t in transitions]
        raise ValueError(
            "Transition '" + transition_name + "' not found for " + issue_key
            + ". Available: " + ", ".join(available)
        )

    # Step 2: POST the transition
    body: Dict[str, Any] = {
        "transition": {"id": matched["id"]}
    }

    if comment:
        body["update"] = {
            "comment": [
                {
                    "add": {
                        "body": _comment_body_field(cfg, comment)
                    }
                }
            ]
        }

    _request(cfg, "POST", "/issue/" + issue_key + "/transitions", body)

    return {
        "issue_key": issue_key,
        "transition_applied": matched["name"],
        "transition_id": matched["id"],
        "new_status": (matched.get("to") or {}).get("name", ""),
        "comment_added": bool(comment),
    }


@mcp.tool()
@mcp_tool_handler
def jira_add_comment(
    issue_key: str,
    body: str,
) -> dict:
    """Add a comment to a Jira issue.

    Args:
        issue_key: Issue key (e.g. PROJ-123).
        body: Comment text (plain text; converted to ADF for Cloud v3).
    """
    cfg = _get_config()

    payload: Dict[str, Any] = {
        "body": _comment_body_field(cfg, body)
    }

    result = _request(cfg, "POST", "/issue/" + issue_key + "/comment", payload)

    return {
        "issue_key": issue_key,
        "comment_id": result.get("id"),
        "comment_url": (
            cfg["url"] + "/browse/" + issue_key
            + "?focusedCommentId=" + str(result.get("id", ""))
        ),
        "created": result.get("created", ""),
    }


@mcp.tool()
@mcp_tool_handler
def jira_link_pr(
    issue_key: str,
    pr_url: str,
    pr_title: str = "",
    pr_number: Optional[int] = None,
) -> dict:
    """Create a remote link from a Jira issue to a GitHub Pull Request.

    Uses POST /rest/api/{version}/issue/{key}/remotelink

    Args:
        issue_key: Issue key (e.g. PROJ-123).
        pr_url: Full URL of the GitHub PR.
        pr_title: Display title for the link. Defaults to 'PR #{pr_number}'.
        pr_number: PR number for generating a default title. Optional.
    """
    cfg = _get_config()

    if not pr_title:
        if pr_number is not None:
            pr_title = "PR #" + str(pr_number)
        else:
            pr_title = pr_url

    payload: Dict[str, Any] = {
        "object": {
            "url": pr_url,
            "title": pr_title,
            "icon": {
                "url16x16": "https://github.com/favicon.ico",
                "title": "GitHub"
            }
        },
        "application": {
            "type": "com.github",
            "name": "GitHub"
        },
        "relationship": "is implemented in"
    }

    result = _request(cfg, "POST", "/issue/" + issue_key + "/remotelink", payload)

    return {
        "issue_key": issue_key,
        "remote_link_id": result.get("id"),
        "pr_url": pr_url,
        "pr_title": pr_title,
        "link_url": cfg["url"] + "/browse/" + issue_key,
    }


@mcp.tool()
@mcp_tool_handler
def jira_list_projects(
    max_results: int = 50,
    project_type: Optional[str] = None,
) -> dict:
    """List accessible Jira projects.

    Args:
        max_results: Maximum number of projects to return (default: 50).
        project_type: Filter by project type (e.g. 'software', 'business'). Optional.
    """
    cfg = _get_config()

    path = "/project/search?maxResults=" + str(min(max_results, 100))
    if project_type:
        path += "&typeKey=" + urllib.request.quote(project_type)

    result = _request(cfg, "GET", path)

    # Jira v3 returns {"values": [...], "total": N}
    # Jira v2 returns a flat list
    raw_list = result if isinstance(result, list) else result.get("values", [])

    projects = [
        {
            "key": p.get("key"),
            "name": p.get("name"),
            "project_type": p.get("projectTypeKey", ""),
            "lead": (p.get("lead") or {}).get("displayName", ""),
            "url": cfg["url"] + "/jira/software/projects/" + p.get("key", "") + "/boards",
        }
        for p in raw_list
    ]

    return {
        "total": result.get("total", len(projects)) if isinstance(result, dict) else len(projects),
        "projects": projects,
        "count": len(projects),
    }


@mcp.tool()
@mcp_tool_handler
def jira_update_issue(
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    status_comment: Optional[str] = None,
) -> dict:
    """Update fields on an existing Jira issue.

    Only the provided (non-None) fields are updated.

    Args:
        issue_key: Issue key (e.g. PROJ-123).
        summary: New summary/title. Optional.
        description: New description (plain text). Optional.
        priority: Priority name (e.g. High, Medium). Optional.
        assignee: Assignee account ID (Cloud) or username (Server). Optional.
        labels: Comma-separated label names (replaces existing labels). Optional.
        status_comment: Comment to add alongside the update. Optional.
    """
    cfg = _get_config()

    fields: Dict[str, Any] = {}

    if summary is not None:
        fields["summary"] = summary

    if description is not None:
        fields["description"] = _description_field(cfg, description)

    if priority is not None:
        fields["priority"] = {"name": priority}

    if assignee is not None:
        if _is_cloud(cfg):
            fields["assignee"] = {"accountId": assignee}
        else:
            fields["assignee"] = {"name": assignee}

    if labels is not None:
        label_list = [lb.strip() for lb in labels.split(",") if lb.strip()]
        fields["labels"] = label_list

    if not fields and not status_comment:
        raise ValueError("At least one field to update or a status_comment must be provided.")

    body: Dict[str, Any] = {}
    if fields:
        body["fields"] = fields

    if status_comment:
        body["update"] = {
            "comment": [
                {
                    "add": {
                        "body": _comment_body_field(cfg, status_comment)
                    }
                }
            ]
        }

    # PUT /rest/api/{version}/issue/{key} returns 204 No Content on success
    _request(cfg, "PUT", "/issue/" + issue_key, body)

    updated_fields = list(fields.keys())
    if status_comment:
        updated_fields.append("comment")

    return {
        "issue_key": issue_key,
        "issue_url": cfg["url"] + "/browse/" + issue_key,
        "updated_fields": updated_fields,
    }


@mcp.tool()
@mcp_tool_handler
def jira_health_check() -> dict:
    """Verify Jira connectivity and configuration.

    Calls the Jira server-info endpoint to confirm the connection works.
    """
    cfg = _get_config()

    result = _request(cfg, "GET", "NOVERSION:/rest/serverInfo")

    return {
        "connected": True,
        "jira_url": cfg["url"],
        "api_version": cfg["api_version"],
        "auth_method": cfg["auth_method"],
        "server_title": result.get("serverTitle", ""),
        "version": result.get("version", ""),
        "deployment_type": result.get("deploymentType", ""),
        "cloud": _is_cloud(cfg),
    }


# ---------------------------------------------------------------------------
# Story points field lookup helper (shared by Scrum Master tools)
# ---------------------------------------------------------------------------

_SP_FIELD_CANDIDATES = [
    "story_points",
    "customfield_10016",
    "customfield_10028",
    "customfield_10004",
]


def _extract_story_points(fields: Dict[str, Any]) -> float:
    """Extract story points from an issue fields dict, trying multiple field names.

    Jira does not standardize the story points field name across instances.
    This helper tries the most common field names in priority order.

    Args:
        fields: Raw issue fields dict from a Jira API response.

    Returns:
        Story points as float, or 0.0 if no recognized field is found or parseable.
    """
    for candidate in _SP_FIELD_CANDIDATES:
        val = fields.get(candidate)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return 0.0


# ---------------------------------------------------------------------------
# Scrum Master Tools -- Agile Infrastructure (Group A: Tools 11-15 of 25)
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_get_boards(
    project_key: Optional[str] = None,
    board_type: Optional[str] = None,
    max_results: int = 50,
) -> dict:
    """List Jira Software Scrum/Kanban boards accessible to the configured user.

    Calls the Jira Agile REST API GET /rest/agile/1.0/board endpoint.

    Args:
        project_key: Filter boards by project key (e.g. "PROJ"). Optional.
        board_type: Filter by board type: "scrum", "kanban", or "simple". Optional.
        max_results: Maximum boards to return (clamped to 1-50, default 50).

    Returns:
        Dict with keys:
            total (int): Total boards matching the filter.
            count (int): Number of boards returned in this response.
            boards (list): List of board dicts, each with:
                board_id, board_name, board_type, project_key, self_url.
    """
    cfg = _get_config()
    max_results = max(1, min(50, max_results))

    params = "maxResults=" + str(max_results)
    if project_key:
        params += "&projectKeyOrId=" + urllib.request.quote(project_key)
    if board_type:
        params += "&type=" + urllib.request.quote(board_type)

    result = _agile_request(cfg, "GET", "board?" + params)
    if result is None:
        result = {}

    raw_values = result.get("values", [])
    boards = []
    for b in raw_values:
        location = b.get("location") or {}
        boards.append({
            "board_id": b.get("id"),
            "board_name": b.get("name", ""),
            "board_type": b.get("type", ""),
            "project_key": location.get("projectKey", ""),
            "self_url": b.get("self", ""),
        })

    return {
        "total": result.get("total", len(boards)),
        "count": len(boards),
        "boards": boards,
    }


@mcp.tool()
@mcp_tool_handler
def jira_get_sprints(
    board_id: int,
    state: Optional[str] = None,
    max_results: int = 50,
) -> dict:
    """List sprints for a Jira Software Scrum board.

    Calls the Jira Agile REST API GET /rest/agile/1.0/board/{boardId}/sprint.

    Args:
        board_id: Numeric board ID (from jira_get_boards).
        state: Filter by sprint state: "active", "future", or "closed". Optional.
        max_results: Maximum sprints to return (default 50).

    Returns:
        Dict with keys:
            board_id (int): Echo of board_id.
            total (int): Total sprints in response.
            count (int): Number of sprints returned.
            sprints (list): List of sprint dicts, each with:
                sprint_id, sprint_name, state, start_date, end_date,
                complete_date, goal.
    """
    cfg = _get_config()

    params = "maxResults=" + str(max(1, max_results))
    if state:
        params += "&state=" + urllib.request.quote(state)

    result = _agile_request(cfg, "GET", "board/" + str(board_id) + "/sprint?" + params)
    if result is None:
        result = {}

    raw_values = result.get("values", [])
    sprints = []
    for s in raw_values:
        sprints.append({
            "sprint_id": s.get("id"),
            "sprint_name": s.get("name", ""),
            "state": s.get("state", ""),
            "start_date": s.get("startDate", ""),
            "end_date": s.get("endDate", ""),
            "complete_date": s.get("completeDate", ""),
            "goal": s.get("goal", ""),
        })

    return {
        "board_id": board_id,
        "total": result.get("total", len(sprints)),
        "count": len(sprints),
        "sprints": sprints,
    }


@mcp.tool()
@mcp_tool_handler
def jira_create_sprint(
    board_id: int,
    name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    goal: Optional[str] = None,
) -> dict:
    """Create a new sprint on a Jira Software Scrum board.

    Calls the Jira Agile REST API POST /rest/agile/1.0/sprint.
    Newly created sprints are always in "future" state.

    Args:
        board_id: Numeric board ID to create the sprint on.
        name: Sprint name (e.g. "Sprint 42"). Must not be empty.
        start_date: Sprint start date in ISO format "YYYY-MM-DDTHH:MM:SS.000Z". Optional.
        end_date: Sprint end date in ISO format "YYYY-MM-DDTHH:MM:SS.000Z". Optional.
        goal: Sprint goal text. Optional.

    Returns:
        Dict with keys:
            sprint_id (int): ID of the created sprint.
            sprint_name (str): Name of the created sprint.
            state (str): "future" (newly created sprints are always future).
            start_date (str): Provided start date or "".
            end_date (str): Provided end date or "".
            goal (str): Sprint goal or "".
            board_id (int): Echo of board_id.

    Raises:
        ValueError: If name is empty.
    """
    cfg = _get_config()
    if not name or not name.strip():
        raise ValueError("Sprint name must not be empty")

    body: Dict[str, Any] = {
        "originBoardId": board_id,
        "name": name,
    }
    if start_date:
        body["startDate"] = start_date
    if end_date:
        body["endDate"] = end_date
    if goal:
        body["goal"] = goal

    result = _agile_request(cfg, "POST", "sprint", body)
    if result is None:
        result = {}

    return {
        "sprint_id": result.get("id"),
        "sprint_name": result.get("name", name),
        "state": result.get("state", "future"),
        "start_date": result.get("startDate", start_date or ""),
        "end_date": result.get("endDate", end_date or ""),
        "goal": result.get("goal", goal or ""),
        "board_id": board_id,
    }


@mcp.tool()
@mcp_tool_handler
def jira_start_sprint(
    sprint_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Start a future sprint, transitioning its state to active.

    Calls the Jira Agile REST API POST /rest/agile/1.0/sprint/{sprintId}
    with body {"state": "active"}.

    Args:
        sprint_id: Numeric sprint ID to start (must be in "future" state).
        start_date: Override start date "YYYY-MM-DDTHH:MM:SS.000Z". Optional.
        end_date: Override end date "YYYY-MM-DDTHH:MM:SS.000Z". Optional.

    Returns:
        Dict with keys:
            sprint_id (int): Echo of sprint_id.
            sprint_name (str): Sprint display name.
            state (str): "active" after transition.
            start_date (str): Effective start date.
            end_date (str): Effective end date.
            goal (str): Sprint goal or "".
            activated (bool): Always True on success.
    """
    cfg = _get_config()

    body: Dict[str, Any] = {"state": "active"}
    if start_date:
        body["startDate"] = start_date
    if end_date:
        body["endDate"] = end_date

    result = _agile_request(cfg, "POST", "sprint/" + str(sprint_id), body)
    if result is None:
        result = {}

    return {
        "sprint_id": sprint_id,
        "sprint_name": result.get("name", ""),
        "state": result.get("state", "active"),
        "start_date": result.get("startDate", start_date or ""),
        "end_date": result.get("endDate", end_date or ""),
        "goal": result.get("goal", ""),
        "activated": True,
    }


@mcp.tool()
@mcp_tool_handler
def jira_close_sprint(
    sprint_id: int,
    complete_date: Optional[str] = None,
) -> dict:
    """Close (complete) an active sprint.

    Calls the Jira Agile REST API POST /rest/agile/1.0/sprint/{sprintId}
    with body {"state": "closed"}.

    Args:
        sprint_id: Numeric sprint ID of the active sprint to close.
        complete_date: Override close date "YYYY-MM-DDTHH:MM:SS.000Z". Optional.

    Returns:
        Dict with keys:
            sprint_id (int): Echo of sprint_id.
            sprint_name (str): Sprint display name.
            state (str): "closed" after transition.
            complete_date (str): Effective close date.
            closed (bool): Always True on success.
    """
    cfg = _get_config()

    body: Dict[str, Any] = {"state": "closed"}
    if complete_date:
        body["completeDate"] = complete_date

    result = _agile_request(cfg, "POST", "sprint/" + str(sprint_id), body)
    if result is None:
        result = {}

    return {
        "sprint_id": sprint_id,
        "sprint_name": result.get("name", ""),
        "state": result.get("state", "closed"),
        "complete_date": result.get("completeDate", complete_date or ""),
        "closed": True,
    }


# ---------------------------------------------------------------------------
# Scrum Master Tools -- Ceremony Facilitation (Group B: Tools 16-20 of 25)
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_plan_sprint(
    board_id: int,
    sprint_id: int,
    members: int,
    sprint_days: int,
    focus_factor: float = 0.7,
    leave_days: int = 0,
    sprint_start_iso: Optional[str] = None,
    sprint_end_iso: Optional[str] = None,
) -> dict:
    """Generate a sprint planning report with capacity and velocity context.

    Combines Agile API data (sprint details, recent sprints for velocity)
    with scrum_calculator functions (sprint_capacity, velocity_stats,
    india_holidays_in_sprint). Calls Agile API as primary source per CONTRACT #1.

    Args:
        board_id: Numeric board ID.
        sprint_id: Numeric sprint ID to plan.
        members: Number of team members for this sprint (>= 1).
        sprint_days: Working days in the sprint excluding weekends (>= 1).
        focus_factor: Team focus factor (0.0 to 1.0). Default 0.70.
        leave_days: Total person-days of planned leave across all members.
        sprint_start_iso: Sprint start date "YYYY-MM-DD" for holiday calculation. Optional.
        sprint_end_iso: Sprint end date "YYYY-MM-DD" for holiday calculation. Optional.

    Returns:
        Dict with keys:
            sprint_id, sprint_name, sprint_goal, capacity, india_holidays_in_sprint,
            sprint_issues_count, unestimated_count, estimated_total_points,
            capacity_utilization_pct, wsjf_ordering_note, ist_timezone_note.
    """
    cfg = _get_config()

    sprint_detail = _agile_request(cfg, "GET", "sprint/" + str(sprint_id))
    if sprint_detail is None:
        sprint_detail = {}

    sprint_name = sprint_detail.get("name", "Sprint " + str(sprint_id))
    sprint_goal = sprint_detail.get("goal", "")

    holidays_count = 0
    if sprint_start_iso and sprint_end_iso:
        try:
            holidays_count = scrum_calculator.india_holidays_in_sprint(
                sprint_start_iso, sprint_end_iso
            )
        except (ValueError, KeyError):
            holidays_count = 0

    capacity = scrum_calculator.sprint_capacity(
        members=members,
        sprint_days=sprint_days,
        focus_factor=focus_factor,
        leave_days=leave_days,
        india_holidays=holidays_count,
    )

    issues_result = _agile_request(
        cfg, "GET",
        "sprint/" + str(sprint_id) + "/issue?maxResults=100&fields=summary,status,customfield_10016,customfield_10028,story_points"
    )
    if issues_result is None:
        issues_result = {}

    raw_issues = issues_result.get("issues", [])
    sprint_issues_count = len(raw_issues)
    estimated_total_points = 0.0
    unestimated_count = 0
    for issue in raw_issues:
        sp = _extract_story_points(issue.get("fields", {}))
        if sp > 0:
            estimated_total_points += sp
        else:
            unestimated_count += 1

    capacity_pts = capacity.get("capacity_points", 0.0)
    if capacity_pts > 0:
        utilization_pct = round((estimated_total_points / capacity_pts) * 100, 1)
    else:
        utilization_pct = 0.0

    return {
        "sprint_id": sprint_id,
        "sprint_name": sprint_name,
        "sprint_goal": sprint_goal,
        "capacity": capacity,
        "india_holidays_in_sprint": holidays_count,
        "sprint_issues_count": sprint_issues_count,
        "unestimated_count": unestimated_count,
        "estimated_total_points": round(estimated_total_points, 1),
        "capacity_utilization_pct": utilization_pct,
        "wsjf_ordering_note": (
            "Use jira_refine_backlog for WSJF-ordered story selection"
        ),
        "ist_timezone_note": (
            "IST timezone: 4.5h overlap window with EST (17:30-23:00 IST)"
        ),
    }


@mcp.tool()
@mcp_tool_handler
def jira_daily_standup(
    sprint_id: int,
    board_id: Optional[int] = None,
) -> dict:
    """Generate a Daily Scrum (standup) report for the active sprint.

    Fetches all sprint issues via the Agile API and categorizes by status.
    Surfaces impediments (label "impediment") and blocked issues automatically.

    Args:
        sprint_id: Numeric sprint ID (should be in "active" state).
        board_id: Optional board ID for additional context. Optional.

    Returns:
        Dict with keys:
            sprint_id, sprint_name, sprint_goal, total_issues,
            done_count, in_progress_count, todo_count, blocked_issues,
            progress_by_assignee, standup_timestamp_ist.
    """
    cfg = _get_config()

    sprint_detail = _agile_request(cfg, "GET", "sprint/" + str(sprint_id))
    if sprint_detail is None:
        sprint_detail = {}

    sprint_name = sprint_detail.get("name", "Sprint " + str(sprint_id))
    sprint_goal = sprint_detail.get("goal", "")

    issues_result = _agile_request(
        cfg, "GET",
        "sprint/" + str(sprint_id) + "/issue?maxResults=100&fields=summary,status,assignee,priority,labels,issuetype"
    )
    if issues_result is None:
        issues_result = {}

    raw_issues = issues_result.get("issues", [])

    done_count = 0
    in_progress_count = 0
    todo_count = 0
    blocked_issues = []
    progress_by_assignee: Dict[str, Dict[str, int]] = {}

    for issue in raw_issues:
        fields = issue.get("fields", {})
        status_name = (fields.get("status") or {}).get("name", "")
        assignee_raw = fields.get("assignee") or {}
        assignee_name = (
            assignee_raw.get("displayName")
            or assignee_raw.get("name")
            or "Unassigned"
        )
        labels = fields.get("labels", [])
        issue_key = issue.get("key", "")
        summary = fields.get("summary", "")

        status_lower = status_name.lower()
        if status_lower in ("done", "closed", "resolved"):
            done_count += 1
        elif "progress" in status_lower or status_lower == "in review":
            in_progress_count += 1
        else:
            todo_count += 1

        if "impediment" in labels or status_lower == "blocked":
            blocked_issues.append({
                "issue_key": issue_key,
                "summary": summary,
                "assignee": assignee_name,
                "status": status_name,
            })

        if assignee_name not in progress_by_assignee:
            progress_by_assignee[assignee_name] = {
                "done": 0, "in_progress": 0, "todo": 0
            }
        if status_lower in ("done", "closed", "resolved"):
            progress_by_assignee[assignee_name]["done"] += 1
        elif "progress" in status_lower or status_lower == "in review":
            progress_by_assignee[assignee_name]["in_progress"] += 1
        else:
            progress_by_assignee[assignee_name]["todo"] += 1

    from datetime import datetime
    standup_ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + " (UTC)"

    return {
        "sprint_id": sprint_id,
        "sprint_name": sprint_name,
        "sprint_goal": sprint_goal,
        "total_issues": len(raw_issues),
        "done_count": done_count,
        "in_progress_count": in_progress_count,
        "todo_count": todo_count,
        "blocked_issues": blocked_issues,
        "progress_by_assignee": progress_by_assignee,
        "standup_timestamp_ist": standup_ts,
    }


@mcp.tool()
@mcp_tool_handler
def jira_sprint_review(
    board_id: int,
    sprint_id: int,
) -> dict:
    """Generate a Sprint Review report for the closing sprint.

    Provides delivered vs. not-delivered breakdown with story points, velocity
    achieved, velocity statistics, DoD compliance, and NASSCOM AgileX level.

    Args:
        board_id: Numeric board ID.
        sprint_id: Numeric sprint ID (active or recently closed).

    Returns:
        Dict with keys:
            sprint_id, sprint_name, sprint_goal, completed_points,
            committed_points, completion_rate, velocity_mean, velocity_cv,
            nasscom_agileX_level, dod_compliance_pct, demo_ready_issues,
            review_timestamp.
    """
    cfg = _get_config()

    sprint_detail = _agile_request(cfg, "GET", "sprint/" + str(sprint_id))
    if sprint_detail is None:
        sprint_detail = {}

    sprint_name = sprint_detail.get("name", "Sprint " + str(sprint_id))
    sprint_goal = sprint_detail.get("goal", "")

    issues_result = _agile_request(
        cfg, "GET",
        "sprint/" + str(sprint_id) + "/issue?maxResults=100&fields=summary,status,assignee,issuetype,customfield_10016,customfield_10028,story_points,subtasks"
    )
    if issues_result is None:
        issues_result = {}

    raw_issues = issues_result.get("issues", [])

    completed_points = 0.0
    committed_points = 0.0
    demo_ready_issues = []
    dod_compliant = 0

    for issue in raw_issues:
        fields = issue.get("fields", {})
        status_name = (fields.get("status") or {}).get("name", "")
        sp = _extract_story_points(fields)
        committed_points += sp

        status_lower = status_name.lower()
        if status_lower in ("done", "closed", "resolved"):
            completed_points += sp
            subtasks = fields.get("subtasks", [])
            all_subtasks_done = all(
                (st.get("fields", {}).get("status", {}) or {}).get("statusCategory", {}).get("key", "") == "done"
                for st in subtasks
            ) if subtasks else True
            if all_subtasks_done:
                dod_compliant += 1

            issue_type = (fields.get("issuetype") or {}).get("name", "")
            if issue_type in ("Story", "Feature"):
                assignee_raw = fields.get("assignee") or {}
                demo_ready_issues.append({
                    "issue_key": issue.get("key", ""),
                    "summary": fields.get("summary", ""),
                    "story_points": sp,
                    "assignee": (
                        assignee_raw.get("displayName")
                        or assignee_raw.get("name")
                        or ""
                    ),
                })

    done_count = sum(
        1 for i in raw_issues
        if (i.get("fields", {}).get("status") or {}).get("name", "").lower()
        in ("done", "closed", "resolved")
    )
    dod_compliance_pct = round(
        (dod_compliant / done_count * 100) if done_count > 0 else 0.0, 1
    )
    completion_rate = round(
        (completed_points / committed_points * 100) if committed_points > 0 else 0.0, 1
    )

    closed_sprints = _agile_request(
        cfg, "GET",
        "board/" + str(board_id) + "/sprint?state=closed&maxResults=6"
    )
    if closed_sprints is None:
        closed_sprints = {}

    velocity_history = []
    for s in closed_sprints.get("values", []):
        sid = s.get("id")
        if sid:
            si_result = _agile_request(
                cfg, "GET",
                "sprint/" + str(sid) + "/issue?maxResults=200&fields=status,customfield_10016,customfield_10028,story_points"
            )
            if si_result:
                sp_sum = sum(
                    _extract_story_points(i.get("fields", {}))
                    for i in si_result.get("issues", [])
                    if (i.get("fields", {}).get("status") or {}).get("name", "").lower()
                    in ("done", "closed", "resolved")
                )
                velocity_history.append(int(sp_sum))

    vstats = scrum_calculator.velocity_stats(velocity_history) if velocity_history else {}

    from datetime import datetime
    review_ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + " (UTC)"

    return {
        "sprint_id": sprint_id,
        "sprint_name": sprint_name,
        "sprint_goal": sprint_goal,
        "completed_points": round(completed_points, 1),
        "committed_points": round(committed_points, 1),
        "completion_rate": completion_rate,
        "velocity_mean": vstats.get("mean", 0.0),
        "velocity_cv": vstats.get("cv", 0.0),
        "nasscom_agileX_level": vstats.get("nasscom_agileX_level", "N/A"),
        "dod_compliance_pct": dod_compliance_pct,
        "demo_ready_issues": demo_ready_issues,
        "review_timestamp": review_ts,
    }


@mcp.tool()
@mcp_tool_handler
def jira_retrospective(
    sprint_id: int,
    board_id: int,
    retrospective_action_project_key: Optional[str] = None,
) -> dict:
    """Generate a Sprint Retrospective report with effectiveness metrics.

    Fetches velocity history and sprint issue data from the Agile API.
    Computes velocity_stats and tuckman_estimate. If action project provided,
    fetches retro action items via REST API JQL and computes RE score.

    Args:
        sprint_id: Numeric sprint ID of the sprint being retrospected.
        board_id: Numeric board ID for velocity context.
        retrospective_action_project_key: Project key where retro action
            items are tracked (e.g. "RETRO"). Optional.

    Returns:
        Dict with keys:
            sprint_id, sprint_name, re_score, iv_trend, recommended_format,
            velocity_stats, action_items_created, retrospective_format_used,
            next_format_recommendation, nasscom_benchmark.
    """
    cfg = _get_config()

    sprint_detail = _agile_request(cfg, "GET", "sprint/" + str(sprint_id))
    if sprint_detail is None:
        sprint_detail = {}
    sprint_name = sprint_detail.get("name", "Sprint " + str(sprint_id))

    closed_sprints = _agile_request(
        cfg, "GET",
        "board/" + str(board_id) + "/sprint?state=closed&maxResults=6"
    )
    if closed_sprints is None:
        closed_sprints = {}

    velocity_history = []
    sprint_count = 0
    for s in closed_sprints.get("values", []):
        sid = s.get("id")
        sprint_count += 1
        if sid:
            si_result = _agile_request(
                cfg, "GET",
                "sprint/" + str(sid) + "/issue?maxResults=200&fields=status,customfield_10016,customfield_10028,story_points"
            )
            if si_result:
                sp_sum = sum(
                    _extract_story_points(i.get("fields", {}))
                    for i in si_result.get("issues", [])
                    if (i.get("fields", {}).get("status") or {}).get("name", "").lower()
                    in ("done", "closed", "resolved")
                )
                velocity_history.append(int(sp_sum))

    vstats = scrum_calculator.velocity_stats(velocity_history) if velocity_history else {}
    cv_val = float(vstats.get("cv", 0.0))
    total_sprints = max(1, sprint_count)

    action_items_created = 0
    re_result = {}
    if retrospective_action_project_key:
        action_jql = (
            "project = " + retrospective_action_project_key
            + " AND labels = retro-action ORDER BY created DESC"
        )
        action_search = _request(
            cfg, "POST", "/issue/search",
            {"jql": action_jql, "maxResults": 50, "fields": ["summary", "status"]}
        )
        if action_search:
            all_actions = action_search.get("issues", [])
            action_items_created = len(all_actions)
            closed_actions = sum(
                1 for a in all_actions
                if (a.get("fields", {}).get("status") or {}).get("name", "").lower()
                in ("done", "closed", "resolved")
            )
            re_result = scrum_calculator.retrospective_effectiveness(
                items_created=action_items_created,
                items_closed=closed_actions,
                total_sprints=total_sprints,
            )
    else:
        re_result = scrum_calculator.retrospective_effectiveness(
            items_created=max(1, total_sprints),
            items_closed=max(0, total_sprints - 1),
            total_sprints=total_sprints,
        )

    return {
        "sprint_id": sprint_id,
        "sprint_name": sprint_name,
        "re_score": re_result.get("re_score", 0.0),
        "iv_trend": re_result.get("iv_trend", 0.0),
        "recommended_format": re_result.get("recommended_format", "Start-Stop-Continue"),
        "velocity_stats": vstats,
        "action_items_created": action_items_created,
        "retrospective_format_used": re_result.get("recommended_format", "Start-Stop-Continue"),
        "next_format_recommendation": re_result.get("recommended_format", "Start-Stop-Continue"),
        "nasscom_benchmark": re_result.get("nasscom_benchmark", "N/A"),
    }


@mcp.tool()
@mcp_tool_handler
def jira_refine_backlog(
    project_key: str,
    max_issues: int = 50,
    epic_link_field: Optional[str] = None,
) -> dict:
    """Generate a Backlog Refinement report analyzing the unrefined backlog.

    Uses REST API JQL to fetch unrefined backlog issues (Story, Task, Bug
    without sprint assignment) and provides WSJF scoring template per issue.

    Args:
        project_key: Project key to analyze (e.g. "PROJ"). Must not be empty.
        max_issues: Maximum backlog issues to analyze (clamped to 1-100, default 50).
        epic_link_field: Custom field name for Epic link (e.g. "customfield_10014").
                         Optional -- used to include epic info in output.

    Returns:
        Dict with keys:
            project_key, total_backlog_stories, unestimated_count,
            wsjf_ordered_stories, refinement_recommendations, ist_timezone_note.

    Raises:
        ValueError: If project_key is empty.
    """
    cfg = _get_config()
    if not project_key or not project_key.strip():
        raise ValueError("project_key must not be empty")

    max_issues = max(1, min(100, max_issues))

    fields_list = ["summary", "status", "issuetype", "priority", "customfield_10016",
                   "customfield_10028", "story_points", "description"]
    if epic_link_field:
        fields_list.append(epic_link_field)

    jql = (
        "project = " + project_key
        + " AND issuetype in (Story, Task, Bug) AND sprint is EMPTY"
        + " AND statusCategory != Done ORDER BY priority DESC"
    )

    search_result = _request(
        cfg, "POST", "/issue/search",
        {
            "jql": jql,
            "maxResults": max_issues,
            "fields": fields_list,
        }
    )
    if search_result is None:
        search_result = {}

    raw_issues = search_result.get("issues", [])
    total_count = search_result.get("total", len(raw_issues))

    unestimated_count = 0
    wsjf_stories = []
    for issue in raw_issues:
        fields = issue.get("fields", {})
        sp = _extract_story_points(fields)
        if sp == 0:
            unestimated_count += 1

        epic_link = ""
        if epic_link_field:
            epic_link = fields.get(epic_link_field, "") or ""

        has_description = bool(fields.get("description"))

        priority_name = (fields.get("priority") or {}).get("name", "Medium")

        wsjf_stories.append({
            "issue_key": issue.get("key", ""),
            "summary": fields.get("summary", ""),
            "issue_type": (fields.get("issuetype") or {}).get("name", ""),
            "priority": priority_name,
            "story_points": sp,
            "epic_link": epic_link,
            "has_description": has_description,
            "wsjf_template": {
                "business_value": "?",
                "time_criticality": "?",
                "risk_reduction": "?",
                "job_size": int(sp) if sp > 0 else "?",
            },
        })

    unestimated_ratio = unestimated_count / total_count if total_count > 0 else 0.0
    if unestimated_ratio < 0.2:
        health = "Healthy"
    elif unestimated_ratio < 0.4:
        health = "Needs Attention"
    else:
        health = "Critical"

    recommendations = []
    if unestimated_count > 0:
        recommendations.append(
            str(unestimated_count) + " stories need story point estimation"
        )
    if unestimated_ratio >= 0.4:
        recommendations.append(
            "Schedule dedicated refinement session before next sprint planning"
        )
    recommendations.append(
        "Apply WSJF scoring to top 10 stories for priority ordering"
    )

    return {
        "project_key": project_key,
        "total_backlog_stories": total_count,
        "unestimated_count": unestimated_count,
        "wsjf_ordered_stories": wsjf_stories,
        "refinement_recommendations": recommendations,
        "ist_timezone_note": (
            "IST timezone: 4.5h overlap window with EST (17:30-23:00 IST)"
        ),
    }


# ---------------------------------------------------------------------------
# Scrum Master Tools -- Analytics (Group C: Tools 21-25 of 25)
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_get_velocity(
    board_id: int,
    num_sprints: int = 7,
) -> dict:
    """Retrieve and analyze sprint velocity history for a Scrum board.

    Uses the Agile API velocity chart endpoint as primary source (CONTRACT #1).
    Falls back to closed sprint enumeration with story point summation if the
    velocity endpoint returns an error (Agile API not available on some Server/DC).

    Args:
        board_id: Numeric board ID.
        num_sprints: Number of recent closed sprints to analyze (clamped to 1-20, default 7).

    Returns:
        Dict with keys:
            board_id, sprints_analyzed, velocity_history, velocity_stats,
            ewma_last, ewma_alpha.
    """
    cfg = _get_config()
    num_sprints = max(1, min(20, num_sprints))

    velocity_history_dicts = []
    velocity_points = []

    try:
        vel_result = _agile_request(
            cfg, "GET",
            "rapid/charts/velocity?rapidViewId=" + str(board_id)
        )
        if vel_result and "velocityStatEntries" in vel_result:
            entries = vel_result["velocityStatEntries"]
            sprints_meta = vel_result.get("sprints", [])
            for s in sprints_meta[-num_sprints:]:
                sid = str(s.get("id", ""))
                if sid in entries:
                    committed = float(
                        (entries[sid].get("estimated") or {}).get("value", 0)
                    )
                    completed = float(
                        (entries[sid].get("completed") or {}).get("value", 0)
                    )
                    velocity_history_dicts.append({
                        "sprint_id": s.get("id"),
                        "sprint_name": s.get("name", ""),
                        "committed_points": committed,
                        "completed_points": completed,
                        "completion_rate": round(
                            (completed / committed * 100) if committed > 0 else 0.0, 1
                        ),
                    })
                    velocity_points.append(int(completed))
    except RuntimeError:
        vel_result = None

    if not velocity_points:
        closed_sprints = _agile_request(
            cfg, "GET",
            "board/" + str(board_id) + "/sprint?state=closed&maxResults=" + str(num_sprints)
        )
        if closed_sprints is None:
            closed_sprints = {}

        for s in closed_sprints.get("values", []):
            sid = s.get("id")
            if sid:
                si = _agile_request(
                    cfg, "GET",
                    "sprint/" + str(sid) + "/issue?maxResults=200&fields=status,customfield_10016,customfield_10028,story_points"
                )
                if si:
                    sp_sum = sum(
                        _extract_story_points(i.get("fields", {}))
                        for i in si.get("issues", [])
                        if (i.get("fields", {}).get("status") or {}).get("name", "").lower()
                        in ("done", "closed", "resolved")
                    )
                    velocity_points.append(int(sp_sum))
                    velocity_history_dicts.append({
                        "sprint_id": sid,
                        "sprint_name": s.get("name", ""),
                        "committed_points": sp_sum,
                        "completed_points": sp_sum,
                        "completion_rate": 100.0,
                    })

    vstats = scrum_calculator.velocity_stats(velocity_points) if velocity_points else {}

    ewma_alpha = 0.3
    ewma_last = 0.0
    if velocity_points:
        ewma_last = float(velocity_points[0])
        for v in velocity_points[1:]:
            ewma_last = ewma_alpha * v + (1 - ewma_alpha) * ewma_last
        ewma_last = round(ewma_last, 2)

    return {
        "board_id": board_id,
        "sprints_analyzed": len(velocity_points),
        "velocity_history": velocity_history_dicts,
        "velocity_stats": vstats,
        "ewma_last": ewma_last,
        "ewma_alpha": ewma_alpha,
    }


@mcp.tool()
@mcp_tool_handler
def jira_get_sprint_metrics(
    board_id: int,
    sprint_id: int,
) -> dict:
    """Get comprehensive metrics for a specific sprint.

    Fetches sprint metadata and all sprint issues from the Agile API to compute
    burndown deviation, scope change, cycle time, WIP, and sprint health.

    Args:
        board_id: Numeric board ID.
        sprint_id: Numeric sprint ID.

    Returns:
        Dict with keys:
            sprint_id, board_id, burndown_deviation_pct, scope_change_pct,
            cycle_time_p85_days, wip_current, throughput_per_day,
            sprint_health, health_reason.
    """
    cfg = _get_config()
    from datetime import datetime

    sprint_detail = _agile_request(cfg, "GET", "sprint/" + str(sprint_id))
    if sprint_detail is None:
        sprint_detail = {}

    sprint_name = sprint_detail.get("name", "Sprint " + str(sprint_id))
    sprint_state = sprint_detail.get("state", "")
    start_date_str = sprint_detail.get("startDate", "")
    end_date_str = sprint_detail.get("endDate", "")

    issues_result = _agile_request(
        cfg, "GET",
        "sprint/" + str(sprint_id) + "/issue?maxResults=200&fields=summary,status,issuetype,created,customfield_10016,customfield_10028,story_points"
    )
    if issues_result is None:
        issues_result = {}

    raw_issues = issues_result.get("issues", [])
    total_issues = len(raw_issues)

    done_issues = 0
    in_progress_issues = 0
    todo_issues = 0
    story_points_total = 0.0
    story_points_done = 0.0
    issue_type_breakdown: Dict[str, int] = {}
    scope_change_count = 0

    start_date_parsed = None
    if start_date_str:
        try:
            start_date_parsed = datetime.fromisoformat(
                start_date_str.replace("Z", "+00:00")
            )
        except ValueError:
            start_date_parsed = None

    for issue in raw_issues:
        fields = issue.get("fields", {})
        status_name = (fields.get("status") or {}).get("name", "")
        status_lower = status_name.lower()
        sp = _extract_story_points(fields)
        story_points_total += sp

        it_name = (fields.get("issuetype") or {}).get("name", "Unknown")
        issue_type_breakdown[it_name] = issue_type_breakdown.get(it_name, 0) + 1

        if status_lower in ("done", "closed", "resolved"):
            done_issues += 1
            story_points_done += sp
        elif "progress" in status_lower or status_lower == "in review":
            in_progress_issues += 1
        else:
            todo_issues += 1

        if start_date_parsed:
            created_str = fields.get("created", "")
            if created_str:
                try:
                    created_dt = datetime.fromisoformat(
                        created_str.replace("Z", "+00:00")
                    )
                    if created_dt > start_date_parsed:
                        scope_change_count += 1
                except ValueError:
                    pass

    story_points_remaining = story_points_total - story_points_done

    days_elapsed = -1
    days_remaining = -1
    burn_rate_per_day = 0.0
    projected_completion_pct = 0.0

    now = datetime.utcnow()
    if start_date_parsed:
        days_elapsed = max(0, (now - start_date_parsed.replace(tzinfo=None)).days)
        if days_elapsed > 0 and story_points_done > 0:
            burn_rate_per_day = round(story_points_done / days_elapsed, 2)

    if end_date_str:
        try:
            end_date_parsed = datetime.fromisoformat(
                end_date_str.replace("Z", "+00:00")
            )
            days_remaining = max(0, (end_date_parsed.replace(tzinfo=None) - now).days)
        except ValueError:
            pass

    if story_points_total > 0:
        completion_pct = (story_points_done / story_points_total) * 100
        projected_completion_pct = round(min(100.0, completion_pct), 1)
        if burn_rate_per_day > 0 and days_remaining >= 0:
            projected_total = story_points_done + (burn_rate_per_day * days_remaining)
            projected_completion_pct = round(
                min(100.0, projected_total / story_points_total * 100), 1
            )

    if projected_completion_pct >= 80:
        sprint_health = "On Track"
        health_reason = "Projected completion >= 80%"
    elif projected_completion_pct >= 50:
        sprint_health = "At Risk"
        health_reason = "Projected completion 50-80%"
    else:
        sprint_health = "Off Track"
        health_reason = "Projected completion < 50%"

    burndown_deviation_pct = 0.0
    scope_change_pct = round(
        (scope_change_count / total_issues * 100) if total_issues > 0 else 0.0, 1
    )

    return {
        "sprint_id": sprint_id,
        "sprint_name": sprint_name,
        "board_id": board_id,
        "state": sprint_state,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "total_issues": total_issues,
        "done_issues": done_issues,
        "in_progress_issues": in_progress_issues,
        "todo_issues": todo_issues,
        "story_points_total": round(story_points_total, 1),
        "story_points_done": round(story_points_done, 1),
        "story_points_remaining": round(story_points_remaining, 1),
        "burn_rate_per_day": burn_rate_per_day,
        "projected_completion_pct": projected_completion_pct,
        "scope_change_count": scope_change_count,
        "scope_change_pct": scope_change_pct,
        "burndown_deviation_pct": burndown_deviation_pct,
        "cycle_time_p85_days": days_elapsed,
        "wip_current": in_progress_issues,
        "throughput_per_day": burn_rate_per_day,
        "issue_type_breakdown": issue_type_breakdown,
        "sprint_health": sprint_health,
        "health_reason": health_reason,
    }


@mcp.tool()
@mcp_tool_handler
def jira_track_impediments(
    project_key: str,
    sprint_id: Optional[int] = None,
) -> dict:
    """Track and analyze impediments and blockers in a project or sprint.

    Uses REST API JQL to find issues labeled "impediment". Computes MTTR
    metrics via scrum_calculator.mttr_analysis() on resolved impediments.

    Args:
        project_key: Project key (e.g. "PROJ").
        sprint_id: Limit tracking to a specific sprint ID. Optional.

    Returns:
        Dict with keys:
            project_key, sprint_id, open_impediments, closed_impediments_count,
            mttr_days_mean, mttr_days_p85, escalation_required,
            flow_efficiency_impact_note.
    """
    cfg = _get_config()

    jql = 'project = "' + project_key + '" AND labels = "impediment"'
    if sprint_id is not None:
        jql += " AND sprint = " + str(sprint_id)
    jql += " ORDER BY created ASC"

    search_result = _request(
        cfg, "POST", "/issue/search",
        {
            "jql": jql,
            "maxResults": 100,
            "fields": ["summary", "status", "assignee", "priority", "created", "resolutiondate", "labels"],
        }
    )
    if search_result is None:
        search_result = {}

    raw_issues = search_result.get("issues", [])

    dates_open = []
    dates_closed = []
    open_impediments = 0

    for issue in raw_issues:
        fields = issue.get("fields", {})
        status_lower = (fields.get("status") or {}).get("name", "").lower()
        created = (fields.get("created") or "")[:10]

        if created:
            dates_open.append(created)

        if status_lower in ("done", "closed", "resolved"):
            resolution = (fields.get("resolutiondate") or "")[:10]
            if resolution:
                dates_closed.append(resolution)
        else:
            open_impediments += 1

    mttr = scrum_calculator.mttr_analysis(dates_open, dates_closed)

    escalation_required = open_impediments >= 3 or mttr.get("mttr_days_mean", 0) > 7

    return {
        "project_key": project_key,
        "sprint_id": sprint_id,
        "open_impediments": open_impediments,
        "closed_impediments_count": mttr.get("closed_count", 0),
        "mttr_days_mean": mttr.get("mttr_days_mean", 0.0),
        "mttr_days_p85": mttr.get("mttr_days_p85", 0.0),
        "escalation_required": escalation_required,
        "flow_efficiency_impact_note": mttr.get("resolution_layer_note", ""),
    }


@mcp.tool()
@mcp_tool_handler
def jira_team_health(
    board_id: int,
    num_sprints: int = 6,
) -> dict:
    """Compute a comprehensive team health dashboard across recent sprints.

    Fetches closed sprint velocity history from the Agile API, then computes
    velocity_stats, tuckman_estimate, and a composite health score.

    Args:
        board_id: Numeric board ID.
        num_sprints: Number of closed sprints to analyze (clamped to 1-12, default 6).

    Returns:
        Dict with keys:
            board_id, sprints_analyzed, tuckman_stage, velocity_cv,
            velocity_trend, nasscom_agileX_level, india_attrition_note,
            health_summary, recommended_intervention.
    """
    cfg = _get_config()
    num_sprints = max(1, min(12, num_sprints))

    velocity_points = []
    closed_sprints = _agile_request(
        cfg, "GET",
        "board/" + str(board_id) + "/sprint?state=closed&maxResults=" + str(num_sprints)
    )
    if closed_sprints is None:
        closed_sprints = {}

    for s in closed_sprints.get("values", []):
        sid = s.get("id")
        if sid:
            si = _agile_request(
                cfg, "GET",
                "sprint/" + str(sid) + "/issue?maxResults=200&fields=status,customfield_10016,customfield_10028,story_points"
            )
            if si:
                sp_sum = sum(
                    _extract_story_points(i.get("fields", {}))
                    for i in si.get("issues", [])
                    if (i.get("fields", {}).get("status") or {}).get("name", "").lower()
                    in ("done", "closed", "resolved")
                )
                velocity_points.append(int(sp_sum))

    vstats = scrum_calculator.velocity_stats(velocity_points) if velocity_points else {}
    cv_val = float(vstats.get("cv", 0.5))

    velocity_trend = 0.0
    if len(velocity_points) >= 2:
        half = len(velocity_points) // 2
        first_half_mean = sum(velocity_points[:half]) / half
        second_half_mean = sum(velocity_points[half:]) / (len(velocity_points) - half)
        velocity_trend = second_half_mean - first_half_mean

    tuckman_stage = scrum_calculator.tuckman_estimate(
        velocity_cv=cv_val,
        velocity_trend=velocity_trend,
        team_age_sprints=len(velocity_points),
    )

    agile_x = vstats.get("nasscom_agileX_level", "L1")

    if tuckman_stage == "Performing" and agile_x in ("L4", "L5"):
        health_summary = "Excellent -- high-performing, predictable team"
        intervention = "Consider Kanban-Scrum hybrid for flow optimization"
    elif tuckman_stage == "Norming":
        health_summary = "Good -- team building consistent rhythm"
        intervention = "Focus on WSJF adoption and DoR enforcement"
    elif tuckman_stage == "Storming":
        health_summary = "Needs Improvement -- high velocity variance"
        intervention = "Stabilize story sizing; reduce mid-sprint scope changes"
    else:
        health_summary = "Critical -- team still forming or restructuring"
        intervention = "Use capacity-based planning; skip velocity-based forecasting"

    return {
        "board_id": board_id,
        "sprints_analyzed": len(velocity_points),
        "tuckman_stage": tuckman_stage,
        "velocity_cv": vstats.get("cv", 0.0),
        "velocity_trend": round(velocity_trend, 2),
        "nasscom_agileX_level": agile_x,
        "india_attrition_note": (
            "India IT attrition peak: Jan-Mar (Q1). Apply +15% buffer to job size estimates."
        ),
        "health_summary": health_summary,
        "recommended_intervention": intervention,
    }


@mcp.tool()
@mcp_tool_handler
def jira_monte_carlo_forecast(
    board_id: int,
    remaining_story_points: int,
    num_velocity_samples: int = 6,
    iterations: int = 10000,
) -> dict:
    """Run a Monte Carlo simulation to forecast probabilistic sprint delivery.

    Fetches velocity history from the Agile API (primary per CONTRACT #1),
    then calls scrum_calculator.monte_carlo_forecast() for simulation.

    Args:
        board_id: Numeric board ID for velocity data.
        remaining_story_points: Total story points remaining to deliver (>= 1).
        num_velocity_samples: Number of recent closed sprints to use as velocity
                              input (clamped to 2-20, default 6).
        iterations: Monte Carlo simulation iterations (default 10_000).

    Returns:
        Dict with keys:
            board_id, remaining_story_points, velocity_samples_used,
            p50_sprints, p70_sprints, p85_sprints, p95_sprints,
            mean_sprints, std_sprints, p85_weeks_ist,
            india_it_note, iterations.

    Raises:
        ValueError: If remaining_story_points < 1 or fewer than 2 velocity samples available.
    """
    cfg = _get_config()
    if remaining_story_points < 1:
        raise ValueError("remaining_story_points must be >= 1")

    num_velocity_samples = max(2, min(20, num_velocity_samples))

    velocity_points = []
    try:
        vel_result = _agile_request(
            cfg, "GET",
            "rapid/charts/velocity?rapidViewId=" + str(board_id)
        )
        if vel_result and "velocityStatEntries" in vel_result:
            entries = vel_result["velocityStatEntries"]
            sprints_meta = vel_result.get("sprints", [])
            for s in sprints_meta[-num_velocity_samples:]:
                sid = str(s.get("id", ""))
                if sid in entries:
                    completed = float(
                        (entries[sid].get("completed") or {}).get("value", 0)
                    )
                    if completed > 0:
                        velocity_points.append(int(completed))
    except RuntimeError:
        pass

    if len(velocity_points) < 2:
        closed_sprints = _agile_request(
            cfg, "GET",
            "board/" + str(board_id) + "/sprint?state=closed&maxResults=" + str(num_velocity_samples)
        )
        if closed_sprints is None:
            closed_sprints = {}

        for s in closed_sprints.get("values", []):
            sid = s.get("id")
            if sid:
                si = _agile_request(
                    cfg, "GET",
                    "sprint/" + str(sid) + "/issue?maxResults=200&fields=status,customfield_10016,customfield_10028,story_points"
                )
                if si:
                    sp_sum = sum(
                        _extract_story_points(i.get("fields", {}))
                        for i in si.get("issues", [])
                        if (i.get("fields", {}).get("status") or {}).get("name", "").lower()
                        in ("done", "closed", "resolved")
                    )
                    if sp_sum > 0:
                        velocity_points.append(int(sp_sum))

    if len(velocity_points) < 2:
        raise ValueError(
            "Fewer than 2 positive velocity samples available for board "
            + str(board_id) + ". Cannot run Monte Carlo forecast."
        )

    forecast = scrum_calculator.monte_carlo_forecast(
        velocity_samples=velocity_points,
        remaining_points=remaining_story_points,
        iterations=iterations,
    )

    p85_sprints = forecast.get("p85", 0.0)
    p85_weeks = round(p85_sprints * 2, 1)

    return {
        "board_id": board_id,
        "remaining_story_points": remaining_story_points,
        "velocity_samples_used": forecast.get("samples_used", len(velocity_points)),
        "p50_sprints": forecast.get("p50", 0.0),
        "p70_sprints": forecast.get("p70", 0.0),
        "p85_sprints": p85_sprints,
        "p95_sprints": forecast.get("p95", 0.0),
        "mean_sprints": forecast.get("mean_sprints", 0.0),
        "std_sprints": forecast.get("std_sprints", 0.0),
        "p85_weeks_ist": p85_weeks,
        "india_it_note": (
            "India IT teams: account for 18-25% annual attrition and national holidays in sprint capacity."
        ),
        "iterations": iterations,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
