# Brownfield Blueprint — mcp-jira-api Gap Closure
<!-- Author: solution_architect | Date: 2026-05-29 | Phase: A -->
<!-- Project: C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\mcp-jira-api -->

---

## 1. Component Change Map

| File | Change Type | Sections Affected | Estimated New Lines |
|------|-------------|-------------------|---------------------|
| `server.py` | Modify + Append | jira_sprint_review function (modify, +12 lines) | 12 |
| `server.py` | Append | Epic Management section (4 new tools) | ~120 |
| `server.py` | Append | Release & Version section (4 new tools) | ~110 |
| `server.py` | Append | Cross-Board Metrics section (3 new tools) | ~105 |
| `server.py` | Modify | Module docstring tool count 41 → 52 | 1 |
| `agile_client.py` | No change | Used as-is via `_agile_request()` | 0 |
| `scrum_calculator.py` | No change | `ahp_score()` used as-is | 0 |
| `tests/fixtures/` | Create | 11 new JSON fixture files | ~110 (JSON) |
| `tests/test_tools_gaps.py` | Create | Full unit test suite | ~350 |
| `tests/test_integration_gaps.py` | Create | Integration tests + Pact | ~120 |

**Total new lines in server.py:** ~348 lines appended/modified (currently 3344 → ~3692)
**Total tool count change:** 41 → 52 (11 new/modified tools)

---

## 2. Function Signatures (Python 3.8 Type Hints)

All imports needed at top of server.py — verify these are already present:
```python
from typing import Any, Dict, List, Optional
import urllib.request
import datetime
```

### Gap 1 — Modified Function

```python
@mcp.tool()
@mcp_tool_handler
def jira_sprint_review(
    board_id: int,
    sprint_id: int,
    dod_criteria_weights: Optional[List[List[float]]] = None,
) -> dict:
```

**Change:** `dod_criteria_weights` added as last parameter with `None` default.
**Backward compat:** All existing callers passing `board_id` + `sprint_id` only are unaffected.

**Critical finding:** The current implementation (lines 1397-1406) already calls
`scrum_calculator.ahp_score()` with a hardcoded 3x3 DoD matrix and returns
`ahp_weights`, `ahp_CR`, `ahp_consistent`, `ahp_dod_criteria`. Gap 1 replaces
that hardcoded call with the user-provided matrix when supplied.

**Also needed:** Add `dod_compliant: bool` to each `demo_ready_issues` dict item
(currently missing — the `dod_compliant` variable is only an int counter, not tracked per story).

### Gap 2 — New Functions

```python
@mcp.tool()
@mcp_tool_handler
def jira_create_epic(
    project_key: str,
    name: str,
    summary: str,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
) -> dict:

@mcp.tool()
@mcp_tool_handler
def jira_get_epic(
    epic_key: str,
) -> dict:

@mcp.tool()
@mcp_tool_handler
def jira_link_to_epic(
    issue_key: str,
    epic_key: str,
) -> dict:

@mcp.tool()
@mcp_tool_handler
def jira_list_epics(
    board_id: int,
) -> dict:
```

### Gap 3 — New Functions

```python
@mcp.tool()
@mcp_tool_handler
def jira_create_version(
    project_key: str,
    name: str,
    release_date: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:

@mcp.tool()
@mcp_tool_handler
def jira_list_versions(
    project_key: str,
) -> dict:

@mcp.tool()
@mcp_tool_handler
def jira_release_version(
    version_id: str,
    release_date: Optional[str] = None,
) -> dict:

@mcp.tool()
@mcp_tool_handler
def jira_release_notes(
    project_key: str,
    version_name: str,
) -> dict:
```

### Gap 4 — New Functions

```python
@mcp.tool()
@mcp_tool_handler
def jira_program_velocity(
    board_ids: List[int],
    num_sprints: int = 5,
) -> dict:

@mcp.tool()
@mcp_tool_handler
def jira_cross_team_health(
    board_ids: List[int],
) -> dict:

@mcp.tool()
@mcp_tool_handler
def jira_dependency_check(
    board_ids: List[int],
) -> dict:
```

---

## 3. Jira API Endpoints Per Tool

### URL Construction Rules

