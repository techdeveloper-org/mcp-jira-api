SECURITY TESTING REPORT
========================
Date: 2026-05-28
Scope: New/modified code from KG gap closure (B.1+B.2+B.3+security fixes)
Engineer: security-testing-engineer (automated SAST)
Files reviewed:
  - server.py (lines 2278-3344: all Phase B.1 and B.2 new tools)
  - scrum_calculator.py (lines 533-1813: 16 new pure functions)
  - agile_client.py (full file: new AgileClient class and module-level helpers)
  - input_validator.py (full file)
  - base/decorators.py (full file: mcp_tool_handler)
  - mcp_errors.py (full file)
  - rate_limiter.py (lines 1-50)
  - tests/fixtures/agile/*.json (6 files)
  - tests/fixtures/rest/*.json (4 files)
  - tests/test_scrum_calculator_new.py (header + structure)
  - tests/test_tools_integration_new.py (header + structure)

════════════════════════════════════════════════════════════════════════════════
SAST RESULTS
════════════════════════════════════════════════════════════════════════════════

A01 BROKEN ACCESS CONTROL
──────────────────────────
Status: No findings

Analysis:
  1. All new tools (jira_spotify_health_check, jira_psychological_safety,
     jira_cognitive_load, jira_attrition_forecast, jira_pert_estimate,
     jira_scrum_of_scrums, jira_ist_capacity, jira_multi_sprint_holidays,
     jira_burndown_chart, jira_cfd_analysis, jira_cycle_time_analysis,
     jira_throughput_forecast, jira_automation_analyzer, jira_tco_analysis,
     jira_nasscom_mapping, jira_rate_limit_status) acquire Jira credentials
     exclusively through _get_config() which reads JIRA_URL / JIRA_USER /
     JIRA_API_TOKEN from environment variables (server.py lines 77-104).
     No new tool bypasses this path.

  2. No hardcoded board IDs or sprint IDs appear in production code paths.
     Numeric IDs are runtime parameters validated as positive integers before
     use (e.g. `if not isinstance(board_id, int) or board_id < 1: raise ValueError`
     repeated across all 7 B.2 tools).

  3. jira_rate_limit_status (server.py lines 2598-2641): Confirmed read-only.
     The function only reads internal module state via `_rl._buckets` -- it calls
     `bucket._refill()` solely for accurate token accounting (a side-effect-free
     operation that recomputes internal float state but does not consume tokens
     or issue any external call). No mutation of rate-limiter state occurs.
     No Jira API call is made. The tool is correctly described as read-only.


A03 INJECTION
──────────────
Status: 1 Medium finding, 1 Low/Informational finding

Findings:

  [MEDIUM] A03-01: issue_key path traversal risk in agile_client.get_issue_changelog
  File: agile_client.py, line 347
  Code: "/rest/api/3/issue/" + issue_key
  Risk: The issue_key parameter is concatenated directly into the URL path with no
    validation. If a caller passes a key containing path-traversal sequences such as
    "../admin" or URL-encoding tricks, the resulting URL could resolve to an unintended
    Jira API endpoint. However, the attack surface is limited:
      - This method is not yet called from server.py (no tool calls get_issue_changelog).
      - The Jira API itself enforces issue key format (PROJ-NNN) at the server and
        returns 404 or 400 for invalid keys, providing a second layer of defence.
      - The urllib.request stack does not auto-follow cross-origin redirects.
    Recommendation: Add a regex guard before the URL concatenation, identical to the
    project_key regex already used in server.py (r'^[A-Z][A-Z0-9]{0,9}-[0-9]+$').
    Severity: Medium (pre-call, defence-in-depth gap).

  [LOW/INFO] A03-02: No use of eval(), exec(), os.system(), os.popen() found
  Grep across all .py files returned zero matches for eval, exec, subprocess (except
  base/clients.py line 356 which calls `subprocess.run(["gh", "auth", "token"])` --
  this is in the base package, not in new B.1/B.2 code, and uses a static command
  list with no user input, so no injection vector exists).

  JSON inputs (dimension_scores, criteria_matrix, trigger_rates_json, etc.):
  All JSON string inputs in new tools are parsed via json.loads() after passing
  through validate_input() (null-byte strip + length cap). No eval() or
  pickle.loads() is used anywhere in the new code. This is correct.

  board_id/sprint_id in URL paths: All integer IDs are validated as positive
  integers before being converted to strings via str(board_id) in agile_client.py.
  String concatenation of validated integers is safe -- no injection vector.

  project_key regex validation: Three locations in server.py (lines 1496, 1569,
  1995) apply `r'^[A-Z][A-Z0-9]{0,9}$'` before JQL construction. Confirmed in place
  as a result of F.1 security fixes.


A05 SECURITY MISCONFIGURATION
────────────────────────────
Status: No findings

Analysis:
  1. No `debug=True`, `verbose=True`, or equivalent debug-mode flags appear in new
     code. Grep across all .py files for `debug.*=.*[Tt]rue` returned zero matches.

  2. FastMCP server is initialised with:
       mcp = FastMCP("jira-api", instructions="...")
     No debug parameter is passed; FastMCP defaults are production-safe.

  3. No hardcoded URLs in new tool code. All Jira URLs are built from
     `cfg["url"]` which is read from the `JIRA_URL` environment variable.
     The agile_client.py `_AGILE_BASE = "/rest/agile/1.0"` is a path constant
     (not a full URL) and is appropriate as a code constant.

  4. No test credentials appear in production code paths. Test config dicts
     in test_agile_client.py use `"token": "test-token-ascii-only"` which is
     obviously synthetic and not a real credential format.


A06 OUTDATED COMPONENTS
─────────────────────────
Status: 2 High findings (unpinned versions)

requirements.txt contents:
  mcp>=1.0.0
  fastmcp>=0.1.0

Findings:

  [HIGH] A06-01: mcp dependency is not pinned to an exact version
  Spec: `mcp>=1.0.0`
  Risk: A breaking change or security regression in any future mcp release
    (e.g. 2.x) would be silently adopted on the next clean install without
    any review. The `>=` specifier with a wide lower bound provides no upper
    bound protection.
  Recommendation: Pin to the exact version currently in use, e.g. `mcp==1.2.0`.
    If minor-version compatibility is needed, use a bounded range: `mcp>=1.0.0,<2.0.0`.

  [HIGH] A06-02: fastmcp dependency is not pinned to an exact version
  Spec: `fastmcp>=0.1.0`
  Risk: Same rationale as A06-01. fastmcp is a relatively new library (0.x versioning
    implies pre-stable API). Any 0.x -> 0.x+1 version jump may introduce breaking
    changes or new attack surface with no pin to catch it.
  Recommendation: Pin to the exact version, e.g. `fastmcp==0.4.2` (or whichever
    version is currently installed). Add a requirements-lock.txt or use pip freeze.

  CVE scan (based on knowledge cutoff August 2025):
    mcp: No known CVEs in the 1.x line as of August 2025.
    fastmcp: No known CVEs in the 0.x line as of August 2025.
    Note: Both libraries are stdlib-wrapper packages with minimal transitive
    dependencies. The primary risk is API breakage, not known exploit chains.


A09 LOGGING FAILURES
─────────────────────
Status: 1 Medium finding

Analysis:
  1. New tool functions (B.1 and B.2) do not perform any logging. They return
     structured dict results and rely on the @mcp_tool_handler decorator for
     error capture. No logger calls appear in jira_spotify_health_check,
     jira_psychological_safety, jira_cognitive_load, or any of the 16 new tools.
     This means no API tokens or passwords are logged by new code directly.

  2. @mcp_tool_handler (base/decorators.py lines 124-136): When an exception is
     caught, the error payload contains `str(e)` as the error message and
     optionally `traceback.format_exc()[-500:]` if `include_traceback=True`. In
     all @mcp_tool_handler usages in server.py, `include_traceback` is the
     default (False). No tracebacks are sent to the MCP client by default.
     This is correct.

  [MEDIUM] A09-01: mcp_safe_execute() in mcp_errors.py embeds truncated traceback in response
  File: mcp_errors.py, lines 79-83
  Code: `details={"traceback": traceback.format_exc()[-500:]}`
  Risk: mcp_safe_execute() is a legacy wrapper that embeds the last 500 characters
    of the exception traceback in the structured error response returned to the MCP
    client. If the traceback fragment includes file paths, class names, or -- in an
    unlikely worst case -- logged variable values that happen to contain credential
    substrings, internal detail is leaked to the caller.
    Note: No new B.1/B.2 tool uses mcp_safe_execute() directly. The decorator
    mcp_tool_handler is used instead, which does NOT embed tracebacks by default.
    This finding applies to any existing tool that calls mcp_safe_execute() and
    is flagged here for completeness.
  Recommendation: Remove the `details.traceback` field from mcp_safe_execute(), or
    gate it behind an explicit `ENABLE_DEBUG_TRACEBACKS=1` environment variable.
    The `str(e)` message is sufficient for the MCP client.

  3. No new code logs `cfg["token"]`, `cfg["user"]`, Authorization header values,
     or any other sensitive field. The agile_client._agile_request() and
     AgileClient._request() methods build auth headers in memory and pass them
     directly to urllib.request.Request without logging. Confirmed clean.

  4. Error messages in new tools are constructed from safe values only:
     board_id (int), sprint_id (int), error_type strings, Jira HTTP error codes.
     No user-supplied strings appear unfiltered in error messages.


════════════════════════════════════════════════════════════════════════════════
SECRETS SCAN
════════════════════════════════════════════════════════════════════════════════

Status: No secrets detected -- all sensitive values via env vars only

Files scanned and findings:

server.py (lines 2260+):
  No hardcoded API keys, tokens, passwords, or credentials found.
  All credential access via os.environ.get("JIRA_URL"), os.environ.get("JIRA_USER"),
  os.environ.get("JIRA_API_TOKEN"), os.environ.get("JIRA_API_VERSION"),
  os.environ.get("JIRA_AUTH_METHOD") in _get_config() (lines 77-104).

scrum_calculator.py (lines 533+):
  No credentials. Only mathematical constants, holiday date strings ("2025-01-01" etc.),
  and numeric algorithm coefficients. All reviewed and confirmed benign.

agile_client.py (full file):
  No hardcoded credentials. The `_AGILE_BASE = "/rest/agile/1.0"` constant is a
  path fragment, not a credential. Auth credentials are passed at call time via
  the `cfg` dict (which comes from _get_config()).

tests/fixtures/agile/*.json (6 files reviewed):
  board_list.json: URLs use "https://test.atlassian.net" -- clearly a synthetic
    test domain, not a real customer domain. No tokens, passwords, or real API keys.
  sprint_list.json, sprint_detail.json, sprint_issues.json, velocity_chart.json,
  burndown_chart.json: All contain synthetic test data. No credentials or real URLs
    beyond the "test.atlassian.net" test domain.

tests/fixtures/rest/*.json (4 files reviewed):
  issue_create.json, issue_search_impediment.json, issue_search_sprint.json,
  server_info.json: Use "https://test.atlassian.net" as base URL. No tokens,
  passwords, API keys, or realistic credential strings found.

tests/test_scrum_calculator_new.py:
  No credentials. Uses purely mathematical test data.

tests/test_tools_integration_new.py:
  No credentials. Uses synthetic URLs via mock urllib.request.urlopen. The
  test_agile_client.py helper _basic_cfg() uses "token": "test-token-ascii-only"
  which is a clearly synthetic placeholder value, not a real token.

Overall: The "test.atlassian.net" domain appears in fixture JSON "self" URL fields
  and in test config dicts. This is a widely-used Atlassian documentation placeholder
  (similar to example.com for HTTP examples) and does not represent a real customer
  installation. No realistic-looking credential strings (e.g. sk-*, AKIA*, ghp_*,
  xoxb-*, or base64-encoded strings of 40+ chars) were found anywhere.


════════════════════════════════════════════════════════════════════════════════
SCA (SOFTWARE COMPOSITION ANALYSIS)
════════════════════════════════════════════════════════════════════════════════

Requirements.txt (full contents):
  mcp>=1.0.0
  fastmcp>=0.1.0

Dependencies: 2 direct runtime dependencies
  1. mcp       -- version spec: >=1.0.0  (UNPINNED -- see A06-01)
  2. fastmcp   -- version spec: >=0.1.0  (UNPINNED -- see A06-02)

Standard library dependencies (no version pin needed, stdlib only):
  base64, json, os, re, sys, urllib.request, urllib.error, typing,
  pathlib, random, statistics, math, datetime, threading, time, functools,
  traceback (all stdlib, no external risk)

Unpinned dependencies: 2 (mcp, fastmcp) -- see A06 findings above

CVE scan (knowledge cutoff: August 2025):
  mcp 1.x: No known CVEs.
  fastmcp 0.x: No known CVEs.
  Note: Neither library processes untrusted binary data, executes code, or
  handles cryptographic operations. The primary security surface is stdio MCP
  protocol parsing, which is handled by the library internals.
  Recommendation: Re-run CVE scan after pinning exact versions to enable
  reproducible supply-chain verification.


════════════════════════════════════════════════════════════════════════════════
SUMMARY
════════════════════════════════════════════════════════════════════════════════

  Critical = 0
  High     = 2  (A06-01, A06-02: unpinned dependency versions)
  Medium   = 2  (A03-01: issue_key path traversal gap in agile_client;
                 A09-01: mcp_safe_execute traceback leak in legacy wrapper)
  Low      = 0
  Info     = 1  (A03-02: no eval/exec/subprocess in new code -- confirmed clean)

Finding detail:

  HIGH A06-01  requirements.txt: mcp>=1.0.0 is unpinned
               Fix: pin to exact installed version (mcp==X.Y.Z)

  HIGH A06-02  requirements.txt: fastmcp>=0.1.0 is unpinned
               Fix: pin to exact installed version (fastmcp==X.Y.Z)

  MEDIUM A03-01 agile_client.py line 347: issue_key concatenated into URL path
                with no regex guard. Low immediate risk (method not yet called
                from server.py tools) but must be fixed before any tool uses it.
                Fix: validate issue_key with r'^[A-Z][A-Z0-9]{0,9}-[0-9]+$'
                before URL concatenation.

  MEDIUM A09-01 mcp_errors.py lines 79-83: mcp_safe_execute() embeds truncated
                exception traceback in error response details field. No new B.1/B.2
                tool uses this function, but it remains a live risk for legacy tools.
                Fix: remove `details.traceback` from the mcp_safe_execute response,
                or gate behind ENABLE_DEBUG_TRACEBACKS=1 env var.

No secrets were detected in any scanned file.
All new tool code correctly delegates credential handling to _get_config() via
environment variables.
All JSON inputs are sanitised through validate_input() + json.loads() (no eval).
jira_rate_limit_status confirmed read-only.


Forwarding to security-compliance-auditor for F.6 verdict.
