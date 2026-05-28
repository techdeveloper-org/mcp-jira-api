BROWNFIELD ARCHITECTURE DELTA BLUEPRINT
========================================
Generated: 2026-05-28
Author: solution-architect agent
Revision: 2 (revised 2026-05-28 — see REVISION LOG at end)
Phase: A -- Analysis only. No code changes in this document.

---

## 1. Current State Summary

mcp-jira-api is a Python 3.8+ FastMCP stdio server with 25 existing tools spread
across 5 cohesive groups: 10 core Jira REST tools, 5 board/sprint infrastructure
tools, 5 ceremony facilitation tools, and 5 analytics tools. The computation
layer (scrum_calculator.py) is a pure-stdlib module with 8 stateless functions;
the network layer is split between server.py (core REST via /rest/api/{version}/)
and agile_client.py (Agile REST via /rest/agile/1.0/). The @mcp_tool_handler
decorator in base/decorators.py provides uniform try/except wrapping and JSON
serialization for all tools, and input_validator.py plus rate_limiter.py supply
cross-cutting infrastructure that is present but under-used (rate_limiter.py
is not yet exposed as an MCP tool).

Baseline verification (read from live code):
  - @mcp_tool_handler decorator count in server.py: 25 (confirmed by grep)
  - tuckman_estimate() call in jira_team_health: line 2051 (confirmed by grep)
  - scrum_calculator.py existing functions: 8 (confirmed by module header)
  - agile_client.py existing functions: 3 (confirmed by module header)

---

## 2. Extension Strategy (append-only, no refactor)

### 2.1 Core Principle

Every extension is strictly append-only. The invariant is: no existing function
signature, no existing tool registration, and no existing import chain is touched.
New code goes below the last existing block in each file. Upgrades to existing
tools are implemented by adding new helper functions that the existing tool bodies
call, not by modifying the bodies themselves.

### 2.2 File-by-file Append Points

**server.py** (2203 lines, last tool ends at line 2198):
  - Append point A1: New import line for rate_limiter at the existing import block
    (line 51-52 region). No change to existing imports.
  - Append point A2: New tool group comment block + 16 new @mcp.tool()
    @mcp_tool_handler functions starting after line 2198.
  - Upgrade point U1: jira_refine_backlog (lines 1517-1636): add helper
    `_compute_wsjf_for_issues()` above the function; call it from within
    wsjf_stories loop. The existing return dict shape is preserved.
  - Upgrade point U2: jira_sprint_review (lines 1277-1407): add helper
    `_ahp_score_demo_items()` above the function. Call it to add an
    "ahp_priority_scores" key to the return dict (new key = backward compatible).
  - Upgrade point U3: jira_team_health (lines 1993-2084): replace line 2051
    (the `tuckman_estimate()` call) with a call to `scrum_calculator.tuckman_markov(
    velocity_history, team_age_sprints)`. Specifically:

      BEFORE (line 2051-2055):
        tuckman_stage = scrum_calculator.tuckman_estimate(
            velocity_cv=cv_val,
            velocity_trend=velocity_trend,
            team_age_sprints=len(velocity_points),
        )

      AFTER:
        tuckman_stage = scrum_calculator.tuckman_markov(
            velocity_history=velocity_points,
            team_age_sprints=len(velocity_points),
        )

    Lines 2057-2070 (the health_summary/intervention decision tree that uses
    the tuckman_stage result) are UNCHANGED. They consume the tuckman_stage string
    variable, which retains the same type and the same four possible values
    ("Forming", "Storming", "Norming", "Performing"). The return dict shape is
    fully preserved.

  - Upgrade point U4: jira_get_velocity tool only (NOT jira_plan_sprint):
    After the existing velocity_stats() call in jira_get_velocity, add a
    SUPPLEMENTAL call to bootstrap_bca_ci() from scrum_calculator.py. The new
    call appends three new keys to the returned velocity dict: "bca_lower",
    "bca_upper", "bca_confidence". The existing "stddev" key produced by
    velocity_stats() is preserved without any change.

    jira_plan_sprint is NOT touched. The sprint_capacity() call inside
    jira_plan_sprint does not use pstdev and has no existing CI computation.
    Adding BCa to jira_plan_sprint is out of scope for this batch.

    Concretely, inside jira_get_velocity, after the line:
      vstats = scrum_calculator.velocity_stats(velocity_points)
    add:
      bca_result = scrum_calculator.bootstrap_bca_ci(
          velocity_points, lambda pts: sum(pts) / len(pts)
      )
      vstats["bca_lower"] = bca_result["ci_low"]
      vstats["bca_upper"] = bca_result["ci_high"]
      vstats["bca_confidence"] = 0.95

    Note: velocity_stats() itself is NOT modified -- the append-only contract
    is honored. Only the jira_get_velocity tool body gains these extra lines.

**scrum_calculator.py** (533 lines):
  - Append point B1: 16 new pure functions appended below line 533.
  - No existing function bodies or signatures are modified.
  - No new imports needed: all 16 new functions use only math, random, statistics,
    datetime.date -- all already imported in the module header.

**agile_client.py** (138 lines):
  - Append point C1: 3 new functions appended below line 138.
  - get_burndown_chart(cfg, board_id, sprint_id) -> Any
  - get_cfd(cfg, board_id) -> Any
  - get_issue_changelog(cfg, issue_key) -> Any
  - No new imports needed; urllib.request, json, base64 already imported.

**server.py import block** (lines 50-52):
  - Add one import line: `from rate_limiter import check_rate_limit, _buckets,
    _BUCKET_DEFAULTS, _RETRY_AFTER_SECONDS`
  - This is an additive import; no existing import is removed or altered.