```
server._request(cfg, METHOD, path):
  URL = cfg["url"] + "/rest/api/" + cfg["api_version"] + path
  Example: path="/issue" → https://co.atlassian.net/rest/api/3/issue

agile_client._agile_request(cfg, METHOD, path):
  URL = cfg["url"] + "/rest/agile/1.0/" + path
  Example: path="board/42/epic" → https://co.atlassian.net/rest/agile/1.0/board/42/epic
```

| Tool | Client | Method | Path |
|------|--------|--------|------|
| `jira_sprint_review` (modified) | agile | existing, no change | existing |
| `jira_create_epic` | `_request` | POST | `/issue` |
| `jira_get_epic` (call 1) | `_request` | GET | `/issue/{key}?fields=summary,status,customfield_10014,customfield_10016` |
| `jira_get_epic` (call 2) | `_request` | GET | `/search?jql="Epic+Link"="{key}"&fields=summary,status,customfield_10016&maxResults=100` |
| `jira_link_to_epic` | `_request` | PUT | `/issue/{issue_key}` |
| `jira_list_epics` | `_agile_request` | GET | `board/{board_id}/epic` |
| `jira_create_version` | `_request` | POST | `/version` |
| `jira_list_versions` | `_request` | GET | `/project/{project_key}/versions` |
| `jira_release_version` | `_request` | PUT | `/version/{version_id}` |
| `jira_release_notes` | `_request` | GET | `/search?jql=project="{key}"+AND+fixVersion="{name}"&fields=summary,issuetype,status&maxResults=100` |
| `jira_program_velocity` (per board) | `_agile_request` | GET | `rapid/charts/velocity?rapidViewId={board_id}` |
| `jira_cross_team_health` (per board, call 1) | `_agile_request` | GET | `board/{board_id}/sprint?state=closed&maxResults=6` |
| `jira_cross_team_health` (per board, call 2) | `_agile_request` | GET | `sprint/{sprint_id}/issue?maxResults=200&fields=status,customfield_10016,customfield_10028,story_points` |
| `jira_dependency_check` (per board, call 1) | `_agile_request` | GET | `board/{board_id}/sprint?state=active` |
| `jira_dependency_check` (per board, call 2) | `_agile_request` | GET | `sprint/{sprint_id}/issue?maxResults=200&fields=summary,issuelinks` |

**Key fields referenced:**
- `customfield_10014` = Epic Link / Epic Name (Cloud)
- `customfield_10016` = Story Points (Cloud; Server may use `customfield_10028`)
- `issuelinks[*].type.name` = link type (e.g. "Blocks")
- `issuelinks[*].outwardIssue.key` = the blocked issue key

---

## 4. Error Handling Strategy Per Tool

**Universal pattern** (all new tools follow this, mirrors existing tools):

```python
def jira_xxx(...) -> dict:
    cfg = _get_config()          # raises EnvironmentError if env vars missing
                                  # @mcp_tool_handler catches → error("Missing env vars")
    # validate inputs
    # call _request() or _agile_request()  # raises RuntimeError on HTTP error
                                  # @mcp_tool_handler catches → error("Jira API error N: ...")
    # parse response
    return {...}                  # @mcp_tool_handler wraps in success(...)
```

**Per-tool specific error cases:**

| Tool | Extra Error Cases |
|------|-------------------|
| `jira_sprint_review` (Gap 1) | CR >= 0.10 → return `error("AHP matrix inconsistent (CR=N)")` before computing score |
| `jira_sprint_review` (Gap 1) | `ahp_score()` returns `{"error":...}` → return `error("AHP matrix error: " + msg)` |
| `jira_sprint_review` (Gap 1) | `demo_ready_issues` empty → `dod_weighted_score = 0.0` (no error) |
| `jira_create_epic` | validate project_key, name, summary non-empty via `validate_input()` |
| `jira_get_epic` | JQL search may return 0 stories → `linked_story_count=0`, `completion_pct=0.0` |
| `jira_list_epics` | agile API returns 404 for non-Jira-Software boards → caught by handler |
| `jira_release_version` | version_id empty → validate_input catches it |
| `jira_release_notes` | version_name sanitized (JQL injection) before JQL insert |
| `jira_program_velocity` | empty `board_ids` → return `error("board_ids must be a non-empty list")` |
| `jira_program_velocity` | `num_sprints` out of 1-20 range → return `error("num_sprints must be 1-20")` |
| `jira_cross_team_health` | >10 boards → return `error("max 10 boards per call")` |
| `jira_dependency_check` | empty `board_ids` → return `error("board_ids must be a non-empty list")` |
| `jira_dependency_check` | no active sprint for a board → skip that board (log in result) |

