SQUAD DISPATCH MANIFEST
========================
Generated: 2026-05-28
Status: DISPATCHING

---

PRE-DISPATCH VERIFICATION
--------------------------
Context plan source: docs/outputs/phase-a5-context.md
Blueprint revision: Revision 2 APPROVED
Assembly protocol: B.1 + B.2 write to staging files; B.3 is sole server.py writer

File size anchors confirmed from context plan:
  scrum_calculator.py : 532 lines  (B.1 appends at line 533+)
  agile_client.py     : 137 lines  (B.2 appends at line 138+)
  server.py           : 2203 lines (B.3 appends new tools after line 2198)

Routing conflict check: CLEAR
  No file is assigned as a write target for more than one agent.
  jira_nasscom_mapping stub ownership: RESOLVED to B.2 (agile-tooling-specialist)
    per context plan lines 296-302. B.1 does NOT write a competing nasscom_mapping
    stub. This reduces B.1 stub count from the draft "15" to the confirmed 11.
  jira_plan_sprint upgrade: EXCLUDED from all agents per blueprint Q-03.
    It is NOT a BCa supplement target. Zero agents write to this function.

---

Agent: scrum-master-agent
  Phase: B.1 (parallel with B.2)
  Runs immediately after this manifest is delivered.

  Exclusive Write Targets:
    1. scrum_calculator.py
         Operation: APPEND ONLY below line 532
         Content: 16 new pure functions (stdlib-only, ASCII-only, Python 3.8+)
         Constraint: Zero changes to existing 8 functions or
                     INDIA_NATIONAL_HOLIDAYS_2025_2026 constant.

    2. docs/outputs/b1-server-additions.py  [CREATE NEW]
         Operation: CREATE staging file with 11 tool stubs
         Content: Standalone async defs with @mcp.tool() + @mcp_tool_handler
                  decorators. No FastMCP(...) instantiation. B.3 merges these
                  into server.py at assembly time.

  Read-Only References (do not modify):
    - server.py lines 1-56    (import block pattern, confirm module-level imports)
    - server.py lines 800-855 (jira_get_boards -- one complete tool example pattern)
    - input_validator.py      (full, 94 lines -- validate_input() call signature)
    - base/response.py        (full, 258 lines -- success() and error() signatures)

  Functions to Implement in scrum_calculator.py (16 total):
    1.  bootstrap_bca_ci(data, stat_func, B=2000, alpha=0.05)
    2.  ahp_score(criteria_matrix)
    3.  tuckman_markov(velocity_history, team_age_sprints)
    4.  spotify_health_check(dimension_scores)
    5.  edmondson_ps_scale(item_scores)
    6.  scrum_of_scrums_overhead(n_teams, p_productivity, c_coordination_cost)
    7.  cognitive_load_index(complexity_list, responsibility_list, cl_max)
    8.  attrition_ramp(months_elapsed, p_max, experienced)
    9.  ist_capacity_correction(nominal_hours, overlap_hours=4.5)
    10. little_law_analysis(avg_wip, avg_cycle_time_days, avg_throughput_per_day)
    11. cycle_time_lognormal_mle(cycle_times_days)
    12. poisson_throughput(completed, period_days)
    13. pert_estimate(optimistic, most_likely, pessimistic)
    14. tco_npv_comparison(jira_premium_inr_annual, azure_inr_annual,
                           years=3, discount_rate=0.10)
    15. burndown_metrics(total_points, completed_points_by_day,
                         sprint_days, days_elapsed)
    16. multi_sprint_holiday_forecast(sprint_start_dates, sprint_end_dates)

  Tool Stubs to Deliver in docs/outputs/b1-server-additions.py (11 total):
    Block E -- Team Health Extended (4 stubs):
      jira_spotify_health_check
      jira_psychological_safety
      jira_cognitive_load
      jira_attrition_forecast
    Block F -- DevOps Tooling pure-computation subset (3 stubs):
      jira_pert_estimate
      jira_tco_analysis
      jira_rate_limit_status
        (requires additive import from rate_limiter; B.3 adds it at assembly)
    Block G -- India Layer (4 stubs):
      jira_scrum_of_scrums
      jira_multi_sprint_holidays
      jira_ist_capacity
      jira_nasscom_mapping: EXCLUDED from B.1 -- owned by B.2 per blueprint
                            conflict resolution (context plan lines 296-302).

  Upgrade Functions (4 -- surgically modify existing tools in server.py):
    NOTE: B.1 does NOT directly modify server.py. B.1 delivers upgrade logic
    as inline comments or supplementary helper calls within b1-server-additions.py.
    B.3 applies all upgrades to server.py at assembly time using blueprint
    Section 2.2 upgrade points U1-U4.
    Upgrades scoped:
      U1: jira_refine_backlog  -- wsjf helper supplement
      U2: jira_sprint_review   -- AHP helper supplement
      U3: jira_team_health     -- tuckman_markov substitution
      U4: jira_get_velocity    -- BCa CI supplement
    jira_plan_sprint: NOT a BCa target. Zero changes (blueprint Q-03).

  Task Count: 16 functions in scrum_calculator.py + 11 stubs in b1-server-additions.py
  Estimated Token Usage: 40,000
  Dependency: none (runs immediately after this manifest)

