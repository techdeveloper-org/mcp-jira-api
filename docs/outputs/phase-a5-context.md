CONTEXT DELIVERY PLAN
=======================
Generated: 2026-05-28
Blueprint: Revision 2 APPROVED
Assembly Protocol: B.1 + B.2 write to staging files; B.3 is sole server.py writer

---

## PRE-FLIGHT: KEY FILE SIZES (verified from live codebase)

  scrum_calculator.py : 532 lines (append at line 533+)
  agile_client.py     : 137 lines (append at line 138+)
  server.py           : 2203 lines (new tools start after line 2198)
  requirements.txt    : 2 lines (mcp>=1.0.0, fastmcp>=0.1.0)
  tests/fixtures/     : 5 JSON files (boards, sprints, sprint_issues, velocity, sprint_detail)

---

## Agent: scrum-master-agent (Phase B.1)

  Token Budget: 40,000 tokens
  Runs: PARALLEL with agile-tooling-specialist (B.2)

  Primary Files (full content):
    1. scrum_calculator.py (532 lines) -- FULL FILE
       Reason: Must read ALL 8 existing functions to understand
               append style, docstring format, existing constants
               (INDIA_NATIONAL_HOLIDAYS_2025_2026 at line 42),
               and the last line (533) to know exact append point.
               All 16 new functions must NOT duplicate existing names.
               Existing functions: velocity_stats, monte_carlo_forecast,
               sprint_capacity, wsjf_score, mttr_analysis,
               retrospective_effectiveness, tuckman_estimate,
               india_holidays_in_sprint.

  Reference Files (pattern matching only -- do not modify):
    2. server.py lines 1-56 (header + imports block)
       Reason: Need to see existing import pattern to confirm
               scrum_calculator is imported as `import scrum_calculator`
               (module-level, NOT from-import).
    3. server.py lines 800-855 (jira_get_boards -- one complete tool example)
       Reason: Pattern for @mcp.tool() + @mcp_tool_handler + _get_config()
               + _agile_request() + return dict structure.
    4. input_validator.py (full, 94 lines)
       Reason: ADR-7 mandates validate_input() on all string params.
               Must know the exact call signature: validate_input(value,
               max_length=4096, field_name="input").
    5. base/response.py (full, 258 lines)
       Reason: Tool stubs in b1-server-additions.py must use success()
               and error() from base.response. Need exact signatures.

  Staging Output File (B.1 WRITES THIS):
    6. docs/outputs/b1-server-additions.py (CREATE NEW)
       This file receives the 11 server.py tool stubs from B.1.
       File must NOT be imported or executed -- delivery artifact only.

  Append Target (B.1 WRITES THIS):
    7. scrum_calculator.py (APPEND ONLY below line 532)
       16 new pure functions -- see function signatures below.

  Key Constraint Reminders:
    - ASCII-ONLY in all .py files (cp1252 safe). No Greek letters,
      no Unicode math, no INR rupee sign. Use mu_hat, sigma_sq,
      lambda_hat, alpha_val, rho_val, tau_val, n_optimal, n_star.
    - STDLIB-ONLY in scrum_calculator.py. Imports already present:
      math, random, statistics, datetime.date, typing.
      Do NOT add any new imports to scrum_calculator.py.
    - Python 3.8+ only. No walrus (:=), no match/case, no dict|union,
      no X|Y type hints (use Union[X, Y] from typing).
    - APPEND-ONLY: zero changes to any of the existing 8 functions.
      Zero changes to INDIA_NATIONAL_HOLIDAYS_2025_2026 constant.
    - All new functions raise ValueError (not AssertionError) for
      invalid inputs. Return Dict[str, Any] (not JSON string).
    - All docstrings must follow Google style (Args/Returns/Raises).

  Function Signatures to Implement (in scrum_calculator.py):

    bootstrap_bca_ci(data, stat_func, B=2000, alpha=0.05)
      -> Dict[str, Any]  # ci_low, ci_high, point_estimate, B_used
      NOTE: blueprint signature uses stat_func parameter.
            Non-deterministic by design (random.seed(None)).
            Test with property assertions only (ci_low <= estimate <= ci_high).

    ahp_score(criteria_matrix)
      -> Dict[str, Any]  # weights, consistency_ratio, is_consistent

    tuckman_markov(velocity_history, team_age_sprints)
      -> str  # "Forming" | "Storming" | "Norming" | "Performing"
      GUARD: if len(velocity_history) < 4: fall back to tuckman_estimate().
             Return additional "model_used" key: "markov" or "heuristic_fallback".
             NOTE: blueprint contract says return str but also needs model_used key.
             Resolve: return Dict[str, Any] with keys: stage (str), model_used (str).
             server.py upgrade reads stage key.

    spotify_health_check(dimension_scores)
      -> Dict[str, Any]  # ths_score, wilcoxon_z, zone, dimension_breakdown
      dimension_scores is Dict[str, List[float]] -- 11 Spotify dimensions.
      Default equal weights (1/11 per dimension), weights as optional param.

    edmondson_ps_scale(item_scores)
      -> Dict[str, Any]  # ps_score, cronbach_alpha, safety_zone
      7-item Likert scale. Reverse-code items at indices 0, 2, 4 (1-based: 1, 3, 5).
      Simplified standardized-item Cronbach alpha formula.

    scrum_of_scrums_overhead(n_teams, p_productivity, c_coordination_cost)
      -> Dict[str, Any]  # net_throughput, n_optimal, overhead_pct, viable_regime
      GUARD: if c_coordination_cost <= 0: raise ValueError.
             Cap n_optimal at max(1, n_teams).
             viable_regime = True if net_throughput > 0.

    cognitive_load_index(complexity_list, responsibility_list, cl_max)
      -> Dict[str, Any]  # cl_team, cli, load_zone
      load_zone: "overloaded" (CLI > 1.0), "high" (> 0.75), "moderate" (> 0.5), "low".

    attrition_ramp(months_elapsed, p_max, experienced)
      -> Dict[str, Any]  # p_attrition, tau, risk_zone
      tau = 6 if experienced else 12.
      P(t) = p_max * (1 - exp(-t/tau)).

    ist_capacity_correction(nominal_hours, overlap_hours=4.5)
      -> Dict[str, Any]  # effective_hours, correction_factor, overlap_note

    little_law_analysis(avg_wip, avg_cycle_time_days, avg_throughput_per_day)
      -> Dict[str, Any]  # l_computed, lambda_computed, w_computed,
                         #   consistency_check, deviation_pct

    cycle_time_lognormal_mle(cycle_times_days)
      -> Dict[str, Any]  # mu_hat, sigma_sq_hat, p50_days, p85_days, p95_days

    poisson_throughput(completed, period_days)
      -> Dict[str, Any]  # lambda_hat, ci_low_95, ci_high_95, period_days

    pert_estimate(optimistic, most_likely, pessimistic)
      -> Dict[str, Any]  # pert_mean, pert_sigma, ci_low_90, ci_high_90

    tco_npv_comparison(jira_premium_inr_annual, azure_inr_annual,
                       years=3, discount_rate=0.10)
      -> Dict[str, Any]  # jira_npv_inr, azure_npv_inr, delta_inr,
                         #   recommended_platform, payback_years

    burndown_metrics(total_points, completed_points_by_day,
                     sprint_days, days_elapsed)
      -> Dict[str, Any]  # ideal_remaining, actual_remaining,
                         #   deviation_pct, projected_completion_day, health_signal

    multi_sprint_holiday_forecast(sprint_start_dates, sprint_end_dates)
      -> Dict[str, Any]  # holiday_counts_per_sprint, total_holidays,
                         #   high_impact_sprints
      GUARD: max 26 sprints (raise ValueError if exceeded).
             Uses INDIA_NATIONAL_HOLIDAYS_2025_2026 constant (already in module).

  Tool Stubs to Deliver (in docs/outputs/b1-server-additions.py):
    11 tools for pure-computation Block E + F + G:
      Block E (Team Health Extended):
        jira_spotify_health_check
        jira_psychological_safety
        jira_cognitive_load
        jira_attrition_forecast
      Block F (DevOps Tooling -- pure computation subset):
        jira_pert_estimate
        jira_tco_analysis
        jira_rate_limit_status
          NOTE: Requires import:
            from rate_limiter import _buckets, _buckets_lock,
                                    _BUCKET_DEFAULTS, _RETRY_AFTER_SECONDS
          This import is additive to server.py; B.3 adds it at assembly time.
      Block G (India Layer):
        jira_scrum_of_scrums (Block D, pure computation)
        jira_multi_sprint_holidays
        jira_ist_capacity
        jira_nasscom_mapping
          NOTE: jira_nasscom_mapping uses existing _agile_request for velocity
                but delegates NASSCOM dimension scoring to scrum_calculator.
                It straddles B.1/B.2 boundary. B.1 owns the stub because the
                India Layer grouping is B.1's responsibility. B.3 will wire the
                agile_client call from jira_nasscom_mapping at assembly time if
                agile-tooling-specialist (B.2) raises a conflict; otherwise B.1
                writes the full stub using existing _agile_request call pattern.

    Each stub file format:
      - Standalone async def with @mcp.tool() + @mcp_tool_handler decorators.
      - No mcp = FastMCP(...) definition -- decorators reference the name `mcp`
        which B.3 will merge into server.py where `mcp` is already defined.
      - All string inputs call validate_input() as first operation after _get_config().
      - All computations delegate to scrum_calculator.<function>().
      - Return dict with snake_case keys.