---

## 5. Backward Compatibility Contract for Gap 1

### Current behavior (must remain identical for existing callers):

```python
# Existing caller (no new param):
result = jira_sprint_review(board_id=42, sprint_id=7)
# Returns: {..., "dod_compliance_pct": 80.0, "ahp_dod_criteria": [...],
#           "ahp_weights": [...], "ahp_CR": 0.05, "ahp_consistent": True, ...}
```

### New behavior (when dod_criteria_weights provided):

```python
# New caller (with optional param):
result = jira_sprint_review(board_id=42, sprint_id=7,
    dod_criteria_weights=[[1,3,5],[0.333,1,2],[0.2,0.5,1]])
# Returns: {..., "dod_compliance_pct": 80.0, "dod_weighted_score": 0.6781,
#           "ahp_weights": [0.637, 0.258, 0.105], "ahp_CR": 0.003, ...}
```

### Change details (minimal diff):

1. Add `dod_criteria_weights=None` as last parameter ← **only signature change**
2. Add per-story `dod_compliant: bool` tracking in the story collection loop ← **needed for weighted score**
3. Add conditional block at end of function:
   - If `dod_criteria_weights is None` → use hardcoded matrix (current behavior, lines 1397-1406 unchanged)
   - If provided → call `ahp_score(dod_criteria_weights)`, check CR, compute `dod_weighted_score`, add to return dict
4. `dod_weighted_score` key appears in return ONLY when `dod_criteria_weights` is not None
5. All existing return keys remain unchanged: `dod_compliance_pct`, `ahp_dod_criteria`, `ahp_weights`, `ahp_CR`, `ahp_consistent`, `ahp_note`

**No existing return key is removed or renamed.**

---

## 6. Interface Contracts (5 Contracts)

### Contract 1: server.py ↔ agile_client.py

```
FROM  : server.py (jira_list_epics, jira_program_velocity, jira_cross_team_health, jira_dependency_check)
TO    : agile_client._agile_request()
INPUT : cfg (dict from _get_config()), method (str), path (str, relative to /rest/agile/1.0/)
OUTPUT: Parsed JSON dict/list or None (204). Raises RuntimeError on HTTP error.
ASSUMES: cfg["url"] is set and does not have trailing slash; auth headers built internally
MUST NOT: Pass full URL as path; use leading slash in path argument
```

### Contract 2: server.py ↔ scrum_calculator.py

```
FROM  : server.py jira_sprint_review (Gap 1 new code path)
TO    : scrum_calculator.ahp_score()
INPUT : criteria_matrix (List[List[float]]) — square n×n pairwise comparison matrix
OUTPUT: {"weights": List[float], "lambda_max": float, "CI": float, "CR": float,
         "consistent": bool, "n": int} on success
        {"error": str} on invalid input
ASSUMES: n >= 2; all values are positive floats; reciprocal symmetry not enforced by function
MUST NOT: Call ahp_score() with an empty list or non-square matrix (returns {"error":...})
          Pass the result to the return dict without checking for "error" key first
```

### Contract 3: server.py ↔ base/response.py

```
FROM  : All new tool functions
TO    : success() / error() from base.response
INPUT : success(data: dict) | error(message: str)
OUTPUT: JSON string (returned by @mcp_tool_handler via success/error wrappers)
ASSUMES: Functions decorated with @mcp_tool_handler return raw dicts that the handler wraps
         All RuntimeError / EnvironmentError caught by handler → error response
MUST NOT: Return raw dicts without going through success()/error() from within tool body
          Raise exceptions intentionally (let @mcp_tool_handler catch and format)
```

### Contract 4: server.py ↔ input_validator.py

```
FROM  : All new tool functions that accept string parameters
TO    : validate_input(value: str, field_name: str) from input_validator
INPUT : value = the string parameter, field_name = parameter name for error message
OUTPUT: Returns cleaned/stripped string on success
        Raises ValueError on invalid input (null bytes, too long, prompt injection)
ASSUMES: @mcp_tool_handler catches ValueError → returns error response
MUST NOT: Call validate_input() on int or List parameters (only str params)
          Skip validation for any user-supplied string that reaches Jira API URL paths or bodies
```

