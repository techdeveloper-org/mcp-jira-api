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
