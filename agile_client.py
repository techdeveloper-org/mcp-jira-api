"""
agile_client.py -- Jira Software Agile REST API client.

Distinction from server.py _request():
  - _request() in server.py targets /rest/api/{version}/ (core Jira REST API)
  - _agile_request() here targets /rest/agile/1.0/ (Jira Software Agile REST API)

The Agile API is a separate endpoint family available only in Jira Software
(not Jira Work Management or Jira Service Management). It provides:
  - Board management: GET /rest/agile/1.0/board
  - Sprint management: GET/POST /rest/agile/1.0/sprint
  - Sprint issues: GET /rest/agile/1.0/sprint/{sprintId}/issue
  - Board backlog: GET /rest/agile/1.0/board/{boardId}/backlog
  - Velocity reports: GET /rest/agile/1.0/rapid/charts/velocity?rapidViewId={boardId}
  - Burndown data: GET /rest/agile/1.0/rapid/charts/burndown?rapidViewId={boardId}&sprintId={sprintId}

Authentication, timeout, and error handling mirror server.py exactly.
Config dict is obtained from server._get_config() -- passed as argument,
not re-read from environment inside this module.

Agile API does NOT use the api_version ("2" or "3") from config.
The path is always /rest/agile/1.0/{resource}.

Windows-Safe: ASCII only (cp1252 compatible)
"""

import base64
import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

_AGILE_BASE = "/rest/agile/1.0"
_TIMEOUT = 30  # seconds -- matches server.py


def _agile_url(cfg: Dict[str, str], path: str) -> str:
    """Build a full Jira Agile REST API URL.

    Constructs the complete URL by concatenating the base Jira URL,
    the Agile API prefix, and the resource path.

    Args:
        cfg: Config dict from server._get_config() containing the 'url' key.
        path: Resource path relative to /rest/agile/1.0/ with no leading slash
              (e.g. "board", "board/42/sprint", "sprint/7/issue").

    Returns:
        Full URL string (e.g. https://company.atlassian.net/rest/agile/1.0/board).
    """
    return cfg["url"] + _AGILE_BASE + "/" + path


def _build_agile_auth_header(cfg: Dict[str, str]) -> str:
    """Build Authorization header value for Agile API requests.

    Mirrors _build_auth_header() in server.py exactly. Supports Basic auth
    (user:token Base64-encoded) and Bearer token auth.

    Args:
        cfg: Config dict from server._get_config() with keys:
             auth_method ("basic" or "bearer"), user, token.

    Returns:
        Authorization header string (e.g. "Basic ..." or "Bearer ...").
    """
    if cfg["auth_method"] == "bearer":
        return "Bearer " + cfg["token"]
    credentials = cfg["user"] + ":" + cfg["token"]
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    return "Basic " + encoded