### Contract 5: tests/ ↔ tests/fixtures/

```
FROM  : tests/test_tools_gaps.py, tests/test_integration_gaps.py
TO    : tests/fixtures/*.json files
INPUT : fixture_loader(filename) from tests/conftest.py → returns parsed dict
OUTPUT: Dict matching the shape of the Jira API response for that endpoint
ASSUMES: Fixture files use placeholder values (not real credentials or issue keys)
         JSON is valid ASCII-only (no Unicode characters)
MUST NOT: Use real API tokens, real Jira URLs, or real issue/board IDs in fixtures
          Have fixture files with keys that differ from what the tool code actually parses
```

---

## 7. DSA Choices for Gap 4 Aggregation

### jira_program_velocity

```
Data structure: Dict[int, Dict] (board_id → per-board result)
  per_team[board_id] = {
      "board_id": int,
      "velocity_by_sprint": List[int],   # ordered chronologically
      "sprint_count": int,
      "avg_velocity": float,
  }

Aggregation: For program total → zip per-team sprint lists by index
  program_total = [sum(per_team[b]["velocity_by_sprint"][i]
                   for b in board_ids if i < len(per_team[b]["velocity_by_sprint"]))
                   for i in range(num_sprints)]

Rationale: Dict keyed by board_id gives O(1) per-team lookup. List for velocity
preserves chronological order. len(board_ids) is bounded (user-provided, validated ≤10
via jira_cross_team_health; jira_program_velocity allows any reasonable count).
```

### jira_cross_team_health

```
Data structure: List[Dict] (unsorted team results, then sorted in-place)
  team_scores = [
      {"board_id": int, "tuckman_stage": str, "velocity_cv": float,
       "nasscom_agileX_level": str, "composite_score": float, "rank": int}
  ]

Scoring: composite_score = (1.0 - velocity_cv) * tuckman_weight + agile_x_weight
  tuckman_weight map: Performing=1.0, Norming=0.75, Storming=0.5, Forming=0.25
  agile_x_weight map: L5=1.0, L4=0.8, L3=0.6, L2=0.4, L1=0.2

Ranking: sorted(team_scores, key=lambda x: x["composite_score"], reverse=True)
  Assign rank = index + 1 in sorted list.

Rationale: Simple list sort is O(n log n) for n boards (n ≤ 10 via validation).
No heap needed. Composite score formula balances velocity stability with maturity level.
```

### jira_dependency_check

```
Data structure: Dict[str, int] (issue_key → board_id) for cross-board lookup
  board_issue_map: Dict[str, int] = {}
  for board_id in board_ids:
      for issue in active_sprint_issues:
          board_issue_map[issue_key] = board_id

Cross-board detection: O(1) lookup per link
  if blocked_key in board_issue_map:
      if board_issue_map[blocked_key] != blocker_board_id:
          # cross-board dependency found

Result list: List[Dict] with blocker_key, blocks_key, blocker_board, blocked_board

Rationale: Dict lookup is O(1) vs O(n) list scan. Suitable since total issues
across all boards can be large (up to 200 per board × 10 boards = 2000 issues).
```

---