### 2.3 Tool Registration Count After Extension

  Existing tools (confirmed @mcp_tool_handler count in live server.py): 25

  New tools in this batch (Blocks D-G):

    Block D -- Agile Metrics (6 tools):
      1.  jira_burndown_chart
      2.  jira_cfd_analysis
      3.  jira_cycle_time_analysis
      4.  jira_throughput_forecast
      5.  jira_scrum_of_scrums
      6.  jira_automation_analyzer

    Block E -- Team Health Extended (4 tools):
      7.  jira_spotify_health_check
      8.  jira_psychological_safety
      9.  jira_cognitive_load
      10. jira_attrition_forecast

    Block F -- DevOps Tooling (3 tools):
      11. jira_pert_estimate
      12. jira_tco_analysis
      13. jira_rate_limit_status

    Block G -- India Layer (3 tools):
      14. jira_multi_sprint_holidays
      15. jira_ist_capacity
      16. jira_nasscom_mapping

  NOTE on tool count: Blocks D-G explicitly enumerate 16 named tools.
  jira_rate_limit_status is included in Block F (DevOps Tooling) and is one of
  the 16 enumerated tools. For implementation purposes, all 16 tools appear in a
  single append block in server.py starting after line 2198, logically grouped
  by comment headers D/E/F/G. The docstring in server.py module header is updated
  to "41 tools."

  NOTE: The orchestration source document (docs/orchestration_prompt.md) states
  "17 new tools / 42 total" in its summary lines, but its own tool table
  enumerates exactly 16 tools. The explicit tool enumeration is the authoritative
  source; this blueprint implements the 16 enumerated tools.

  REVISED TOOL COUNT ARITHMETIC:
    Existing: 25 tools (verified by @mcp_tool_handler count)
    New in this batch: 16 tools (Blocks D + E + F + G)
    Upgraded (same tool name, no count change): 4 tools
      (jira_refine_backlog, jira_sprint_review, jira_team_health, jira_get_velocity)
    Total after extension: 41 tools (25 + 16)

  The module-level docstring count changes from "25" to "41".

### 2.4 India Layer and Topology

Three India-Layer tools (jira_multi_sprint_holidays, jira_ist_capacity,
jira_nasscom_mapping) are purely computational: they call only scrum_calculator.py
functions and require no new agile_client.py calls. They are grouped with the
Scrum Master tools in server.py (Block G).

### 2.5 Agent Coordination Protocol (RESOLVED Q-07)

Both scrum-master-agent (Phase B.1) and agile-tooling-specialist (Phase B.2)
run in parallel. Without a defined protocol, both would need to append to
server.py, creating git merge conflicts. The following artifact-based assembly
workflow eliminates all write conflicts:

  Step 1 -- scrum-master-agent (B.1) writes to:
    a) scrum_calculator.py: all 16 new pure functions (append to line 533+)
    b) docs/outputs/b1-server-additions.py: a standalone Python file containing
       the 11 pure-computation server.py tool stubs as standalone async def blocks
       with @mcp.tool() and @mcp_tool_handler decorators. This file is NOT
       imported or executed -- it is a code delivery artifact only.

  Step 2 -- agile-tooling-specialist (B.2) writes to:
    a) agile_client.py: the 3 new agile client methods (append to line 138+)
    b) docs/outputs/b2-server-additions.py: a standalone Python file containing
       the 6 network-dependent server.py tool stubs as standalone async def blocks
       with @mcp.tool() and @mcp_tool_handler decorators. This file is NOT
       imported or executed -- it is a code delivery artifact only.

  Step 3 -- python-backend-engineer (B.3) is the SOLE direct writer to server.py:
    a) Read docs/outputs/b1-server-additions.py (11 tool stubs from B.1)
    b) Read docs/outputs/b2-server-additions.py (6 tool stubs from B.2)
    c) Append the required import line(s) to server.py import block
    d) Append all 16 tool stubs to server.py in a single pass (B1 stubs first,
       then B2 stubs), inserting logical comment headers (Block D, E, F, G)
    e) Run Python syntax check: python -m py_compile server.py
    f) Run backward-compat gate (section 5.3)
    g) Run full test suite: pytest tests/ -v

  This protocol guarantees:
    - Zero concurrent writes to server.py
    - Both B.1 and B.2 can work fully in parallel on their respective files
    - python-backend-engineer has a single authoritative assembly step
    - Any syntax error in a stub is caught before it touches the production file
    - Rollback is trivial: server.py was never touched until step 3(d)

  The docs/outputs/b1-server-additions.py and b2-server-additions.py files are
  ephemeral review artifacts. They are not added to .gitignore (they should be
  committed as part of the implementation record) but they have no runtime role.

---

## 3. Component Boundary Map

### 3.1 Synchronous Call Chain (CPU-bound computation)

```
MCP Client (Claude Code)
        |
        | MCP stdio protocol
        v
[server.py]  @mcp.tool() + @mcp_tool_handler
        |
        | Direct Python call (synchronous, in-process)
        |-- validate inputs: input_validator.validate_input()
        |-- call pure function: scrum_calculator.<function>()
        |-- return dict
        v
[base/decorators.py] mcp_tool_handler wraps dict -> JSON string
        |
        v
MCP Client receives JSON string
```

Pure-computation tools (Category 1 subset + upgrades):
  jira_scrum_of_scrums, jira_spotify_health_check, jira_psychological_safety,
  jira_cognitive_load, jira_attrition_forecast, jira_pert_estimate,
  jira_tco_analysis, jira_multi_sprint_holidays, jira_ist_capacity,
  jira_nasscom_mapping, jira_rate_limit_status

### 3.2 Network + Computation Call Chain (I/O-bound)

```
MCP Client
        |
        v
[server.py] @mcp.tool() + @mcp_tool_handler
        |
        |-- _get_config()  (reads env vars)
        |
        |-- agile_client._agile_request()  (HTTP to Jira Agile API)
        |   |
        |   |-- urllib.request.urlopen()  (stdlib HTTP)
        |   v
        |   /rest/agile/1.0/rapid/charts/burndown
        |   /rest/agile/1.0/rapid/charts/cumulativeFlowDiagram
        |   /rest/api/3/issue/{key}?expand=changelog
        |
        |-- scrum_calculator.<function>()  (pure math on fetched data)
        |
        v
[base/decorators.py] mcp_tool_handler -> JSON string
```

Network + computation tools (Category 1 subset requiring new agile_client methods):
  jira_burndown_chart, jira_cfd_analysis, jira_cycle_time_analysis,
  jira_throughput_forecast, jira_nasscom_mapping (uses existing agile_client)