---

## Agent: agile-tooling-specialist (Phase B.2)

  Token Budget: 40,000 tokens
  Runs: PARALLEL with scrum-master-agent (B.1)

  Primary Files (full content):
    1. agile_client.py (137 lines) -- FULL FILE
       Reason: Must read ALL existing functions:
               _agile_url(), _build_agile_auth_header(), _agile_request().
               The new 3 functions follow _agile_request() exactly.
               Append point is line 138+.

  Reference Files (pattern matching only -- do not modify):
    2. server.py lines 1-56 (header + imports block)
       Reason: Confirms import pattern:
               `from agile_client import _agile_request, _agile_url,
               _build_agile_auth_header`
               New agile_client functions will also be imported by B.3.
    3. server.py lines 800-855 (jira_get_boards -- one complete tool example)
       Reason: Pattern for tool stubs in b2-server-additions.py.
               Must match decorator order, docstring format, _get_config() call.
    4. input_validator.py (full, 94 lines)
       Reason: ADR-7 mandates validate_input() on all string params in tool stubs.
    5. base/response.py (full, 258 lines)
       Reason: Tool stubs must use success() and error() from base.response.

  Staging Output File (B.2 WRITES THIS):
    6. docs/outputs/b2-server-additions.py (CREATE NEW)
       6 server.py tool stubs for network-dependent tools.

  Append Target (B.2 WRITES THIS):
    7. agile_client.py (APPEND ONLY below line 137)
       3 new functions following _agile_request() convention.

  Key Constraint Reminders:
    - ASCII-ONLY in all .py files (cp1252 safe).
    - agile_client.py adds 3 functions, ZERO new imports
      (urllib.request, json, base64 already imported at line 27-31).
    - Python 3.8+ only. No walrus, no match/case.
    - APPEND-ONLY: zero changes to _agile_url, _build_agile_auth_header,
      _agile_request.
    - Functions follow (cfg, ...) first-argument convention.
    - get_issue_changelog uses urllib.request DIRECTLY (not _agile_request)
      because changelog is /rest/api/{version}/ not /rest/agile/1.0/.
      See blueprint ADR-4 for the exact URL construction pattern.
    - Raise RuntimeError on HTTP errors (same format as _agile_request()).
    - Return Any (parsed JSON dict/list or None for 204).
    - All docstrings: Google style.

  Function Signatures to Implement (in agile_client.py):

    get_burndown_chart(cfg, board_id, sprint_id)
      # type: (Dict[str, str], int, int) -> Any
      # Calls: _agile_request(cfg, "GET",
      #   "rapid/charts/burndown?rapidViewId={}&sprintId={}".format(board_id, sprint_id))

    get_cfd(cfg, board_id)
      # type: (Dict[str, str], int) -> Any
      # Calls: _agile_request(cfg, "GET",
      #   "rapid/charts/cumulativeFlowDiagram?rapidViewId={}".format(board_id))

    get_issue_changelog(cfg, issue_key)
      # type: (Dict[str, str], str) -> Any
      # URL: cfg["url"] + "/rest/api/" + cfg["api_version"]
      #      + "/issue/" + issue_key
      #      + "?expand=changelog&fields=changelog,summary,created"
      # Auth: _build_agile_auth_header(cfg) -- reuse existing function.
      # HTTP: urllib.request.Request + urlopen (mirrors _agile_request pattern).
      # IMPORTANT: No circular import. agile_client.py must NOT import server.py.

  Tool Stubs to Deliver (in docs/outputs/b2-server-additions.py):
    6 network-dependent tools for Block D:
      jira_burndown_chart(board_id, sprint_id)
        -> agile_client.get_burndown_chart(cfg, board_id, sprint_id)
        -> scrum_calculator.burndown_metrics(total_points, points_by_day,
                                             sprint_days, elapsed)
        RISK R-01: Wrap in try/except RuntimeError. Return degraded response
                   with "endpoint_available": False if RuntimeError raised.

      jira_cfd_analysis(board_id)
        -> agile_client.get_cfd(cfg, board_id)
        -> scrum_calculator.little_law_analysis(avg_wip, avg_ct, avg_throughput)
        RISK R-01: Same RuntimeError fallback pattern as jira_burndown_chart.

      jira_cycle_time_analysis(board_id, sprint_id, max_issues=30)
        -> agile_client.get_issue_changelog(cfg, issue_key) per issue, cap 30
        -> scrum_calculator.cycle_time_lognormal_mle(cycle_times_days)
        RISK R-02: Cap at 30 issues. Add "issues_analyzed" and "issues_skipped"
                   keys to response. Short-circuit if total elapsed > 20 seconds.

      jira_throughput_forecast(board_id, period_days=14)
        -> Existing _agile_request(cfg, "GET",
               "board/{}/sprint?state=closed".format(board_id))
        -> scrum_calculator.poisson_throughput(completed, period_days)

      jira_automation_analyzer(rules_dag, lambda_rate, mu_rate)
        -> NO network call. Purely local computation.
        -> M/M/1: rho = lambda_rate / mu_rate; E[L] = rho/(1-rho);
                  E[W] = 1/(mu_rate - lambda_rate).
                  stability_warning if rho >= 1.0.
        -> Kahn's DAG cycle detection O(V+E) inline (~20 lines).
           rules_dag is JSON-encoded adjacency list str.
           Parse with json.loads(). Return is_dag, cycle_detected,
           topological_order.

      jira_nasscom_mapping(board_id, num_sprints=6)
        NOTE: B.2 owns this stub because it uses existing _agile_request
              for velocity data (same as jira_get_velocity pattern).
              Uses existing velocity_stats() for NASSCOM level.
              Adds multi-dimensional NASSCOM scoring output.
              The 5 NASSCOM AgileX dimensions come from _nasscom_agile_x_level
              logic already in scrum_calculator.py.
              B.1 scrum-master-agent does NOT write a competing nasscom_mapping stub.