## 8. Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---------|------|-------------|--------|------------|
| R-01 | customfield_10014 = Epic Link on Cloud but may be different ID on Server/DC | HIGH | MEDIUM | Document clearly: tool uses customfield_10014; Server/DC teams may need to adjust. Add note in return dict. Not blocking. |
| R-02 | Story Points field ID varies: customfield_10016 (Cloud) vs customfield_10028 (Server) | HIGH | LOW | Use existing `_extract_story_points()` helper which already handles both |
| R-03 | `"Epic Link"` JQL syntax (for jira_get_epic linked stories search) works only on Jira Cloud; Server uses `cf[10014]` | MEDIUM | MEDIUM | Use conditional: if Cloud → `"Epic Link"="{key}"`, if Server → `cf[10014]="{key}"`. Detect via `_is_cloud(cfg)`. |
| R-04 | jira_list_epics uses Agile API `/board/{id}/epic` — not available on Jira Work Management boards | MEDIUM | LOW | Document constraint: works only on Jira Software boards (Scrum/Kanban). Return error if 404. |
| R-05 | Empty `board_ids` list in Gap 4 tools causes ZeroDivisionError or empty iteration | HIGH | HIGH | Validate at start: `if not board_ids: return error("board_ids must be a non-empty list")` |
| R-06 | AHP matrix CR >= 0.10 when user provides inconsistent weights | MEDIUM | LOW | Return `error("AHP matrix inconsistent (CR=N). CR must be < 0.10.")` before computing score. |
| R-07 | `jira_release_notes` JQL uses version_name with special chars (spaces, parentheses) | MEDIUM | MEDIUM | Sanitize: `version_name.replace('"', '\\"')`. URL-encode the JQL query string via `urllib.request.quote()`. |
| R-08 | `jira_cross_team_health` with 10 boards makes up to 70 Jira API calls (10 boards × 7 calls each) | MEDIUM | MEDIUM | Enforce max 10 boards limit. Document API call count in docstring. |
| R-09 | `jira_program_velocity` velocity API endpoint `/rapid/charts/velocity?rapidViewId=` deprecated in newer Jira Cloud versions | LOW | HIGH | Use as-is (same endpoint used by existing `jira_get_velocity` which is already in production). If deprecated, same issue affects existing tool. |
| R-10 | `demo_ready_issues` items currently don't have `dod_compliant` boolean — Gap 1 needs it | HIGH | MEDIUM | **Fix required:** In the story collection loop (lines ~1342-1354), track `all_subtasks_done` per Story item and add `"dod_compliant": all_subtasks_done` to each `demo_ready_issues` append. |

---

## 9. Architecture Decision Records

### ADR-1: All 11 new/modified tools in server.py (no module split)

```
Chosen:    Add all code to server.py (monolithic entry point)
Why:       (1) All existing 41 tools follow this exact pattern — no exceptions;
           (2) stdio MCP transport has no benefit from modularization;
           (3) @mcp.tool() + @mcp_tool_handler decorators require functions
               to be importable from the server module scope at startup;
           (4) Splitting into epic_tools.py/version_tools.py adds sys.path
               manipulation with zero operational benefit.
Rejected:
  separate epic_tools.py  — requires sys.path.insert + import in server.py, adds 2 files,
                            no separation of concerns benefit for stdlib-only tool functions
  plugin architecture     — severe over-engineering for a scoped gap closure of 11 functions
```

### ADR-2: Dual API client strategy

```
Chosen:    agile_client._agile_request() for /rest/agile/1.0/ endpoints
           server._request() for /rest/api/{version}/ endpoints
Why:       (1) Epic LIST only exists in Agile API (board/{id}/epic — not in Core API);
           (2) Epic CREATE/UPDATE, Version CREATE/UPDATE only in Core API;
           (3) Mirrors existing pattern: jira_get_boards/sprints → agile_client,
               jira_create_issue/update_issue → _request();
           (4) agile_client handles its own auth + timeout identically to _request().
Rejected:
  agile_client only  — /rest/api/3/version does not exist under /rest/agile/1.0/
  Core API only      — /rest/agile/1.0/board/{id}/epic not available in Core API path
  New HTTP client    — duplicates auth/timeout/error logic already in both clients
```

### ADR-3: Reuse scrum_calculator.ahp_score() for Gap 1

```
Chosen:    Call existing scrum_calculator.ahp_score(dod_criteria_weights) directly
Why:       (1) Function already implemented at line 745 with power iteration algorithm;
           (2) CR < 0.10 consistency validation already built in;
           (3) Fully tested in test_scrum_calculator.py;
           (4) Pure function — no I/O, no side effects, deterministic;
           (5) Current code (lines 1397-1406) already calls it with hardcoded matrix
               — Gap 1 just makes that matrix a parameter.
Rejected:
  New AHP implementation — duplicates 100 lines of tested math, risks CR formula bugs,
                          violates DRY, doubles test surface for same computation
```

### ADR-4: dod_criteria_weights as Optional[List[List[float]]] = None

```
Chosen:    Optional last parameter with None default in jira_sprint_review
Why:       (1) Full backward compat — existing callers pass only board_id + sprint_id;
           (2) Matches Optional pattern used throughout server.py for all optional params;
           (3) None sentinel is unambiguous — no falsy confusion with empty list;
           (4) List[List[float]] precisely describes the n×n matrix input shape;
           (5) Python 3.8 compatible syntax.
Rejected:
  Required parameter   — breaks every existing jira_sprint_review caller immediately,
                         requires all consumers to provide matrix even when not needed
  New separate tool    — jira_sprint_review_ahp would duplicate 120 lines of logic,
                         creates two tools for one workflow
  Dict parameter       — less explicit, requires key-value parsing overhead
```