### 3.3 Circular Import Verification

Current import graph:
  server.py -> agile_client (from agile_client import ...)
  server.py -> scrum_calculator (import scrum_calculator)
  server.py -> base.decorators (from base.decorators import mcp_tool_handler)
  server.py -> input_validator (implicit via validate calls inside tools)
  agile_client.py -> [no internal imports, only stdlib]
  scrum_calculator.py -> [no internal imports, only stdlib]
  base/decorators.py -> base/response (_serialize)
  base/response.py -> [no internal imports]
  input_validator.py -> [no internal imports]
  rate_limiter.py -> [no internal imports, only os/threading/time]

Post-extension additions:
  server.py -> rate_limiter (new import for jira_rate_limit_status)
  agile_client.py: adds 3 functions, no new imports

Conclusion: No circular imports are introduced. The dependency graph remains
a strict DAG with server.py at the root.

### 3.4 Module Responsibility Table

| Module | Responsibility | I/O | New Additions |
|---|---|---|---|
| server.py | Tool registration, input validation, orchestration | HTTP (via agile_client) | 16 new tools + 4 upgrades |
| scrum_calculator.py | Pure statistical computation | None | 16 new functions |
| agile_client.py | Jira Agile REST HTTP client | HTTP | 3 new functions |
| base/decorators.py | Error handling, JSON wrapping | None | No changes |
| base/response.py | JSON serialization | None | No changes |
| input_validator.py | String sanitization | None | No changes |
| rate_limiter.py | Token bucket state | None | No changes (exposed via new tool) |
| mcp_errors.py | Legacy error helpers | None | No changes |
| docs/outputs/b1-server-additions.py | B.1 delivery artifact | None | Created by scrum-master-agent |
| docs/outputs/b2-server-additions.py | B.2 delivery artifact | None | Created by agile-tooling-specialist |

---

## 4. ADR Set

### ADR-1: Append-Only Extension Model for scrum_calculator.py

**Status:** Accepted
**Date:** 2026-05-28

**Context:**
scrum_calculator.py is a pure-stdlib module with 8 existing functions. The KG
specifies 16 new functions. Multiple agents (scrum-master-agent,
agile-tooling-specialist) will work on this file concurrently or sequentially.
Modifying existing functions risks breaking 5 existing tool integrations (jira_plan_sprint,
jira_sprint_review, jira_team_health, jira_get_velocity, jira_monte_carlo_forecast)
and the 25-strong test suite.

**Decision:**
Treat scrum_calculator.py as append-only. New functions are added below line 533
(the current last line). No existing function signature or body is changed.
When an upgrade requires behavioral change in an existing function, a new helper
function is introduced in scrum_calculator.py; the upgrade in server.py calls
the new helper IN ADDITION TO (not instead of) the existing call.

Specifically for the BCa CI upgrade:
  - velocity_stats() in scrum_calculator.py is NOT modified.
  - bootstrap_bca_ci() is a NEW function appended to scrum_calculator.py.
  - The upgrade adds a supplemental call to bootstrap_bca_ci() in the
    jira_get_velocity tool body ONLY, appending three new keys:
    "bca_lower", "bca_upper", "bca_confidence" to the response dict.
  - The existing "stddev" key produced by velocity_stats() is fully preserved.
  - jira_plan_sprint is NOT affected (sprint_capacity() has no CI computation).
  - Backward compat: all existing output keys are preserved; only new keys are added.

**Consequence:**
Minor: velocity_stats() will still use statistics.pstdev internally. The upgraded
jira_get_velocity will call bootstrap_bca_ci() as a supplemental computation,
appending "bca_lower", "bca_upper", "bca_confidence" keys to the response.
The "stddev" key produced by the existing velocity_stats() call is preserved.
This is backward compatible because no existing key is removed or renamed.

**Alternatives Rejected:**
- In-place modification of velocity_stats() to replace pstdev with BCa: rejected
  because it modifies an existing function signature/behaviour and breaks the test
  for the existing pstdev contract in test_scrum_calculator.py.

---

### ADR-2: Tool Grouping and Naming Convention

**Status:** Accepted
**Date:** 2026-05-28

**Context:**
16 new tools span 4 logical categories: agile metrics, team health, devops tooling,
and India layer. They must be distinguishable in the MCP tool list and must not
collide with existing 25 tool names.

**Decision:**
New tools follow existing naming pattern: `jira_<noun_phrase>`. Tools are
grouped into 4 new comment blocks in server.py:

  Block D: Agile Metrics (6 tools):
    jira_burndown_chart, jira_cfd_analysis, jira_cycle_time_analysis,
    jira_throughput_forecast, jira_scrum_of_scrums, jira_automation_analyzer

  Block E: Team Health Extended (4 tools):
    jira_spotify_health_check, jira_psychological_safety,
    jira_cognitive_load, jira_attrition_forecast

  Block F: DevOps Tooling (3 tools):
    jira_pert_estimate, jira_tco_analysis, jira_rate_limit_status

  Block G: India Layer (3 tools):
    jira_multi_sprint_holidays, jira_ist_capacity, jira_nasscom_mapping

The docstring Tools count in server.py module header will be updated from "25" to
"41" and the tool list extended; all other structure of the header comment is
preserved.

**Consequence:**
Tool count jumps from 25 to 41. The module-level docstring is the only existing
text that changes.

**Alternatives Rejected:**
- Separate server file per new category: rejected because FastMCP stdio servers
  are single-process; splitting tools across servers would require a router/proxy
  not currently in the architecture.

---

### ADR-3: Pure Function Contract for scrum_calculator.py

**Status:** Accepted
**Date:** 2026-05-28

**Context:**
scrum_calculator.py is specified as "stdlib only, no network I/O, stateless pure
functions." The 16 new functions include statistical computations (MLE, bootstrap,
Markov chain), financial modeling (NPV/TCO), and calendar arithmetic
(multi-sprint holiday forecasting). Several of these involve iterative algorithms
(bootstrap resampling, Monte Carlo for Markov chain), which require random.

