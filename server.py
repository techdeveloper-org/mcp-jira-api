"""
Jira MCP Server - FastMCP-based Jira integration for Claude Code.

Supports both Jira Cloud (v3, ADF format) and Jira Server/Data Center (v2, plain text).
Backend: urllib.request (stdlib only, no external deps)
Transport: stdio

Tools (53):
  Core Jira (11):
    jira_create_issue, jira_get_issue, jira_search_issues,
    jira_transition_issue, jira_add_comment, jira_link_pr,
    jira_list_projects, jira_create_project, jira_get_transitions,
    jira_update_issue, jira_health_check
  Scrum Master -- Board & Sprint Infrastructure (5):
    jira_get_boards, jira_get_sprints, jira_create_sprint,
    jira_start_sprint, jira_close_sprint
  Scrum Master -- Ceremony Facilitation (5):
    jira_plan_sprint, jira_daily_standup, jira_sprint_review,
    jira_retrospective, jira_refine_backlog
  Scrum Master -- Analytics (5):
    jira_get_velocity, jira_get_sprint_metrics, jira_track_impediments,
    jira_team_health, jira_monte_carlo_forecast
  Epic Management (4):
    jira_create_epic, jira_get_epic, jira_link_to_epic, jira_list_epics
  Release & Version Management (4):
    jira_create_version, jira_list_versions, jira_release_version,
    jira_release_notes
  Cross-Board / Multi-Team Metrics (3):
    jira_program_velocity, jira_cross_team_health, jira_dependency_check

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
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from pathlib import Path

# Ensure src/mcp/ is in path for base package imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

# mcp 2.0 renamed FastMCP to MCPServer and moved it to mcp.server.mcpserver.
# Both names are probed so this server runs under either major version; the
# API used below (tool decorator, run(transport=...)) is identical in both.
try:
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp < 2.0
    from mcp.server.fastmcp import FastMCP as MCPServer

try:
    from mcp.types import ToolAnnotations
except ImportError:  # pragma: no cover - annotations unsupported on this mcp
    ToolAnnotations = None

from base.decorators import mcp_tool_handler

# Scrum Master extension imports
from agile_client import _agile_request, _agile_url, _build_agile_auth_header, AgileClient
from base.response import success, error
from input_validator import validate_input
from idempotency import run_once
import scrum_calculator

mcp = MCPServer(
    "jira-api",
    instructions="Jira operations via REST API (Cloud v3 ADF + Server v2 plain text)"
)


def _tool(read_only=False, destructive=True, idempotent=False, open_world=True):
    """Register a tool with explicit MCP ToolAnnotations.

    The MCP specification's per-hint defaults are readOnlyHint=false,
    destructiveHint=true, idempotentHint=false and openWorldHint=true -- every
    default points at the more dangerous value, so an unannotated tool is
    indistinguishable from an explicit worst-case declaration. Every tool on
    this server declares its four hints explicitly so a host's auto-approval and
    automatic-retry decisions rest on a stated property rather than an omission.

    Args:
        read_only: True when the tool has no side effects at all.
        destructive: True when the tool's effect is irreversible.
        idempotent: True only when repeating the call with identical arguments
            leaves the same cumulative effect as a single call. A tool made
            retry-safe only by a caller-supplied idempotency key does not
            qualify: the underlying operation stays non-idempotent and the
            protection is conditional on the caller reusing the key.
        open_world: True when the tool reaches an external system.

    Returns:
        The decorator returned by the underlying MCP tool registration.
    """
    if ToolAnnotations is None:
        return mcp.tool()
    try:
        return mcp.tool(
            annotations=ToolAnnotations(
                readOnlyHint=read_only,
                destructiveHint=destructive,
                idempotentHint=idempotent,
                openWorldHint=open_world,
            )
        )
    except TypeError:  # pragma: no cover - older mcp without annotations kwarg
        return mcp.tool()


_ISSUE_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,9}-[0-9]+$")


def _safe_issue_key(issue_key: str) -> str:
    """Validate an issue key before it is concatenated into a REST API path.

    Several tools build their request path by string concatenation
    (``"/issue/" + issue_key + "/transitions"``). An unvalidated value there is
    path injection: a key of ``PROJ-1/../../project/OTHER`` addresses a
    different resource than the caller named, and ``PROJ-1?expand=x`` appends a
    query the caller never asked for. Constraining the value to Jira's own key
    grammar removes both, and does so before the URL is built rather than by
    escaping afterwards.

    Args:
        issue_key: Caller-supplied Jira issue key.

    Returns:
        The validated key, whitespace-trimmed.

    Raises:
        ValueError: If the key does not match Jira's PROJ-123 key grammar.
    """
    cleaned = validate_input(issue_key, max_length=64, field_name="issue_key")
    if not _ISSUE_KEY_RE.match(cleaned):
        raise ValueError(
            "issue_key must match ^[A-Za-z][A-Za-z0-9]{0,9}-[0-9]+$ "
            "(e.g. PROJ-123), got: " + cleaned
        )
    return cleaned


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
            Use the special prefix NOVERSION: to bypass the version
            prefix. This is for the Agile API, which lives at
            /rest/agile/1.0/... (e.g. NOVERSION:/rest/agile/1.0/board).
            Core API resources are versioned and must NOT use it --
            the previous example here, NOVERSION:/rest/serverInfo,
            was itself the bug in issue #3.

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


def _adf_paragraph(para: str) -> Dict[str, Any]:
    """Build one ADF paragraph, mapping single newlines to hardBreak nodes.

    ADF ignores a newline character inside a text node, so a line break has to
    be its own node or it disappears from the rendered issue.

    Args:
        para: One paragraph of plain text, possibly containing single newlines.

    Returns:
        An ADF paragraph node.
    """
    content: List[Dict[str, Any]] = []
    for i, line in enumerate(para.split("\n")):
        if i:
            content.append({"type": "hardBreak"})
        if line:
            content.append({"type": "text", "text": line})
    if not content:
        content = [{"type": "text", "text": ""}]
    return {"type": "paragraph", "content": content}


def _text_to_adf(text: str) -> Dict[str, Any]:
    """Convert plain text to an ADF document, one paragraph per paragraph.

    Paragraphs are separated by a blank line, matching how the text was
    written. Issue #4: this previously emitted a SINGLE paragraph node holding
    the entire text with raw newlines inside it. ADF renders neither the
    newlines nor the paragraph breaks, so every structured description -- one
    with steps, or acceptance criteria, or a before/after contrast -- arrived
    in Jira as one undifferentiated block. It degraded exactly the tickets
    carrying the most information.

    Args:
        text: Plain text content to convert.

    Returns:
        ADF document dict with one paragraph node per source paragraph.
    """
    paras = [p for p in re.split(r"\n\s*\n", (text or "").strip()) if p.strip()]
    if not paras:
        paras = [""]
    return {
        "type": "doc",
        "version": 1,
        "content": [_adf_paragraph(p) for p in paras],
    }


def _adf_to_text(value: Any) -> str:
    """Flatten a description field to plain text, whatever shape it arrives in.

    Jira Cloud (v3) returns an ADF document; Jira Server (v2) returns a plain
    string. Callers want the text either way, so both are handled here rather
    than at every call site.

    Paragraph nodes are joined with a blank line and hardBreak nodes with a
    single newline, which round-trips the structure `_text_to_adf` writes.

    Args:
        value: An ADF document dict, a plain string, or None.

    Returns:
        Plain text, or "" when the field is absent.
    """
    if not value:
        return ""
    if isinstance(value, str):
        return value

    def walk(node: Any) -> str:
        if isinstance(node, list):
            return "".join(walk(n) for n in node)
        if not isinstance(node, dict):
            return ""
        kind = node.get("type")
        if kind == "text":
            return node.get("text", "")
        if kind == "hardBreak":
            return "\n"
        inner = walk(node.get("content", []))
        return inner + "\n\n" if kind == "paragraph" else inner

    return walk(value.get("content", [])).strip()


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

@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
@mcp_tool_handler
def jira_create_issue(
    project_key: str,
    summary: str,
    issue_type: str = "Task",
    description: str = "",
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    """Create a Jira issue.

    Jira's create-issue endpoint is not idempotent and offers no de-duplication
    key of its own: a retry sent after a lost response files a second issue
    that looks identical to the first. Supply ``idempotency_key`` -- generated
    once when you decide to create the issue and reused unchanged on every
    retry of that same decision -- so a repeat call replays the recorded result
    instead of creating a duplicate. A key regenerated per attempt provides no
    protection at all.

    Args:
        project_key: Jira project key (e.g. PROJ).
        summary: Issue summary/title.
        issue_type: Issue type name (e.g. Task, Bug, Story). Default: Task.
        description: Issue description (plain text; converted to ADF for Cloud).
        priority: Priority name (e.g. High, Medium, Low). Optional.
        assignee: Assignee account ID (Cloud) or username (Server). Optional.
        labels: Comma-separated label names. Optional.
        idempotency_key: Optional caller-generated key scoped to one logical
            issue-creation intent.
    """
    def _create() -> dict:
        """Perform the underlying non-idempotent issue creation."""
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

    return run_once("jira_create_issue", idempotency_key, _create)


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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
    issue_key = _safe_issue_key(issue_key)
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

    # Issue #5: description was absent from this dict entirely -- a caller
    # could write one and never read it back. Cloud returns ADF and Server
    # returns a plain string, so it is flattened here: most consumers want the
    # text, not a nested document they have to walk themselves.
    return {
        "issue_key": result.get("key"),
        "issue_id": result.get("id"),
        "issue_url": cfg["url"] + "/browse/" + result.get("key", ""),
        "summary": raw_fields.get("summary", ""),
        "description": _adf_to_text(raw_fields.get("description")),
        "status": status_name,
        "issue_type": issuetype_name,
        "priority": priority_name,
        "assignee": assignee_name,
        "reporter": reporter_name,
        "created": raw_fields.get("created", ""),
        "updated": raw_fields.get("updated", ""),
        "labels": raw_fields.get("labels", []),
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_search_issues(
    jql: str,
    max_results: int = 20,
    next_page_token: Optional[str] = None,
    fields: Optional[str] = None,
) -> dict:
    """Search Jira issues using JQL (Jira Query Language).

    Args:
        jql: JQL query string (e.g. 'project = PROJ AND status = "In Progress"').
        max_results: Maximum number of results to return (default: 20, max: 100).
        next_page_token: Cursor from a previous call's next_page_token,
            to fetch the following page. Optional.
            Issue #6: this was `start_at`, an offset. /search/jql is
            cursor-paginated and rejects startAt with a 400, so an offset
            cannot be honoured here and is not accepted rather than
            silently ignored.
        fields: Comma-separated field names to include. Optional.
    """
    cfg = _get_config()

    body: Dict[str, Any] = {
        "jql": jql,
        "maxResults": min(max_results, 100),
    }
    if next_page_token:
        body["nextPageToken"] = next_page_token

    if fields:
        body["fields"] = [f.strip() for f in fields.split(",") if f.strip()]
    else:
        body["fields"] = ["summary", "status", "assignee", "priority", "issuetype", "created"]

    result = _request(cfg, "POST", "/search/jql", body)

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

    # Issue #6. /search/jql returns exactly [isLast, issues] -- no total,
    # no startAt, no maxResults, because Jira moved this endpoint from
    # offset pagination to a cursor. Reporting the old keys would emit
    # total: 0 next to a populated issue list, which a caller testing
    # "total == 0" reads as no matches while holding matches. The true
    # total is not obtainable from this endpoint at all, so it is not
    # reported rather than fabricated.
    return {
        "count": len(issues),
        "is_last": bool(result.get("isLast", True)),
        "next_page_token": result.get("nextPageToken", ""),
        "issues": issues,
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_get_transitions(issue_key: str) -> dict:
    """Get available workflow transitions for a Jira issue.

    Args:
        issue_key: Issue key (e.g. PROJ-123).
    """
    issue_key = _safe_issue_key(issue_key)
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


@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
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
    issue_key = _safe_issue_key(issue_key)
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


@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
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
    issue_key = _safe_issue_key(issue_key)
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


@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
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
    issue_key = _safe_issue_key(issue_key)
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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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


_PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")

# Company-managed (classic) templates only. Team-managed ("next-gen") project
# creation requires a different, less stable API surface and is intentionally
# not offered here -- a caller wanting that gets a clear error, not a project
# created under the wrong model.
_PROJECT_TEMPLATES = {
    "scrum": "com.pyxis.greenhopper.jira:gh-scrum-template",
    "kanban": "com.pyxis.greenhopper.jira:gh-kanban-template",
}


@_tool(read_only=False, destructive=True, idempotent=False, open_world=True)
@mcp_tool_handler
def jira_create_project(
    key: str,
    name: str,
    template: str = "scrum",
    description: Optional[str] = None,
    lead_account_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    """Create a company-managed (classic) Jira Software project.

    Project creation is destructive in the sense that a wrong key cannot be
    renamed later without breaking every issue reference built on it, and it
    is not idempotent: Jira's create-project endpoint has no de-duplication
    key of its own, and a retry sent after a lost response attempts a second
    project with the same key, which then fails with a confusing "key already
    exists" error rather than cleanly returning the first project. Supply
    ``idempotency_key`` -- generated once per logical intent and reused
    unchanged across every retry -- so a repeat call replays the recorded
    project instead of re-attempting creation.

    Only company-managed (classic) templates are supported (see
    ``_PROJECT_TEMPLATES``). Team-managed ("next-gen") projects use a
    different, less stable creation API and are out of scope for this tool.

    Args:
        key: Project key, 2-10 uppercase letters/digits, starting with a
            letter (e.g. FAB). Jira enforces this same grammar server-side;
            it is validated here first so a malformed key fails locally
            instead of after a network round trip.
        name: Project display name.
        template: One of "scrum" or "kanban". Default: "scrum".
        description: Optional project description.
        lead_account_id: Optional Cloud accountId to set as project lead.
            When omitted, the authenticated user (GET /myself) is used --
            Jira Cloud rejects project creation with no lead at all, so a
            default here removes a near-mandatory extra round trip for the
            common case of "I am creating a project I will also lead".
        idempotency_key: Optional caller-generated key scoped to one logical
            project-creation intent.

    Returns:
        Dict with keys: project_key, project_id, project_url, name, template.

    Raises:
        ValueError: If key is malformed or template is not a recognized name.
    """
    key = validate_input(key, max_length=10, field_name="key")
    if not _PROJECT_KEY_RE.match(key):
        raise ValueError(
            "key must match ^[A-Z][A-Z0-9]{1,9}$ (2-10 uppercase "
            "letters/digits, starting with a letter), got: " + key
        )
    name = validate_input(name, field_name="name")
    if template not in _PROJECT_TEMPLATES:
        raise ValueError(
            "template must be one of " + ", ".join(sorted(_PROJECT_TEMPLATES))
            + ", got: " + template
        )

    def _create() -> dict:
        """Perform the underlying non-idempotent project creation."""
        cfg = _get_config()

        lead = lead_account_id
        if not lead:
            me = _request(cfg, "GET", "/myself")
            lead = (me or {}).get("accountId")
            if not lead:
                raise RuntimeError(
                    "Could not resolve lead_account_id from /myself; pass "
                    "lead_account_id explicitly."
                )

        payload: Dict[str, Any] = {
            "key": key,
            "name": name,
            "projectTypeKey": "software",
            "projectTemplateKey": _PROJECT_TEMPLATES[template],
            "leadAccountId": lead,
        }
        if description:
            payload["description"] = description

        result = _request(cfg, "POST", "/project", payload)

        return {
            "project_key": result.get("key", key),
            "project_id": result.get("id", ""),
            "project_url": cfg["url"] + "/jira/software/projects/"
            + result.get("key", key) + "/boards",
            "name": name,
            "template": template,
        }

    return run_once("jira_create_project", idempotency_key, _create)


@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
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
    issue_key = _safe_issue_key(issue_key)
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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_health_check() -> dict:
    """Verify Jira connectivity and configuration.

    Calls the Jira server-info endpoint to confirm the connection works.
    """
    cfg = _get_config()

    # serverInfo is an ordinary VERSIONED Core API resource, not an
    # Agile one. It was the only non-Agile caller of the NOVERSION:
    # prefix, which produced /rest/serverInfo -- a path Jira does not
    # serve, so this tool 404'd on every Cloud site regardless of
    # whether the credentials were valid. Issue #3.
    result = _request(cfg, "GET", "/serverInfo")

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


_MAX_SPRINT_PAGES = 40


def _recent_closed_sprints(
    cfg: Dict[str, str], board_id: int, count: int
) -> Dict[str, Any]:
    """Return the ``count`` most recently closed sprints for a board.

    The Agile API lists a board's sprints oldest-first and applies
    ``maxResults`` by truncating from the front of that order. A request for
    ``board/{id}/sprint?state=closed&maxResults=6`` therefore returns the six
    *oldest* closed sprints on the board, not the six most recent -- so every
    velocity average, trend comparison and health score derived from that slice
    described the team's distant past and silently drifted further out of date
    with each sprint the board completed. Nothing in the response distinguished
    that from a correct answer.

    The bound is applied after the full closed-sprint set has been walked, not
    before: narrowing to "closed" and ordering are the API's job, but selecting
    the most recent N is only meaningful once the end of the sequence is known.
    Paging stops at _MAX_SPRINT_PAGES so a pathological board cannot spin here.

    Args:
        cfg: Config dict from _get_config().
        board_id: Numeric board ID.
        count: Number of most-recent closed sprints to return.

    Returns:
        Dict shaped like the raw Agile response, with ``values`` holding the
        most recent ``count`` closed sprints in chronological order, plus
        ``total`` (closed sprints seen) and ``pagination_truncated``.
    """
    count = max(1, count)
    collected: List[Dict[str, Any]] = []
    start_at = 0
    page_size = 50
    pages = 0
    truncated = False

    while pages < _MAX_SPRINT_PAGES:
        result = _agile_request(
            cfg, "GET",
            "board/" + str(board_id) + "/sprint?state=closed&startAt="
            + str(start_at) + "&maxResults=" + str(page_size)
        )
        if result is None:
            result = {}

        values = result.get("values", [])
        collected.extend(values)
        pages += 1

        if result.get("isLast", True) or not values:
            break
        start_at += len(values)
    else:
        truncated = True

    return {
        "values": collected[-count:],
        "total": len(collected),
        "pagination_truncated": truncated,
    }


# ---------------------------------------------------------------------------
# Scrum Master Tools -- Agile Infrastructure (Group A: Tools 11-15 of 25)
# ---------------------------------------------------------------------------

@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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


@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
@mcp_tool_handler
def jira_create_sprint(
    board_id: int,
    name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    goal: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    """Create a new sprint on a Jira Software Scrum board.

    Calls the Jira Agile REST API POST /rest/agile/1.0/sprint.
    Newly created sprints are always in "future" state.

    The Agile API happily accepts two sprints with the same name on the same
    board, so a retry after a lost response leaves a duplicate sprint that the
    team then has to reconcile by hand. Supply ``idempotency_key`` -- generated
    once per logical intent and reused unchanged across every retry -- so a
    repeat call replays the recorded sprint instead of creating another.

    Args:
        board_id: Numeric board ID to create the sprint on.
        name: Sprint name (e.g. "Sprint 42"). Must not be empty.
        start_date: Sprint start date in ISO format "YYYY-MM-DDTHH:MM:SS.000Z". Optional.
        end_date: Sprint end date in ISO format "YYYY-MM-DDTHH:MM:SS.000Z". Optional.
        goal: Sprint goal text. Optional.
        idempotency_key: Optional caller-generated key scoped to one logical
            sprint-creation intent.

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
    if not name or not name.strip():
        raise ValueError("Sprint name must not be empty")

    def _create() -> dict:
        """Perform the underlying non-idempotent sprint creation."""
        cfg = _get_config()

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

    return run_once("jira_create_sprint", idempotency_key, _create)