---

## Agent: python-backend-engineer (Phase B.3)

  Token Budget: 60,000 tokens
  Runs: AFTER B.1 and B.2 complete (sequential dependency)

  Primary Files (full content -- all required for sole-writer assembly):
    1. server.py (2203 lines) -- FULL FILE
       Reason: Sole writer. Must read entire file to:
               (a) Verify upgrade points U1-U4 exact line numbers,
               (b) Add import line for rate_limiter and input_validator,
               (c) Append all 16 stubs in single pass after line 2198,
               (d) Update module-level docstring tool count 25->41.
    2. scrum_calculator.py -- FULL FILE (post-B.1 version)
       Reason: Verify B.1 appended correctly. Run ASCII gate.
               Run py_compile gate.
    3. agile_client.py -- FULL FILE (post-B.2 version)
       Reason: Verify B.2 appended correctly. Run ASCII gate.
               Run py_compile gate.
    4. docs/outputs/b1-server-additions.py (B.1 artifact)
       Reason: Read and integrate 11 tool stubs into server.py.
    5. docs/outputs/b2-server-additions.py (B.2 artifact)
       Reason: Read and integrate 6 tool stubs into server.py.
    6. rate_limiter.py (full)
       Reason: Verify _buckets, _buckets_lock, _BUCKET_DEFAULTS,
               _RETRY_AFTER_SECONDS symbols exist before adding import.

  Reference Files (read for context only):
    7. base/decorators.py (full)
       Reason: Confirm @mcp_tool_handler decorator behaviour so
               integration of stubs is syntactically correct.
    8. input_validator.py (full)
       Reason: Confirm validate_input import is additive (not already present
               in server.py at line 50-52 import block).

  Assembly Steps (B.3 executes in order):
    Step 1: Read b1-server-additions.py -- validate no syntax errors with
            python -m py_compile docs/outputs/b1-server-additions.py
    Step 2: Read b2-server-additions.py -- same syntax check.
    Step 3: Apply upgrade U3 to server.py (tuckman_markov substitution at line 2051).
            EXACT change documented in blueprint Section 2.2 Upgrade point U3.
    Step 4: Apply upgrade U4 to server.py (BCa supplement in jira_get_velocity).
            EXACT change documented in blueprint Section 2.2 Upgrade point U4.
    Step 5: Apply upgrade U1 to server.py (wsjf helper for jira_refine_backlog).
    Step 6: Apply upgrade U2 to server.py (AHP helper for jira_sprint_review).
    Step 7: Add import lines to server.py import block (lines 50-52 region):
            - from rate_limiter import _buckets, _buckets_lock,
                                      _BUCKET_DEFAULTS, _RETRY_AFTER_SECONDS
            - from input_validator import validate_input
              (only if not already present)
    Step 8: Append comment block "# --- Block D: Agile Metrics (6 tools) ---"
            followed by 6 stubs from b2-server-additions.py.
    Step 9: Append comment block "# --- Block E: Team Health Extended (4 tools) ---"
            followed by 4 stubs from b1-server-additions.py.
    Step 10: Append comment block "# --- Block F: DevOps Tooling (3 tools) ---"
             followed by 3 stubs from b1-server-additions.py.
    Step 11: Append comment block "# --- Block G: India Layer (3 tools) ---"
             followed by 3 stubs from b1-server-additions.py.
    Step 12: Update server.py module-level docstring: "Tools (25):" -> "Tools (41):".
    Step 13: Run validation gates:
             python -m py_compile server.py scrum_calculator.py agile_client.py
             grep -n ":=" server.py scrum_calculator.py agile_client.py  (expect 0)
             grep -n "match " server.py scrum_calculator.py agile_client.py  (expect 0)
             python -c "open('scrum_calculator.py','rb').read().decode('ascii')"
             python -c "open('agile_client.py','rb').read().decode('ascii')"
             python -c "open('server.py','rb').read().decode('ascii')"
             pytest tests/ -v
    Step 14: Verify backward compat: diff of server.py must show zero
             deletions in lines 1-799 (core tools) and lines 800-1065
             (board/sprint infrastructure tools).

  Key Constraint Reminders:
    - B.3 is the SOLE writer to server.py. Do not modify server.py
      before B.1 and B.2 have both delivered their staging files.
    - Verify 16 new @mcp_tool_handler decorators are present post-assembly.
    - Zero signature changes to any of the existing 25 tools.
    - requirements.txt must remain unchanged (2 lines only).