**Decision:**
All 16 new functions are pure in the following sense:
  1. No file I/O, no network calls, no subprocess invocations.
  2. No mutations of module-level state (INDIA_NATIONAL_HOLIDAYS_2025_2026 is
     read, not written).
  3. Functions using random (bootstrap_bca_ci, tuckman_markov) use random.seed(None)
     following the pattern established by monte_carlo_forecast().
  4. All inputs are validated via explicit guard clauses that raise ValueError.
  5. All math symbols (mu, sigma, lambda, rho, tau) are represented as ASCII
     variable names (mu_hat, sigma_sq, lambda_hat, rho, tau_val etc.) to preserve
     ASCII-only file constraint.

**Consequence:**
bootstrap_bca_ci() is non-deterministic (resampling uses random). This is
intentional and documented in the function docstring. Callers must not depend on
identical output across runs when B (bootstrap iterations) is small.

**Alternatives Rejected:**
- Using numpy for MLE / BCa: rejected because it would add an external dependency,
  violating the no-new-deps constraint.
- Deterministic BCa with fixed seed: rejected because it would provide false
  precision and misrepresent bootstrap confidence intervals.

---

### ADR-4: Three New agile_client.py Methods and Endpoint Coverage

**Status:** Accepted
**Date:** 2026-05-28

**Context:**
Three new endpoints are required that are not currently called by any existing
agile_client.py function:
  GET /rest/agile/1.0/rapid/charts/burndown?rapidViewId={boardId}&sprintId={sprintId}
  GET /rest/agile/1.0/rapid/charts/cumulativeFlowDiagram?rapidViewId={boardId}
  GET /rest/api/3/issue/{key}?expand=changelog

The first two are Agile API endpoints; the third is a core REST endpoint.

**Decision:**
Add 3 new functions to agile_client.py following existing _agile_request() calling
convention:

  get_burndown_chart(cfg, board_id, sprint_id) -> Any:
    Calls: _agile_request(cfg, "GET",
      "rapid/charts/burndown?rapidViewId=<board_id>&sprintId=<sprint_id>")

  get_cfd(cfg, board_id) -> Any:
    Calls: _agile_request(cfg, "GET",
      "rapid/charts/cumulativeFlowDiagram?rapidViewId=<board_id>")

  get_issue_changelog(cfg, issue_key) -> Any:
    Uses server._request() pattern directly (urllib.request) because the changelog
    endpoint is on /rest/api/{version}/ not /rest/agile/1.0/. The function
    accepts cfg dict and constructs the URL as:
    cfg["url"] + "/rest/api/" + cfg["api_version"] + "/issue/" + issue_key
    + "?expand=changelog&fields=changelog,summary,created"
    This avoids importing server._request() into agile_client.py (would create
    a circular import server -> agile_client -> server).

**Consequence:**
agile_client.py grows from 138 lines to approximately 230 lines. The get_issue_changelog
function duplicates the urllib.request pattern from server._request() rather than
importing it. This is a deliberate trade-off to preserve the no-circular-import
guarantee.

**Alternatives Rejected:**
- Moving _request() to a shared http_client.py module: rejected as a refactoring
  step; this blueprint is extension-only, not refactor-only. The duplication is
  minimal (15 lines) and confined to agile_client.py.
- Having server.py tools call _request() for changelog and pass result to
  agile_client functions: rejected as awkward inversion of dependencies.

---

### ADR-5: rate_limiter.py Exposure as MCP Tool (jira_rate_limit_status)

**Status:** Accepted
**Date:** 2026-05-28

**Context:**
rate_limiter.py contains a module-level dict `_buckets` and related constants
that represent the current token bucket state. This state is invisible to MCP
clients. The KG specifies a jira_rate_limit_status tool to expose this as a
read-only MCP tool.

**Decision:**
Expose rate_limiter.py internals as a new read-only MCP tool jira_rate_limit_status
by importing the module-level symbols directly:
  from rate_limiter import _buckets, _buckets_lock, _BUCKET_DEFAULTS, _RETRY_AFTER_SECONDS

The tool function computes a snapshot of current bucket states under _buckets_lock
and returns a JSON-serializable dict. It does not consume tokens (read-only).
The tool is registered in Block F (DevOps Tooling) in server.py.

Since rate_limiter.py's _buckets dict uses tuple keys (client_id, bucket_name),
the tool converts these to string keys for JSON serialization (e.g.,
"default:tool_calls").

**Consequence:**
Imports from rate_limiter.py are added to server.py's import block. The rate_limiter
module remains unchanged. Exposing private symbols (_buckets, _buckets_lock) is
acceptable here because server.py and rate_limiter.py are in the same package and
the access is read-only under the lock.

**Alternatives Rejected:**
- Adding a public get_bucket_status() function to rate_limiter.py: not rejected,
  but deferred. The solution above keeps rate_limiter.py unchanged, satisfying
  the no-existing-file-modification constraint.
- Exposing rate limit state via a health check endpoint: rejected because jira_health_check
  already exists and serves a different purpose; mixing concerns would reduce clarity.

---

### ADR-6: Python 3.8 Compatibility Gate

**Status:** Accepted
**Date:** 2026-05-28

**Context:**
The project targets Python 3.8+ on Windows (cp1252). Three language features
introduced after 3.8 are commonly generated by LLMs:
  - Walrus operator (:=) -- Python 3.8+ but banned per project convention
  - match/case statements -- Python 3.10+
  - dict union operator (| for dicts) -- Python 3.9+
  - Union type hints using | (X | Y) -- Python 3.10+
  - f-string = specifier (f"{x=}") -- Python 3.8 only partial support

**Decision:**
All new Python code (in server.py, scrum_calculator.py, agile_client.py) must
comply with the following ruleset:
  1. No walrus operator (:=).
  2. No match/case.
  3. No dict union (use dict.update() or {**a, **b}).
  4. Use Union[X, Y] from typing, not X | Y.
  5. Use Optional[X] for nullable types, not X | None.
  6. Type hint literals use typing.List, typing.Dict, typing.Tuple, not list[], dict[], tuple[].
  7. No f-string self-documenting expressions (f"{x=}").
  8. No structural pattern matching in any form.