def _agile_request(
    cfg: Dict[str, str],
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute a Jira Agile REST API request.

    Mirrors the _request() interface in server.py exactly. Path is relative
    to /rest/agile/1.0/ (do NOT include the prefix in the path argument).

    Agile API endpoints accessed by callers in server.py:
      GET  board                                              -> list boards
      GET  board/{boardId}/sprint                            -> list sprints
      POST sprint                                            -> create sprint
      POST sprint/{sprintId}                                 -> start or close sprint
      GET  sprint/{sprintId}/issue                           -> issues in sprint
      GET  sprint/{sprintId}                                 -> get sprint details
      GET  board/{boardId}/backlog                           -> board backlog
      GET  rapid/charts/velocity?rapidViewId={boardId}      -> velocity chart
      GET  rapid/charts/burndown?rapidViewId={boardId}&sprintId={sprintId} -> burndown

    Args:
        cfg: Config dict from server._get_config().
        method: HTTP method string ("GET", "POST", "PUT", "DELETE").
        path: Resource path relative to /rest/agile/1.0/ with no leading slash.
        body: Optional request body dict (JSON-serialized). None for GET requests.

    Returns:
        Parsed JSON response as dict or list, or None for 204 No Content responses.

    Raises:
        RuntimeError: On HTTP error responses (same format as server._request()).
    """
    url = _agile_url(cfg, path)
    auth_header = _build_agile_auth_header(cfg)

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
            "Jira Agile API error " + str(exc.code) + ": " + detail
        ) from exc


# ---------------------------------------------------------------------------
# AgileClient class -- object-oriented wrapper around _agile_request()
# ---------------------------------------------------------------------------

class AgileClient:
    """Object-oriented client for the Jira Software Agile REST API.

    Wraps the module-level _agile_request() function with a class interface
    so callers can hold a configured instance without passing cfg on every call.

    Authentication, timeout, and error handling delegate to _agile_request().
    All methods mirror the _request() interface in server.py.

    Args:
        cfg: Config dict from server._get_config() containing url, user,
             token, api_version, and auth_method keys.
    """

    def __init__(self, cfg: Dict[str, str]) -> None:
        """Initialize the AgileClient with a Jira config dict.

        Args:
            cfg: Config dict from server._get_config().
        """
        self._cfg = cfg

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, body: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a Jira Agile or core REST API request.

        Supports both /rest/agile/1.0/ paths and absolute /rest/api/... paths.
        When path starts with /rest/, the URL is built directly from cfg['url'] + path.
        Otherwise the path is treated as relative to /rest/agile/1.0/.

        Args:
            method: HTTP method string ("GET", "POST", "PUT", "DELETE").
            path: Resource path. Either absolute starting with /rest/ or
                  relative to /rest/agile/1.0/ (no leading slash).
            params: Optional query parameters dict (key-value pairs added to URL).
            body: Optional request body dict (JSON-serialized). None for GET requests.

        Returns:
            Parsed JSON response as dict or list, or None for 204 No Content responses.

        Raises:
            RuntimeError: On HTTP error responses.
        """
        if path.startswith("/rest/"):
            url = self._cfg["url"] + path
        else:
            url = self._cfg["url"] + _AGILE_BASE + "/" + path

        if params:
            query_parts = []
            for k, v in params.items():
                encoded_v = urllib.request.quote(str(v), safe="")
                query_parts.append(k + "=" + encoded_v)
            url = url + "?" + "&".join(query_parts)

        auth_header = _build_agile_auth_header(self._cfg)
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
                "Jira Agile API error " + str(exc.code) + ": " + detail
            ) from exc

    def get_boards(self, project_key: Optional[str] = None, board_type: Optional[str] = None, max_results: int = 50) -> Dict[str, Any]:
        """List Jira Software Scrum/Kanban boards accessible to the configured user.

        Args:
            project_key: Filter boards by project key (e.g. "PROJ"). Optional.
            board_type: Filter by board type: "scrum", "kanban", or "simple". Optional.
            max_results: Maximum boards to return (clamped to 1-50, default 50).

        Returns:
            Dict with values list of board objects.
        """
        params: Dict[str, Any] = {"maxResults": max(1, min(50, max_results))}
        if project_key:
            params["projectKeyOrId"] = project_key
        if board_type:
            params["type"] = board_type
        return self._request("GET", "board", params=params)

    def get_sprints(self, board_id: int, state: Optional[str] = None, max_results: int = 50) -> Dict[str, Any]:
        """List sprints for a Jira Software Scrum board.

        Args:
            board_id: Numeric board ID (from get_boards).
            state: Filter by sprint state: "active", "future", or "closed". Optional.
            max_results: Maximum sprints to return (default 50).

        Returns:
            Dict with values list of sprint objects.
        """
        params: Dict[str, Any] = {"maxResults": max(1, max_results)}
        if state:
            params["state"] = state
        return self._request("GET", "board/" + str(board_id) + "/sprint", params=params)

    def get_sprint(self, sprint_id: int) -> Dict[str, Any]:
        """Fetch details for a single sprint by ID.

        Args:
            sprint_id: Numeric sprint ID.

        Returns:
            Dict with sprint fields including id, name, state, startDate,
            endDate, completeDate, goal, and originBoardId.
        """
        return self._request("GET", "sprint/" + str(sprint_id))

    def get_sprint_issues(self, sprint_id: int, fields: str = "summary,status,story_points,customfield_10016,customfield_10028,created,resolutiondate", max_results: int = 100) -> Dict[str, Any]:
        """Fetch issues belonging to a sprint.

        Args:
            sprint_id: Numeric sprint ID.
            fields: Comma-separated Jira field names to include in each issue.
            max_results: Maximum issues to return (default 100).

        Returns:
            Dict with issues list and total count from the Jira Agile API.
        """
        params: Dict[str, Any] = {
            "fields": fields,
            "maxResults": max_results,
        }
        return self._request("GET", "sprint/" + str(sprint_id) + "/issue", params=params)

    def get_velocity(self, board_id: int) -> Dict[str, Any]:
        """Fetch velocity chart data from the Jira Agile rapid charts endpoint.

        Args:
            board_id: Rapid view ID (board ID) for velocity data.

        Returns:
            Dict with velocityStatEntries list keyed by sprint ID.
        """
        return self._request(
            "GET",
            "rapid/charts/velocity",
            params={"rapidViewId": board_id}
        )

    def get_burndown_chart(self, board_id: int, sprint_id: int) -> Dict[str, Any]:
        """Fetch sprint burndown chart data from Jira Agile API.

        Args:
            board_id: Rapid view ID (board ID) for the sprint.
            sprint_id: Sprint ID to fetch burndown data for.

        Returns:
            Dict with completedPoints, incompletedPoints arrays by day.
        """
        return self._request(
            "GET",
            "rapid/charts/burndown",
            params={"rapidViewId": board_id, "sprintId": sprint_id}
        )

    def get_cfd(self, board_id: int) -> Dict[str, Any]:
        """Fetch cumulative flow diagram data from Jira Agile API.

        Args:
            board_id: Rapid view ID (board ID) for the CFD.

        Returns:
            Dict with column data by day for CFD analysis.
        """
        return self._request(
            "GET",
            "rapid/charts/cumulativeFlowDiagram",
            params={"rapidViewId": board_id}
        )

    def get_issue_changelog(self, issue_key: str) -> Dict[str, Any]:
        """Fetch issue details with changelog for cycle time computation.

        Args:
            issue_key: Jira issue key (e.g. PROJ-123). Must match ^[A-Z][A-Z0-9]{0,9}-[0-9]+$.

        Returns:
            Dict with changelog, created, and resolutiondate fields.
        """
        if not re.match(r'^[A-Z][A-Z0-9]{0,9}-[0-9]+$', issue_key):
            raise ValueError("issue_key must match ^[A-Z][A-Z0-9]{0,9}-[0-9]+$ (e.g. PROJ-123)")
        return self._request(
            "GET",
            "/rest/api/3/issue/" + issue_key,
            params={"fields": "changelog,created,resolutiondate", "expand": "changelog"}
        )