---

Agent: agile-tooling-specialist
  Phase: B.2 (parallel with B.1)
  Runs immediately after this manifest is delivered.

  Exclusive Write Targets:
    1. agile_client.py
         Operation: APPEND ONLY below line 137
         Content: 3 new functions following _agile_request() convention
         Constraint: Zero changes to _agile_url, _build_agile_auth_header,
                     _agile_request. Zero new imports (urllib.request, json,
                     base64 already imported at lines 27-31).

    2. docs/outputs/b2-server-additions.py  [CREATE NEW]
         Operation: CREATE staging file with 6 tool stubs
         Content: Standalone async defs for all 6 network-dependent tools.

  Read-Only References (do not modify):
    - agile_client.py        (full -- primary file, append target)
    - server.py lines 1-56   (import block pattern)
    - server.py lines 800-855 (jira_get_boards -- tool pattern reference)
    - input_validator.py     (full, 94 lines -- validate_input() call signature)
    - base/response.py       (full, 258 lines -- success() and error() signatures)

  Functions to Implement in agile_client.py (3 total):
    1. get_burndown_chart(cfg, board_id, sprint_id)
         Calls: _agile_request(cfg, "GET",
                "rapid/charts/burndown?rapidViewId={}&sprintId={}")
    2. get_cfd(cfg, board_id)
         Calls: _agile_request(cfg, "GET",
                "rapid/charts/cumulativeFlowDiagram?rapidViewId={}")
    3. get_issue_changelog(cfg, issue_key)
         URL: /rest/api/{api_version}/issue/{issue_key}?expand=changelog&...
         HTTP: urllib.request directly (ADR-4: changelog is core REST not Agile API)
         Auth: _build_agile_auth_header(cfg) reused
         NOTE: issue_key must NOT be interpolated without sanitization (STRIDE)

  Tool Stubs to Deliver in docs/outputs/b2-server-additions.py (6 total):
    Block D -- Agile Metrics (5 stubs):
      jira_burndown_chart(board_id, sprint_id)
        -> agile_client.get_burndown_chart + scrum_calculator.burndown_metrics
        RISK R-01: try/except RuntimeError; return degraded response with
                   "endpoint_available": False on failure.
      jira_cfd_analysis(board_id)
        -> agile_client.get_cfd + scrum_calculator.little_law_analysis
        RISK R-01: same RuntimeError fallback pattern.
      jira_cycle_time_analysis(board_id, sprint_id, max_issues=30)
        -> agile_client.get_issue_changelog per issue, cap 30
        -> scrum_calculator.cycle_time_lognormal_mle
        RISK R-02: cap at 30 issues; include "issues_analyzed"/"issues_skipped"
                   keys; short-circuit if total elapsed > 20 seconds.
      jira_throughput_forecast(board_id, period_days=14)
        -> existing _agile_request board/{id}/sprint?state=closed
        -> scrum_calculator.poisson_throughput
      jira_automation_analyzer(rules_dag, lambda_rate, mu_rate)
        -> NO network call; pure local computation
        -> M/M/1 queue model + Kahn's DAG cycle detection O(V+E)
        -> rules_dag is JSON-encoded adjacency list str (parse with json.loads)
    Block D (India Layer boundary tool -- 1 stub):
      jira_nasscom_mapping(board_id, num_sprints=6)
        -> existing _agile_request velocity endpoint
        -> scrum_calculator velocity_stats for NASSCOM level scoring
        NOTE: B.2 owns this stub per conflict resolution. B.1 does NOT deliver
              a competing stub. Ownership assigned because stub uses
              _agile_request for network calls (B.2 domain).

  Task Count: 3 functions in agile_client.py + 6 stubs in b2-server-additions.py
  Estimated Token Usage: 40,000
  Dependency: none (runs immediately after this manifest, parallel with B.1)

---