The python-backend-engineer agent is responsible for running a 3.8-compat lint
pass (or manual review) before merging any agent's contribution.

**Consequence:**
Minor verbosity increase in type hints. All agents must use `from typing import
List, Dict, Optional, Tuple, Any` headers consistently.

---

### ADR-7: Input Validation Gate for All New Tools

**Status:** Accepted
**Date:** 2026-05-28

**Context:**
Existing tools call _get_config() and proceed without systematically validating
string inputs through input_validator.py. The KG specifies "All new inputs
validated via input_validator.py before any computation."

**Decision:**
Every new tool function in server.py that accepts a string parameter (project_key,
issue_key, board_id as str, free-text fields) must call validate_input() from
input_validator.py as the first operation after _get_config(). Integer and float
parameters are validated using explicit guard clauses (if x < 1: raise ValueError).
String parameters with known-safe patterns (ISO date strings, enum values) are
validated for length only (max_length=100). Free-text fields (description, notes,
goal) use max_length=4096.

The import `from input_validator import validate_input` is added to server.py
if not already present. Currently, input_validator is not imported in server.py
(validation is done ad-hoc with inline checks). The new import is additive.

**Consequence:**
New tools have a consistent validation pattern. Existing tools are not retroactively
changed (they keep their inline validation).

---

### ADR-8: Markov Chain Tuckman Model via tuckman_markov()

**Status:** Accepted
**Date:** 2026-05-28

**Context:**
jira_team_health currently calls scrum_calculator.tuckman_estimate() at line 2051
in server.py to determine the Tuckman stage. The KG specifies upgrading this to
a Markov chain model via a new tuckman_markov() function in scrum_calculator.py.

**Decision:**
Add tuckman_markov(velocity_history, team_age_sprints) to scrum_calculator.py.
The function computes transition probabilities between Forming/Storming/Norming/
Performing states using velocity variance ratios and applies matrix exponentiation
over team_age_sprints steps to yield a steady-state probability distribution.
The state with the highest probability is returned as the stage string.

In server.py, the upgrade to jira_team_health replaces the SINGLE LINE at line 2051
(the tuckman_estimate() call) with a call to scrum_calculator.tuckman_markov().
The lines AFTER this (2057-2070: the health_summary/intervention decision tree that
uses the tuckman_stage result) are NOT changed -- they are consumers of the
tuckman_stage variable, which retains the same type (str) and same set of possible
values ("Forming", "Storming", "Norming", "Performing").

The existing scrum_calculator.tuckman_estimate() function is NOT removed (other
tests and callers may depend on it). The upgraded tool simply calls the new function
at the single substitution point.

**Consequence:**
tuckman_estimate() remains in scrum_calculator.py and in tests. tuckman_markov()
is a richer model but has the same return type. jira_team_health is upgraded to
use tuckman_markov(). Tests for jira_team_health must be updated to expect the
Markov-based output, but the schema (keys and value types) does not change.

---

## 5. Interface Contracts

### 5.1 scrum-master-agent --> python-backend-engineer (Integration Contract)

scrum-master-agent is responsible for implementing:
  - 16 new pure functions in scrum_calculator.py (append to line 533+)
  - 5 upgraded tool bodies in server.py delivered as stubs in
    docs/outputs/b1-server-additions.py (see Section 2.5 for assembly protocol)
  - New tool bodies in docs/outputs/b1-server-additions.py for:
      jira_scrum_of_scrums, jira_spotify_health_check, jira_psychological_safety,
      jira_cognitive_load, jira_attrition_forecast, jira_pert_estimate,
      jira_tco_analysis, jira_multi_sprint_holidays, jira_ist_capacity,
      jira_nasscom_mapping, jira_rate_limit_status

**Handoff artifact: scrum_calculator.py additions**

Each new function delivered to python-backend-engineer MUST:
  1. Have a Google-style docstring with Args, Returns, Raises sections.
  2. Accept only stdlib-compatible types (int, float, str, List[int], Dict[str, Any] etc.)
  3. Raise ValueError for invalid inputs (not AssertionError).
  4. Return a Dict[str, Any] (not a JSON string -- server.py tools handle serialization).
  5. Use only ASCII characters (no Greek letters, no Unicode math).
  6. Not import anything outside the already-imported header (math, random,
     statistics, datetime.date, typing).
  7. Append below the last line of the current file without altering existing content.

**Expected function signatures (scrum-master-agent output):**

  bootstrap_bca_ci(data, stat_func, B=2000, alpha=0.05)
    -> Dict[str, Any]  # keys: ci_low, ci_high, point_estimate, B_used

  ahp_score(criteria_matrix)
    -> Dict[str, Any]  # keys: weights, consistency_ratio, is_consistent

  tuckman_markov(velocity_history, team_age_sprints)
    -> str  # one of: "Forming", "Storming", "Norming", "Performing"

  spotify_health_check(dimension_scores)
    -> Dict[str, Any]  # keys: ths_score, wilcoxon_z, zone, dimension_breakdown

  edmondson_ps_scale(item_scores)
    -> Dict[str, Any]  # keys: ps_score, cronbach_alpha, safety_zone

  scrum_of_scrums_overhead(n_teams, p_productivity, c_coordination_cost)
    -> Dict[str, Any]  # keys: net_throughput, n_optimal, overhead_pct

  cognitive_load_index(complexity_list, responsibility_list, cl_max)
    -> Dict[str, Any]  # keys: cl_team, cli, load_zone

  attrition_ramp(months_elapsed, p_max, experienced)
    -> Dict[str, Any]  # keys: p_attrition, tau, risk_zone

  ist_capacity_correction(nominal_hours, overlap_hours=4.5)
    -> Dict[str, Any]  # keys: effective_hours, correction_factor, overlap_note

  little_law_analysis(avg_wip, avg_cycle_time_days, avg_throughput_per_day)
    -> Dict[str, Any]  # keys: l_computed, lambda_computed, w_computed,
                       #       consistency_check, deviation_pct

  cycle_time_lognormal_mle(cycle_times_days)
    -> Dict[str, Any]  # keys: mu_hat, sigma_sq_hat, p50_days, p85_days, p95_days

  poisson_throughput(completed, period_days)
    -> Dict[str, Any]  # keys: lambda_hat, ci_low_95, ci_high_95, period_days

  pert_estimate(optimistic, most_likely, pessimistic)
    -> Dict[str, Any]  # keys: pert_mean, pert_sigma, ci_low_90, ci_high_90

  tco_npv_comparison(
      jira_premium_inr_annual, azure_inr_annual,
      years=3, discount_rate=0.10
  )
    -> Dict[str, Any]  # keys: jira_npv_inr, azure_npv_inr, delta_inr,
                       #       recommended_platform, payback_years

  burndown_metrics(
      total_points, completed_points_by_day,
      sprint_days, days_elapsed
  )
    -> Dict[str, Any]  # keys: ideal_remaining, actual_remaining,
                       #       deviation_pct, projected_completion_day,
                       #       health_signal

  multi_sprint_holiday_forecast(
      sprint_start_dates, sprint_end_dates
  )
    -> Dict[str, Any]  # keys: holiday_counts_per_sprint, total_holidays,
                       #       high_impact_sprints