@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
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


@_tool(read_only=False, destructive=True, idempotent=False, open_world=True)
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

@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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

    # Issue #8: this field is named ..._ist and returned UTC, with
    # " (UTC)" appended -- the code contradicted its own key inside one
    # expression. IST is UTC+5:30, so the error crossed a working-day
    # boundary: a 10:22 IST standup was reported as 04:52.
    from datetime import datetime, timedelta, timezone
    _ist = timezone(timedelta(hours=5, minutes=30))
    standup_ts = datetime.now(_ist).strftime(
        "%Y-%m-%dT%H:%M:%S+05:30 (IST)")

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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_sprint_review(
    board_id: int,
    sprint_id: int,
    dod_criteria_weights: Optional[List[List[float]]] = None,
) -> dict:
    """Generate a Sprint Review report for the closing sprint.

    Provides delivered vs. not-delivered breakdown with story points, velocity
    achieved, velocity statistics, DoD compliance, and NASSCOM AgileX level.
    When dod_criteria_weights is supplied, computes an AHP-weighted DoD score
    using the caller-provided pairwise comparison matrix instead of the default.

    Args:
        board_id: Numeric board ID.
        sprint_id: Numeric sprint ID (active or recently closed).
        dod_criteria_weights: Optional n x n pairwise comparison matrix (list of
            lists of floats) for AHP-weighted DoD scoring. When None (default),
            uses the built-in 3-criterion DoD matrix (backward compatible).
            The matrix must be consistent (CR < 0.10); otherwise an error is
            returned. When provided, dod_weighted_score is added to the result.

    Returns:
        Dict with keys:
            sprint_id, sprint_name, sprint_goal, completed_points,
            committed_points, completion_rate, velocity_mean, velocity_cv,
            nasscom_agileX_level, dod_compliance_pct, demo_ready_issues,
            review_timestamp, ahp_dod_criteria, ahp_weights, ahp_CR,
            ahp_consistent, ahp_note. Also dod_weighted_score (float) when
            dod_criteria_weights is provided.
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
                    "dod_compliant": all_subtasks_done,
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

    closed_sprints = _recent_closed_sprints(cfg, board_id, 6)

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

    if dod_criteria_weights is not None:
        user_ahp = scrum_calculator.ahp_score(dod_criteria_weights)
        if "error" in user_ahp:
            return error("AHP matrix error: " + user_ahp["error"])
        if not user_ahp.get("consistent", False):
            return error(
                "AHP matrix inconsistent (CR="
                + str(round(user_ahp.get("CR", 0.0), 4))
                + "). CR must be < 0.10. Revise pairwise comparison matrix."
            )
        w = user_ahp["weights"]
        first_weight = w[0] if w else 1.0
        scored = []
        for story in demo_ready_issues:
            binary = 1.0 if story.get("dod_compliant", False) else 0.0
            scored.append(binary * first_weight)
        dod_weighted_score = round(
            sum(scored) / len(scored) if scored else 0.0, 4
        )
        ahp_dod_criteria = ["user_criterion_" + str(i + 1) for i in range(user_ahp["n"])]
        ahp_weights = user_ahp["weights"]
        ahp_cr = user_ahp["CR"]
        ahp_consistent = user_ahp["consistent"]
        ahp_note = "User-provided AHP matrix. CR < 0.10 confirms consistent weighting."
    else:
        dod_weighted_score = None
        dod_matrix = [
            [1.0,       3.0,  5.0],
            [1.0 / 3.0, 1.0,  2.0],
            [1.0 / 5.0, 0.5,  1.0],
        ]
        default_ahp = scrum_calculator.ahp_score(dod_matrix)
        ahp_dod_criteria = ["functionality", "quality", "completeness"]
        ahp_weights = default_ahp.get("weights", [])
        ahp_cr = default_ahp.get("CR", None)
        ahp_consistent = default_ahp.get("consistent", None)
        ahp_note = "Standard 3-criterion DoD matrix. CR < 0.10 confirms consistent weighting."

    result = {
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
        "ahp_dod_criteria": ahp_dod_criteria,
        "ahp_weights": ahp_weights,
        "ahp_CR": ahp_cr,
        "ahp_consistent": ahp_consistent,
        "ahp_note": ahp_note,
    }
    if dod_weighted_score is not None:
        result["dod_weighted_score"] = dod_weighted_score
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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

    closed_sprints = _recent_closed_sprints(cfg, board_id, 6)

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
        if not re.match(r'^[A-Z][A-Z0-9]{0,9}$', retrospective_action_project_key):
            return {"error": "retrospective_action_project_key must match ^[A-Z][A-Z0-9]{0,9}$"}
        action_jql = (
            "project = " + retrospective_action_project_key
            + " AND labels = retro-action ORDER BY created DESC"
        )
        action_search = _request(
            cfg, "POST", "/search/jql",
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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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
    if not re.match(r'^[A-Z][A-Z0-9]{0,9}$', project_key.strip()):
        raise ValueError("project_key must match ^[A-Z][A-Z0-9]{0,9}$ (e.g. PROJ)")

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
        cfg, "POST", "/search/jql",
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

        js_val = int(sp) if sp > 0 else 1
        try:
            wsjf_val = round(scrum_calculator.wsjf_score(1, 1, 1, js_val), 4)
        except (ValueError, ZeroDivisionError):
            wsjf_val = 0.0
        wsjf_stories.append({
            "issue_key": issue.get("key", ""),
            "summary": fields.get("summary", ""),
            "issue_type": (fields.get("issuetype") or {}).get("name", ""),
            "priority": priority_name,
            "story_points": sp,
            "epic_link": epic_link,
            "has_description": has_description,
            "wsjf_score": wsjf_val,
            "wsjf_template": {
                "business_value": "?",
                "time_criticality": "?",
                "risk_reduction": "?",
                "job_size": js_val,
            },
        })

    wsjf_stories.sort(key=lambda x: x.get("wsjf_score", 0.0), reverse=True)

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

@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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
            board_id, sprints_analyzed, velocity_history, velocity_stats
            (includes mean, stdev, min, max, nasscom_benchmark; plus supplemental
            BCa bootstrap CI keys bca_ci_lower, bca_ci_upper, bca_point_estimate,
            bca_confidence, bca_B when velocity data is available), ewma_last,
            ewma_alpha.
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
        closed_sprints = _recent_closed_sprints(cfg, board_id, num_sprints)

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

    if velocity_points:
        bca_result = scrum_calculator.bootstrap_bca_ci(
            [float(v) for v in velocity_points],
            confidence=0.95,
            B=1000,
        )
        if "error" not in bca_result:
            vstats["bca_ci_lower"] = bca_result["lower"]
            vstats["bca_ci_upper"] = bca_result["upper"]
            vstats["bca_point_estimate"] = bca_result["point_estimate"]
            vstats["bca_confidence"] = bca_result["confidence"]
            vstats["bca_B"] = bca_result["B"]
        else:
            vstats["bca_note"] = bca_result.get("note", bca_result.get("error", "BCa skipped"))

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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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
        Dict with keys (among others):
            sprint_id, board_id, sprint_name, state,
            total_issues, done_issues, in_progress_issues, todo_issues,
            story_points_total, story_points_done, projected_completion_pct,
            burndown_deviation_pct, scope_change_pct,
            cycle_time_p85_days (proxy: days elapsed / done issues, not lognormal MLE),
            wip_current, throughput_per_day, sprint_health, health_reason,
            issue_type_breakdown, days_elapsed, days_remaining,
            nasscom_agile_x_level.
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

    # Issue #7. projected_completion_pct is initialised to 0.0 and only
    # computed when story_points_total > 0, so the branch below read
    # "never measured" as "zero per cent done". Two silent consequences:
    # a sprint that had not started reported "Off Track", and any team
    # tracking by issue count rather than story points reported "Off
    # Track" permanently -- story_points_total was always 0, and the
    # issue counts this function already computes were never consulted.
    measured = story_points_total > 0
    if not measured and total_issues > 0:
        projected_completion_pct = round(
            done_issues / float(total_issues) * 100, 1)
        measured = True

    if sprint_state != "active":
        sprint_health = "Not Started" if sprint_state == "future" else "Closed"
        health_reason = (
            "Sprint state is '%s'; health applies to active sprints"
            % sprint_state)
        projected_completion_pct = None
    elif not measured:
        sprint_health = "No Data"
        health_reason = "Sprint has no issues and no story points"
        projected_completion_pct = None
    elif projected_completion_pct >= 80:
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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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
    if not project_key or not re.match(r'^[A-Z][A-Z0-9]{0,9}$', project_key.strip()):
        raise ValueError("project_key must match ^[A-Z][A-Z0-9]{0,9}$ (e.g. PROJ)")

    jql = 'project = "' + project_key + '" AND labels = "impediment"'
    if sprint_id is not None:
        jql += " AND sprint = " + str(sprint_id)
    jql += " ORDER BY created ASC"

    search_result = _request(
        cfg, "POST", "/search/jql",
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


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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
    closed_sprints = _recent_closed_sprints(cfg, board_id, num_sprints)

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

    tuckman_meta = {}
    if len(velocity_points) >= 2:
        markov_result = scrum_calculator.tuckman_markov(velocity_points)
        if "error" not in markov_result:
            tuckman_stage = markov_result["current_stage"]
            tuckman_meta = {
                "tuckman_stage_probabilities": markov_result["stage_probabilities"],
                "tuckman_nasscom_level": markov_result["nasscom_agile_x_level"],
                "tuckman_empirical_caveat": markov_result["empirical_caveat"],
            }
        else:
            tuckman_stage = scrum_calculator.tuckman_estimate(
                velocity_cv=cv_val,
                velocity_trend=velocity_trend,
                team_age_sprints=len(velocity_points),
            )
    else:
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

    result = {
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
    result.update(tuckman_meta)
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
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
    iterations = max(1, min(100000, iterations))

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
        closed_sprints = _recent_closed_sprints(cfg, board_id, num_velocity_samples)

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

# ---------------------------------------------------------------------------
# Phase B.1 New Tools: Scrum Master Knowledge Graph Extensions (9 tools)
# ---------------------------------------------------------------------------


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_spotify_health_check(
    board_id: int,
    dimension_scores: str,
    prev_dimension_scores: Optional[str] = None,
) -> dict:
    """Run Spotify Squad Health Check scoring for a team.

    Computes THS (Team Health Score) across 11 standard dimensions using
    uniform weights. Optionally computes Wilcoxon signed-rank Z statistic
    for quarter-on-quarter delta if prev_dimension_scores is provided.

    11 required dimensions (keys in dimension_scores JSON):
      easy_to_release, suitable_process, tech_quality, value, speed,
      mission, fun, learning, support, pawns_or_players, team_spirit

    Args:
        board_id: Jira board ID for context (used for audit trail, not for data fetch).
        dimension_scores: JSON string mapping each of the 11 dimension names to
            a list of integer scores (0=unhealthy, 1=neutral, 2=healthy).
            Example: '{"easy_to_release": [1, 2, 1], "suitable_process": [2, 2], ...}'
        prev_dimension_scores: Optional JSON string mapping dimension names to
            previous period mean scores (floats) for delta computation.
            Example: '{"easy_to_release": 1.5, "suitable_process": 2.0, ...}'

    Returns:
        Dict with keys:
            THS (float): Team Health Score 0.0-2.0.
            dimension_scores (Dict[str, float]): Per-dimension mean scores.
            health_color (str): "Green" (>=1.5), "Amber" (>=0.75), "Red" (<0.75).
            wilcoxon_Z (float or null): Z statistic if prev provided.
            delta_vs_previous (float or null): THS delta from previous period.
    """
    if not isinstance(board_id, int) or board_id <= 0:
        raise ValueError("board_id must be a positive integer")
    clean_scores = validate_input(dimension_scores, max_length=4096, field_name="dimension_scores")
    scores_dict = json.loads(clean_scores)
    prev_dict = None
    if prev_dimension_scores:
        clean_prev = validate_input(prev_dimension_scores, max_length=4096, field_name="prev_dimension_scores")
        prev_dict = json.loads(clean_prev)
    result = scrum_calculator.spotify_health_check(scores_dict, prev_scores=prev_dict)
    if "error" in result:
        return {"success": False, "error": result["error"], "error_type": "COMPUTATION_ERROR"}
    result["success"] = True
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_psychological_safety(
    board_id: int,
    item_scores: str,
) -> dict:
    """Compute Edmondson Psychological Safety Scale score for a team.

    Applies reverse-coding to items at positions 0, 2, 4 (0-indexed) per
    Edmondson (1999). Returns a PS score in range 1.0-7.0.

    Args:
        board_id: Jira board ID for context (not used for data fetch).
        item_scores: JSON array of exactly 7 integers, each in [1, 7].
            Example: '[3, 5, 2, 6, 4, 5, 3]'
            Items at positions 0, 2, 4 are reverse-coded (8 - score).

    Returns:
        Dict with keys:
            PS_score (float): Mean psychological safety score (1.0-7.0).
            cronbach_alpha (float): Estimated Cronbach alpha.
            interpretation (str): "Low" (<3.5), "Moderate" (3.5-5.5), "High" (>5.5).
            reverse_coded_positions (List[int]): [0, 2, 4].
    """
    if not isinstance(board_id, int) or board_id <= 0:
        raise ValueError("board_id must be a positive integer")
    clean_scores = validate_input(item_scores, max_length=4096, field_name="item_scores")
    raw_scores = json.loads(clean_scores)
    if not isinstance(raw_scores, list):
        return {"success": False, "error": "item_scores must be a JSON array of 7 integers", "error_type": "VALIDATION_ERROR"}
    result = scrum_calculator.edmondson_ps_scale(raw_scores)
    if "error" in result:
        return {"success": False, "error": result["error"], "error_type": "COMPUTATION_ERROR"}
    result["success"] = True
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_cognitive_load(
    board_id: int,
    complexity_json: str,
    responsibility_json: str,
    cl_max: float = 10.0,
) -> dict:
    """Compute Team Topology Cognitive Load Index (CLI) for a team's domain portfolio.

    CLI = sum(complexity[d] * responsibility[d] for d in common domains) / cl_max
    overloaded = CLI > 1.0

    Args:
        board_id: Jira board ID for context (not used for data fetch).
        complexity_json: JSON object mapping domain name to complexity weight (float >= 0).
            Example: '{"payments": 3.5, "auth": 2.0, "reporting": 1.5}'
        responsibility_json: JSON object mapping domain name to responsibility
            fraction (float >= 0).
            Example: '{"payments": 0.8, "auth": 1.0, "reporting": 0.5}'
        cl_max: Maximum cognitive load threshold (default 10.0). Must be > 0.

    Returns:
        Dict with keys:
            CL_team (float): Raw cognitive load sum across common domains.
            CLI (float): Normalized cognitive load index (CL_team / cl_max).
            overloaded (bool): True if CLI > 1.0.
            domain_contributions (Dict[str, float]): Per-domain load contribution.
            cl_max (float): Threshold used.
            topology_efficiency (Dict[str, float]): Reference mode efficiency factors.
    """
    if not isinstance(board_id, int) or board_id <= 0:
        raise ValueError("board_id must be a positive integer")
    if cl_max <= 0.0:
        raise ValueError("cl_max must be > 0")
    clean_comp = validate_input(complexity_json, max_length=4096, field_name="complexity_json")
    clean_resp = validate_input(responsibility_json, max_length=4096, field_name="responsibility_json")
    complexity = json.loads(clean_comp)
    responsibility = json.loads(clean_resp)
    result = scrum_calculator.cognitive_load_index(complexity, responsibility, cl_max=cl_max)
    result["success"] = True
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_attrition_forecast(
    board_id: int,
    months: float,
    p_max: float,
    tau: float = 6.0,
) -> dict:
    """Forecast cumulative attrition impact on team velocity using exponential model.

    P(t) = p_max * (1 - exp(-months / tau))
    effective_velocity_factor = 1 - P(t)

    tau reference values (NASSCOM HR 2024):
      6 months for experienced hires; 12 months for fresh graduates.

    Args:
        board_id: Jira board ID for context (not used for data fetch).
        months: Time elapsed in months (must be > 0).
        p_max: Maximum asymptotic attrition probability; fraction in (0, 1].
        tau: Exponential time constant in months (default 6.0, must be > 0).

    Returns:
        Dict with keys:
            attrition_probability (float): Cumulative attrition at t=months.
            months (float): Input time.
            tau_months (float): Time constant used.
            p_max (float): Input maximum attrition fraction.
            effective_velocity_factor (float): Remaining effective velocity fraction.
            india_context (str): NASSCOM HR 2024 context note.
    """
    if not isinstance(board_id, int) or board_id <= 0:
        raise ValueError("board_id must be a positive integer")
    result = scrum_calculator.attrition_ramp(months, p_max, tau=tau)
    if "error" in result:
        return {"success": False, "error": result["error"], "error_type": "VALIDATION_ERROR"}
    result["success"] = True
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_pert_estimate(
    optimistic: float,
    most_likely: float,
    pessimistic: float,
) -> dict:
    """Compute a PERT (Program Evaluation and Review Technique) task estimate.

    mu = (optimistic + 4 * most_likely + pessimistic) / 6
    sigma = (pessimistic - optimistic) / 6
    90% CI = mu +/- 1.645 * sigma

    Args:
        optimistic: Best-case estimate in days (must be <= most_likely).
        most_likely: Most probable estimate in days.
        pessimistic: Worst-case estimate in days (must be >= most_likely).

    Returns:
        Dict with keys:
            mu_days (float): PERT weighted mean estimate in days.
            sigma_days (float): PERT standard deviation in days.
            ci_90_lower (float): 90% CI lower bound in days.
            ci_90_upper (float): 90% CI upper bound in days.
            optimistic (float): Input optimistic value.
            most_likely (float): Input most_likely value.
            pessimistic (float): Input pessimistic value.
    """
    result = scrum_calculator.pert_estimate(optimistic, most_likely, pessimistic)
    if "error" in result:
        return {"success": False, "error": result["error"], "error_type": "VALIDATION_ERROR"}
    result["success"] = True
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_scrum_of_scrums(
    teams: int,
    productivity_per_team: float,
    coordination_cost: float,
) -> dict:
    """Compute Scrum of Scrums Brook's Law overhead and optimal team count.

    T_n = teams * p - c * teams * (teams - 1) / 2
    n_optimal = p / c + 0.5
    overhead_ratio = coordination_overhead / total_raw_capacity

    Args:
        teams: Number of participating Scrum teams (must be >= 2).
        productivity_per_team: Baseline sprint velocity per team (must be > 0).
            Typically in story points per sprint.
        coordination_cost: Communication overhead cost per team pair per sprint
            (must be > 0 and < productivity_per_team). Typically in story points.

    Returns:
        Dict with keys:
            T_n (float): Net throughput after coordination overhead.
            n_optimal (float): Team count that maximizes throughput.
            overhead_ratio (float): Fraction of capacity lost to coordination.
            teams (int): Input team count.
            productivity_per_team (float): Input p value.
            coordination_cost (float): Input c value.
    """
    result = scrum_calculator.scrum_of_scrums_overhead(
        teams, productivity_per_team, coordination_cost
    )
    if "error" in result:
        return {"success": False, "error": result["error"], "error_type": "VALIDATION_ERROR"}
    result["success"] = True
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_ist_capacity(
    nominal_capacity: float,
    overlap_hours: float = 4.0,
) -> dict:
    """Compute IST timezone distributed team effective capacity.

    Applies a correction factor for the reduced collaboration window when
    teams span IST (UTC+5:30) and US timezones.

    correction_factor = overlap_hours / 8.0
    effective_capacity = nominal_capacity * correction_factor

    Args:
        nominal_capacity: Nominal sprint capacity in story points or hours.
        overlap_hours: Daily effective collaboration window in hours (default 4.0).
            Typical US-India overlap: 4 hours/day (9am-1pm IST window).

    Returns:
        Dict with keys:
            effective_capacity (float): Adjusted capacity after timezone correction.
            nominal (float): Input nominal capacity.
            overlap_hours (float): Overlap hours used.
            correction_factor (float): overlap_hours / 8.0.
            q1_seasonal_buffer_factor (float): 1.15 for Q1 Jan-Mar attrition buffer.
            india_context (str): IST timezone and Q1 context note.
    """
    result = scrum_calculator.ist_capacity_correction(nominal_capacity, overlap_hours=overlap_hours)
    result["success"] = True
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_multi_sprint_holidays(
    sprint_start: str,
    sprint_duration_days: int = 14,
    num_sprints: int = 3,
) -> dict:
    """Forecast India national holidays across consecutive sprint windows.

    Uses INDIA_NATIONAL_HOLIDAYS_2025_2026 constant from scrum_calculator.py.
    Dates outside 2025-2026 range will show 0 holidays (no error).

    Args:
        sprint_start: Sprint 1 start date as ISO string "YYYY-MM-DD".
        sprint_duration_days: Calendar days per sprint (default 14, must be >= 1).
        num_sprints: Number of consecutive sprints to analyze (default 3, must be >= 1).

    Returns:
        Dict with key:
            sprints (List[Dict]): Per-sprint records, each with:
                sprint_number (int): 1-based index.
                start_date (str): Sprint start "YYYY-MM-DD".
                end_date (str): Sprint end "YYYY-MM-DD" (inclusive).
                holiday_count (int): India holidays in window.
                holiday_names (List[str]): Holiday names in window.
                effective_days (int): sprint_duration_days - holiday_count.
    """
    clean_start = validate_input(sprint_start, max_length=20, field_name="sprint_start")
    result = scrum_calculator.multi_sprint_holiday_forecast(
        clean_start, sprint_duration_days, num_sprints
    )
    if "error" in result:
        return {"success": False, "error": result["error"], "error_type": "VALIDATION_ERROR"}
    result["success"] = True
    return result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_rate_limit_status() -> dict:
    """Return the current rate limiter bucket status (read-only).

    Reads the internal rate_limiter module state to report on current token
    counts, capacity, and refill rates for all active buckets. This tool
    makes NO modifications to rate limiter state.

    Only meaningful when ENABLE_RATE_LIMITING=1 is set in the environment.
    When rate limiting is disabled, returns a disabled status report.

    Returns:
        Dict with keys:
            rate_limiting_enabled (bool): Whether ENABLE_RATE_LIMITING=1 is set.
            buckets (List[Dict]): Per-bucket status records, each with:
                client_id (str): Client identifier.
                bucket_name (str): Bucket name (e.g. "tool_calls").
                capacity (float): Maximum token capacity.
                refill_rate_per_sec (float): Tokens added per second.
                tokens_available (float): Approximate current token count.
            bucket_count (int): Total number of active buckets.
    """
    import rate_limiter as _rl

    enabled = os.environ.get("ENABLE_RATE_LIMITING") == "1"

    buckets_snapshot = []
    with _rl._buckets_lock:
        for (client_id, bucket_name), bucket in _rl._buckets.items():
            with bucket._lock:
                bucket._refill()
                buckets_snapshot.append({
                    "client_id": client_id,
                    "bucket_name": bucket_name,
                    "capacity": bucket._capacity,
                    "refill_rate_per_sec": bucket._refill_rate,
                    "tokens_available": round(bucket._tokens, 4),
                })

    return {
        "success": True,
        "rate_limiting_enabled": enabled,
        "buckets": buckets_snapshot,
        "bucket_count": len(buckets_snapshot),
    }


# ---------------------------------------------------------------------------
# Phase B.2 New Tools: Agile Tooling Knowledge Graph Extensions (7 tools)
# ---------------------------------------------------------------------------


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_burndown_chart(board_id: int, sprint_id: int) -> dict:
    """Fetch sprint burndown data and compute burndown health metrics.

    Retrieves raw burndown chart data from the Jira Agile rapid charts API
    and passes it to scrum_calculator.burndown_metrics() to produce ideal
    vs. actual trend comparison, slope analysis, and sprint health verdict.

    Args:
        board_id: Numeric Jira board ID (rapid view ID). Must be >= 1.
        sprint_id: Numeric sprint ID for the burndown period. Must be >= 1.

    Returns:
        Dict with success=True and keys:
            board_id (int): Echo of board_id.
            sprint_id (int): Echo of sprint_id.
            total_points (float): Total story points at sprint start.
            burndown_metrics (dict): Output from scrum_calculator.burndown_metrics().
    """
    if not isinstance(board_id, int) or board_id < 1:
        raise ValueError("board_id must be >= 1")
    if not isinstance(sprint_id, int) or sprint_id < 1:
        raise ValueError("sprint_id must be >= 1")

    cfg = _get_config()
    client = AgileClient(cfg)

    raw = client.get_burndown_chart(board_id, sprint_id)
    if raw is None:
        return {
            "success": False,
            "error": "Jira returned no burndown data for board_id={} sprint_id={}".format(board_id, sprint_id),
            "error_type": "INVALID_RESPONSE",
        }

    completed_arr = raw.get("completedPoints") or []
    incompleted_arr = raw.get("incompletedPoints") or []

    if not completed_arr and not incompleted_arr:
        return {
            "success": False,
            "error": "Burndown response missing completedPoints and incompletedPoints arrays",
            "error_type": "INVALID_RESPONSE",
        }

    if incompleted_arr and completed_arr:
        first_incomplete = incompleted_arr[0] if isinstance(incompleted_arr[0], (int, float)) else 0
        first_complete = completed_arr[0] if isinstance(completed_arr[0], (int, float)) else 0
        total_points = float(first_incomplete + first_complete)
    elif incompleted_arr:
        first = incompleted_arr[0]
        total_points = float(first) if isinstance(first, (int, float)) else 0.0
    else:
        total_points = float(max(completed_arr)) if completed_arr else 0.0

    if completed_arr and isinstance(completed_arr[0], dict):
        completed_by_day = [float(entry.get("value", 0)) for entry in completed_arr]
    else:
        completed_by_day = [float(v) for v in completed_arr]

    metrics = scrum_calculator.burndown_metrics(total_points, completed_by_day)

    return {
        "success": True,
        "board_id": board_id,
        "sprint_id": sprint_id,
        "total_points": total_points,
        "burndown_metrics": metrics,
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_cfd_analysis(board_id: int) -> dict:
    """Fetch cumulative flow diagram data and apply Little's Law analysis.

    Retrieves CFD column data from the Jira Agile rapid charts API and
    passes arrival/departure streams to scrum_calculator.little_law_analysis()
    to estimate average WIP, average cycle time, and throughput rate.

    Args:
        board_id: Numeric Jira board ID (rapid view ID). Must be >= 1.

    Returns:
        Dict with success=True and keys:
            board_id (int): Echo of board_id.
            little_law (dict): Output from scrum_calculator.little_law_analysis().
    """
    if not isinstance(board_id, int) or board_id < 1:
        raise ValueError("board_id must be >= 1")

    cfg = _get_config()
    client = AgileClient(cfg)

    raw = client.get_cfd(board_id)
    if raw is None:
        return {
            "success": False,
            "error": "Jira returned no CFD data for board_id={}".format(board_id),
            "error_type": "INVALID_RESPONSE",
        }

    column_data = raw.get("columnData") or []
    if not column_data:
        return {
            "success": False,
            "error": "CFD response missing columnData array",
            "error_type": "INVALID_RESPONSE",
        }

    arrivals = []
    departures = []

    for day_entry in column_data:
        day_label = day_entry.get("date", "")
        columns = day_entry.get("columns") or []

        if columns:
            first_col_count = int(columns[0].get("count", 0)) if columns else 0
            arrivals.append({"date": day_label, "count": first_col_count})

        done_count = 0
        for col in columns:
            col_name = (col.get("name") or col.get("status") or "").lower()
            if "done" in col_name or "complete" in col_name or "closed" in col_name:
                done_count = int(col.get("count", 0))
                break
        departures.append({"date": day_label, "count": done_count})

    little_law_result = scrum_calculator.little_law_analysis(arrivals, departures)

    return {
        "success": True,
        "board_id": board_id,
        "little_law": little_law_result,
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_cycle_time_analysis(board_id: int, sprint_id: int) -> dict:
    """Compute cycle time distribution for issues resolved in a sprint.

    Fetches sprint issues and individual issue changelogs, computes cycle
    time in days from created to resolutiondate, then fits a log-normal
    distribution using scrum_calculator.cycle_time_lognormal_mle().

    Args:
        board_id: Numeric Jira board ID. Must be >= 1.
        sprint_id: Numeric sprint ID. Must be >= 1.

    Returns:
        Dict with success=True and keys:
            board_id (int): Echo of board_id.
            sprint_id (int): Echo of sprint_id.
            lognormal_fit (dict): Output from scrum_calculator.cycle_time_lognormal_mle().
            per_issue_cycle_times (dict): Mapping of issue_key to cycle_time_days.
            resolved_count (int): Number of issues with resolved cycle times.
    """
    if not isinstance(board_id, int) or board_id < 1:
        raise ValueError("board_id must be >= 1")
    if not isinstance(sprint_id, int) or sprint_id < 1:
        raise ValueError("sprint_id must be >= 1")

    cfg = _get_config()
    client = AgileClient(cfg)

    sprint_issues_raw = client.get_sprint_issues(
        sprint_id,
        fields="summary,status,created,resolutiondate"
    )
    if sprint_issues_raw is None:
        return {
            "success": False,
            "error": "No issues found for sprint_id={}".format(sprint_id),
            "error_type": "INVALID_RESPONSE",
        }

    issue_list = sprint_issues_raw.get("issues") or []

    cycle_times_dict = {}
    cycle_time_list = []

    for issue in issue_list:
        key = issue.get("key", "")
        fields = issue.get("fields") or {}
        created_str = fields.get("created") or ""
        resolution_str = fields.get("resolutiondate") or ""

        if not created_str or not resolution_str:
            continue

        try:
            from datetime import datetime as _dt
            fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
            try:
                created_dt = _dt.strptime(created_str[:26] + "+0000", fmt)
            except ValueError:
                created_dt = _dt.fromisoformat(created_str[:10])
            try:
                resolved_dt = _dt.strptime(resolution_str[:26] + "+0000", fmt)
            except ValueError:
                resolved_dt = _dt.fromisoformat(resolution_str[:10])

            if hasattr(created_dt, "date"):
                delta_days = (resolved_dt.date() - created_dt.date()).days
            else:
                delta_days = (resolved_dt - created_dt).days

            if delta_days >= 0:
                cycle_times_dict[key] = delta_days
                cycle_time_list.append(float(delta_days))
        except Exception:
            continue

    if len(cycle_time_list) < 2:
        return {
            "success": False,
            "error": (
                "Insufficient resolved issues for cycle time analysis: "
                "found {} resolved issues, need at least 2".format(len(cycle_time_list))
            ),
            "error_type": "INSUFFICIENT_DATA",
        }

    lognormal_result = scrum_calculator.cycle_time_lognormal_mle(cycle_time_list)

    return {
        "success": True,
        "board_id": board_id,
        "sprint_id": sprint_id,
        "lognormal_fit": lognormal_result,
        "per_issue_cycle_times": cycle_times_dict,
        "resolved_count": len(cycle_time_list),
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_throughput_forecast(
    board_id: int,
    num_sprints: int = 5,
    forecast_periods: int = 3,
) -> dict:
    """Forecast future sprint throughput using a Poisson model.

    Fetches closed sprint data from the Jira Agile API, extracts completed
    issue counts for recent sprints, then applies
    scrum_calculator.poisson_throughput() to produce a probabilistic
    delivery forecast over the requested number of future periods.

    Args:
        board_id: Numeric Jira board ID. Must be >= 1.
        num_sprints: Number of historical closed sprints to use as input
                     to the forecast model (default 5). Must be >= 1.
        forecast_periods: Number of future sprints to forecast (default 3).
                          Must be >= 1.

    Returns:
        Dict with success=True and keys:
            board_id (int): Echo of board_id.
            historical_sprints (int): Actual number of closed sprints sampled.
            forecast_periods (int): Echo of forecast_periods.
            poisson_forecast (dict): Output from scrum_calculator.poisson_throughput().
    """
    if not isinstance(board_id, int) or board_id < 1:
        raise ValueError("board_id must be >= 1")
    num_sprints = max(1, int(num_sprints))
    forecast_periods = max(1, int(forecast_periods))

    cfg = _get_config()
    client = AgileClient(cfg)

    sprints_raw = client.get_sprints(board_id, state="closed", max_results=100)
    if sprints_raw is None:
        return {
            "success": False,
            "error": "No closed sprints found for board_id={}".format(board_id),
            "error_type": "INVALID_RESPONSE",
        }

    sprint_values = sprints_raw.get("values") or sprints_raw.get("sprints") or []
    recent_sprints = sprint_values[-num_sprints:] if len(sprint_values) >= num_sprints else sprint_values

    completed_per_sprint = []
    for s in recent_sprints:
        count = (
            s.get("completedIssuesCount")
            or s.get("completedIssues")
            or s.get("issueCount")
            or 0
        )
        completed_per_sprint.append(int(count))

    if not completed_per_sprint or all(c == 0 for c in completed_per_sprint):
        return {
            "success": False,
            "error": (
                "Cannot compute throughput forecast: no completed issue counts "
                "found in closed sprints for board_id={}".format(board_id)
            ),
            "error_type": "INSUFFICIENT_DATA",
        }

    poisson_result = scrum_calculator.poisson_throughput(
        completed_per_sprint, forecast_periods
    )

    return {
        "success": True,
        "board_id": board_id,
        "historical_sprints": len(completed_per_sprint),
        "forecast_periods": forecast_periods,
        "poisson_forecast": poisson_result,
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_automation_analyzer(
    trigger_rates_json: str,
    service_rates_json: str,
    rules_dag_json: str,
) -> dict:
    """Analyze Jira automation rule queue stability and DAG cycle safety.

    Applies M/M/1 queueing theory to each automation rule to estimate
    queue stability, expected queue length, and wait time. Also performs
    Kahn's topological sort on the rules DAG to detect circular trigger
    chains that would cause infinite automation loops.

    Args:
        trigger_rates_json: JSON array of floats representing per-rule
                            trigger arrival rates (events per minute).
                            Example: "[2.0, 0.5, 1.2]"
        service_rates_json: JSON array of floats representing per-rule
                            service (execution) rates (completions per minute).
                            Must have the same length as trigger_rates_json.
                            Example: "[5.0, 3.0, 4.0]"
        rules_dag_json: JSON object (adjacency list) mapping each rule name
                        to a list of downstream rule names it triggers.
                        Example: '{"rule_A": ["rule_B"], "rule_B": [], "rule_C": ["rule_A"]}'

    Returns:
        Dict with success=True and keys:
            mm1_analysis (list): Per-rule dicts with fields:
                rule_index (int), lambda_val (float), mu_val (float),
                rho_val (float), stable (bool), E_L (float), E_W (float).
            dag_has_cycle (bool): True if a circular trigger chain was detected.
            node_count (int): Total number of rules in the DAG.
    """
    clean_trigger = validate_input(trigger_rates_json, max_length=4096, field_name="trigger_rates_json")
    clean_service = validate_input(service_rates_json, max_length=4096, field_name="service_rates_json")
    clean_dag = validate_input(rules_dag_json, max_length=8192, field_name="rules_dag_json")

    try:
        trigger_rates = json.loads(clean_trigger)
    except ValueError as exc:
        return {"success": False, "error": "Invalid JSON for trigger_rates_json: " + str(exc), "error_type": "VALIDATION_ERROR"}

    try:
        service_rates = json.loads(clean_service)
    except ValueError as exc:
        return {"success": False, "error": "Invalid JSON for service_rates_json: " + str(exc), "error_type": "VALIDATION_ERROR"}

    try:
        rules_dag = json.loads(clean_dag)
    except ValueError as exc:
        return {"success": False, "error": "Invalid JSON for rules_dag_json: " + str(exc), "error_type": "VALIDATION_ERROR"}

    if not isinstance(trigger_rates, list) or not isinstance(service_rates, list):
        return {"success": False, "error": "trigger_rates_json and service_rates_json must be JSON arrays", "error_type": "VALIDATION_ERROR"}

    if len(trigger_rates) != len(service_rates):
        return {
            "success": False,
            "error": "trigger_rates and service_rates must have equal length; got {} and {}".format(
                len(trigger_rates), len(service_rates)
            ),
            "error_type": "VALIDATION_ERROR",
        }

    if not isinstance(rules_dag, dict):
        return {"success": False, "error": "rules_dag_json must be a JSON object (adjacency list)", "error_type": "VALIDATION_ERROR"}

    mm1_analysis = []
    for i in range(len(trigger_rates)):
        lambda_val = float(trigger_rates[i])
        mu_val = float(service_rates[i])
        if mu_val <= 0:
            rho_val = float("inf")
            stable = False
            e_l = float("inf")
            e_w = float("inf")
        else:
            rho_val = lambda_val / mu_val
            stable = rho_val < 1.0
            if stable:
                e_l = rho_val / (1.0 - rho_val)
                e_w = 1.0 / (mu_val - lambda_val)
            else:
                e_l = float("inf")
                e_w = float("inf")

        mm1_analysis.append({
            "rule_index": i,
            "lambda_val": round(lambda_val, 6),
            "mu_val": round(mu_val, 6),
            "rho_val": round(rho_val, 6) if rho_val != float("inf") else "inf",
            "stable": stable,
            "E_L": round(e_l, 4) if e_l != float("inf") else "inf",
            "E_W": round(e_w, 4) if e_w != float("inf") else "inf",
        })

    in_degree = {}
    for node in rules_dag:
        if node not in in_degree:
            in_degree[node] = 0
        for neighbor in rules_dag.get(node, []):
            in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

    queue = [n for n, d in in_degree.items() if d == 0]
    processed = 0
    while queue:
        node = queue.pop(0)
        processed += 1
        for neighbor in rules_dag.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    dag_has_cycle = processed < len(in_degree)

    return {
        "success": True,
        "mm1_analysis": mm1_analysis,
        "dag_has_cycle": dag_has_cycle,
        "node_count": len(rules_dag),
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_tco_analysis(
    user_count: int,
    years: int = 3,
    discount_rate: float = 0.10,
) -> dict:
    """Compute Total Cost of Ownership and NPV comparison for Jira licensing tiers.

    Delegates to scrum_calculator.tco_npv_comparison() which models
    licensing, infrastructure, and support costs across Jira Cloud Standard,
    Jira Cloud Premium, and Jira Data Center tiers for the given team size,
    amortized over the specified time horizon using NPV discounting.

    Args:
        user_count: Number of Jira users for the TCO calculation. Must be >= 1.
        years: Time horizon in years for NPV computation (default 3).
               Must be >= 1.
        discount_rate: Annual discount rate as a decimal fraction (default 0.10
                       for 10%). Must be in range (0, 1).

    Returns:
        Dict with success=True and the full output dict from
        scrum_calculator.tco_npv_comparison(). Keys include:
            jira_premium_3yr_npv_inr (float): NPV of Jira Premium total cost (INR).
            azure_devops_3yr_npv_inr (float): NPV of Azure DevOps total cost (INR).
            break_even_users (int): User count at which both platforms cost the same.
            recommendation (str): "Jira Premium" or "Azure DevOps".
            user_count (int): Input user count echoed back.
            discount_rate (float): Discount rate used.
    """
    if not isinstance(user_count, int) or user_count < 1:
        raise ValueError("user_count must be >= 1")

    try:
        years_int = int(years)
        if years_int < 1:
            raise ValueError("years must be >= 1")
    except (TypeError, ValueError) as exc:
        return {"success": False, "error": "Invalid years value: " + str(exc), "error_type": "VALIDATION_ERROR"}

    try:
        rate = float(discount_rate)
        if rate <= 0.0 or rate >= 1.0:
            raise ValueError("discount_rate must be in range (0, 1)")
    except (TypeError, ValueError) as exc:
        return {"success": False, "error": "Invalid discount_rate value: " + str(exc), "error_type": "VALIDATION_ERROR"}

    tco_result = scrum_calculator.tco_npv_comparison(user_count, years_int, rate)
    tco_result["success"] = True
    return tco_result


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_nasscom_mapping(board_id: int, sprint_id: int) -> dict:
    """Map Jira sprint data to NASSCOM AgileX L1-L5 maturity dimensions.

    Fetches sprint issues and velocity history from the Jira Agile API,
    then evaluates each of the five NASSCOM AgileX maturity dimensions
    using evidence directly observable from Jira data. Produces a maturity
    score per dimension and an overall level estimate (L1-L5).

    NASSCOM AgileX dimensions assessed:
        L1 Initiation: Backlog exists and sprint has issues.
        L2 Planning: Sprint has a defined goal and issues are estimated.
        L3 Execution: Velocity variance is consistent (CV <= 0.25).
        L4 Optimization: Cycle time data is available (issues are resolved).
        L5 Innovation: Multiple closed sprints with high retrospective
                       completion rate (proxied from completion ratio).

    Args:
        board_id: Numeric Jira board ID. Must be >= 1.
        sprint_id: Numeric sprint ID to evaluate. Must be >= 1.

    Returns:
        Dict with success=True and keys:
            board_id (int): Echo of board_id.
            sprint_id (int): Echo of sprint_id.
            nasscom_agile_x (dict): Per-dimension maturity evidence and score.
            overall_level (str): Estimated overall maturity level "L1" through "L5".
            india_context (str): Note on NASSCOM AgileX applicability in India.
    """
    if not isinstance(board_id, int) or board_id < 1:
        raise ValueError("board_id must be >= 1")
    if not isinstance(sprint_id, int) or sprint_id < 1:
        raise ValueError("sprint_id must be >= 1")

    cfg = _get_config()
    client = AgileClient(cfg)

    sprint_issues_raw = client.get_sprint_issues(
        sprint_id,
        fields="summary,status,created,resolutiondate,story_points,customfield_10016,customfield_10028"
    )
    if sprint_issues_raw is None:
        sprint_issues_raw = {}

    issue_list = sprint_issues_raw.get("issues") or []

    sprint_meta_raw = {}
    try:
        sprint_meta_raw = client.get_sprint(sprint_id) or {}
    except Exception:
        sprint_meta_raw = {}

    sprint_goal = sprint_meta_raw.get("goal") or ""

    velocity_raw = {}
    velocity_history = []
    try:
        velocity_raw = client.get_velocity(board_id) or {}
    except Exception:
        velocity_raw = {}

    if velocity_raw:
        entries = velocity_raw.get("velocityStatEntries") or {}
        for entry_id in sorted(entries.keys()):
            entry = entries[entry_id]
            completed_val = entry.get("completed") or {}
            points = completed_val.get("value", 0)
            try:
                velocity_history.append(int(float(points)))
            except (TypeError, ValueError):
                continue

    maturity_scores = {}

    has_issues = len(issue_list) > 0
    maturity_scores["L1_initiation"] = {
        "dimension": "Initiation",
        "evidence": "Sprint has {} issue(s)".format(len(issue_list)),
        "met": has_issues,
        "score": 1 if has_issues else 0,
    }

    estimated_issues = 0
    for issue in issue_list:
        fields = issue.get("fields") or {}
        sp = (
            fields.get("story_points")
            or fields.get("customfield_10016")
            or fields.get("customfield_10028")
        )
        if sp is not None:
            try:
                if float(sp) > 0:
                    estimated_issues += 1
            except (TypeError, ValueError):
                pass

    has_goal = bool(sprint_goal and sprint_goal.strip())
    has_estimates = estimated_issues > 0
    l2_met = has_goal and has_estimates
    maturity_scores["L2_planning"] = {
        "dimension": "Planning",
        "evidence": "goal='{}' | {} issue(s) estimated".format(
            sprint_goal[:60] if sprint_goal else "", estimated_issues
        ),
        "met": l2_met,
        "score": 2 if l2_met else (1 if has_goal or has_estimates else 0),
    }

    velocity_cv = None
    if len(velocity_history) >= 2:
        import statistics as _stats
        v_mean = _stats.mean(velocity_history)
        if v_mean > 0:
            v_stddev = _stats.pstdev(velocity_history)
            velocity_cv = v_stddev / v_mean
        else:
            velocity_cv = 0.0

    l3_met = velocity_cv is not None and velocity_cv <= 0.25
    maturity_scores["L3_execution"] = {
        "dimension": "Execution",
        "evidence": "velocity CV={} ({} sprints sampled)".format(
            round(velocity_cv, 4) if velocity_cv is not None else "n/a",
            len(velocity_history)
        ),
        "met": l3_met,
        "score": 3 if l3_met else (2 if velocity_cv is not None else 1),
    }

    resolved_count = sum(
        1 for issue in issue_list
        if (issue.get("fields") or {}).get("resolutiondate")
    )
    l4_met = resolved_count > 0
    maturity_scores["L4_optimization"] = {
        "dimension": "Optimization",
        "evidence": "{} of {} issues resolved (cycle time data available)".format(
            resolved_count, len(issue_list)
        ),
        "met": l4_met,
        "score": 4 if l4_met else 3,
    }

    closed_sprint_count = len(velocity_history)
    total_issue_count = len(issue_list)
    done_issue_count = sum(
        1 for issue in issue_list
        if (((issue.get("fields") or {}).get("status") or {}).get("name") or "").lower()
        in ("done", "closed", "resolved", "complete")
    )
    completion_ratio = (done_issue_count / total_issue_count) if total_issue_count > 0 else 0.0
    l5_met = closed_sprint_count >= 5 and completion_ratio >= 0.85 and l3_met
    maturity_scores["L5_innovation"] = {
        "dimension": "Innovation",
        "evidence": "{} closed sprints | completion ratio={} | L3 met={}".format(
            closed_sprint_count, round(completion_ratio, 3), l3_met
        ),
        "met": l5_met,
        "score": 5 if l5_met else (4 if closed_sprint_count >= 5 and l3_met else 3),
    }

    scores = [
        maturity_scores["L1_initiation"]["score"],
        maturity_scores["L2_planning"]["score"],
        maturity_scores["L3_execution"]["score"],
        maturity_scores["L4_optimization"]["score"],
        maturity_scores["L5_innovation"]["score"],
    ]
    min_score = min(scores)
    if min_score >= 5:
        overall_level = "L5"
    elif min_score >= 4:
        overall_level = "L4"
    elif min_score >= 3:
        overall_level = "L3"
    elif min_score >= 2:
        overall_level = "L2"
    else:
        overall_level = "L1"

    india_context = (
        "NASSCOM AgileX framework is specifically designed for Indian IT/ITES teams. "
        "L3+ is the industry-average for Tier-1 Indian IT services firms (TCS, Infosys, Wipro). "
        "L5 corresponds to NASSCOM Digital Transformation Index top-quartile performers. "
        "Velocity benchmarks: 35-45 SP per 2-week sprint for co-located India teams."
    )

    return {
        "success": True,
        "board_id": board_id,
        "sprint_id": sprint_id,
        "nasscom_agile_x": maturity_scores,
        "overall_level": overall_level,
        "india_context": india_context,
    }


# ---------------------------------------------------------------------------
# Epic Management Tools (4)
# ---------------------------------------------------------------------------

@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
@mcp_tool_handler
def jira_create_epic(
    project_key: str,
    name: str,
    summary: str,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    """Create a Jira Epic in the specified project.

    Epic creation is a plain issue creation and is therefore not idempotent.
    Supply ``idempotency_key`` -- generated once per logical intent and reused
    unchanged across every retry -- to make a retry after a lost response
    replay the recorded epic rather than create a second one.

    Args:
        project_key: Jira project key (e.g. PROJ).
        name: Epic name (short label shown on the epic; Cloud customfield_10014).
        summary: Epic title/summary displayed as the issue summary.
        start_date: Optional ISO-8601 start date string (e.g. 2026-06-01).
        due_date: Optional ISO-8601 due date string (e.g. 2026-09-30).
        idempotency_key: Optional caller-generated key scoped to one logical
            epic-creation intent.

    Returns:
        Dict with keys: epic_key, epic_id, summary, name, epic_url.
    """
    project_key = validate_input(project_key, field_name="project_key")
    name = validate_input(name, field_name="name")
    summary = validate_input(summary, field_name="summary")

    def _create() -> dict:
        """Perform the underlying non-idempotent epic creation."""
        cfg = _get_config()

        fields = {
            "project": {"key": project_key},
            "issuetype": {"name": "Epic"},
            "summary": summary,
            "customfield_10014": name,
        }
        if due_date:
            fields["duedate"] = due_date
        if start_date:
            fields["customfield_10015"] = start_date

        result = _request(cfg, "POST", "/issue", {"fields": fields})
        return {
            "epic_key": result.get("key", ""),
            "epic_id": result.get("id", ""),
            "summary": summary,
            "name": name,
            "epic_url": cfg["url"] + "/browse/" + result.get("key", ""),
        }

    return run_once("jira_create_epic", idempotency_key, _create)


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_get_epic(
    epic_key: str,
) -> dict:
    """Fetch Epic details including linked story count and story point rollup.

    Args:
        epic_key: Epic issue key (e.g. PROJ-42).

    Returns:
        Dict with keys: epic_key, summary, status, linked_story_count,
        story_points_total, done_story_count, completion_pct.
    """
    epic_key = _safe_issue_key(epic_key)
    cfg = _get_config()

    safe_epic_key = urllib.request.quote(epic_key, safe="")
    detail = _request(
        cfg, "GET",
        "/issue/" + safe_epic_key + "?fields=summary,status,customfield_10014,customfield_10016"
    )
    raw_fields = detail.get("fields", {})
    status_name = (raw_fields.get("status") or {}).get("name", "")
    epic_summary = raw_fields.get("summary", "")

    jql_safe_key = epic_key.replace('"', '\\"')
    jql = '"Epic Link" = "' + jql_safe_key + '" ORDER BY created ASC'
    if not _is_cloud(cfg):
        jql = 'cf[10014] = "' + jql_safe_key + '" ORDER BY created ASC'
    stories_result = _request(
        cfg, "GET",
        "/search?jql=" + urllib.request.quote(jql)
        + "&fields=summary,status,customfield_10016,customfield_10028,story_points"
        + "&maxResults=100"
    )

    story_issues = (stories_result or {}).get("issues", [])
    linked_story_count = len(story_issues)
    sp_total = 0.0
    done_count = 0
    for issue in story_issues:
        sp = _extract_story_points(issue.get("fields", {}))
        sp_total += sp
        st_name = (issue.get("fields", {}).get("status") or {}).get("name", "")
        if st_name.lower() in ("done", "closed", "resolved"):
            done_count += 1

    completion_pct = round(
        (done_count / linked_story_count * 100) if linked_story_count > 0 else 0.0, 1
    )
    return {
        "epic_key": epic_key,
        "summary": epic_summary,
        "status": status_name,
        "linked_story_count": linked_story_count,
        "story_points_total": round(sp_total, 1),
        "done_story_count": done_count,
        "completion_pct": completion_pct,
    }


@_tool(read_only=False, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_link_to_epic(
    issue_key: str,
    epic_key: str,
) -> dict:
    """Link an existing issue to an Epic by setting the Epic Link field.

    Args:
        issue_key: Issue key to link (e.g. PROJ-10).
        epic_key: Target epic key (e.g. PROJ-42).

    Returns:
        Dict with keys: issue_key, epic_key, linked (bool).
    """
    issue_key = _safe_issue_key(issue_key)
    epic_key = _safe_issue_key(epic_key)
    cfg = _get_config()

    _request(
        cfg, "PUT",
        "/issue/" + urllib.request.quote(issue_key, safe=""),
        {"fields": {"customfield_10014": epic_key}}
    )
    return {
        "issue_key": issue_key,
        "epic_key": epic_key,
        "linked": True,
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_list_epics(
    board_id: int,
    max_epics: int = 500,
) -> dict:
    """List all Epics for a Jira Software board.

    Uses the Agile REST API (/rest/agile/1.0/board/{id}/epic).
    Works only on Jira Software Scrum/Kanban boards.

    The Agile API pages this endpoint at 50 results by default. The previous
    implementation read exactly one page and then reported ``total`` as the
    length of that page, so a board with 120 epics returned 50 of them labelled
    "total: 50" -- indistinguishable from a board that genuinely has 50. This
    now follows the ``isLast`` cursor to the end and reports ``truncated`` when
    the caller's own bound stopped it early.

    Args:
        board_id: Numeric board ID.
        max_epics: Upper bound on epics to return (default 500). Reaching this
            bound sets ``truncated`` to True.

    Returns:
        Dict with keys: board_id, epics (list of dicts), total, truncated.
    """
    cfg = _get_config()
    max_epics = max(1, max_epics)

    epics = []
    start_at = 0
    page_size = 50
    truncated = False

    while True:
        result = _agile_request(
            cfg, "GET",
            "board/" + str(board_id) + "/epic?startAt=" + str(start_at)
            + "&maxResults=" + str(page_size)
        )
        if result is None:
            result = {}

        raw_epics = result.get("values", [])
        for e in raw_epics:
            if len(epics) >= max_epics:
                truncated = True
                break
            epics.append({
                "key": e.get("key", ""),
                "summary": e.get("summary", ""),
                "done": e.get("done", False),
            })

        if truncated or result.get("isLast", True) or not raw_epics:
            break
        start_at += len(raw_epics)

    return {
        "board_id": board_id,
        "epics": epics,
        "total": len(epics),
        "truncated": truncated,
    }


# ---------------------------------------------------------------------------
# Release & Version Management Tools (4)
# ---------------------------------------------------------------------------

@_tool(read_only=False, destructive=False, idempotent=False, open_world=True)
@mcp_tool_handler
def jira_create_version(
    project_key: str,
    name: str,
    release_date: Optional[str] = None,
    description: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    """Create a project version (release) in Jira.

    Version creation is not idempotent. Supply ``idempotency_key`` -- generated
    once per logical intent and reused unchanged across every retry -- so a
    retry after a lost response replays the recorded version instead of
    creating a second one with the same name.

    Args:
        project_key: Jira project key (e.g. PROJ).
        name: Version name (e.g. v1.2.0).
        release_date: Optional ISO-8601 release date (e.g. 2026-06-30).
        description: Optional description of the release.
        idempotency_key: Optional caller-generated key scoped to one logical
            version-creation intent.

    Returns:
        Dict with keys: version_id, name, released, project_key.
    """
    project_key = validate_input(project_key, field_name="project_key")
    name = validate_input(name, field_name="name")

    def _create() -> dict:
        """Perform the underlying non-idempotent version creation."""
        cfg = _get_config()

        payload = {
            "project": project_key,
            "name": name,
            "released": False,
            "archived": False,
        }
        if release_date:
            payload["releaseDate"] = release_date
        if description:
            payload["description"] = description

        result = _request(cfg, "POST", "/version", payload)
        return {
            "version_id": result.get("id", ""),
            "name": result.get("name", name),
            "released": False,
            "project_key": project_key,
        }

    return run_once("jira_create_version", idempotency_key, _create)


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_list_versions(
    project_key: str,
) -> dict:
    """List all versions for a Jira project.

    Args:
        project_key: Jira project key (e.g. PROJ).

    Returns:
        Dict with keys: project_key, versions (list), total.
        Each version has: id, name, released, archived, releaseDate.
    """
    project_key = validate_input(project_key, field_name="project_key")
    cfg = _get_config()

    result = _request(
        cfg, "GET",
        "/project/" + urllib.request.quote(project_key, safe="") + "/versions"
    )
    if result is None:
        result = []

    versions = [
        {
            "id": v.get("id", ""),
            "name": v.get("name", ""),
            "released": v.get("released", False),
            "archived": v.get("archived", False),
            "releaseDate": v.get("releaseDate", None),
        }
        for v in (result if isinstance(result, list) else [])
    ]
    return {
        "project_key": project_key,
        "versions": versions,
        "total": len(versions),
    }


@_tool(read_only=False, destructive=True, idempotent=False, open_world=True)
@mcp_tool_handler
def jira_release_version(
    version_id: str,
    release_date: Optional[str] = None,
) -> dict:
    """Mark a Jira project version as released.

    Args:
        version_id: Numeric version ID (from jira_create_version or jira_list_versions).
        release_date: Optional ISO-8601 release date. Defaults to today's date.

    Returns:
        Dict with keys: version_id, released (True), release_date.
    """
    version_id = validate_input(version_id, field_name="version_id")
    cfg = _get_config()

    from datetime import date as _date
    today = _date.today().isoformat()
    effective_date = release_date if release_date else today

    _request(
        cfg, "PUT",
        "/version/" + urllib.request.quote(version_id, safe=""),
        {"released": True, "releaseDate": effective_date}
    )
    return {
        "version_id": version_id,
        "released": True,
        "release_date": effective_date,
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_release_notes(
    project_key: str,
    version_name: str,
) -> dict:
    """Generate release notes from all issues fixed in a version.

    Fetches issues via JQL fixVersion filter and groups by issue type
    (Bug, Story, Task, Sub-task, etc.).

    Args:
        project_key: Jira project key (e.g. PROJ).
        version_name: Exact version name as it appears in Jira (e.g. v1.2.0).

    Returns:
        Dict with keys: project_key, version, groups (dict by issue type), total_issues.
    """
    project_key = validate_input(project_key, field_name="project_key")
    version_name = validate_input(version_name, field_name="version_name")
    cfg = _get_config()

    safe_version = version_name.replace('"', '\\"')
    safe_project = project_key.replace('"', '\\"')
    jql = 'project="' + safe_project + '" AND fixVersion="' + safe_version + '" ORDER BY issuetype ASC'
    path = (
        "/search?jql=" + urllib.request.quote(jql)
        + "&fields=summary,issuetype,status&maxResults=100"
    )
    result = _request(cfg, "GET", path)
    if result is None:
        result = {}

    issues = result.get("issues", [])
    groups = {}
    for issue in issues:
        itype = (issue.get("fields", {}).get("issuetype") or {}).get("name", "Other")
        entry = {
            "key": issue.get("key", ""),
            "summary": (issue.get("fields", {}) or {}).get("summary", ""),
            "status": ((issue.get("fields", {}).get("status")) or {}).get("name", ""),
        }
        groups.setdefault(itype, []).append(entry)

    return {
        "project_key": project_key,
        "version": version_name,
        "groups": groups,
        "total_issues": len(issues),
    }


# ---------------------------------------------------------------------------
# Cross-Board / Multi-Team Metrics (3)
# ---------------------------------------------------------------------------

@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_program_velocity(
    board_ids: List[int],
    num_sprints: int = 5,
) -> dict:
    """Aggregate velocity across multiple Scrum boards for program-level reporting.

    Calls the Agile velocity chart endpoint per board and builds a combined view
    showing per-team and total program velocity. No native multi-board Jira API exists;
    this tool loops over board_ids (ADR-5).

    Args:
        board_ids: List of numeric board IDs to aggregate.
        num_sprints: Number of recent sprints to include (1-20, default 5).

    Returns:
        Dict with keys: board_count, num_sprints, per_team (dict keyed by
        stringified board_id, since JSON object keys are always strings),
        program_total_avg (float), sprints_sampled.
    """
    if not board_ids:
        return error("board_ids must be a non-empty list")
    if not 1 <= num_sprints <= 20:
        return error("num_sprints must be between 1 and 20")
    cfg = _get_config()

    per_team = {}
    all_velocities = []
    for board_id in board_ids:
        v_data = _agile_request(
            cfg, "GET",
            "rapid/charts/velocity?rapidViewId=" + str(board_id)
        )
        if v_data is None:
            v_data = {}

        entries = v_data.get("velocityStatEntries", {})
        sprint_ids_sorted = sorted(entries.keys(), key=lambda x: int(x))[-num_sprints:]
        completed = [
            float(entries[sid].get("completed", {}).get("value", 0))
            for sid in sprint_ids_sorted
        ]
        avg_v = round(sum(completed) / len(completed), 1) if completed else 0.0
        per_team[str(board_id)] = {
            "board_id": board_id,
            "velocity_by_sprint": [round(v, 1) for v in completed],
            "sprint_count": len(completed),
            "avg_velocity": avg_v,
        }
        all_velocities.extend(completed)

    program_total_avg = round(
        sum(all_velocities) / len(all_velocities), 1
    ) if all_velocities else 0.0

    return {
        "board_count": len(board_ids),
        "num_sprints": num_sprints,
        "per_team": per_team,
        "program_total_avg": program_total_avg,
        "sprints_sampled": len(all_velocities),
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_cross_team_health(
    board_ids: List[int],
) -> dict:
    """Run team health analysis across multiple boards and return ranked comparison.

    Replicates the jira_team_health logic per board, computes a composite score,
    and ranks teams. Maximum 10 boards per call to limit API calls (DoS protection).

    Args:
        board_ids: List of numeric board IDs (max 10).

    Returns:
        Dict with keys: teams (list ranked by composite_score), top_team_board_id,
        lowest_team_board_id, board_count.
    """
    if not board_ids:
        return error("board_ids must be a non-empty list")
    if len(board_ids) > 10:
        return error("max 10 boards per call to limit Jira API load")
    cfg = _get_config()

    tuckman_weight_map = {
        "Performing": 1.0, "Norming": 0.75,
        "Storming": 0.5, "Forming": 0.25,
    }
    agile_x_weight_map = {
        "L5": 1.0, "L4": 0.8, "L3": 0.6, "L2": 0.4, "L1": 0.2,
    }

    team_scores = []
    for board_id in board_ids:
        velocity_points = []
        closed = _recent_closed_sprints(cfg, board_id, 6)

        for s in closed.get("values", []):
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
            first_mean = sum(velocity_points[:half]) / half
            second_mean = sum(velocity_points[half:]) / (len(velocity_points) - half)
            velocity_trend = second_mean - first_mean

        tuckman_stage = scrum_calculator.tuckman_estimate(
            velocity_cv=cv_val,
            velocity_trend=velocity_trend,
            team_age_sprints=len(velocity_points),
        )
        agile_x = vstats.get("nasscom_agileX_level", "L1")

        t_w = tuckman_weight_map.get(tuckman_stage, 0.25)
        a_w = agile_x_weight_map.get(agile_x, 0.2)
        composite = round((t_w + a_w) / 2.0, 4)

        team_scores.append({
            "board_id": board_id,
            "tuckman_stage": tuckman_stage,
            "velocity_cv": round(cv_val, 4),
            "nasscom_agileX_level": agile_x,
            "composite_score": composite,
            "sprints_analyzed": len(velocity_points),
        })

    ranked = sorted(team_scores, key=lambda x: x["composite_score"], reverse=True)
    for idx, team in enumerate(ranked):
        team["rank"] = idx + 1

    return {
        "board_count": len(board_ids),
        "teams": ranked,
        "top_team_board_id": ranked[0]["board_id"] if ranked else None,
        "lowest_team_board_id": ranked[-1]["board_id"] if ranked else None,
    }


@_tool(read_only=True, destructive=False, idempotent=True, open_world=True)
@mcp_tool_handler
def jira_dependency_check(
    board_ids: List[int],
) -> dict:
    """Find cross-board blockers -- issues on one board that block issues on another.

    Fetches active sprint issues per board, maps issue keys to boards, then checks
    each issue's 'Blocks' outward links for cross-board dependencies.

    Args:
        board_ids: List of numeric board IDs to check.

    Returns:
        Dict with keys: cross_board_blockers (list), total_blockers,
        boards_checked, boards_with_active_sprint.
    """
    if not board_ids:
        return error("board_ids must be a non-empty list")
    cfg = _get_config()

    board_issue_map = {}
    boards_with_sprint = 0

    for board_id in board_ids:
        sprint_result = _agile_request(
            cfg, "GET",
            "board/" + str(board_id) + "/sprint?state=active"
        )
        if sprint_result is None:
            sprint_result = {}
        active_sprints = sprint_result.get("values", [])
        if not active_sprints:
            continue
        boards_with_sprint += 1
        sprint_id = active_sprints[0].get("id")
        if not sprint_id:
            continue

        issues_result = _agile_request(
            cfg, "GET",
            "sprint/" + str(sprint_id) + "/issue?maxResults=200&fields=summary,issuelinks"
        )
        if issues_result is None:
            issues_result = {}

        for issue in issues_result.get("issues", []):
            board_issue_map[issue.get("key", "")] = board_id

    cross_board_blockers = []
    for issue_key, blocker_board in list(board_issue_map.items()):
        issue_detail = _request(
            cfg, "GET",
            "/issue/" + urllib.request.quote(issue_key, safe="") + "?fields=issuelinks"
        )
        if issue_detail is None:
            continue
        for link in (issue_detail.get("fields", {}).get("issuelinks") or []):
            link_type = (link.get("type") or {}).get("name", "")
            if link_type == "Blocks":
                out_issue = link.get("outwardIssue") or {}
                blocked_key = out_issue.get("key", "")
                if blocked_key and blocked_key in board_issue_map:
                    blocked_board = board_issue_map[blocked_key]
                    if blocked_board != blocker_board:
                        cross_board_blockers.append({
                            "blocker_key": issue_key,
                            "blocks_key": blocked_key,
                            "blocker_board": blocker_board,
                            "blocked_board": blocked_board,
                        })

    return {
        "cross_board_blockers": cross_board_blockers,
        "total_blockers": len(cross_board_blockers),
        "boards_checked": len(board_ids),
        "boards_with_active_sprint": boards_with_sprint,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