---

## Agent: unit-testing-specialist (Phase C.1)

  Token Budget: 35,000 tokens
  Runs: AFTER B.3 completes (tests target post-assembly code)

  Primary Files (full content):
    1. scrum_calculator.py -- FULL FILE (post-B.3 version, 533+ lines)
       Reason: Must see ALL 24 functions (8 existing + 16 new) to write
               complete unit tests. Tests are pure (no mocks for scrum_calculator).
    2. tests/test_scrum_calculator.py -- FULL FILE
       Reason: Existing test pattern reference. Must extend this file
               (not create a new one). Pattern uses class-based TestXxx
               groups, descriptive method names, property-based assertions
               for non-deterministic functions.

  Reference Files (pattern matching only):
    3. tests/fixtures/ directory listing (5 files)
       Needed filenames:
         boards_response.json
         sprints_response.json
         sprint_issues_response.json
         velocity_response.json
         sprint_detail_response.json
       Reason: Understand available fixture data for integration tests.
               Unit tests for scrum_calculator need no fixtures (pure).
    4. agile_client.py -- lines 1-35 (header + imports only)
       Reason: Understand the cfg dict shape passed to tools so unit
               test mocks can construct valid cfg dicts.

  Key Constraint Reminders:
    - Tests for bootstrap_bca_ci() and tuckman_markov() (when model_used=markov)
      MUST use property-based assertions ONLY. Never assert exact float values.
      Valid assertions: ci_low <= point_estimate <= ci_high; ci_high > ci_low.
    - Tests for tuckman_markov() with len(velocity_history) < 4 must verify
      model_used == "heuristic_fallback".
    - Tests for multi_sprint_holiday_forecast() must assert max 26 sprints
      guard raises ValueError.
    - Tests for scrum_of_scrums_overhead() must assert c_coordination_cost <= 0
      raises ValueError.
    - All new test classes follow existing naming: TestBootstrapBcaCi,
      TestAhpScore, TestTuckmanMarkov, etc.
    - ASCII-only in test files (cp1252 safe).
    - Python 3.8+ only.
    - Do NOT modify existing test classes or existing test methods.
      Append new test classes below the last existing test in the file.
    - Target: 90%+ line coverage for new functions (property-based
      assertions count for non-deterministic functions).

  Coverage Targets per New Function:
    Required test scenarios per function (at minimum):
      happy path (valid inputs) -> returns dict with expected keys
      empty/None input -> raises ValueError or returns error dict
      boundary value -> specific to each function
      non-deterministic functions (BCa, Markov) -> property assertions only