Agent: python-backend-engineer
  Phase: B.3 (sequential -- after B.1 AND B.2 complete)
  Blocked until: docs/outputs/b1-server-additions.py AND
                 docs/outputs/b2-server-additions.py both exist and pass
                 py_compile validation.

  Exclusive Write Targets:
    1. server.py  [SOLE WRITER]
         Operations (in order):
           Step 1:  Syntax-check b1-server-additions.py
                    (python -m py_compile docs/outputs/b1-server-additions.py)
           Step 2:  Syntax-check b2-server-additions.py
                    (python -m py_compile docs/outputs/b2-server-additions.py)
           Step 3:  Apply upgrade U3 -- tuckman_markov substitution
                    (exact line documented in blueprint Section 2.2 U3)
           Step 4:  Apply upgrade U4 -- BCa supplement in jira_get_velocity
                    (exact line documented in blueprint Section 2.2 U4)
           Step 5:  Apply upgrade U1 -- wsjf helper for jira_refine_backlog
           Step 6:  Apply upgrade U2 -- AHP helper for jira_sprint_review
           Step 7:  Add import lines to server.py import block:
                      from rate_limiter import _buckets, _buckets_lock,
                                              _BUCKET_DEFAULTS, _RETRY_AFTER_SECONDS
                      from input_validator import validate_input
                      (only if not already present)
           Step 8:  Append "# --- Block D: Agile Metrics (6 tools) ---"
                    + 6 stubs from b2-server-additions.py
           Step 9:  Append "# --- Block E: Team Health Extended (4 tools) ---"
                    + 4 stubs from b1-server-additions.py
           Step 10: Append "# --- Block F: DevOps Tooling (3 tools) ---"
                    + 3 stubs from b1-server-additions.py
           Step 11: Append "# --- Block G: India Layer (4 tools) ---"
                    + 4 stubs from b1-server-additions.py
                    NOTE: Block G is 4 stubs (3 from B.1 + jira_nasscom_mapping
                    from B.2), not 3. Header label must match actual count.
           Step 12: Update module-level docstring:
                    "Tools (25):" -> "Tools (41):"
           Step 13: Run all validation gates (see below)
           Step 14: Verify backward compat: zero deletions in server.py
                    lines 1-799 (core tools) and lines 800-2198 (excluding
                    the 4 targeted upgrade substitutions U1-U4)

  Read-Only References (do not modify):
    - docs/outputs/b1-server-additions.py  (B.1 artifact -- read and integrate)
    - docs/outputs/b2-server-additions.py  (B.2 artifact -- read and integrate)
    - scrum_calculator.py                  (full, post-B.1 -- verify append, ASCII gate)
    - agile_client.py                      (full, post-B.2 -- verify append, ASCII gate)
    - rate_limiter.py                      (full -- verify _buckets, _buckets_lock,
                                            _BUCKET_DEFAULTS, _RETRY_AFTER_SECONDS symbols)
    - base/decorators.py                   (full -- confirm @mcp_tool_handler behavior)
    - input_validator.py                   (full -- confirm validate_input import is additive)

  Validation Gates (Step 13):
    python -m py_compile server.py scrum_calculator.py agile_client.py
    grep -n ":=" server.py scrum_calculator.py agile_client.py       (expect 0 hits)
    grep -n "match " server.py scrum_calculator.py agile_client.py   (expect 0 hits)
    python -c "open('scrum_calculator.py','rb').read().decode('ascii')"
    python -c "open('agile_client.py','rb').read().decode('ascii')"
    python -c "open('server.py','rb').read().decode('ascii')"
    pytest tests/ -v

  Task Count: 16 new stubs appended + 4 upgrade substitutions + 2 import lines
              + 1 docstring update = 23 surgical changes to server.py
  Estimated Token Usage: 60,000
  Dependency: B.1 complete AND B.2 complete (hard sequential gate)

---

OVERLAP VERIFICATION
---------------------

  File                              B.1 Write   B.2 Write   B.3 Write
  --------------------------------  ----------  ----------  ----------
  scrum_calculator.py               YES         NO          NO (read-only)
  agile_client.py                   NO          YES         NO (read-only)
  server.py                         NO          NO          YES (sole writer)
  docs/outputs/b1-server-additions  YES         NO          NO (read-only)
  docs/outputs/b2-server-additions  NO          YES         NO (read-only)

  Verdict: CLEAR -- no file is written by more than one agent.

  Additional conflict checks:
    jira_nasscom_mapping stub: owned exclusively by B.2 (b2-server-additions.py).
      B.1 stub list contains 11 entries, not 12. Confirmed no duplication.
    jira_plan_sprint: no agent writes any change to this tool. Confirmed excluded.
    Upgrades U1-U4: authored and applied exclusively by B.3 in server.py.
      B.1/B.2 provide the new calculator functions that U1-U4 will call, but
      neither B.1 nor B.2 modifies server.py lines where upgrades are applied.

---

DISPATCH SEQUENCE
------------------

  NOW (parallel):
    --> scrum-master-agent      [B.1]
    --> agile-tooling-specialist [B.2]

  AFTER B.1 AND B.2 COMPLETE:
    --> python-backend-engineer  [B.3]

  AFTER B.3 COMPLETE (parallel):
    --> unit-testing-specialist       [C.1]
    --> integration-testing-engineer  [C.2]
    --> hallucination-detector        [C.3]
    --> context-faithfulness-engineer [C.4]

  AFTER C.3 AND C.4 COMPLETE:
    --> reliability-auditor [D]

  AFTER D -- GO VERDICT (parallel):
    --> security-defense-architect [F.1]
    --> security-testing-engineer  [F.2]

  AFTER F.1 AND F.2 COMPLETE:
    --> security-compliance-auditor [F.3]

  AFTER F.3 -- PASS VERDICT:
    --> devops-engineer [G]

---

STATUS: DISPATCHED