**Handoff artifact: docs/outputs/b1-server-additions.py tool stubs**

For each new server.py tool delivered in b1-server-additions.py:
  - Complete @mcp.tool() + @mcp_tool_handler decorated function.
  - Function accepts typed parameters (Optional[str] for nullable strings,
    int/float for numeric, List-style params as comma-separated strings).
  - All string inputs run through validate_input() before computation.
  - All computations delegated to scrum_calculator functions.
  - Return dict follows existing key naming conventions (snake_case keys).

**Backward-compat gate (python-backend-engineer validates):**
  - Diff of scrum_calculator.py: only additions below line 533, zero deletions.
  - Diff of server.py (after B.3 assembly): only additions and the 4 targeted
    upgrade blocks; no changes to lines 1-799 (existing core tools) or lines
    800-1065 (board/sprint infrastructure tools).
  - All existing tests still pass (pytest tests/).

---

### 5.2 agile-tooling-specialist --> python-backend-engineer (Integration Contract)

agile-tooling-specialist is responsible for implementing:
  - 3 new functions in agile_client.py (append to line 138+)
  - New tool bodies in docs/outputs/b2-server-additions.py for:
      jira_burndown_chart, jira_cfd_analysis, jira_cycle_time_analysis,
      jira_throughput_forecast, jira_automation_analyzer, jira_nasscom_mapping

**Resolved: jira_automation_analyzer input contract (RESOLVED Q-01)**

jira_automation_analyzer accepts automation rules as a user-supplied JSON input
parameter. It does NOT call any Jira REST API. The tool has no network I/O.

Tool signature:
  jira_automation_analyzer(rules_dag: str, lambda_rate: float, mu_rate: float)

Where rules_dag is a JSON-encoded adjacency list representing automation rule
triggers and actions. Example: '{"rule_A": ["rule_B", "rule_C"], "rule_B": []}'

The tool performs two purely local computations:
  1. M/M/1 queueing analysis: rho = lambda_rate / mu_rate (server utilisation).
     Inputs: lambda_rate (average rule trigger rate, events/min),
             mu_rate (average rule execution rate, events/min).
     Outputs: rho (utilisation ratio), mean_queue_length, mean_wait_time_mins,
              stability_warning (if rho >= 1.0).
  2. Kahn's topological sort for DAG cycle detection O(V+E) on the rules_dag
     adjacency list. Returns: is_dag (bool), cycle_detected (bool),
     topological_order (list of rule names if no cycle, else empty list).

This design is intentional: Jira does not expose automation rules via a public
REST API on Cloud or Server. Users who want to analyse their automation rule
graph must supply it as input. The tool is self-contained and testable without
any Jira connectivity.

agile-tooling-specialist implements the Kahn DAG algorithm inline in the tool
body (it is short: ~20 lines) rather than delegating to scrum_calculator.py,
because the algorithm is graph-theoretic, not statistical. Alternatively,
if scrum_calculator.py grows a graph_dag_check() function, the tool delegates
to it instead -- python-backend-engineer decides at assembly time.

**Handoff artifact: agile_client.py additions**

Each new function delivered to python-backend-engineer MUST:
  1. Accept (cfg, ...) as first argument following _agile_request() convention.
  2. Use _agile_request() for /rest/agile/1.0/ paths.
  3. For get_issue_changelog: use urllib.request directly (mirrors _request()
     pattern in server.py) because changelog is a core REST endpoint.
  4. Return Any (parsed JSON dict/list or None for 204).
  5. Raise RuntimeError on HTTP errors (same format as _agile_request()).
  6. Have a complete Google-style docstring.
  7. ASCII-only.

**Expected function signatures (agile-tooling-specialist output):**

  get_burndown_chart(cfg, board_id, sprint_id)
    # type: (Dict[str, str], int, int) -> Any
    # GET /rest/agile/1.0/rapid/charts/burndown?rapidViewId={board_id}&sprintId={sprint_id}

  get_cfd(cfg, board_id)
    # type: (Dict[str, str], int) -> Any
    # GET /rest/agile/1.0/rapid/charts/cumulativeFlowDiagram?rapidViewId={board_id}

  get_issue_changelog(cfg, issue_key)
    # type: (Dict[str, str], str) -> Any
    # GET /rest/api/{version}/issue/{key}?expand=changelog&fields=changelog,summary,created

**Handoff artifact: docs/outputs/b2-server-additions.py tool stubs for network tools**

For each of the 6 network-dependent new tools delivered in b2-server-additions.py:
  - @mcp.tool() + @mcp_tool_handler
  - Call _get_config(), then call the corresponding agile_client function.
  - Pass raw API data to scrum_calculator pure functions for metric computation.
  - Handle None return from agile_client (server is unreachable / 204 response)
    with a graceful fallback dict (not an exception).