---

## Agent: integration-testing-engineer (Phase C.2)

  Token Budget: 35,000 tokens
  Runs: PARALLEL with unit-testing-specialist (Phase C.1)

  Primary Files (full content):
    1. server.py -- FULL FILE (post-B.3 version)
       Reason: Must understand all 41 tool signatures to write
               integration test stubs that call each new tool end-to-end.
    2. tests/test_tools_integration.py -- READ IF EXISTS (may not exist yet)
       Reason: Pattern reference for mock-based integration tests.
               If file does not exist, use test_agile_client.py as pattern.
    3. tests/test_agile_client.py -- FULL FILE
       Reason: Existing mock pattern for agile_client tests.
               Integration tests mock agile_client at the server.py boundary.

  Reference Files (pattern matching only):
    4. tests/fixtures/boards_response.json -- full content
    5. tests/fixtures/sprints_response.json -- full content
    6. tests/fixtures/sprint_issues_response.json -- full content
    7. tests/fixtures/velocity_response.json -- full content
    8. tests/fixtures/sprint_detail_response.json -- full content
       Reason: Use fixture data to construct mock responses for
               agile_client function mocks in integration tests.
    9. base/response.py -- lines 213-257 (success() and error() functions)
       Reason: Verify response shape expected from tool handlers.
    10. agile_client.py -- FULL FILE (post-B.2 version)
        Reason: Know function signatures of new get_burndown_chart,
                get_cfd, get_issue_changelog to write correct mocks.

  Key Constraint Reminders:
    - Integration tests mock agile_client functions using unittest.mock.patch.
    - Tests must NOT make real HTTP calls to Jira.
    - Tests must NOT require JIRA_URL, JIRA_USER, JIRA_API_TOKEN env vars to be set.
      Mock _get_config() to return a test config dict.
    - New integration tests validate:
        (a) Tool receives correct args and calls correct agile_client function.
        (b) agile_client response is correctly passed to scrum_calculator function.
        (c) Return dict contains expected top-level keys.
    - Write integration tests for all 16 new tools (not just the 6 network tools).
      Pure-computation tools (Blocks E, F, G) need integration tests that
      call the tool directly without mocking agile_client.
    - ASCII-only in test files.
    - Python 3.8+ only.

---