### ADR-5: jira_program_velocity loops _agile_request() per board_id

```
Chosen:    Sequential loop calling /rapid/charts/velocity?rapidViewId={board_id} per board
Why:       (1) Jira REST API has no native multi-board velocity aggregation endpoint;
           (2) Same velocity endpoint already used by existing jira_get_velocity tool;
           (3) Pattern consistent with jira_scrum_of_scrums which does mathematical
               aggregation across teams without multi-board API;
           (4) n ≤ reasonable limit (no validation like jira_cross_team_health's 10-board cap
               needed — velocity calls are lighter than health calls);
           (5) stdlib urllib.request is synchronous — no async loop needed.
Rejected:
  New multi-board Jira API endpoint — does not exist in Jira REST API specification
  Calling jira_get_velocity MCP tool recursively — would create nested @mcp_tool_handler
    invocations with double JSON serialization overhead
  Parallel calls via threading — adds complexity, stdlib-only constraint, and rate limit risk
```

---

## Appendix: Fixture File Shapes

```
tests/fixtures/epic_create_response.json
  {"id": "10042", "key": "PROJ-42", "self": "https://test.atlassian.net/rest/api/3/issue/10042"}

tests/fixtures/epic_detail_response.json
  {"key": "PROJ-42", "fields": {"summary": "Test Epic", "status": {"name": "In Progress"},
   "customfield_10014": "Q1 Goals", "customfield_10016": null}}

tests/fixtures/epic_stories_response.json
  {"issues": [{"key": "PROJ-10", "fields": {"summary": "Story 1",
   "status": {"name": "Done"}, "customfield_10016": 5.0}},
   {"key": "PROJ-11", "fields": {"summary": "Story 2",
   "status": {"name": "In Progress"}, "customfield_10016": 3.0}}], "total": 2}

tests/fixtures/epics_list_response.json
  {"values": [{"id": 1, "key": "PROJ-42", "summary": "Q1 Goals", "done": false},
               {"id": 2, "key": "PROJ-43", "summary": "Q2 Goals", "done": true}],
   "total": 2}

tests/fixtures/version_create_response.json
  {"id": "10010", "name": "v1.0.0", "self": "https://test.atlassian.net/rest/api/3/version/10010",
   "released": false, "archived": false}

tests/fixtures/versions_list_response.json
  [{"id": "10010", "name": "v1.0.0", "released": false, "archived": false,
    "releaseDate": null},
   {"id": "10009", "name": "v0.9.0", "released": true, "archived": false,
    "releaseDate": "2026-01-15"}]

tests/fixtures/version_release_response.json
  {"id": "10010", "name": "v1.0.0", "released": true, "releaseDate": "2026-05-29",
   "archived": false}

tests/fixtures/release_notes_search_response.json
  {"issues": [{"key": "PROJ-5", "fields": {"summary": "Fix login bug",
   "issuetype": {"name": "Bug"}, "status": {"name": "Done"}}},
   {"key": "PROJ-6", "fields": {"summary": "Add OAuth2",
   "issuetype": {"name": "Story"}, "status": {"name": "Done"}}}],
   "total": 2, "maxResults": 100, "startAt": 0}

tests/fixtures/cross_board_velocity_response.json
  {"sprints": [{"id": 1, "name": "Sprint 1"}, {"id": 2, "name": "Sprint 2"}],
   "velocityStatEntries": {"1": {"estimated": {"value": 20}, "completed": {"value": 18}},
   "2": {"estimated": {"value": 22}, "completed": {"value": 21}}}}

tests/fixtures/cross_team_health_board_response.json
  {"values": [{"id": 101, "state": "closed", "name": "Sprint 1"},
               {"id": 102, "state": "closed", "name": "Sprint 2"}]}

tests/fixtures/dependency_links_response.json
  {"issues": [{"key": "PROJ-20", "fields": {"summary": "Backend API",
   "issuelinks": [{"id": "10001", "type": {"name": "Blocks", "outward": "blocks"},
   "outwardIssue": {"key": "TEAM2-5", "fields": {"summary": "Frontend depends on API",
   "status": {"name": "In Progress"}}}}]}}], "total": 1}
```

---

**Blueprint complete. Ready for consensus_agent review.**