**Tool-to-function mapping (agile-tooling-specialist follows this):**

  jira_burndown_chart(board_id, sprint_id):
    agile_client.get_burndown_chart(cfg, board_id, sprint_id)
    -> scrum_calculator.burndown_metrics(total_points, points_by_day, sprint_days, elapsed)

  jira_cfd_analysis(board_id):
    agile_client.get_cfd(cfg, board_id)
    -> scrum_calculator.little_law_analysis(avg_wip, avg_ct, avg_throughput)

  jira_cycle_time_analysis(board_id, sprint_id, max_issues=30):
    agile_client.get_issue_changelog(cfg, issue_key) -- called per issue, cap 30
    -> scrum_calculator.cycle_time_lognormal_mle(cycle_times_days)

  jira_throughput_forecast(board_id, period_days=14):
    Existing _agile_request(cfg, "GET", "board/{board_id}/sprint?state=closed")
    -> scrum_calculator.poisson_throughput(completed, period_days)

  jira_automation_analyzer(rules_dag, lambda_rate, mu_rate):
    No network call -- purely local computation (see Q-01 resolution above).
    Inline M/M/1 rho computation + Kahn DAG cycle detection.
    No agile_client or scrum_calculator delegation required.

  jira_nasscom_mapping(board_id, num_sprints=6):
    Existing _agile_request for velocity + existing velocity_stats()
    -> scrum_calculator._nasscom_agile_x_level() (already exists)
    + new nasscom_dimension_scores dict construction

**Backward-compat gate (python-backend-engineer validates):**
  - Diff of agile_client.py: only additions below line 138, zero deletions.
  - Existing _agile_request, _agile_url, _build_agile_auth_header unchanged.
  - All existing tests still pass.

---

### 5.3 Python 3.8 Compat Validation (python-backend-engineer gate)

Before merging any agent contribution, python-backend-engineer must verify:

  1. Run: python -m py_compile scrum_calculator.py agile_client.py server.py
     Expected: zero errors.

  2. Run: grep -n ":=" scrum_calculator.py agile_client.py server.py
     Expected: zero matches (no walrus operators).

  3. Run: grep -n "match " scrum_calculator.py agile_client.py server.py
     Expected: zero matches (no match/case).

  4. Run: python -c "import sys; assert sys.version_info < (3,9), 'test py38'"
     on CI -- enforced at pipeline level.

  5. Run: pytest tests/ -v
     Expected: all tests green.

  6. Check requirements.txt: diff must show zero changes.

---

## 6. Risk Register

### R-01: Rapid Charts Endpoint Availability
**Probability:** Medium | **Impact:** High
**Description:** The /rest/agile/1.0/rapid/charts/burndown and cumulativeFlowDiagram
endpoints are marked as "internal" or "deprecated" in some versions of Jira Cloud
and are absent in Jira Data Center < 8.x. Tools jira_burndown_chart and
jira_cfd_analysis will fail on such instances.
**Mitigation:** Wrap agile_client.get_burndown_chart() and get_cfd() calls in
try/except RuntimeError inside the server.py tool handlers. Return a degraded
response dict with "endpoint_available": false and a note explaining the fallback.
Follow the existing pattern in jira_get_velocity (lines 1670-1698) where
RuntimeError from the velocity chart endpoint triggers a fallback to sprint
enumeration.

### R-02: Changelog API Call Volume for jira_cycle_time_analysis
**Probability:** High | **Impact:** Medium
**Description:** jira_cycle_time_analysis fetches a changelog per issue. For a
sprint with 30 issues (capped per R-02 mitigation), this generates 30 sequential
HTTP calls. Each call is synchronous (urllib.request). At 300ms per call this is
9 seconds -- well within MCP client timeouts.
**Mitigation:** (1) Cap max_issues at 30 per tool call (not 100). (2) Short-circuit
if total elapsed exceeds 20 seconds (check datetime.utcnow() in the loop).
(3) Document the cap clearly in the tool docstring. (4) Add "issues_analyzed" and
"issues_skipped" keys to the response dict.

### R-03: bootstrap_bca_ci() Non-Determinism in Tests
**Probability:** Medium | **Impact:** Low
**Description:** bootstrap_bca_ci() uses random.seed(None) (non-deterministic).
Tests asserting exact CI values will fail intermittently.
**Mitigation:** Tests for bootstrap_bca_ci() must use property-based assertions:
ci_low <= point_estimate <= ci_high; ci_high - ci_low > 0; both bounds are finite.
Never assert exact float values for BCa CI outputs.

### R-04: Jira Premium INR Prices Drift in jira_tco_analysis
**Probability:** High | **Impact:** Low
**Description:** tco_npv_comparison() hard-codes Jira Premium ~INR 41.7L and
Azure ~INR 20.4L per year. These prices change. Hard-coded constants become stale.
**Mitigation:** Accept jira_annual_cost_inr and azure_annual_cost_inr as optional
parameters with the KG values as defaults. Expose them in the tool signature:
jira_tco_analysis(jira_annual_cost_inr=4170000, azure_annual_cost_inr=2040000, ...).
Document the default assumption year (2025) in the docstring.

### R-05: tuckman_markov() Insufficient Data Regime
**Probability:** Medium | **Impact:** Medium
**Description:** Markov chain transition probability estimation requires at least
4 velocity data points to differentiate states. With fewer than 4 sprints, the
matrix will be degenerate (division by zero or uniform distribution).
**Mitigation:** Add a guard in tuckman_markov(): if len(velocity_history) < 4,
fall back to tuckman_estimate() (the existing heuristic). Return an additional
"model_used" key: "markov" or "heuristic_fallback". python-backend-engineer
validates this key is present in the response.

### R-06: ASCII-Only Constraint Violation by Agents
**Probability:** Medium | **Impact:** High
**Description:** Statistical formulas naturally use Greek letters. LLM-generated
code for MLE, Cronbach alpha, etc. often contains Unicode math symbols.
cp1252 cannot encode them; the MCP server process will crash on file load.
**Mitigation:** python-backend-engineer runs:
  python -c "open('scrum_calculator.py', 'rb').read().decode('ascii')"
as a pre-merge gate. Any non-ASCII byte causes a UnicodeDecodeError that blocks
the merge. All variable names for Greek letters use ASCII spellings:
  mu -> mu_val, sigma -> sigma_val, lambda -> lambda_hat, alpha -> alpha_val,
  tau -> tau_val, rho -> rho_val.