## Agent: hallucination-detector (Phase C.3)

  Token Budget: 30,000 tokens
  Runs: PARALLEL with unit-testing-specialist and integration-testing-engineer

  Primary Files (full content):
    1. scrum_calculator.py -- lines 533 to EOF (NEW FUNCTIONS ONLY)
       Reason: Only the 16 new functions are subject to hallucination review.
               Existing 8 functions are pre-verified and not in scope.
               Reading from line 533 gives the exact append section.

  Specification Source (math verification reference):
    2. docs/orchestration_prompt.md -- lines 1-107 (Category 3 section only)
       Reason: The exact math specifications for all 16 functions are in
               Category 3 (lines 44-63) and Category 1 tool-to-function
               mapping (lines 15-32). Contains formal math: BCa formula,
               Tuckman Markov chain 4-state matrix, AHP power iteration,
               Wilcoxon Z, Edmondson Cronbach alpha, Brooks' T(n) formula,
               Little's Law L=lambda*W, log-normal MLE mu_hat/sigma_sq,
               Poisson lambda_hat CI, PERT 3-point formula, M/M/1 rho,
               TCO NPV, IST capacity correction.

  Phase Output File (WRITE):
    3. docs/outputs/phase-c-hallucination.md (CREATE)
       Format: Per-function table: function_name | spec_clause | code_line |
               implemented_correctly (Yes/No) | deviation (if No) | severity

  Key Constraint Reminders:
    - Check mathematical correctness only. Do not check Python syntax
      (that is B.3's job). Do not check docstrings (that is faithfulness-engineer).
    - Flag any incorrect formula implementation as HIGH severity.
    - Flag missing guard clauses (e.g., division by zero when mean=0) as MEDIUM.
    - Flag non-ASCII characters in .py source as CRITICAL (cp1252 violation).
    - Report format is structured table, not prose.
    - If a function cannot be verified against spec (spec is ambiguous), flag as
      UNVERIFIABLE and escalate to reliability-auditor.

---

## Agent: context-faithfulness-engineer (Phase C.4)

  Token Budget: 30,000 tokens
  Runs: PARALLEL with hallucination-detector (Phase C.3)

  Primary Files (full content):
    1. scrum_calculator.py -- lines 533 to EOF (NEW FUNCTIONS ONLY)
       Reason: Verify docstrings match implementation (not just math).
               Check Google-style docstring completeness: Args, Returns, Raises.
    2. server.py -- lines 2199 to EOF (NEW TOOLS ONLY)
       Reason: Verify new tool docstrings match tool behavior.
               Verify validate_input() is called on all string params.
               Verify return dict keys match docstring documentation.

  Specification Source (faithfulness reference):
    3. docs/orchestration_prompt.md -- full file (all 4 categories)
       Reason: Ground truth for tool names, parameter names, return key names,
               and behavior descriptions. Faithfulness check verifies code
               matches the spec's stated intent, not just the math formulas.

  Phase Output File (WRITE):
    4. docs/outputs/phase-c-faithfulness.md (CREATE)
       Format: Per-file section. Per-function row:
               function_name | docstring_complete (Y/N) | params_documented (Y/N) |
               return_keys_documented (Y/N) | spec_aligned (Y/N) | notes

  Key Constraint Reminders:
    - Do NOT re-check math (that is hallucination-detector's job).
    - Check that docstring Args sections name every parameter.
    - Check that docstring Returns sections enumerate every key in return dict.
    - Check that docstring Raises sections document every ValueError guard.
    - Check that tool stubs in server.py call validate_input() for string params.
    - Check that pure-computation tools do NOT call agile_client (ADR-3).
    - Check that network tools DO call agile_client (ADR-4).
    - Report format is structured table, not prose.

---

## Agent: reliability-auditor (Phase D)

  Token Budget: 25,000 tokens
  Runs: AFTER C.3 and C.4 complete (sequential dependency)

  Primary Files (full content):
    1. docs/outputs/phase-c-hallucination.md (from Phase C.3)
       Reason: Input report to audit. Verify completeness of hallucination
               checks. Escalate any UNVERIFIABLE items.
    2. docs/outputs/phase-c-faithfulness.md (from Phase C.4)
       Reason: Input report to audit. Verify completeness of faithfulness
               checks.

  Reference Files (for spot-check verification):
    3. scrum_calculator.py -- lines 533 to EOF (NEW FUNCTIONS ONLY)
       Reason: Spot-check 3-5 high-risk functions against both reports.
               High-risk functions: bootstrap_bca_ci, tuckman_markov,
               ahp_score (AHP power iteration is most complex math).
    4. docs/orchestration_prompt.md -- lines 44-63 (Category 3 math specs)
       Reason: Independent ground truth for spot-check verification.

  Phase C Test Output Files (also read):
    5. tests/test_scrum_calculator.py (post-Phase-C version)
       Reason: Verify test coverage for the 3-5 spot-checked functions.
               Does test_bootstrap_bca_ci use property-based assertions?
               Does test_tuckman_markov test < 4 sprint fallback?

  Phase Output File (WRITE):
    6. docs/outputs/phase-d-reliability.md (CREATE)
       Format: PASS/FAIL verdict per function.
               Summary: total HIGH/MEDIUM/LOW/CRITICAL issues across Phase C.
               Blocking issues: any CRITICAL or HIGH that must be fixed before Phase E.
               Go/No-Go for Phase E: GO | NO-GO (with reason if NO-GO).

  Key Constraint Reminders:
    - reliability-auditor has VETO POWER. A NO-GO blocks all Phase E and F work.
    - If any CRITICAL hallucination is found (wrong formula), halt Phase E
      and return to B.1 or B.2 for correction.
    - Spot-check must cover at minimum: bootstrap_bca_ci, tuckman_markov, ahp_score.
    - Report the go/no-go verdict prominently at the TOP of the output file.

---

## Agent: security-defense-architect (Phase F.1)

  Token Budget: 30,000 tokens
  Runs: AFTER Phase D GO verdict (parallel with F.2)

  Primary Files (full content):
    1. server.py -- FULL FILE (post-B.3 version)
       Reason: STRIDE threat model requires full tool surface analysis.
               All 41 tools are in scope for threat modelling.
               Focus: new 16 tools + jira_rate_limit_status (exposes
               internal state) + jira_automation_analyzer (accepts
               user-supplied JSON/DAG -- highest injection risk).
    2. input_validator.py (full, 94 lines)
       Reason: Verify PROMPT_INJECTION_PATTERNS are sufficient for new tools.
               Verify validate_input() is called correctly in new tools.
    3. rate_limiter.py -- FULL FILE
       Reason: jira_rate_limit_status exposes _buckets dict. Verify the
               snapshot is read-only under _buckets_lock. Check for race
               conditions (documented in Risk R-07).
    4. agile_client.py -- FULL FILE (post-B.2)
       Reason: get_issue_changelog uses urllib.request with user-supplied
               issue_key. Verify URL construction is not vulnerable to
               path traversal (issue_key must be sanitised).

  Phase Output File (WRITE):
    5. docs/outputs/phase-f1-stride.md (CREATE)
       Format: STRIDE threat table per new tool.
               Columns: Tool | Threat | STRIDE_Category | Likelihood |
               Impact | Mitigation | Status (Mitigated/Open)

  Key Constraint Reminders:
    - Focus STRIDE analysis on the 16 new tools only.
      Existing 25 tools are out of scope unless a new tool interacts
      with them in a new way.
    - jira_automation_analyzer highest-risk tool: user supplies
      rules_dag as JSON string. Validate: json.loads() error handling,
      adjacency list size cap, no exec() or eval() anywhere.
    - jira_rate_limit_status: Read-only access to internal state.
      Verify _buckets_lock is acquired before reading. Document
      approximate-snapshot limitation (Risk R-07).
    - Report each OPEN threat with a concrete remediation recommendation.

---

## Agent: security-testing-engineer (Phase F.2)

  Token Budget: 30,000 tokens
  Runs: PARALLEL with security-defense-architect (Phase F.1)

  Primary Files (full content):
    1. server.py -- FULL FILE (post-B.3 version)
       Reason: Write security tests targeting all 41 tools.
               Focus on new tools with highest attack surface.
    2. input_validator.py (full)
       Reason: SAST check: verify validate_input() covers null bytes,
               length limits, and injection patterns.
    3. agile_client.py -- FULL FILE (post-B.2)
       Reason: SAST check: get_issue_changelog URL construction.
               Verify issue_key is not directly interpolated without
               sanitization.
    4. rate_limiter.py -- FULL FILE
       Reason: SAST check: verify _buckets_lock usage is correct.
    5. requirements.txt (2 lines)
       Reason: Dependency vulnerability check: mcp>=1.0.0, fastmcp>=0.1.0.
               Verify no known CVEs for these versions.

  Reference Files (pattern matching for test writing):
    6. tests/fixtures/ -- all 5 JSON files
       Reason: Construct malicious fixture variants for injection tests.
               Malicious issue_key: "../../../etc/passwd", "'; DROP TABLE --".
               Malicious rules_dag: deeply nested JSON, circular reference.

  Phase Output File (WRITE):
    7. docs/outputs/phase-f2-sast.md (CREATE)
       Format: SAST finding table.
               Columns: File | Line | CWE | Severity | Description |
               Recommendation | Status (Fixed/Open)
       Also include: DAST test results (dynamic tests against mock server).

  Key Constraint Reminders:
    - Security tests must mock all external calls (_get_config, _agile_request).
    - Test jira_automation_analyzer with malicious JSON inputs:
        rules_dag with 1000-node graph (DoS), circular reference, null bytes.
    - Test get_issue_changelog with path-traversal issue_key values.
    - Test validate_input() null-byte stripping with "\x00" injection.
    - Report each CVE/CWE with CVSS score estimate.

---

## Agent: security-compliance-auditor (Phase F.3)

  Token Budget: 20,000 tokens
  Runs: AFTER F.1 and F.2 complete (sequential dependency)

  Primary Files (full content):
    1. docs/outputs/phase-f1-stride.md (from Phase F.1)
       Reason: Review STRIDE analysis for completeness and accuracy.
               Verify all OPEN threats have assigned owners.
    2. docs/outputs/phase-f2-sast.md (from Phase F.2)
       Reason: Review SAST/DAST findings. Verify Critical/High findings
               have concrete mitigations, not just descriptions.

  Reference Files (spot-check only):
    3. server.py -- lines 2199 to EOF (new tools only)
       Reason: Spot-check 3 high-risk tools against STRIDE table:
               jira_automation_analyzer, jira_rate_limit_status,
               jira_cycle_time_analysis.
    4. input_validator.py (full)
       Reason: Verify PROMPT_INJECTION_PATTERNS completeness recommendation.

  Phase Output File (WRITE):
    5. docs/outputs/phase-f3-compliance.md (CREATE)
       Format: Compliance verdict table.
               Security Gate: PASS | FAIL (with blocking issues listed).
               Columns per finding: Finding_ID | Source_Phase |
               Severity | Resolution_Status | Auditor_Verdict
       Must include: Overall Security Gate verdict at TOP of file.

  Key Constraint Reminders:
    - Security-compliance-auditor has GATE POWER over Phase G.
      FAIL verdict blocks devops-engineer (Phase G) until resolved.
    - Any Critical or High OPEN finding from F.1 or F.2 = automatic FAIL.
    - Verify F.1 STRIDE analysis covers all 16 new tools (not just some).
    - Verify F.2 tested jira_automation_analyzer with malicious inputs.

---

## Agent: devops-engineer (Phase G)

  Token Budget: 25,000 tokens
  Runs: AFTER Phase D GO verdict AND Phase F.3 PASS verdict

  Primary Files (full content):
    1. server.py -- FULL FILE (final version)
       Reason: Run final validation gates. Verify tool count = 41.
               Verify module-level docstring updated to "Tools (41):".
               Run ASCII gate: grep -Pn '[^\x00-\x7F]' server.py
    2. scrum_calculator.py -- FULL FILE (final version)
       Reason: Run ASCII gate. Run py_compile. Count functions (expect 24).
    3. agile_client.py -- FULL FILE (final version)
       Reason: Run ASCII gate. Run py_compile. Count functions (expect 6).
    4. requirements.txt (2 lines)
       Reason: Verify ZERO changes. mcp>=1.0.0 and fastmcp>=0.1.0 only.
               No new dependencies were introduced.
    5. CLAUDE.md (root project file)
       Reason: Update "Available Tools (25 total)" -> "Available Tools (41 total)"
               in the tools section. Update the tools list to include all 16 new tools.
               Update the file structure section if scrum_calculator.py or
               agile_client.py descriptions changed.

  Phase Output File (WRITE):
    6. docs/outputs/phase-g-devops.md (CREATE)
       Format: Final validation report.
               Gate results: ASCII check | py_compile | pytest | tool count | req diff.
               Each gate: PASS | FAIL with output snippet.
               Final Status: COMPLETE | BLOCKED (with reason if BLOCKED).

  Key Constraint Reminders:
    - Run ALL validation gates from blueprint Section 5.3 in sequence:
        1. python -m py_compile scrum_calculator.py agile_client.py server.py
        2. grep -n ":=" scrum_calculator.py agile_client.py server.py
        3. grep -n "match " scrum_calculator.py agile_client.py server.py
        4. python -c "open('scrum_calculator.py','rb').read().decode('ascii')"
        5. python -c "open('agile_client.py','rb').read().decode('ascii')"
        6. python -c "open('server.py','rb').read().decode('ascii')"
        7. pytest tests/ -v
        8. diff requirements.txt (expect no change)
    - Verify backward compat gate: zero deletions in server.py lines 1-2198
      (except for the 4 targeted upgrade substitutions U1-U4).
    - Verify @mcp_tool_handler count in server.py == 41 after assembly.
    - If ANY gate fails: report BLOCKED and specify exact file + line of failure.
      Do NOT proceed to CLAUDE.md update if a gate fails.
    - CLAUDE.md update is the LAST step -- only after all gates pass.

---

## BLOCKING GATE

This plan is ACTIVE. Phase B agents (scrum-master-agent and agile-tooling-specialist)
may now be dispatched in parallel.

Dispatch order:
  PARALLEL:  scrum-master-agent (B.1) + agile-tooling-specialist (B.2)
  THEN:      python-backend-engineer (B.3)  [waits for both B.1 and B.2]
  PARALLEL:  unit-testing-specialist (C.1) + integration-testing-engineer (C.2)
             + hallucination-detector (C.3) + context-faithfulness-engineer (C.4)
             [all wait for B.3]
  THEN:      reliability-auditor (D)  [waits for C.3 and C.4]
  THEN IF GO verdict from D:
  PARALLEL:  security-defense-architect (F.1) + security-testing-engineer (F.2)
  THEN:      security-compliance-auditor (F.3)  [waits for F.1 and F.2]
  THEN IF PASS verdict from F.3:
             devops-engineer (G)

---

## CONTEXT ECONOMY NOTES

  scrum_calculator.py is 532 lines -- fits in single read within 40k token budget.
  agile_client.py is 137 lines -- trivially fits.
  server.py is 2203 lines -- requires full context for B.3 (60k budget).
  For B.1 and B.2: server.py is provided as REFERENCE only (lines 1-56 + lines 800-855).
    Total server.py reference load for B.1/B.2: ~110 lines (~1,200 tokens).
  For hallucination-detector and faithfulness-engineer: only NEW code sections
    (scrum_calculator.py lines 533+, server.py lines 2199+) are delivered.
    This avoids loading 530+ lines of already-verified existing functions.
  For reliability-auditor: only the Phase C output reports + spot-check lines.
    This minimizes redundant re-reading of source code already reviewed.
  For security agents: full server.py is needed for STRIDE surface analysis.
  For devops-engineer: full files needed for ASCII gate + pytest run.

---
END OF CONTEXT DELIVERY PLAN