### R-07: Token Bucket State Snapshot Races in jira_rate_limit_status
**Probability:** Low | **Impact:** Low
**Description:** The snapshot in jira_rate_limit_status reads _buckets under
_buckets_lock, but the token count inside each TokenBucket is accessed without
its own lock (outside the bucket's _lock). A racing token consumption during
snapshot can produce a slightly stale token count.
**Mitigation:** Accept this as a known limitation. The tool is a diagnostic
read-only view, not a transactional gate. Document in the tool docstring:
"Token counts are approximate snapshots and may not reflect concurrent consumption."

### R-08: scrum_of_scrums_overhead() Degenerate Inputs
**Probability:** Low | **Impact:** Medium
**Description:** Formula T(n) = n*p - c*n*(n-1)/2 can produce negative net
throughput if c (coordination cost) is high relative to p (productivity).
n_optimal = p/c + 0.5 is also undefined if c = 0.
**Mitigation:** Add guard: if c <= 0: raise ValueError("c_coordination_cost must
be > 0"). Cap n_optimal at max(1, n_teams). Add "viable_regime" boolean key:
True if net_throughput > 0.

---

## 7. Resolved Questions

### Q-01: jira_automation_analyzer Scope -- RESOLVED

**Resolution:** jira_automation_analyzer accepts automation rules as a
user-supplied JSON input parameter (rules_dag: str, a JSON-encoded adjacency
list of rule triggers and actions). It does NOT call any Jira REST API.

The tool performs two purely local computations:
  1. M/M/1 queueing analysis: rho = lambda_rate / mu_rate
     (lambda_rate = avg trigger rate events/min, mu_rate = avg execution rate
     events/min). Outputs: rho, mean_queue_length, mean_wait_time_mins,
     stability_warning (if rho >= 1.0).
  2. Kahn's topological sort O(V+E) for DAG cycle detection on the rules_dag
     adjacency list. Outputs: is_dag, cycle_detected, topological_order.

Rationale: Jira does not expose automation rules via any public REST API on
Cloud or Server editions. Requiring user-supplied input is the only viable
approach without an unofficial/unsupported API scrape.

---

### Q-02: jira_nasscom_mapping vs jira_get_velocity Overlap -- ACCEPTABLE (no change required)

The existing velocity_stats() returns a single CV-based NASSCOM AgileX level.
jira_nasscom_mapping adds multi-dimensional NASSCOM scoring across all 5 AgileX
dimensions. The exact 5 dimensions are derivable from the NASSCOM AgileX model
constants already present in scrum_calculator.py (_nasscom_agile_x_level).
Implementation detail is delegated to agile-tooling-specialist.

---

### Q-03: Bootstrap BCa Upgrade Scope -- RESOLVED

**Resolution:** BOTH jira_plan_sprint AND jira_get_velocity descriptions in
section 2.2 U4 originally mentioned BCa, but the authoritative scope is:

  - jira_get_velocity: YES -- receives BCa upgrade. After the velocity_stats()
    call, a supplemental bootstrap_bca_ci() call adds three new keys:
    "bca_lower", "bca_upper", "bca_confidence" to the response.
    Existing "stddev" key is preserved. Backward compatible (additive keys only).

  - jira_plan_sprint: NO -- is NOT modified. sprint_capacity() inside
    jira_plan_sprint has no stddev/CI computation. Adding BCa here would require
    defining a new CI domain for capacity estimation, which is out of scope for
    this batch.

Backward compatibility contract:
  - Existing output keys for jira_get_velocity: all preserved unchanged.
  - New keys added: "bca_lower" (float), "bca_upper" (float),
    "bca_confidence" (float, value 0.95).
  - Clients that do not use the new keys are unaffected.

---

### Q-04: edmondson_ps_scale Cronbach Alpha -- ACCEPTABLE

The simplified standardized-item formula (alpha = n*r_bar / (1 + (n-1)*r_bar))
is used for a fixed 7-item scale. scrum-master-agent defaults to this formula
and documents the assumption in the docstring.

---

### Q-05: jira_spotify_health_check Dimension Weights -- ACCEPTABLE

Original Spotify Squad Health Check uses equal weights (1/11 per dimension).
scrum-master-agent implements with equal weights as the default and makes weights
an optional parameter. Documented in docstring.

---

### Q-06: multi_sprint_holiday_forecast Sprint Count Limit -- ACCEPTABLE

Maximum list length: 26 sprints (guard clause raises ValueError if exceeded).
Out-of-range dates silently return 0 holidays (documented in docstring).

---

### Q-07: Conflict Resolution for Concurrent Agent Edits to server.py -- RESOLVED

**Resolution:** Artifact-based assembly workflow. See Section 2.5 for full
protocol specification. Summary:
  - scrum-master-agent (B.1): writes to scrum_calculator.py + docs/outputs/b1-server-additions.py
  - agile-tooling-specialist (B.2): writes to agile_client.py + docs/outputs/b2-server-additions.py
  - python-backend-engineer (B.3): sole writer to server.py; assembles both
    artifact files into server.py in a single pass.
  - Zero concurrent writes to server.py. No merge conflicts possible.

---

### Q-08: Test Coverage Responsibility -- ACCEPTABLE

Each implementing agent delivers test stubs alongside their implementation.
python-backend-engineer validates that all stubs pass before assembly into
server.py. The python-backend-engineer backward-compat gate (section 5.3 item 5)
ensures coverage is not regressed.

---

STATUS: SUBMITTED FOR CONSENSUS REVIEW (Revision 2)

---

REVISION LOG
=============
Revision 1 (2026-05-28): Fixed ISSUE-1 (tool count), ISSUE-2 (upgrade line ref), ISSUE-3 (BCa scope), ISSUE-4 (Q-01/Q-03 resolved), ISSUE-5 (assembly protocol defined)
Revision 2 (2026-05-28): Corrected tool count to 16 new / 41 total. Source doc inconsistency noted.

STATUS: SUBMITTED FOR CONSENSUS REVIEW (Revision 2)
